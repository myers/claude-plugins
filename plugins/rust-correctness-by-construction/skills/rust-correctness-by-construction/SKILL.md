---
name: rust-correctness-by-construction
description: >-
  Use when writing or reviewing systems / kernel / driver / embedded /
  concurrency Rust for correctness by construction, or designing an API that's
  hard to misuse — to make illegal states and concurrency bugs unrepresentable,
  rejected by the compiler rather than caught at runtime.
  Triggers: typestate, phantom/ghost/branded types, PhantomData, generativity,
  sealed traits, "parse don't validate", newtype invariants, smart constructors,
  making invalid states unrepresentable, compile-time deadlock prevention, lock
  ordering, capability/witness tokens, units of measure, verification tools
  (Loom, Kani, MIRI, Flux, Prusti, Creusot). Porting C to Rust or keeping a Rust
  crate in sync with upstream C: use the c-to-rust-port skill instead.
---

# Correctness by Construction in Rust

## What this skill is for

The central idea, attributed to Yaron Minsky: design your types so that the
states you don't want *cannot be written down*. A bug that can't be represented
can't occur. Instead of validating at runtime and hoping every call site
remembered to check, you push the invariant into the type system so the
compiler rejects the bad program before it runs — at zero runtime cost.

This skill is weighted toward systems / kernel / concurrency Rust, where the
payoff is highest: a deadlock the type checker refuses to compile is worth more
than a thousand passing tests. The flagship example is Fuchsia's Netstack3,
which encodes lock-acquisition order in the type system so any lock cycle is a
compile error — and which, after eleven months on 60 devices, had three bugs.

Two traditions feed into this and both are in scope:

1. **Type-driven API design** — typestate, newtypes, sum types, phantom/branded
   types, sealed traits, "parse don't validate". Make the *shape* of the data
   match the shape of reality.
2. **Static-analysis-as-types** — teach the compiler a property it doesn't know
   natively (lock order, permissions, proofs) by encoding it in traits and
   invariant lifetimes. Netstack3, GhostCell, capability tokens.

## How to use this skill

Name the invariant the code needs to protect, route to the matching reference
doc via the decision tree below, then read `references/applying-the-patterns.md`
to decide *how hard* to lean on the type system. Do **not** load all references
at once; each is a deep dive meant to be read when its pattern is the right tool.

### Decision tree: what invariant are you protecting?

- **"I'm porting C to Rust, or maintaining a Rust crate that stays in sync with
  a living upstream C" (which Rust tool a C idiom maps to, the faithful → prove →
  idiomatic workflow, keeping the two diffable across resyncs, reporting
  divergences)** → this is a different skill. Use **`c-to-rust-port`**, which owns
  the porting workflow and routes back here for each type-level technique.

- **"This value must satisfy a constraint that's expensive or dangerous to
  re-check" (a parsed email, a non-empty slice, an in-range index, validated
  user input at a trust boundary)** → newtypes, smart constructors, sum types,
  "parse don't validate". See `references/type-system-patterns.md` §1–§3.

- **"This object moves through a sequence of states, and some operations are
  only legal in some states" (a connection: unconnected → connected → closed; a
  builder with required fields; a GPIO pin: input vs output; a protocol
  handshake)** → typestate, the builder-typestate pattern, session types. See
  `references/type-system-patterns.md` §4 and `references/foundational-papers.md`
  (Ferrite, for protocols).

- **"This trait/state set must stay closed so I can reason about all
  implementors"** → sealed traits. See `references/type-system-patterns.md` §5.

- **"I have aliasing + mutation and need to separate *permission to mutate* from
  *the data*, or I want a brand that ties a value to one specific
  owner/arena/region" (graphs, doubly-linked lists, arenas, capability handles
  that must not be forged or mixed between contexts)** → branded/ghost types,
  generativity, GhostCell/qcell. See `references/type-system-patterns.md` §6.

- **"Locks must always be acquired in a fixed order, and I want lock-cycle
  deadlocks to be a compile error" (any multi-lock kernel/driver/netstack
  subsystem)** → static lock ordering, the Netstack3 `lock_order` approach. See
  `references/concurrency-lock-ordering.md`. **This is the centerpiece for
  systems work — read it first if concurrency is the concern.**

