# Faithful-port skill family (`c-to-rust-superpowers`) — design

**Status:** design (spec only; no build this session) · **Date:** 2026-06-17
> **Superseded by [`2026-06-19-c-to-rust-superpowers-build-design.md`](2026-06-19-c-to-rust-superpowers-build-design.md)** — the architecture here stands; the four open questions are resolved and the build is done there.

**Decided with:** Myers, via brainstorming. Scope this session = design + committed spec. Building is a
separate future session (under `superpowers:writing-skills` — see the Iron Law note).

## Goal

When Claude does C→Rust port work under the superpowers ladder, the right port-specific skill should be
reached for at the right rung — and the whole port lifecycle should be a first-class, discoverable workflow.
Three use-cases must be first-class:

1. **`new`** — do a fresh C→Rust port (plan → implement → review).
2. **`remediate`** — bring an *existing* port up to our standards (sweep → triage → fix → re-sweep).
3. **`resync`** — upstream C changed → bring the Rust port up to date (C-diff → propagate → re-prove).

And the review that blesses any of them must be done by **an agent that knows the standards and has different
context than the porter** — structurally, not by luck.

## The unifying insight (the architecture in one line)

> **Every mode = (an *entry* generates a work-list) → (per item: faithful fix + prove + the
> faithful-port-reviewer gate) → (confirm).**

The middle (per-item fix + the mandatory independent review gate) and the close are **identical** across
modes. Only the **entry** differs — i.e. how the work-list is born:

| Mode | Entry (work-list source) | Close |
|---|---|---|
| `new` | a plan/spec (`superpowers:writing-plans`, shaped by `c-to-rust-port`) | finish branch |
| `remediate` | a **Rust-vs-C sweep** (`faithful-port-review` sweep mode) **+ a method-gap pass** | re-sweep to confirm coverage/no-regression |
| `resync` | a **C-old↔C-new diff** over the pinned upstream → map each hunk to its Rust via the diff-stable correspondence / anchor comments → classify *absorb-upstream* / *revealed-port-bug* / *no-op* | re-prove (differential oracle) + bump the pinned upstream SHA |

`resync` and `remediate` share machinery and often co-occur (an upstream change frequently surfaces a latent
port bug in the region it touches).

## Chosen architecture

**Composed family + a reviewer prompt template + a thin-delegating spine.**

