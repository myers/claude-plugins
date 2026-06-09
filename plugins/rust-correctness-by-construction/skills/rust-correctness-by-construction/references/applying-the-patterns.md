# Applying the Patterns: Ladder, Limits, Principles

Read this once you've picked an invariant to protect (via the decision tree in
`SKILL.md`) and are deciding *how hard to lean on the type system* and *how to
implement it well*. It is technique-agnostic — it applies regardless of which
specific pattern doc you're working from.

## The ladder of enforcement

For any given invariant, prefer the highest rung you can reach ergonomically.
Climbing costs design effort; the return is that whole classes of bugs stop
being expressible. But each rung also costs flexibility and readability, so
don't climb past the point where the team can still maintain the code.

1. **Runtime check** — `assert!`, `if !valid { return Err(..) }`. Always
   available, zero design cost, but the check can be forgotten and the failure
   is a runtime event.
2. **Newtype + smart constructor** — validate *once* at construction, then the
   type itself is the evidence. (`parse, don't validate`.) Cheap and high-value;
   usually the right default.
3. **Sum types** — replace "flag + maybe-null field" products with an enum so
   illegal combinations can't be written.
4. **Typestate** — move the state into a type parameter so the *set of available
   methods* changes with state and bad transitions don't compile.
5. **Branded / ghost types** — tie values to a unique invariant lifetime so they
   can't be mixed across owners/arenas, and separate permission from data.
6. **Static relations between types** — encode a partial order (lock ordering)
   or a proof obligation in the trait system so violations are conflicting/
   missing impls, i.e. compile errors.
7. **External verification** — when the property exceeds the type system, prove
   it with Kani / Flux / Prusti / Creusot, or stress it with Loom / MIRI.

## When NOT to climb

Types are not free. Push back (gently) and stay on a lower rung when:

- **The state space is large and irregular.** Typestate shines for a handful of
  states with clear transitions. For many states with a dense transition matrix,
  the marker-type and impl explosion hurts more than it helps; an enum + runtime
  check, or a generated state machine, may be clearer. (See Yoshua Wuyts on the
  limits, in `foundational-papers.md`.)
- **The invariant must hold across an FFI / hardware boundary.** The compiler
  can't see past `extern "C"` or an MMIO write; a type-level guarantee there is
  false comfort. Document and check at the boundary, verify with tooling.
- **The encoding would be write-only.** If a teammate (or future-you) can't read
  the trait bounds, the safety is illusory because people will route around it
  with `unsafe` or clones. The LWN "too complex for my small brain" thread
  (linked in the concurrency doc) is the cautionary tale: a sound scheme that
  several expert reviewers found hard to reason about.
- **A simpler encoding gives the same guarantee.** E.g. for total lock orders, a
  `const`-generic level number can replace a tower of traits. Reach for the
  blanket-impl partial order only when you genuinely need a partial (not total)
  order. The concurrency doc covers this tradeoff explicitly.

## Working principles when applying these patterns

- **Encode the property where it's *defined*, enforce it in *one* module, then
  let the rest of the codebase lean on the type checker.** This
  definition → enforcement → consumption split (Liebow-Feeser) keeps `unsafe` and
  tricky invariants in one auditable place while the consuming code stays
  ordinary safe Rust.
- **Make the illegal state fail at construction, not at use.** A
  `NonEmpty<T>` that can only be built from at least one element beats a `Vec<T>`
  plus a "remember it's non-empty" comment.
- **Consume the old state on transition.** Typestate only works if the
  transition method takes `self` by value, so the stale handle can't be reused.
- **Prefer zero-sized markers.** Marker types (`enum Locked {}`, unit structs)
  and `PhantomData` compile away entirely, so type-level safety has no runtime
  footprint — critical in kernel/embedded contexts.
- **Cite the boundary.** When you stop at a lower rung, say so in a comment and
  name what still has to be checked at runtime or by a tool.
