# Type-System & API-Design Patterns

Techniques for making the *shape* of your data match the shape of reality, so
illegal values and illegal operations don't typecheck. Ordered roughly by the
ladder of enforcement.

## Contents
1. Newtypes & smart constructors
2. Sum types over product-with-flags
3. Parse, don't validate
4. Typestate (and builder-typestate)
5. Sealed traits
6. Phantom, branded & ghost types (generativity, GhostCell, qcell)
7. Zero-sized witness / capability tokens
8. Const generics & units of measure

---

## 1. Newtypes & smart constructors

A newtype is a single-field tuple struct with a *private* field plus a
constructor that's the only way in. The constructor validates once; afterward
the type itself is proof the invariant holds, so no downstream code re-checks.

```rust
pub struct Email(String); // field is private to this module

impl Email {
    pub fn parse(raw: &str) -> Result<Self, EmailError> {
        if raw.contains('@') && /* ...real validation... */ true {
            Ok(Email(raw.to_owned()))
        } else {
            Err(EmailError::Malformed)
        }
    }
    pub fn as_str(&self) -> &str { &self.0 }
}
```

Now a function that takes `Email` can never receive an unvalidated string. The
standard library ships this idea as `NonZeroU32`, `NonZeroUsize`, etc.: the
"can't be zero" invariant lives in the type, which also lets the compiler niche-
optimize `Option<NonZeroU32>` down to a bare `u32`.

Use newtypes also to prevent *unit confusion* between values of the same
primitive type: `struct Meters(f64)`, `struct Seconds(f64)` — passing one where
the other is expected becomes a type error. (For full dimensional analysis, see
§8.)

**Systems angle:** wrap raw register values, physical addresses, and indices in
newtypes (`struct PhysAddr(u64)`, `struct Pfn(usize)`) so you can't accidentally
pass a virtual address where a physical one is required, or add a byte offset to
a page-frame number.

## 2. Sum types over product-with-flags

The classic Minsky/Wlaschin transformation. A struct with a discriminant flag
plus fields that are only meaningful for some flag values admits illegal states:

```rust
// BAD: nothing stops `is_connected = false` with a live socket,
// or `is_connected = true` with `socket = None`.
struct Connection {
    is_connected: bool,
    socket: Option<Socket>,
    disconnect_reason: Option<String>,
}
```

Replace the product-with-flags with a sum type so only the legal combinations
can be written:

```rust
enum Connection {
    Disconnected { reason: Option<String> },
    Connected { socket: Socket },
}
```

Now `Connected` without a socket is unrepresentable, and you can't read a
`disconnect_reason` off a live connection. The compiler's exhaustiveness check
forces every `match` to handle both arms. Wlaschin's canonical example: a
contact that must have an email *or* a postal address (or both) but never
neither — model it as an enum, not three nullable fields.

## 3. Parse, don't validate

Alexis King's framing (see `foundational-papers.md`). A *validator* checks data
and returns `bool`/`Result<(), E>`, throwing away what it learned — so every
later use has to re-check or trust a comment. A *parser* checks data and returns
a *more precisely typed value* that carries the evidence forward.

```rust
// validate: returns nothing useful; the knowledge evaporates.
fn validate_non_empty(v: &[i32]) -> Result<(), Error> { /* ... */ }

// parse: the return type proves non-emptiness for all later code.
fn parse_non_empty(v: Vec<i32>) -> Result<NonEmpty<i32>, Error> { /* ... */ }
```

Maxims to apply:
- **Use a data structure that makes illegal states unrepresentable.** Reach for
  `NonEmpty`, `NonZero*`, a refined newtype, or an enum before reaching for a
  runtime guard.
- **Push the burden of proof upward as far as possible, but no further.** Parse
  at the trust boundary (deserialization, syscall entry, FFI surface), so the
  core operates only on already-validated types. Don't push validation past the
  point where you still have the raw input to reject.
- **Avoid "shotgun parsing"** — validation logic interleaved with processing
  logic scattered across the code. Concentrate it at the boundary.

## 4. Typestate (and builder-typestate)

