# Concurrency & Static Lock-Ordering

The highest-value application of "make illegal states unrepresentable" in
systems code: teach the compiler your lock-acquisition order so any lock-cycle
deadlock becomes a compile error, at zero runtime cost. This is the Netstack3
approach, and it's the reason this skill leans toward systems work.

## Contents
1. Why Send/Sync isn't enough
2. The Netstack3 result (why this is worth the trouble)
3. The `lock_order` mechanism, step by step
4. The `Locked` context: enforcing order at acquisition
5. Using it today: the `lock_tree` crate
6. The simpler alternative: const-generic total order
7. Tradeoffs and when this is overkill
8. Capability/context tokens for concurrency
9. `pin-init`: safely building non-movable lock types
10. Session types for protocol correctness

---

## 1. Why Send/Sync isn't enough

`Send` and `Sync` are themselves examples of teaching the compiler a property it
doesn't know natively — `Send` is an `unsafe` auto-trait used as the bound on
`thread::spawn`. But they only rule out *data races* and unsafe cross-thread
moves. They say nothing about *deadlock*: two threads each holding one lock and
waiting for the other is perfectly `Send + Sync` and perfectly deadlocked.

Deadlock from lock cycles is prevented by always acquiring locks in a consistent
global order. Traditionally that order lives in a comment or a wiki page and is
enforced by code review and runtime tools (Linux `lockdep`, Fuchsia's runtime
lock validator). The Netstack3 insight: encode the order as a *partial order on
types* so the compiler enforces it statically.

## 2. The Netstack3 result

Netstack3 is Fuchsia's from-scratch Rust network stack. Per LWN's coverage of
Joshua Liebow-Feeser's RustConf 2024 talk "Safety in an Unsafe World": the
codebase spans 63 crates and ~60 developer-years, contains more code than the
top ten crates on crates.io combined, and holds 77 mutexes across thousands of
lines. Its Go predecessor, netstack2, "had a lot of deadlocks." After the team
ran the new stack on 60 devices full-time for eleven months, Netstack3 had three
bugs. The lock-ordering type machinery is a large part of why.

The methodology Liebow-Feeser describes generalizes beyond locks —
**definition → enforcement → consumption**: attach a property to a type, enforce
it (via field privacy and a little `unsafe`) in exactly one module, then let all
consuming code rely on the type checker and stay ordinary safe Rust. Rust, in
his framing, is an "X-safe" language: you can teach it any property X.

## 3. The `lock_order` mechanism, step by step

The real crate lives in the Fuchsia tree at
`src/connectivity/network/netstack3/core/lock-order/`. Here's the shape of it.

**Step 1 — lock levels are types**, usually empty enums (zero-sized, can't be
instantiated, exist only to be reasoned about):

```rust
enum LockA {}
enum LockB {}
enum LockC {}
```

**Step 2 — describe how to acquire each lock** via a `LockFor` impl that names
the guard type and how to take it. (Simplified.)

**Step 3 — declare the order** with two traits, `LockAfter` and `LockBefore`
(duals of each other). Anchor the top of the hierarchy at the special
`Unlocked` level, then chain:

```rust
impl LockAfter<Unlocked> for LockA {}   // A may be taken first
impl_lock_after!(LockA => LockB);        // B is acquired after A
impl_lock_after!(LockB => LockC);        // C after B
```

**The cycle-detection trick is in `impl_lock_after!`.** Each invocation expands
to *two* impls — the direct edge and a *transitive blanket* impl:

```rust
// impl_lock_after!(LockA => LockB) expands to roughly:
impl LockAfter<LockA> for LockB {}
impl<X> LockAfter<X> for LockB
where
    LockA: LockAfter<X>,
{}
```

The blanket impl says "B is after everything A is after." Chain enough of these
and the transitive closure of the order is reflected in the trait system. Now if
you ever declare an edge that closes a cycle (say `LockC => LockA`), the
transitive blanket impls make `LockA: LockAfter<LockA>` derivable through *two*
different paths — **overlapping/conflicting trait implementations**, which is a
hard compile error. You cannot express a cyclic lock order. The deadlock is
unrepresentable.

All of this is zero-sized marker types and trait resolution; nothing survives to
runtime.

## 4. The `Locked` context: enforcing order at acquisition

Declaring the order is half of it. The other half is making sure code actually
*acquires* locks in that order. Netstack3 threads a context object — `Locked` —
that tracks, in its type, the deepest lock currently held.

```rust
// Root context: nothing locked yet (level = Unlocked).
let mut locked = Locked::new(&state);

// Acquire LockB; get back the guard AND a new Locked whose level is LockB,
// borrowing the old context so it can't be used to acquire out of order.
let (guard_b, mut locked_b) = locked.lock_and::<LockB>();

// From a LockB context you can only acquire locks that are LockAfter<LockB>.
let (guard_c, mut locked_c) = locked_b.lock_and::<LockC>();

// Trying to take LockA now fails to compile: LockA is not LockBefore the
// current level, i.e. `LockA: LockAfter<LockB>` does not hold.
// let (guard_a, _) = locked_b.lock_and::<LockA>(); // ERROR
```

`lock_and::<L>()` requires `L: LockAfter<CurrentLevel>` (equivalently the
current level is `LockBefore<L>`), and returns a new `Locked` borrowing the old
one — so the old context is frozen while the deeper one is live, and you cannot
acquire a shallower lock without first releasing. Out-of-order acquisition is a
type error with a message like "LockA does not implement LockBefore<LockB>".

