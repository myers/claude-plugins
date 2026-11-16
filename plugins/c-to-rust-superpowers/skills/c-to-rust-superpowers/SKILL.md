---
name: c-to-rust-superpowers
description: >-
  Orchestrate a C-to-Rust port across the superpowers ladder. Three modes: `new`
  (a C file with no Rust yet — produce the Rust), `remediate` (an existing Rust
  port — bring it up to standard), and `resync` (upstream C changed since the
  pinned SHA — update the port). Use when planning, porting, sweeping, resyncing,
  or reviewing a C-to-Rust port. Bundles the translation method (faithful → prove
  → idiomatic) and a mandatory fresh-context faithful-port-reviewer gate that
  re-derives the C reference independently.
  Triggers: starting a C→Rust port, planning a port, bringing an old port up to
  standard, a faithful-port sweep of an existing crate, an upstream C change /
  re-sync against a pinned SHA, or wiring the per-item review gate.
---

# C → Rust Superpowers — the port lifecycle spine

This skill is the **orchestration spine** for C→Rust port work. It does not do the
translation itself and it does not do the review itself — it **sequences the
superpowers rungs** and slots the port skills in at the plan and review rungs.

## The unifying insight

> **Every mode = (an *entry* generates a work-list) → (per item: faithful fix +
> prove + the faithful-port-reviewer gate) → confirm. Only the *entry* differs.**

The middle (per-item faithful fix + prove + the mandatory independent review gate)
and the close are **identical** across all three modes. What changes between modes
is only **how the work-list is born**:

| Mode | Entry (work-list source) | Close |
|---|---|---|
| `new` | a plan/spec from `superpowers:writing-plans`, shaped by `c-to-rust-port` | `superpowers:finishing-a-development-branch` |
| `remediate` | a `faithful-port-review` **sweep + method-gap pass** | re-sweep to confirm coverage/no-regression, then finishing |
| `resync` | a **C-old↔C-new git diff** over the pinned reference set | re-prove (differential oracle vs new C) + bump the pinned SHA, then finishing |

`resync` and `remediate` share machinery and often co-occur — an upstream change
frequently surfaces a latent port bug in the region it touches.

## The rung delegation (names only — DELEGATE, never fork)

This spine **delegates** to the real superpowers rungs by name. It does **not**
fork or edit superpowers' own SKILL.md files. The canonical sequence:

```
superpowers:brainstorming
  → superpowers:writing-plans            (shaped by the sibling c-to-rust-port skill)
  → superpowers:subagent-driven-development   (TDD inside — "prove it" is the RED test)
  → the faithful-port-reviewer gate      (MANDATORY — see "The review gate" below)
  → superpowers:finishing-a-development-branch
```

The reaching is done by Claude, driven by `using-superpowers` + sharp descriptions
+ the cross-references in this skill. superpowers cannot programmatically call our
skills; this body is the reliability layer.

## Entry checks (every mode)

Before the entry builds its work-list, every mode settles two things.

### The reference pin and the reference set