**Rejected — merge into one "faithful-port" skill.** A single skill runs in *one agent, one context*, so the
porter would review its own port with its own blind spots — exactly the failure `faithful-port-review`
exists to prevent. Its thesis (*a green suite proves the port matches the mock, not the real counterpart; the
mock shares the porter's blind spots*) **demands a different-context checker.** Merge also bloats one skill
and is inconsistent with reaching for two skills at two rungs.

**Rejected — a bare "porting router" skill.** `using-superpowers` already routes by description. But note: a
router that merely points is redundant; a router that *orchestrates the lifecycle and owns the new content*
(triage, re-sweep, mode-switching) earns its keep — that is `c-to-rust-superpowers` below, not a bare router.

## Components (four skills + the superpowers rungs they ride)

1. **★ `c-to-rust-superpowers` (NEW) — the spine.** A thin **orchestration skill** (a workflow skill, sibling
   in spirit to `subagent-driven-development`). It is the named entry for all port work and has the three
   modes (`new`/`remediate`/`resync`). It **delegates** to the real superpowers rungs (does **not** fork
   them) and slots the port skills in at the plan and review rungs. It **owns the content unique to porting
   orchestration**: the three entries, the **triage/oracle-sequencing** step, and the **re-sweep/re-prove**
   close.
   - Layering: **`c-to-rust-superpowers` : `c-to-rust-port` :: `subagent-driven-development` :
     `test-driven-development`** (orchestration/lifecycle : method/content).
2. **`c-to-rust-port` — the translation *method*.** faithful → prove → idiomatic; the idiom/translation
   catalog; diff-stability gating; stay-light-on-CbC for living ports. Used at the **plan rung** (shapes the
   plan) and per-item during the fix-loop. Unchanged except small cross-reference wiring.
3. **`faithful-port-review` + `faithful-port-reviewer.md` (NEW template) — the *check*.** Owns the divergence
   taxonomy (the three classes), the re-derive-independently method, CbC tolerance, the caveman output, and
   **sweep mode**. The taxonomy is **not** duplicated into `c-to-rust-port`. Two uses: the per-item review
   gate (via the template) and the `remediate` entry (sweep).
4. **`rust-correctness-by-construction` — the type-technique catalog** for the idiomatic phase. Already
   cleanly seamed to `c-to-rust-port`. Unchanged.

Delegated-to (unchanged, not forked): **`superpowers:{brainstorming, writing-plans,
subagent-driven-development, requesting-code-review, test-driven-development, finishing-a-development-branch}`**.

## The reviewer prompt template — contract (★ the connective tissue)

`plugins/faithful-port-review/skills/faithful-port-review/faithful-port-reviewer.md` — a fill-in-the-blank
prompt dispatched to a **fresh `general-purpose` subagent** via the Task tool (the faithful-port twin of
`superpowers:requesting-code-review`'s `code-reviewer.md`). Placeholders:

- `{DIFF}` / `{BASE_SHA}` / `{HEAD_SHA}` — the work product (the changed Rust).
- `{C_REFERENCE_MAPPING}` — **the new, load-bearing field**: which C reference file/function each changed
  Rust unit ports (e.g. `ring.rs:send_msg ↔ mt7921/usb.c:mt7921u_mcu_send_message`). The reviewer gets this,
  **never the porter's prose about what the C "means."**

Body instructs the subagent to: **load `faithful-port-review`**; open the cited C itself and re-derive each
behavior; apply the three divergence classes; adversarially verify each candidate; report in the skill's
caveman/divergences-only format.

**Why fresh context is the whole point:** a reviewer handed only `{DIFF} + {C_REFERENCE_MAPPING}` — never the
porter's session/rationale — is *forced* to re-derive the reference independently; it has nothing else. That
is the structural implementation of "the review is the check the mock cannot be."

## How the "reaching" works (the honest mechanism — no fork)

superpowers cannot *programmatically* call our skills (vendored third-party plugin; editing its SKILL.md is
lost on update; no skill-invoked hook). **The reacher is Claude**, driven by three things:

1. **`using-superpowers`** (injected every session) — the *engine*: "if a skill might apply, invoke it."
2. **Descriptions** — the *trigger*: `c-to-rust-superpowers`/`c-to-rust-port` fire while planning/porting;
   `faithful-port-review` fires while reviewing/sweeping. Keep descriptions sharp + stage-aware.
3. **Cross-references** — the *reliability*, and they live in **our** skills (the only ones we can edit):
   - `c-to-rust-superpowers` body sequences the rungs explicitly: brainstorming → writing-plans (shaped by
     `c-to-rust-port`) → subagent-driven-development (TDD inside) → **the `faithful-port-reviewer` gate
     (mandatory)** → finishing. Plus the `remediate`/`resync` entries.
   - `c-to-rust-port` body: "Planning uses `writing-plans`; the review gate is the `faithful-port-reviewer`."
   - `faithful-port-review` body: "Used as the review rung of `c-to-rust-superpowers`; also the `remediate`
     entry (sweep)."

**Enforcement caveat (the one non-magic part):** descriptions + cross-refs make this *highly reliable* but
not a hard programmatic guarantee. A hard guarantee (review rung *always* runs) needs a **hook** (shell
pre-merge gate) or a **packaged agent type** — both heavier, both deferred. For the reach described here,
descriptions + cross-refs is the right weight. (Mechanism choice this session: **prompt template**, not a
packaged agent type.)

## The three modes in detail

**`new`** (build → check):
```
c-to-rust-superpowers new
  → brainstorming → writing-plans (shaped by c-to-rust-port; plan records each unit's C reference)
  → per unit: subagent-driven-development (implementer → TDD; the behavior-pinning/differential test
              = c-to-rust-port "prove it", RED first) → ★ faithful-port-reviewer gate
  → idiomatic phase: rust-correctness-by-construction (gated by diff-stability)
  → finishing-a-development-branch
```

**`remediate`** (check → fix → re-check) — "bring this port up to our standards":
```
c-to-rust-superpowers remediate
  → SWEEP: faithful-port-review sweep across the whole port  +  a METHOD-GAP pass
           (faithfulness divergences AND missing prove-tests / over-oxidation on hot files / missing anchors)
  → TRIAGE + ORACLE-SEQUENCE: bucket findings — fix-now (has a live oracle) / cheap-safe / latent-or-gated.
           ★ Do NOT fix what you can't validate — a speculative fix adds new mock-masked bugs.
  → per finding: c-to-rust-port fix via subagent-driven-development → ★ faithful-port-reviewer gate
  → RE-SWEEP to confirm coverage + no regression → finishing
```
(This is exactly the xhci/mt76 sweep-then-fix campaign run 2026-06-17 — now codified.)

**`resync`** (diff → propagate → re-prove) — "upstream C changed, update the port":
```
c-to-rust-superpowers resync
  → DIFF: git diff <pinned-old-SHA>..<new-SHA> over the reference C files = the work-list
  → MAP each changed C hunk to its Rust via the diff-stable correspondence / anchor comments
  → CLASSIFY each: absorb-upstream-change | fix-revealed-port-bug | no-op-for-Rust
  → per actionable item: c-to-rust-port fix via subagent-driven-development → ★ faithful-port-reviewer gate
  → RE-PROVE (differential oracle vs new C) + BUMP the pinned upstream SHA → finishing
```

## "Up to standard" = both dimensions (confirmed)

The `remediate` sweep checks **both**:
- **Faithfulness** — divergences from the C reference (the three classes).
- **Method/quality** — missing behavior-pinning "prove" tests, over-oxidation on hot/churning files
  (diff-stability debt), missing anchor comments. (`c-to-rust-port`'s standards.)

## Reconciling the CbC tension (write this into the skills so they don't read as contradictory)

- `c-to-rust-port`: **stay light on CbC** (diff-stability for a living port).
- `rust-correctness-by-construction`: **lean on types** (max safety).
- `faithful-port-review`: **tolerate CbC** iff behavior-preserving.

Consistent once sequenced: **faithful first → prove → oxidize only as diff-stability allows → and the
reviewer verifies any oxidation is byte/behavior-identical.** The reviewer is the referee that keeps
oxidation honest (it already carries the "over-tolerance = a behavior change in an oxidation costume" guard).
Diff-stability *pays off at `resync`*: a clean C-diff maps onto the Rust only because the port stayed light.

## Concrete artifacts a future build session creates

1. **`plugins/c-to-rust-superpowers/`** — the new spine plugin/skill: `SKILL.md` with the three modes, the
   delegation to the superpowers rungs, the triage/oracle-sequencing step, the re-sweep/re-prove closes, and
   the mandatory `faithful-port-reviewer` gate. (Or house the skill inside an existing plugin — packaging TBD
   at build.)
2. **`faithful-port-review/faithful-port-reviewer.md`** — the reviewer prompt template (★) with the
   `{C_REFERENCE_MAPPING}` field; + a short "As a review gate" section in its `SKILL.md`.
3. **`c-to-rust-port/SKILL.md`** — small "Execution & review" cross-reference section (writing-plans for the
   plan; the `faithful-port-reviewer` gate; the CbC-reconciliation sentence).
4. **Sharpen descriptions** on `c-to-rust-superpowers`/`c-to-rust-port`/`faithful-port-review` so they fire at
   the plan, review, and sweep stages.
5. (Deferred, optional) a hook or packaged agent type if a *hard* enforcement guarantee is later wanted.

## Explicit non-goals

- Do **not** fork or edit superpowers' own SKILL.md files (delegate, don't fork the ladder).
- Do **not** merge the doing and checking skills.
- Do **not** build a packaged agent type now (mechanism = prompt template).
- Do **not** duplicate the divergence taxonomy into `c-to-rust-port`.

## Build-session note (writing-skills Iron Law)

Creating/editing these skills falls under `superpowers:writing-skills` → **no skill change without a failing
test first.** The reviewer template and each skill edit must be RED→GREEN validated with **out-of-repo,
renamed, no-confession artifacts** (the cold-RED discipline): a port unit with a planted divergence whose
answer is not grep-reachable in-repo, reviewed *through the template* — confirm it catches the bug AND maps
it to a class, plus a regression that a clean port passes. (Same method used to validate the 2026-06-17
generalization of `faithful-port-review`.)

## Open questions for the build session

- Does the review rung **replace** subagent-driven-development's code-quality reviewer for port work, or run
  as a **third** stage after it? (Lean: a third, port-specific stage — code-quality and faithful-port are
  different lenses.)
- `{C_REFERENCE_MAPPING}` source: the plan records each unit's C reference, so the controller assembles it —
  confirm the implementer handoff carries it through.
- Packaging: is `c-to-rust-superpowers` its own plugin, or a skill inside an existing plugin? (Marketplace +
  discovery implications.)
- Does `remediate`'s method-gap pass want its own checklist/lens, or is it `faithful-port-review` sweep with
  an added "method gaps" section?
