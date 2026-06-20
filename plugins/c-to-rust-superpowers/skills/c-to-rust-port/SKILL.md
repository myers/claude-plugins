---
name: c-to-rust-port
description: >-
  Use when creating or maintaining a Rust port of a C codebase — especially a
  Rust crate that must stay in sync with upstream C long-term, where you re-sync
  periodically and diff C↔Rust to catch port bugs or absorb upstream changes.
  Covers the faithful → prove → idiomatic workflow, deciding which correctness
  upgrades are safe to keep without wrecking diff-ability (stay light on
  correctness-by-construction), gating structural changes on upstream churn, and
  reporting divergences.
  Triggers: porting C to Rust, wrapping a C library in Rust, keeping a Rust port
  in sync with upstream C, diffing C against Rust, differential / behavioral
  equivalence testing, or a C idiom (tagged union, goto-cleanup, ops struct,
  kref/refcount, intrusive list, void* context, NULL, errno, buffer cast,
  container_of, bitflags, MMIO, sentinel) that needs the right Rust mapping. For
  the deep type-system technique catalog, see the rust-correctness-by-construction
  skill.
---

# Creating & Maintaining a C → Rust Port

## What this skill is for

Porting C to Rust, and — the harder, longer job — keeping a Rust crate **in sync
with a living upstream C** that other people keep changing. You re-sync
periodically, diff your Rust against the new C, and either fix a port bug or
absorb an upstream change. That ongoing diff is the constraint everything else
serves.

This skill owns the **process**. The deep catalog of *which type encodes which
invariant* (typestate, branded types, lock-ordering, units, verification tools)
lives in the **`rust-correctness-by-construction`** skill; this one tells you how
to run a faithful translation, prove it, and decide how far to push those
techniques without making the next resync miserable.

## Governing principle: stay light on CbC

Correctness-by-construction is a ladder, and on a *living* port you usually want
to stay near the bottom of it. The reason is **diff-stability**: every structural
type-level upgrade scrambles the line-for-line correspondence you rely on every
resync, so a clever refactor you do once is a cost you pay on *every* future
upstream patch to that region.

So the default here is the opposite of the general CbC skill's "lean as hard on
types as the team can maintain." Here: **adopt the upgrades that are local (they
survive resync for free), and defer the structural ones unless that subsystem is
frozen upstream.** Locality, not maximal safety, is the optimization target.

## Governing principle: port the structure, not just the statements

A faithful port is **per-reference-function**: each function you write ports *one*
reference function, cites it (`// C: <ref>:<fn>`), and is checked against it. The
moment you write a function with **no single reference counterpart** — one you
assembled from pieces of three reference functions because it "reads cleaner as
one routine" — you have built something with **no oracle**. Nothing checks its
ordering or its conditionality, because there is no single reference to diff it
against.

This bites hardest when the reference's behavior comes from a **structure**, not a
straight line: a state machine (`switch (state)`), a callback fired on a state
*transition*, behavior split across layers (a hub driver + a bus callback + the
core). **The control flow and the state-conditions ARE the behavior.** Flattening
them into one linear, unconditional procedure is the same bug as dropping a
barrier — you dropped the *ordering* and the *gating*. A mock can't catch it: the
mock completes every step successfully regardless of state, so the flattened
bundle passes every test and fails on the real counterpart (the canonical case: a
device `reset_device` that bundles the reference's hub-driven port-reset +
state-transition Reset-Device + `xhci_set_address`'s `switch (state)` EP0 re-arm
into one straight-line routine — green mock, dead EP0 on silicon).

Two rules fall out, and both are Phase-1 faithfulness, not oxidation:

1. **Preserve the reference's structure.** If the reference gates a step on state,
   gate it. If it fires a step from a callback on a transition, don't run it
   unconditionally inline. If it splits work across layers, keep the seam. Port
   each reference function; let the **same call structure** compose them.
2. **The one-liner you can't explain is the one you must keep.** A `trb_halted = 1`
   that looks like skippable internal bookkeeping is exactly what a "tidy" bundle
   drops and exactly the whole bug. A reference step survives until a *written*
   reason clears it — not until it looks unnecessary.

(This is the impl-side twin of `faithful-port-review`'s **class 4 — Structure /
state-machine collapse**. The reviewer catches the flattened bundle; this
principle stops you writing it.)

## The workflow at a glance

The full discipline — phasing, the lookup table, per-idiom mappings, the
diff-stability tags, and the reporting recipe — is in
`references/translation-catalog.md`. The shape of it:

1. **Phase 1 — faithful + safe.** Sound (no UB; `unsafe` behind a checked
   boundary), behavior-preserving, and structurally close enough to the C to diff
   side by side. Resist cleverness. **One ported function ⇄ one reference
   function** — keep the reference's structure (state gating, transition
   callbacks, layer seams); a routine assembled from several reference functions
   has no oracle (see *port the structure, not just the statements*).
2. **Phase 1.5 — prove it.** Establish behavioral equivalence before touching
   idioms (differential/behavioral oracles, MIRI over `unsafe`, Loom over atomics
   — see the CbC skill's `verification-tools.md`).
3. **Phase 2 — idiomatic upgrade**, gated by **diff-stability + upstream churn**:
   - Adopt every **[D-light]** upgrade freely (local; survives resync).
   - Gate **[D-mod]/[D-heavy]** upgrades on `git log` churn of the C file — hot
     files stay diff-light only; cold/stable subsystems can take the structural
     treatment.
   - When you do take a [D-heavy] upgrade, leave an **anchor comment**
     (`// C: fn() err_label:`) so the next upstream diff has a landing point.
4. **Report only what needs action** (see the catalog's reporting recipe):
   divergences that need a fix or a decision, terse, no "what's correct" section.

## Where to look

- `references/translation-catalog.md` — the C-idiom → Rust-tool lookup table, the
  22 per-idiom mappings tagged on both the phase axis (`[P1]/[P2]`) and the
  diff-stability axis (`[D-light]/[D-mod]/[D-heavy]`), the diff-stability lists +
  churn-gating workflow, reading ownership intent out of C, what *not* to upgrade,
  and the divergence-reporting recipe.

## Execution & review

Planning a port uses `superpowers:writing-plans` — and **this method shapes that
plan** (the phasing, the per-unit C reference, the diff-stability gating all land
in the plan). The review gate is the **`faithful-port-reviewer`** template in the
sibling **`faithful-port-review`** skill; it re-derives the C independently and
runs per ported unit.

Reconciling correctness-by-construction with faithfulness: **faithful first →
prove → oxidize only as diff-stability allows → the reviewer verifies any
oxidation is byte/behavior-identical.**

## Relationship to `rust-correctness-by-construction`

Clean seam: **this skill = the port workflow; that skill = the technique
catalog.** When the catalog here routes you to a `type-system-patterns.md` §N or
`concurrency-lock-ordering.md`, that file lives in the CbC skill — load it for the
implementation detail. Conversely, if you are *not* porting (greenfield Rust, API
design, a multi-lock subsystem with no C original), start in the CbC skill
instead.