The **reference pin** is the C commit the port is faithful to. Pin the commit the
shipping product actually builds (for a distro package, the source version its
package recipe fetches, e.g. OpenWrt's `PKG_SOURCE_VERSION`), not upstream HEAD.
A port of HEAD matches a library nobody ships.

Record the pin in `REFERENCE.md` at the root of the port, the one place every
mode reads and `resync` bumps:

- upstream repo URL and the pinned SHA;
- where the SHA came from (the file and line that makes the product build it);
- the **reference set**: the paths the port is faithful to.

The reference set is wider than the `.c` files. It covers the `.h` headers (the
API), the upstream tests (the oracle) and the build files (`CMakeLists.txt`,
`Makefile`, linker version scripts: what is compiled and exported). A change to
any of them can change what the port must do.

### The library-plank check

Ask: **is the target a library that C consumers link?** If yes, the port is a
library plank: load the `c-to-rust-port` skill's `references/library-planks.md`
and apply it alongside this spine. Each mode below marks where it bites. If no,
skip it.

## The three modes in detail

### `new` — build → check

A C file, no Rust yet. Produce the Rust.

```
c-to-rust-superpowers new
  → entry checks (pin + reference set → REFERENCE.md; library-plank check)
  → brainstorming → writing-plans (shaped by c-to-rust-port; the plan records each unit's C reference)
  → per unit: subagent-driven-development (implementer → TDD; the behavior-pinning /
              differential test = c-to-rust-port "prove it", RED first) → ★ faithful-port-reviewer gate
  → idiomatic phase: rust-correctness-by-construction (gated by diff-stability)
  → finishing-a-development-branch
```

**Brainstorming shrinks when the decisions are already made.** If a spec or
ticket already fixes the unit, the oracle and the compatibility rule (ABI,
API-compatible, or wire-only), brainstorming has nothing left to explore there.
Ask only the open build decisions (pipeline depth, build shape, how the Rust
reaches header inlines, and the like) in one round, then go to writing-plans.
The spec doc is the existing spec or ticket.

For a library plank, the plan states which `library-planks.md` sections it
applies (header contract, mixed `.so` build, oracle, UB and ledger).

### `remediate` — check → fix → re-check

An existing Rust crate ported months ago. Bring it up to our porting standards.

```
c-to-rust-superpowers remediate
  → entry checks (REFERENCE.md present and pinned to what ships, else that is
           finding #1; library-plank check)
  → SWEEP: faithful-port-review sweep across the whole port  +  a METHOD-GAP pass
           (faithfulness divergences AND missing prove-tests / over-oxidation on hot
            files (diff-stability debt) / missing anchor comments; for a library
            plank, also every library-planks.md rule the port breaks)
  → TRIAGE + ORACLE-SEQUENCE: bucket findings —
           fix-now (has a live oracle) / cheap-safe / latent-or-gated.
           ★ Do NOT fix what you can't validate — a speculative fix adds new mock-masked bugs.
  → per finding: c-to-rust-port fix via subagent-driven-development → ★ faithful-port-reviewer gate
  → RE-SWEEP to confirm coverage + no regression → finishing
```

### `resync` — diff → propagate → re-prove

Upstream C changed since the pinned SHA. Update the Rust port to match.

```
c-to-rust-superpowers resync
  → entry checks (old SHA from REFERENCE.md; new SHA = what the product now ships;
           library-plank check)
  → DIFF: git diff <pinned-old-SHA>..<new-SHA> over the whole reference set
          (.c, .h, tests, build files) = the work-list
  → MAP each changed C hunk to its Rust via the diff-stable correspondence / anchor comments
  → CLASSIFY each: absorb-upstream-change | fix-revealed-port-bug | no-op-for-Rust
           (.h hunk = API change; tests hunk = oracle change; build-file hunk =
            compile-set or export change)
  → per actionable item: c-to-rust-port fix via subagent-driven-development → ★ faithful-port-reviewer gate
  → RE-PROVE (differential oracle vs new C) + BUMP the SHA in REFERENCE.md → finishing
```

## The review gate (D2)

The faithful-port-reviewer runs as a **third review stage** per port task — it does
**not** replace subagent-driven-development's code-quality reviewer. Per ported task
the verdicts are: SDD spec-compliance + SDD code-quality + the **faithful-port-reviewer
gate**.

- **Why third, not replace:** the faithful reviewer's power is having *only* `{DIFF_FILE}` +
  `{C_REFERENCE_MAPPING}` and nothing else — that isolation is what forces independent
  re-derivation and is the structural implementation of "the review is the check the mock
  cannot be." Code-quality ("good Rust?") and faithful-port ("same bytes on the wire?") are
  different lenses; a clean-but-unfaithful idiom passes one and fails the other.
- **Dispatched concurrently** with the code-quality reviewer — both read the same diff
  independently and run in parallel, so it costs the same wall-clock as a single review
  stage.
- **Template by path, from the running version.** The controller hands the reviewer
  subagent the absolute path of `faithful-port-reviewer.md` and of the
  `faithful-port-review` SKILL.md (the template's `{SKILL_PATH}`), taken from the
  plugin directory that passed the version check below, and tells it to read those
  files. "Load the skill" alone lets a stale
  session load an older cached version.
- **Version check before the first dispatch.** The loaded skill's base directory
  names its version (`.../c-to-rust-superpowers/<version>/skills/...`). Compare it
  with the version `~/.claude/plugins/installed_plugins.json` lists for
  `c-to-rust-superpowers`. If they differ, the session is running a stale copy
  (`/clear` does not reload plugins): read every skill file, the template included,
  from the installed `installPath` instead, and tell the user to restart Claude Code.
  A harness with no `installed_plugins.json` skips the check and passes the paths
  of the copy it loaded.
- **The diff travels as a diff-only file** (`{DIFF_FILE}`), not as SDD's review
  package: that package's `git log --oneline` hands the reviewer the porter's commit
  subjects. Fill `{WIRING}` with the unchanged files the unit relies on (shim, export
  map, build lines) and `{LIBRARY_PLANK}` with `no`, or, on a library plank, the
  stay-C headers and the unit's release-gate output.
- **Ported-units-only:** the gate runs **only on tasks whose diff touches ported units**
  (has C-reference anchors). Pure infra / test-harness / tooling tasks skip it.

## The anchor-harvest handoff (D3)

The mapping the reviewer needs is a **byproduct of porting**, not a separate artifact:

- The **implementer writes the C-reference anchors as it ports** — `// C: <file>:<name>`
  on each ported function and data item, per the catalog's *Anchor comments and the
  harvest*, which also gives the harvest command.
- The SDD **controller harvests `{C_REFERENCE_MAPPING}` from the task's diff** (greps the
  anchors out of the just-written code) and fills the field of the `faithful-port-reviewer`
  template.
- Because the mapping *is* the code, it cannot drift from the code and needs no separate
  planning artifact.
- The reviewer **never receives the porter's prose/rationale** — only the diff + the
  harvested mapping. That isolation is the point.

**When the harvest finds no anchor (the `remediate` / pre-skill case), do NOT absorb it
silently.** In a `new` port the implementer writes anchors as it goes, so the harvest is a
clean grep. But in `remediate` — and any port written before the anchor convention — a unit
often ties to its reference only by **prose** (a doc-comment / file-header "Mirrors FreeBSD
`foo()` L251-269"), with no greppable `// C:` anchor. The controller still resolves the
mapping (read the prose, open the reference, hand-build the `{C_REFERENCE_MAPPING}` line) so
the gate can run — **but a hand-resolved anchor is a method gap, not a free pass.** Two
required actions, never just the first:
  1. **Emit it as `MISSING ANCHOR` in the sweep's `METHOD GAPS` block** ("anchor back-filled
     by controller — was prose-only"), so the pre-skill port's anchor debt is *visible* and
     does not read as "fully anchored." Silently hand-building the mapping is exactly how a
     whole un-anchored file passes a remediate sweep with no finding.
  2. **Back-fill the real `// C:` anchor into the code** as part of the remediate fix, so the
     next harvest greps mechanically and the debt is actually paid down — not re-resolved
     from prose every sweep. (`faithful-port-review`'s MISSING-ANCHOR method-gap, broadened
     beyond `[D-heavy]` to cover exactly this harvest-mechanics harm.)

## Relationship to the other skills

- **`c-to-rust-superpowers`** (this skill) = the **lifecycle / orchestration**: the three
  entries, the triage/oracle-sequencing step, the re-sweep/re-prove closes, and the
  mandatory review gate.
- **`c-to-rust-port`** = the **method**: faithful → prove → idiomatic; the idiom/translation
  catalog; diff-stability gating. Used at the plan rung (shapes the plan) and per-item in the
  fix loop.
- **`faithful-port-review`** = the **check**: the divergence taxonomy, the re-derive-
  independently method, sweep mode, and the `faithful-port-reviewer.md` gate template.
- **`rust-correctness-by-construction`** (separate plugin) = the **type-technique catalog**
  for the idiomatic phase.

Layering analogy:

> **`c-to-rust-superpowers` : `c-to-rust-port` :: `subagent-driven-development` :
> `test-driven-development`** (orchestration/lifecycle : method/content).