- **"A function should only run if the caller can prove it holds a capability /
  has done a check / is in the right context" (capability OS work, syscall
  gating, 'you may touch this hardware only with this token')** → zero-sized
  witness/proof tokens, the guard pattern. See `references/type-system-patterns.md`
  §7 and the capability sub-section in `references/concurrency-lock-ordering.md`.

- **"Numbers with units must not be mixed" (sensor fusion, physics, navigation)**
  → units-of-measure types. See `references/type-system-patterns.md` §8.

- **"The invariant is genuinely beyond what types express ergonomically"
  (functional correctness, arithmetic ranges across a whole module, weak-memory
  atomic orderings, deadlock freedom across an FFI boundary the compiler can't
  see)** → stop encoding and reach for a tool. See
  `references/verification-tools.md`.

- **"How hard should I lean on types here, and what are the implementation
  pitfalls?"** → the ladder of enforcement, when *not* to climb, and the
  working principles. See `references/applying-the-patterns.md`.

- **"Show me real systems code that does this well"** → see
  `references/exemplar-codebases.md` (Netstack3, Rust-for-Linux `pin-init`,
  Oxide Hubris, embedded HALs, `heapless`/`bbqueue`).

- **"I want the original papers / essays"** → see
  `references/foundational-papers.md`.

## Porting C to Rust is a separate skill

If your starting point is a C codebase — whether a one-time port or a Rust crate
that tracks a living upstream — the workflow (faithful + safe → prove it →
idiomatic upgrade, kept diffable across resyncs) lives in the **`c-to-rust-port`**
skill. It owns the C-idiom → Rust-tool catalog and the diff-stability discipline,
and routes back to *this* skill for the deep detail on each type-level technique.

**The idiomatic-upgrade (oxidation) pass is a behavior-preserving refactor — two
hard rules, both learned from real regressions:**

1. **Don't start oxidizing without a reasonable behavior-pinning test suite.** The
   tests are the oracle that lets you refactor safely. If the faithful port's
   tests only cover *degenerate* inputs (e.g. an RMW exercised only via
   `set`/`clear`, where `val == mask`), they pin nothing — **write the
   characterization tests first** (assert the reference's observable behavior on
   the *non-degenerate* cases), then oxidize. Oxidizing against a degenerate suite
   is oxidizing blind.

2. **The reference's behavior is the spec — do not "fix" it, and do not change
   what a test asserts.** "Make illegal states unrepresentable" becomes a *trap*
   here: a deliberate quirk of the reference can look like a bug to design out.
   Real example — an RMW that writes the caller's `val` **unmasked** (bits outside
   `mask` survive: `val | (cur & !mask)`) is intentional, not a bug; "clamping
   `val` to the mask" to make escape unrepresentable is a wire-observable
   *regression*. The faithful port's behavior-pinning tests must stay green with
   their assertions **byte-identical** — mechanical retyping (`Reg(0x10)` for
   `0x10`) is fine, but the moment you rewrite a test's *expected value*, stop:
   you changed behavior. That is a regression wearing an oxidation costume, not a
   correctness-by-construction win. (Review companion: the `faithful-port-review`
   skill checks exactly this.)

## Reference docs

- `references/type-system-patterns.md` — newtypes, sum types, parse-don't-validate,
  typestate, builder-typestate, sealed traits, phantom/branded/ghost types,
  generativity, witness tokens, const generics, units of measure.
- `references/concurrency-lock-ordering.md` — the Netstack3 `lock_order` approach
  to compile-time deadlock prevention, the `Locked` context pattern, the
  const-generic alternative and its tradeoffs, capability tokens, beyond
  Send/Sync, `pin-init` for non-movable lock types.
- `references/applying-the-patterns.md` — the ladder of enforcement, when *not*
  to climb, and working principles for implementing any of these patterns well.
- `references/foundational-papers.md` — the canonical papers and essays
  (Minsky, Wlaschin, Feldman, King; GhostCell, Ghosts of Departed Proofs,
  Ferrite, Retrofitting Typestates, Flux).
- `references/exemplar-codebases.md` — real systems/kernel code to read and
  imitate.
- `references/verification-tools.md` — Loom, MIRI, Kani, Flux, Prusti, Creusot:
  what each proves, what each can't, and when to reach for it.