The payoff: every multi-lock code path in the stack is checked for ordering
correctness by the compiler, every time, with no runtime cost and no reliance on
a test happening to hit the bad interleaving.

## 5. Using it today: the `lock_tree` crate

Fuchsia's `lock_order` isn't published to crates.io. A near-verbatim BSD-2
republication exists as **`lock_tree`** (`cargo add lock_tree`;
docs.rs/lock_tree; github.com/howtocodeit/lock_tree) — "named lock_tree due to a
crates.io conflict." Treat the in-tree `lock_order` rustdoc as the source of
truth and `lock_tree` as the convenient way to experiment. Do not confuse it
with the unrelated `lock_ordering` crate (a different `LockedAt`-based design) or
`locktree` (a separate linear-sequence macro).

For a from-scratch implementation in your own kernel (e.g. Asterinas/Tatara),
you don't need the crate — the pattern is ~100 lines: the two traits, the
`impl_lock_after!` macro emitting the direct + transitive blanket impls, and a
`Locked<'a, Level>` context with `lock_and`.

## 6. The simpler alternative: const-generic total order

If your locks admit a single **total** order (every pair is comparable), you
don't need the trait tower. Give each lock a `const` level number and bound
acquisition with a const comparison:

```rust
struct Locked<const LEVEL: usize>(/* ... */);

impl<const LEVEL: usize> Locked<LEVEL> {
    fn lock<const N: usize>(&mut self, m: &Mutex<T>) -> (Guard<T>, Locked<N>)
    where
        // Only acquire strictly deeper locks. Evaluated at monomorphization.
        // (Expressed via a const assertion / where-bound on N > LEVEL.)
    { /* ... */ }
}
```

This was argued at length by commenter "khim" in the LWN discussion: 77 locks is
a flat enum, and a total order is "just a number." It's far easier to read, the
error messages are simpler, and it sidesteps the O(N²) transitive-impl blowup.
The cost: it forces a *total* order even on locks that are genuinely unordered,
so it can reject safe code that the partial-order scheme would accept, and it
gives less informative names. Use const-generic levels as the *default*; reach
for the trait-based partial order only when you truly need incomparable locks.

## 7. Tradeoffs and when this is overkill

Read the LWN comment threads on "Safety in an unsafe world" (lwn.net/Articles/995814/)
and especially "Too complex for my small brain" (lwn.net/Articles/997577/) before
adopting this wholesale. Honest caveats:

- **It prevents lock *cycles*, not every deadlock.** A deadlock that crosses an
  FFI/C boundary, or that arises from a condition-variable protocol rather than
  lock acquisition order, is invisible to the type system.
- **The enforced order is a chain, slightly stronger than the true partial
  order** (analysis by LWN commenter farnz): the scheme topologically flattens
  the DAG, so it can arbitrarily order locks that "should" be unordered and
  reject some safe programs.
- **Trait resolution can blow up.** Large hierarchies produce O(N²) transitive
  impls and have caused multi-hour build times in similar schemes.
- **Reviewers found it hard.** The thread title is not ironic — several
  competent engineers found the trait machinery difficult to reason about. If
  the team can't read it, they'll route around it. Weigh that honestly.

Liebow-Feeser himself noted the simplified talk example has problems in
practice. The technique is powerful and proven at scale, but it is not free and
not universally the right call. For many codebases a const-generic total order,
plus a runtime validator (`lockdep`-style) in debug builds, is the better
balance.

## 8. Capability/context tokens for concurrency

The `Locked` context object is a *capability token* (see
`type-system-patterns.md` §7) specialized to concurrency: holding a
`Locked<Level>` is proof of "these locks and no shallower ones are held," and
the only operations available are those consistent with that proof. The same
shape generalizes to any "you may do X only in context Y" rule: pass a ZST proof
of the context, mint it only where the context is genuinely established, and
require it (by reference) on the gated operation. For a capability OS, this is
how you make a syscall that's only callable when the caller holds the right
capability — unforgeable because the token's constructor is private and gated.

## 9. `pin-init`: safely building non-movable lock types

Kernel lock primitives are frequently *self-referential* or *address-sensitive*
(a `Mutex` registered in an intrusive wait list, a `CondVar`, a `ListHead`):
once constructed they must not move, and they must be initialized *in place*.
Rust's normal "construct on the stack, then move into place" breaks this.

Rust-for-Linux's `pin-init` crate solves it: `#[pin_data]` on the struct,
`pin_init!` to describe in-place construction, and the `PinInit<Self, E>` trait
for fallible in-place init. This makes "this object was initialized in its final
location and never moved" a type-level guarantee, which is exactly what's needed
before a lock can soundly participate in the ordering scheme above. If you're
building lock types in a no_std kernel, study `pin-init` (rust.docs.kernel.org/pin_init/,
github.com/Rust-for-Linux/pin-init) and the "Safe Pinned Initialization Problem"
writeup before rolling your own.

## 10. Session types for protocol correctness

Where lock ordering is about *resource acquisition* order, session types are
about *message/protocol* order on a channel: encode the protocol so that sending
or receiving out of sequence doesn't compile. The Ferrite library (ECOOP 2022,
github.com/ferrite-rs/ferrite, crate `ferrite-session`) embeds linear and shared
session types in Rust; a program that typechecks *is* a proof of protocol
adherence. Note Rust's affine (not linear) types mean a channel can be dropped,
which Ferrite handles via a linearity encoding. Reach for this when correctness
of a stateful wire/IPC protocol is the concern; for most in-process state
machines, plain typestate (`type-system-patterns.md` §4) is lighter weight. See
`foundational-papers.md` for the paper.
