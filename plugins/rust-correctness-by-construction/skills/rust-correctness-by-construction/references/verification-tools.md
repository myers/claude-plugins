# Verification Tools (When Types Aren't Enough)

The type system is the first line of defense and the only one that's zero-cost
and always-on. But some invariants exceed what types express ergonomically:
functional correctness, arithmetic ranges across a whole module, weak-memory
atomic orderings, deadlock freedom across an FFI boundary the compiler can't
see. When you hit that wall, stop encoding and reach for a tool.

Crucially, **none of these replaces the others, and none is a substitute for
good types** — they cover the residue the type system can't reach. Each has a
soundness boundary; know it.

## Quick selection guide

| Concern | Reach for | Cost | Guarantee |
|---|---|---|---|
| Lock-free / atomics correctness under weak memory | **Loom** | Use loom's atomics under `#[cfg(loom)]` | Permutes interleavings; not sound or complete |
| Undefined behavior in `unsafe` (aliasing, init, data races) | **MIRI** | Run tests under MIRI | Flags UB on executed paths; can't prove absence |
| Bounded functional properties of safe *sequential* code | **Kani** | Write proof harnesses | Proof up to a bound; **no concurrency support** |
| Cheap value refinements / ranges | **Flux** | Lightweight annotations | Refinement types; inference keeps it light |
| Deep functional correctness (sortedness, etc.) | **Prusti** / **Creusot** | Heavier specs | Deductive proof |

## Loom — concurrency permutation testing

github.com/tokio-rs/loom; docs.rs/loom. Exhaustively explores thread
interleavings under the C11 memory model, with state-reduction to tame the
combinatorial blowup. You write the data structure against loom's drop-in
replacements for `std`'s atomics/`UnsafeCell`/threads under `#[cfg(loom)]`, then
run a test that spawns the threads; loom runs every meaningful interleaving.

**Soundness boundary (important):** loom treats `SeqCst` as `AcqRel` (can raise
false alarms), and does not fully explore load-buffering behavior (so it can
*miss* bugs). It is neither sound nor complete — it's a very good bug-finder, not
a proof. The Tokio ecosystem standard for vetting lock-free code. matklad's
"Properly Testing Concurrent Data Structures"
(matklad.github.io/2024/07/05/properly-testing-concurrent-data-structures.html)
derives the idea from first principles.

*Use when:* you wrote a lock-free structure or hand-rolled atomics and need
confidence the orderings are right. This is the natural complement to the
*deadlock*-prevention of `concurrency-lock-ordering.md`: lock ordering stops
cycles statically; loom stress-tests the memory orderings types can't see.

## MIRI — undefined-behavior interpreter

github.com/rust-lang/miri. An interpreter for Rust's mid-level IR that detects
UB as it executes: out-of-bounds, use-after-free, invalid values, data races,
and aliasing violations under Stacked Borrows / Tree Borrows. Run your existing
test suite under MIRI to vet `unsafe` blocks.

**Soundness boundary:** MIRI only sees UB on the paths your tests actually
execute (and the non-deterministic choices it explores). It cannot prove your
`unsafe` is sound in general — green MIRI means "no UB on these runs," not
"correct." Still the single best routine check for any crate with `unsafe`.

## Kani — bounded model checking

model-checking.github.io/kani/. Encodes program executions as SAT/SMT problems
and verifies assertions over *all* inputs up to a bound (loop unwinding depth,
input size). You write proof harnesses with `kani::any()` symbolic inputs and
`assert!`/`kani::assume`. Within the bound, a passing harness is a proof.

**Soundness boundary:** results hold only up to the chosen bound, and **Kani
does not support concurrency** — it warns and analyzes concurrent code as if
sequential. Use it for the safe, sequential, arithmetic-heavy core (parsers,
encoders, index math), not for your locking.

## Flux — refinement (liquid) types

arxiv.org/abs/2207.04034; rust-formal-methods.github.io. A rustc plugin adding
refinement types: attach logical predicates to types (`i32{v: v > 0}`,
length-indexed slices) and the checker discharges them via SMT, with inference
that keeps annotation overhead low. Lighter than Prusti/Creusot; aimed at ranges,
indices, and similar "almost a type" properties. Used to verify process
isolation in Tock OS. *Use when:* you want array-bounds / range invariants
checked without writing full functional specs, and want it to feel like an
extension of the type system rather than a separate proof effort.

## Prusti & Creusot — deductive functional verification

- **Prusti** (Astrauskas et al., "The Prusti Project," NASA Formal Methods 2022)
  — built on the Viper backend; supports deep functional specs (pre/postconditions,
  invariants, e.g. proving a sort produces a sorted permutation) at higher
  annotation cost.
- **Creusot** (Denis, Jourdan, Marché) — deductive verification via Pearlite, a
  spec language designed to work *with* Rust ownership using prophecy variables
  for mutable borrows; compiles to Why3.

*Use when:* you need machine-checked functional correctness of an algorithm and
are willing to invest in specifications — certification contexts, crypto, core
data-structure invariants.

## How this fits the ladder

The skill's ladder of enforcement ends at "external verification." Apply it in
this order so you only pay for what the cheaper rungs couldn't deliver:

1. Encode what you can in **types** (the rest of this skill). Zero cost, always
   on, prevents the bug from being written.
2. Run **MIRI** over your test suite if there's any `unsafe`. Cheap, routine.
3. For lock-free/atomic code, add **Loom** tests. For lock *ordering*, prefer the
   static scheme in `concurrency-lock-ordering.md`.
4. For arithmetic/index invariants the types don't capture, add **Flux**
   refinements (light) or **Kani** harnesses (bounded proof, sequential only).
5. For deep functional correctness, invest in **Prusti** or **Creusot**.

Always say, in a comment, which rung a given invariant rests on and what remains
unchecked — so the next reader knows where the guarantees stop.
