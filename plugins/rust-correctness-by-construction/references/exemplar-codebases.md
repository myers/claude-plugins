# Exemplar Codebases

Real systems/kernel/concurrency Rust that applies these patterns well. Read
these to see the techniques at production scale, and imitate their structure.

## Netstack3 + `lock_order` — the gold standard for concurrency

Fuchsia's from-scratch Rust network stack; the definitive example of
compile-time lock-ordering. The mechanism is dissected in
`concurrency-lock-ordering.md`.

- Lock machinery: `src/connectivity/network/netstack3/core/lock-order/`
  (`src/lib.rs`, `src/relation.rs`) in the Fuchsia tree
  (fuchsia.googlesource.com / cs.opensource.google).
- Rustdoc: fuchsia-docs.firebaseapp.com/rust/lock_order/
- Design docs: `src/connectivity/network/netstack3/docs/` — especially
  `STATIC_TYPING.md`, `TENETS_AND_DESIGN_DECISIONS.md`, `PUB_CRATE.md`.
- Talk: Joshua Liebow-Feeser, RustConf 2024, "Safety in an Unsafe World"
  (youtube.com/watch?v=qd3x5MCUrhw; slides at joshlf.com/talks-and-publications/).
- Standalone republication to experiment with: `lock_tree` (docs.rs/lock_tree).

*What to steal:* the definition→enforcement→consumption split; the
`LockAfter`/`LockBefore` trait pair with transitive blanket impls; the `Locked`
context threading. Directly applicable to a kernel like Asterinas/Tatara.

## Rust-for-Linux — pinned init, kernel refcounting, driver typing

- **`pin-init`** (github.com/Rust-for-Linux/pin-init; rust.docs.kernel.org/pin_init/)
  and the "Safe Pinned Initialization Problem" writeup
  (rust-for-linux.com/the-safe-pinned-initialization-problem). In-place,
  fallible construction of non-movable, self-referential types (Mutex, CondVar,
  intrusive `ListHead`) via `#[pin_data]` / `pin_init!` / `PinInit<Self, E>`.
  *What to steal:* how to make "initialized in place, never moved" a type-level
  fact before a lock can participate in an ordering scheme.
- **Kernel `Arc` / `Ref`** — reference counting backed by C `refcount_t` with
  saturating (not panicking) overflow behavior; a study in wrapping a C
  primitive in a sound Rust type.
- **Security impact study:** "Rust for Linux: Understanding the Security Impact
  of Rust in the Linux Kernel," ACSAC 2024 (par.nsf.gov/servlets/purl/10603953).
  Quantifies which driver vulnerability classes Rust eliminates automatically
  vs. which still need idioms. *What to steal:* a sober map of what the type
  system buys you in driver code and what it doesn't.

## Oxide Hubris / Humility — memory-isolated task RTOS

hubris.oxide.computer; cliffle.com/blog/on-hubris-and-humility/;
oxide.computer/blog/hubris-and-humility. A ~2000-line-kernel RTOS where all
tasks are fixed at build time (no `fork`, no dynamic allocation), IPC is
type-safe via the Idol IDL, and `probe_for_read` returns `Option<&[T]>` so
"this memory is valid" is a type-level fact — with the returned borrow
preventing memory-map mutation while the slice is live. The Stanford CS242
"Type Safety" lecture (stanford-cs242.github.io/f18/lectures/07-1-sergio.html)
uses Oxide-adjacent work to frame "types as proof witnesses." *What to steal:*
build-time task topology as unrepresentable-misconfiguration; witness-returning
accessors.

## Embedded HALs — typestate at its most idiomatic

The Embedded Rust Book's GPIO pattern
(doc.rust-lang.org/stable/embedded-book/design-patterns/hal/gpio.html and the
"Typestate Programming" chapter at
docs.rust-embedded.org/book/static-guarantees/typestate-programming.html), plus
real HAL crates (`embedded-hal`, the stm32 family). Pins are zero-sized types
parameterized by mode (`Input<Floating>`, `Output<PushPull>`, ...), state traits
are sealed, and `into_input`/`into_output` consume and return the
re-typed pin. The eCorax "GPIO war" post (ecorax.net/macro-bunker-1/) shows the
const-generic refinement `Pin<MODE, const PORT: char, const N: u8>` and the
macros used to fight typestate combinatorial explosion. *What to steal:* the
canonical small typestate; type-erasure escape hatches for when you must move a
property to runtime.

## Cliffle's writing & `lilos`

- **"The Typestate Pattern in Rust"** (cliffle.com/blog/rust-typestate/) — the
  definitive typestate explainer; the three requirements and real-world examples.
- **`lilos`** (cliffle.com) — a tiny async embedded OS that reached 1.0, with
  cancellation-safe async APIs. *What to steal:* a small, readable codebase
  showing typestate and async-correctness invariants together.

## `heapless` / `bbqueue` — capacity and access in the type

- **`heapless`** — fixed-capacity collections (`Vec`, `String`, `pool`) whose
  capacity is a const generic in the type and which never allocate; ideal for
  no_std. *What to steal:* capacity-in-the-type, allocation impossible by
  construction.
- **`bbqueue`** — lock-free SPSC bip-buffer where reads/writes go through grant
  tokens (`GrantR`/`GrantW`) that are the only handles to the buffer regions, so
  misuse (writing where you may only read, or double-committing) doesn't
  typecheck. *What to steal:* grant-token (capability) design for a concurrent
  data structure.

## Quick map: codebase → primary technique

- Compile-time lock ordering → **Netstack3 / `lock_order`**
- In-place init of non-movable lock types → **Rust-for-Linux `pin-init`**
- Witness-returning memory accessors, build-time topology → **Oxide Hubris**
- Idiomatic small typestate → **embedded HAL GPIO**, **Cliffle**
- Capacity/grant tokens in concurrent structures → **`heapless`**, **`bbqueue`**