Typestate encodes a state machine in a type parameter, so the *set of methods
available* changes with the state and illegal transitions fail to compile. Three
requirements (Cliffle): (a) operations are only available in certain states,
(b) the state is encoded at the type level, (c) transitions *consume* the old
state value.

```rust
use core::marker::PhantomData;

// Zero-sized state markers.
pub struct Idle;
pub struct Armed;
pub struct Firing;

pub struct Reactor<S> {
    // ...real fields...
    _state: PhantomData<S>,
}

impl Reactor<Idle> {
    pub fn new() -> Self { Reactor { _state: PhantomData } }
    pub fn arm(self) -> Reactor<Armed> { Reactor { _state: PhantomData } }
}

impl Reactor<Armed> {
    pub fn fire(self) -> Reactor<Firing> { Reactor { _state: PhantomData } }
    pub fn disarm(self) -> Reactor<Idle> { Reactor { _state: PhantomData } }
}
```

`reactor.fire()` only compiles on a `Reactor<Armed>`; calling it on `Idle` is a
type error, and because `arm`/`fire` take `self` by value the pre-transition
handle is consumed and can't be reused. The markers are zero-sized, so this is
genuinely zero-cost.

Real-world typestate you already use: RAII guards, `serde::Serializer` (each
method returns the next legal type), iterators.

**Builder-typestate** applies the same trick to enforce required fields at
compile time — `build()` only exists once every required field has been set:

```rust
pub struct Builder<HasName, HasUrl> {
    name: Option<String>,
    url: Option<String>,
    _m: PhantomData<(HasName, HasUrl)>,
}
// `build` is implemented only for Builder<Set, Set>, so forgetting a
// required field is a compile error, not a runtime panic.
```

The `typed-builder` and `typestate` crates generate this machinery; the
`typestate` proc-macro DSL (`#[typestate]`, `#[automaton]`, `#[state]`) can even
emit a state-diagram. See `exemplar-codebases.md` for the embedded-HAL GPIO
version (pin modes as typestate) and its const-generic refinement.

**Caution:** typestate scales well to a few states with clear transitions. For a
dense transition matrix or many states, the marker/impl count explodes; consider
an enum + runtime check or a generated machine instead.

## 5. Sealed traits

A sealed trait can be *named* and used as a bound by downstream code but cannot
be *implemented* outside your crate. This lets you (a) treat the set of
implementors as closed and exhaustive, (b) add methods later without breaking
callers, and (c) build typestate marker traits nobody can subvert.

```rust
mod private { pub trait Sealed {} }

pub trait LockLevel: private::Sealed {
    // methods you can add freely later
}

pub struct LevelA;
impl private::Sealed for LevelA {}
impl LockLevel for LevelA {}
// Downstream crates can write `T: LockLevel` bounds but cannot add new
// LockLevel impls, because they can't name `private::Sealed`.
```

The `sealed` crate provides `#[sealed]` for traits and impls if you prefer to
skip the boilerplate. Sealing is the standard companion to typestate marker
traits and to the lock-level traits in `concurrency-lock-ordering.md`.

## 6. Phantom, branded & ghost types

### PhantomData

`PhantomData<T>` is a zero-sized field that makes a type "behave as if" it owns
or borrows a `T` without storing one. Three uses: carry an otherwise-unused type
or lifetime parameter (the typestate marker in §4); control variance; and act as
a proof/brand carrier. Variance idioms for an *invariant* lifetime (needed for
branding) are `PhantomData<fn(&'a ()) -> &'a ()>` (invariant via mixed
variance) or `PhantomData<Cell<&'a ()>>`.

### Branding with generative lifetimes

A *brand* ties a value to one specific provenance so values from different
sources can't be mixed, even though they have the same type. The trick (from
Haskell's `ST` monad) is a lifetime that is *invariant* and *generative* —
freshly minted per call and never unifiable with any other. The `generativity`
crate packages this:

```rust
use generativity::{make_guard, Id};

fn example() {
    make_guard!(guard);     // mints a unique invariant brand 'id
    let id: Id = guard.into();
    // Two separate make_guard! sites produce brands that the type checker
    // refuses to unify, so an index/handle branded with one can never be
    // used with the other's container.
}
```

