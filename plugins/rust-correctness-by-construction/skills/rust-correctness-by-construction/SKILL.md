---
name: rust-correctness-by-construction
description: >-
  Use when writing or reviewing systems / kernel / driver / embedded /
  concurrency Rust for correctness by construction, designing an API that's hard
  to misuse, porting C to Rust, or maintaining a Rust port against a living
  upstream C (diffing the two to catch port bugs or absorb upstream changes) — to
  make illegal states and concurrency bugs unrepresentable, rejected by the
  compiler rather than caught at runtime.
  Triggers: typestate, phantom/ghost/branded types, PhantomData, generativity,
  sealed traits, "parse don't validate", newtype invariants, smart constructors,
  making invalid states unrepresentable, compile-time deadlock prevention, lock
  ordering, capability/witness tokens, units of measure, verification tools
  (Loom, Kani, MIRI, Flux, Prusti, Creusot), or a C idiom (tagged union,
  goto-cleanup, ops struct, kref/refcount, intrusive list, void* context, NULL,
  errno, buffer cast) that needs the right Rust tool.
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

- **"I'm porting C to Rust and want to know which Rust tool a given C idiom maps
  to" (tagged unions, goto-cleanup, ops structs, kref/refcount, intrusive lists,
  void* context, NULL, errno, buffer casts)** → the C-idiom catalog, phased for
  faithful-translation vs. idiomatic-upgrade. See
  `references/c-to-rust-translation.md`. **Start here for any port; it owns the
  porting workflow and routes to the other docs for each upgrade.**

- **"I'm maintaining a Rust port against a *living* upstream C — re-syncing
  periodically and diffing the two to catch port bugs or absorb upstream
  changes, and I need to know which correctness upgrades won't wreck
  diff-ability"** → the diff-stability axis: which CbC techniques are local
  (safe to keep) vs. structural (defer or fork), how to gate on upstream churn,
  and how to report divergences. See `references/c-to-rust-translation.md`
  ("Diff-stability" and "Reporting C↔Rust divergences").

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

## Porting C is a primary use case

It has its own discipline — the "make illegal states unrepresentable" tools can
actively *hurt* if applied too early — so the full three-phase workflow
(faithful + safe → prove it → idiomatic upgrade) lives in
`references/c-to-rust-translation.md`. **Start there for any port.** The short
version: produce a sound translation that stays structurally close to the C so
the two can be diffed (apply only translations that are simultaneously safe *and*
faithful; defer the cleverer upgrades to a TODO list); establish behavioral
equivalence with the original before touching idioms; then work the TODO list one
type-level upgrade at a time, re-running the oracles after each.

## Reference docs

- `references/c-to-rust-translation.md` — **entry point for any C port.** A
  C-idiom → Rust-tool catalog with a quick-lookup table, the full
  faithful → prove → idiomatic-upgrade workflow, reading ownership intent out of
  C conventions, and what not to upgrade.
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
