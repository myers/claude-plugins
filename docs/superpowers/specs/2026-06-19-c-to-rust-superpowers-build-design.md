# `c-to-rust-superpowers` — build design

**Status:** design, approved for build · **Date:** 2026-06-19
**Decided with:** Myers, via brainstorming.
**Supersedes:** [`2026-06-17-faithful-port-skill-family-design.md`](2026-06-17-faithful-port-skill-family-design.md) —
that spec's architecture stands unchanged; this one **resolves its four open questions** and records the
packaging decision (one plugin). Read the 2026-06-17 spec for the full architecture, the unifying insight, the
rejected alternatives, and the three modes; this doc is the delta that makes it buildable.

## What this spec adds

The 2026-06-17 brainstorm fully designed the family (spine + method + reviewer template, riding the
superpowers ladder, no fork) but left it **design-only with four open questions**. This session closes those
questions and approves the build.

## Decisions

### D1 — Packaging: one plugin (was the "Packaging" open question)

`c-to-rust-port` + `faithful-port-review` + the new `c-to-rust-superpowers` spine ship as **one plugin**,
`plugins/c-to-rust-superpowers/`, holding **three skills**:

- `c-to-rust-superpowers/` — the orchestration spine (NEW; 3 modes: new / remediate / resync)
- `c-to-rust-port/` — the translation method (moved in, content unchanged except cross-ref wiring)
- `faithful-port-review/` — the check + the NEW `faithful-port-reviewer.md` template (moved in)

`rust-correctness-by-construction` **stays its own plugin** — it is a cleanly-seamed external type-technique
catalog, useful for non-porting Rust work; folding it in would over-couple it.

**marketplace.json:** the `c-to-rust-port` and `faithful-port-review` entries collapse into one
`c-to-rust-superpowers` entry; the `rust-correctness-by-construction` entry is unchanged.

**Rationale:** one install, one discoverable workflow (the goal). The standalone "sweep an existing codebase"
use that `faithful-port-review`'s old description sold survives *inside* the family as `remediate` mode's
entry, so nothing is lost. This does **not** merge contexts — porter and reviewer remain separate-context per
the 2026-06-17 rejection of a single merged skill.

### D2 — Review gate: third stage, concurrent, ported-units-only (Q1)

The faithful-port-reviewer runs as a **third review stage** per port task, *not* a replacement for SDD's
code-quality reviewer. Per ported task the verdicts are: SDD spec-compliance + SDD code-quality + the
**faithful-port-reviewer gate**.

- **Why third, not replace:** the faithful reviewer's power is having *only* `{DIFF}` + `{C_REFERENCE_MAPPING}`
  and nothing else — that isolation is what forces independent re-derivation and is the structural
  implementation of "the review is the check the mock cannot be." Giving it code-quality duties (and the plan
  context that comes with them) dilutes the isolation and splits its attention. Code-quality ("good Rust?")
  and faithful-port ("same bytes on the wire?") are different lenses; a clean-but-unfaithful idiom passes one
  and fails the other.
- **Cost guard (the cost of a third stage, neutralized):**
  - **Ported-units-only:** the gate runs only on tasks whose diff touches ported units (has C-reference
    anchors); pure infra / test-harness / tooling tasks skip it.
  - **Concurrent:** the faithful-port reviewer and the code-quality reviewer read the same diff independently
    and are dispatched in parallel — same wall-clock as a single review stage.

### D3 — `{C_REFERENCE_MAPPING}` source: harvested from anchors (Q2)

The **implementer writes the C-reference anchors as it ports** (`// C: <fn>() <label>:` per
`c-to-rust-port`'s anchor-comment convention). The SDD controller **harvests the mapping from the task's
diff** (the anchors are in the just-written code) and fills the `{C_REFERENCE_MAPPING}` field of the reviewer
template. The mapping is therefore a byproduct of porting, cannot drift from the code (it *is* the code), and
needs no separate planning artifact. The reviewer still never receives the porter's prose/rationale — only
diff + harvested mapping.

### D4 — `remediate` method-gap pass: a sweep section, TDD'd in (Q3)

The method-gap pass is an **added "method gaps" section in `faithful-port-review` sweep mode** (not a new
skill): flags missing behavior-pinning "prove" tests, over-oxidation on hot/churning files (diff-stability
debt), and missing anchor comments. It is built **TDD-first**: a cold-RED artifact exhibiting each method gap
is authored *before* the section exists, and the section is written to make it GREEN.

## Concrete artifacts the build creates

1. **`plugins/c-to-rust-superpowers/.claude-plugin/plugin.json`** — new plugin manifest (name
   `c-to-rust-superpowers`, version `1.0.0`, author Myers).
2. **`plugins/c-to-rust-superpowers/skills/c-to-rust-superpowers/SKILL.md`** — the spine: three modes, explicit
   delegation to the superpowers rungs, the triage/oracle-sequencing step, the re-sweep/re-prove closes, the
   mandatory faithful-port-reviewer gate (D2), and the anchor-harvest handoff (D3).
3. **Move** `plugins/c-to-rust-port/skills/c-to-rust-port/` → `plugins/c-to-rust-superpowers/skills/c-to-rust-port/`
   (preserve history). Add its "Execution & review" cross-ref section (writing-plans for the plan; the
   faithful-port-reviewer gate; the CbC-reconciliation sentence).
4. **Move** `plugins/faithful-port-review/skills/faithful-port-review/` →
   `plugins/c-to-rust-superpowers/skills/faithful-port-review/`. Add: the NEW
   **`faithful-port-reviewer.md`** prompt template (`{DIFF}` / `{BASE_SHA}` / `{HEAD_SHA}` /
   `{C_REFERENCE_MAPPING}`); a short "As a review gate" section in its SKILL.md; the "method gaps" sweep
   section (D4).
5. **`.claude-plugin/marketplace.json`** — collapse the two old entries into one `c-to-rust-superpowers` entry
   (D1); update the README table if it enumerates plugins.
6. **Delete** the now-empty `plugins/c-to-rust-port/` and `plugins/faithful-port-review/` plugin dirs.
7. Sharpen descriptions on the three skills so they fire at the plan, review, and sweep stages.

## Build discipline (writing-skills Iron Law — unchanged from 2026-06-17)

No skill change without a failing test first. The reviewer template and every skill edit are RED→GREEN
validated with **out-of-repo, renamed, no-confession artifacts** (cold-RED): a port unit with a planted
divergence whose answer is not grep-reachable in-repo, reviewed *through the template* — confirm it catches
the bug AND maps it to a divergence class, plus a regression that a clean port passes. The D4 method-gap
section gets its own cold-RED artifact per gap type (missing prove-test / over-oxidation / missing anchor).

## Non-goals (unchanged from 2026-06-17)

- Do **not** fork or edit superpowers' own SKILL.md files (delegate, don't fork the ladder).
- Do **not** merge porter and reviewer into one context (D2 keeps them separate).
- Do **not** build a packaged agent type or enforcement hook now (mechanism = prompt template).
- Do **not** duplicate the divergence taxonomy into `c-to-rust-port`.
- Do **not** fold `rust-correctness-by-construction` into the plugin (D1).

## Open questions

None. The four from 2026-06-17 are resolved (D1–D4). Ready for `writing-plans`.