Use branding for arena indices that must not be used with the wrong arena, for
"this handle came from this specific allocator/region," and as the foundation
for GhostCell.

### GhostCell / qcell: separating permission from data

GhostCell splits a collection's *permission to mutate* (a `GhostToken<'id>`)
from its *data* (`GhostCell<'id, T>`). A single token, branded with a unique
`'id`, grants safe interior mutability over an entire graph or doubly-linked
list with zero per-cell overhead, and even allows concurrent unsynchronized
*reads*. Borrowing the token `&mut` gives exclusive mutation of all cells with
that brand; borrowing it `&` gives shared read access. Aliasing-xor-mutation is
preserved at the token, so the data structure needs no `RefCell` runtime checks
and no `unsafe` at the call site.

The `qcell` crate is the production-ready family:
- `LCell` / `LCellOwner` — the lifetime-branded, GhostCell-style variant.
- `QCell` — owner identified by a runtime id (one owner, many cells).
- `TCell` / `TLCell` — owner identified by a marker type.

Reach for these when you have a heavily-aliased mutable structure (graphs,
intrusive lists, arenas) and want to avoid both `RefCell` runtime panics and
`unsafe`. See the GhostCell paper in `foundational-papers.md` for the soundness
proof.

## 7. Zero-sized witness / capability tokens

A *witness* (or capability token) is a value whose mere existence proves
something was checked or that the holder is permitted to do something. Make it
zero-sized so it's free, and make its constructor the only place the check
happens.

```rust
// Only `enter_critical` can mint a CriticalSection token; functions that
// require interrupts-off take `&CriticalSection`, so they cannot be called
// outside one — and the token is ZST, so it costs nothing.
pub struct CriticalSection(());

pub fn with_critical<R>(f: impl FnOnce(&CriticalSection) -> R) -> R {
    disable_interrupts();
    let cs = CriticalSection(());
    let r = f(&cs);
    enable_interrupts();
    r
}

pub fn touch_shared_hw(_proof: &CriticalSection) { /* safe: irqs are off */ }
```

This generalizes the guard pattern (a `MutexGuard` is simultaneously a proof
"the lock is held" and the only handle to the protected data) and is the natural
encoding for capability-based systems: a function that needs a capability takes
the capability token by reference, and tokens are unforgeable because their
constructors are private and gated. For the lock-context version of this idea —
where the token also carries *which locks are held* so ordering is checked — see
`concurrency-lock-ordering.md`.

Rust-for-Linux uses a related trick: `probe_for_read` returns
`Option<&[T]>`, turning "this user pointer is valid" into a type-level fact, and
the returned borrow prevents the memory map from being mutated while the slice
is live.

## 8. Const generics & units of measure

### Const generics for size/shape invariants

Put sizes and shapes in the type so mismatches are compile errors:

```rust
struct Matrix<const R: usize, const C: usize> { data: [[f64; C]; R] }

impl<const R: usize, const K: usize> Matrix<R, K> {
    fn mul<const C: usize>(self, rhs: Matrix<K, C>) -> Matrix<R, C> { /* ... */ }
    // Inner dimensions must match by construction; a shape error won't compile.
}
```

`const { assert!(...) }` blocks let you attach compile-time-evaluated invariants
to monomorphized code — useful for "this buffer size must be a power of two"
style checks. `heapless` uses const-generic capacities so a fixed-size collection
carries its capacity in the type and never allocates.

### Units of measure

The `uom` crate gives zero-cost dimensional analysis over the SI/ISQ system:

```rust
use uom::si::f64::{Length, Time, Velocity};
use uom::si::{length::kilometer, time::second};

let d = Length::new::<kilometer>(5.0);
let t = Time::new::<second>(15.0);
let v: Velocity = d / t;   // typechecks: length / time = velocity
// let bad = d + t;        // compile error: can't add length to time
```

Quantities are newtypes over a storage float with phantom dimension exponents,
so the dimension algebra happens entirely at compile time and the runtime
representation is just the number. Use it for sensor fusion, navigation, and any
physics-adjacent code where a unit mix-up is the classic expensive bug. The
`yaiouom` crate is an extensible, linter-checked alternative.
