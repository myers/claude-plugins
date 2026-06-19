---
name: faithful-port-review
description: Use when reviewing, finishing, or sweeping a faithful port — code translated from a known-good reference implementation (C/Rust driver, filesystem, storage engine, protocol, codec, or algorithm) into another language — before it merges or runs against its real counterpart (device/silicon, disk/on-disk format, peer, or production). Triggers include "faithful port", "ported from FreeBSD/Linux/OpenZFS", driver or filesystem bring-up, a port whose mock/device-free tests are green but is unproven against the real device/disk/peer, checksum/endianness/wire-format fidelity, sweeping an existing ported codebase for latent reference divergences, or "the diff is the bug".
---

# Faithful-Port Review

A faithful port's **reference is the spec**. Every divergence from the reference
is a bug until a *written* reason says otherwise (fixed, justified in an
exceptions ledger with evidence, or a numbered tracking issue — never just a
plausible-sounding comment).

**Core principle: a green test suite proves the port matches the *mock's*
assumptions, not the *real counterpart's*.** The "real counterpart" is whatever
the port is checked against in production — a device/silicon, a disk and its
on-disk format, a network peer, the kernel, or a concurrent producer. Mock-based
tests are written by the same person who wrote the port, against the same mental
model. They cannot catch a divergence that both the port and the mock share.
**This review is the check the mock cannot be** — so it is worth running even when
every test is green, and *especially* then.

This review supplements a normal code review (see superpowers
`requesting-code-review`); it does not replace it. Run it as the review stage of
a faithful-port task, before silicon/merge, and as a standalone **sweep** over an
existing ported codebase.

## As a review gate

This skill is the **review rung of `c-to-rust-superpowers`**. Dispatch it via the
sibling `faithful-port-reviewer.md` template to a **fresh subagent given only the
diff + `{C_REFERENCE_MAPPING}`** — no porter prose, no commit message — so it must
re-derive the C independently. Its other entry is `remediate` (**sweep mode**),
which audits a whole existing port rather than a single diff.

## The one move that defines this review

For every behavior, **re-derive the reference independently — do not trust the
port's own account of it.** The port's doc-comments, commit message, and tests
all encode the author's model. If that model is wrong, they are wrong *together*
and consistently. So:

- Open the reference yourself. Read the actual function, not the port's citation
  of it.
- Ask "does this match the **real reference / counterpart**?" not "does this match
  the cited line / pass the mock?"

## The three recurring bug classes (grounded in real production failures)

Each class is its **generic principle** — the lens is the same whether the real
counterpart is a device, a disk, a peer, the kernel, or a concurrent producer. The
per-domain instances below are *hooks, not limits*: recognize the **shape**, then
find your domain's version. Do not dismiss a lens because your port has no
hardware — *every* port has all three.

| Class | Generic principle (and why green tests miss it) | The catch |
|---|---|---|
| **1. Mock-masked timing / ordering / failure** | The mock collapses the counterpart's real *temporal and failure behavior* — it resolves synchronously, in submission order, always succeeding. A wait/poll/retry loop, an ordering assumption, or an error path that is correct against the mock breaks when the real side is slow, reorders, fails transiently, or returns partial. | Every wait / order / error path: still correct if the result arrived *later*, *out of order*, *failed once*, or came back *short*? Compare the budget + retry to the reference's. |
| **2. Wrong reference variant / dispatch** | The port is byte-faithful to implementation `X` and cites `X`, but the path THIS object / config / platform actually takes binds `Y`. Tests assert against `X`; nothing checks that `X` is the one that runs. | Trace the real dispatch — ops vtable, type-tagged switch, feature-flag gate, endianness / version variant — to the function THIS case binds. Verify against `Y`, not the cited `X`. |
| **3. Referent identity / lifetime** | Something stores a *reference* to a structure — a pointer, offset, index, id, or a **checksum / hash computed over the bytes** — valid only while the referent stays put and byte-identical. A realloc, rebuild, re-encode, or in-place mutation *after* the reference was captured silently breaks it. | Every captured reference: confirm its referent is the *same, unmodified* bytes / allocation for the reference's whole life — not moved, not re-encoded, not re-checksummed out of step. |

**The same three lenses, instantiated per domain** (find your column; the shape is identical):

| | Device driver | Storage / filesystem (e.g. ZFS / Zarn) | Protocol / codec |
|---|---|---|---|
| **1** | poll bails on first empty event; HW posts ms later → timeout | I/O completes out of order; checksum-fail → read-the-other-copy repair path; short read; txg ordering | peer NAKs / retransmits / reorders; decoder fed a chunk split mid-token |
| **2** | device ops-vtable binds `mt792xu_rr`, not generic `mt76u_rr` | checksum / compress / encrypt fn chosen by dataset props; **byteswap variant chosen by on-disk endianness** (a native-endian hardcode is faithful to the *wrong* variant) | wrong message-version handler; wrong cipher mode for the negotiated suite |
| **3** | DMA ring base programmed into a register, then reallocated / moved | **block-pointer checksum captured, then the block re-encoded / compressed before write**; a dnode held by object-id across an eviction / realloc | length or CRC computed over a frame that is edited afterward |

These share a root: **the divergence is invisible to a mock and has no confession
in the code.** Do not wait for a comment to warn you.

## Checklist

Walk the diff (or the whole module, in sweep mode) and **examine every item** — you
re-derive each behavior from the reference independently. You **report only the
divergences** (see Output format); you do *not* write down the ones you found
faithful. Checking is mandatory; listing the faithful ones is not — "report only
divergences" must never decay into "skim for obvious bugs."

1. **Wait/poll/retry loops** — timing, ordering, empty/partial-result and transient-failure handling vs the real counterpart (class 1).
2. **Dispatch** — for every op, the concrete implementation THIS object/config/platform binds, not the generic/cited one (class 2).
3. **Captured references** — pointers, offsets, ids, **checksums/hashes-over-bytes**: the referent stays the same bytes/allocation for the reference's life (class 3).
4. **Constants & serialized bytes** — request codes, masks, offsets, endianness, on-disk/wire field layouts pinned to *literal* reference values (a test asserting against the port's own named constant is circular).
5. **Dropped/added/reordered steps** — a "tidy helper" that drops or reorders a reference step (a barrier, a re-read, a second write, a checksum-after-transform) is a divergence.
6. **Error/edge semantics** — short reads, retries, terminal vs transient errors mapped as the reference maps them.

## Tolerating correct-by-construction oxidation

The faithful-first/oxidize-second method (the faithful → prove → idiomatic method
of the `c-to-rust-port` skill) deliberately produces a *second* version that
**diverges from the C on purpose** — idiomatic Rust that makes a bug class
unrepresentable (typestate, newtype invariants, RAII, `Result` instead of errno,
an iterator instead of an index loop). **Do not flag a correct-by-construction
oxidation as a faithfulness bug.**

Distinguish:
- **Unfaithful divergence (bug):** changes the *behavior / serialized bytes /
  counterpart interaction* — a different SETUP packet, a dropped barrier, a
  re-allocated ring, a checksum over different bytes, a swapped endianness.
- **CbC oxidation (good):** preserves behavior exactly while making illegal states
  unrepresentable — the bytes (on wire / on disk) and the order of counterpart
  interactions are identical; only the Rust shape changed.

The test is **observable behavior**, not textual similarity to the C. A faithful
port is *allowed* to look un-C-like (RAII guard vs goto-cleanup) as long as the
device sees the same thing. When unsure whether a divergence is behavioral,
verify it *is* behavior-preserving (read both paths) before flagging — and frame
it as a question, not a Critical. See `rust-correctness-by-construction` for what
legitimate oxidations look like.

**The dangerous failure mode is over-tolerance — a behavior change wearing an
oxidation costume.** A "cleaner" idiom can subtly change a computed value or wire
byte while looking *more* correct than the reference. Real example: the reference
RMW is `val |= reg_rr() & ~mask` (the caller's `val` is written **unmasked** — bits
outside `mask` survive); the textbook idiom `(cur & !mask) | (val & mask)` masks
`val` and silently drops those bits — a wire-observable divergence dressed as a
tidy-up. Tolerance does **not** mean trusting that a cleaner idiom is equivalent —
it means *verifying* equivalence by computing the output for an input that
exercises the difference. And note green tests routinely miss these: when only the
*degenerate* callers are exercised (e.g. `set_bits`/`clear_bits`, where `val ==
mask` so the masking is a no-op), the suite passes while a direct call with
out-of-mask `val` would diverge. Re-derive the behavior; do not grade the idiom.

**The tests are the oracle — an oxidation that rewrites them is the smell.** An
oxidation pass is a *behavior-preserving refactor* (TDD: behavior unchanged →
tests stay green). The faithful port's behavior-pinning tests (wire bytes,
register values written, order of device interactions) are what *prove* the
oxidation faithful — so when reviewing an oxidation, **diff the tests too**:
- Mechanical adaptation to a new type signature (`Reg(0x70)` where a bare `0x70`
  was, `Ok(v)` where a bare `v` was) is fine.
- A test whose **asserted behavior changed** — different expected wire bytes, a
  different written value, a removed/weakened assertion — is a confession that
  *behavior* changed. That is the bug, not a test update. The rmw example above
  slips through precisely when the wire-byte test is rewritten to the new masked
  bytes (or narrowed to the degenerate callers) instead of going RED.

So the oxidized code must keep the faithful port's behavior assertions
**byte-identical**. If it can't, you found a behavioral divergence, not an
oxidation — flag it.

## Sweep mode (whole-codebase audit, e.g. a 100%-faithful port like Zarn)

When auditing an existing ported codebase rather than a single diff:
- Enumerate the ported modules and map each to its reference file(s).
- Run the checklist per module; **dispatch one reviewer per module/reference pair**
  so each has the budget to actually open the reference.
- **Adversarially verify** every candidate divergence before reporting it: is it
  truly behavioral, or a justified/CbC one? Majority-refute borderline findings.
- Report a per-module table of **counts only**: `reviewed / divergences-found /
  verified-real / CbC-or-justified` (counts, not a faithful enumeration). Log what
  you did **not** cover (a module whose reference you couldn't locate) — silent
  truncation reads as "audited everything."

### Method gaps (remediate sweep)

A `remediate` sweep brings an existing port up to standard. Faithfulness
divergences are only half the job — a port can be byte-faithful *today* yet carry
**method debt** that makes the next bug or the next upstream resync expensive. So
in a remediate sweep, ALSO run a second pass that flags these three **standards
gaps**, and report them in a SEPARATE `METHOD GAPS` block, distinct from
`DIVERGENCES`. A method gap is **not** a faithfulness bug — do not put it in
`DIVERGENCES`, and do not let a clean `DIVERGENCES` block excuse a method gap.

- **Missing prove-test.** A ported unit with no behavior-pinning / differential
  test — nothing that pins the *observable* output (wire bytes, register values
  written, order of counterpart interactions) to a literal reference value.
  Without it there is **no oracle** that proves the port faithful, and a later
  oxidation has nothing to keep it honest (this is the "tests are the oracle"
  smell from the oxidation section, one step earlier: the test never existed). A
  test that only asserts against the port's own named constant is circular and
  counts as missing.
- **Over-oxidation on a hot file.** A `[D-mod]` or `[D-heavy]` *structural*
  oxidation (see `c-to-rust-port`'s diff-stability tags — `[D-light]` cosmetic,
  `[D-mod]` re-shaped, `[D-heavy]` re-architected) applied to a reference file
  with **high upstream churn**. `git log --oneline -- <ref>` the reference (or
  read a churn note if one is recorded): a file patched often will be resynced
  often, and every step away from its C shape makes that resync more expensive —
  **diff-stability debt**. Cross-ref `c-to-rust-port`'s diff-stability gating:
  heavy oxidation is *earned* on a cold, frozen file, **not** on a hot one. The
  same `[D-heavy]` oxidation on a file with one commit ever is NOT a gap — judge
  it by the reference's churn, not by the oxidation alone.
- **Missing anchor.** A ported `[D-heavy]` region with no
  `// C: <fn>() <label>:` anchor comment tying it back to the reference. When the
  upstream diff lands, a heavily re-architected region with no anchor gives the
  resync **no landing point** — the next porter cannot find where the C function
  went. `[D-heavy]` earns its keep only if it stays resync-navigable.

Verify each candidate gap the same adversarial way as a divergence: confirm the
prove-test really is absent (not just renamed), confirm the reference really is
hot (`git log` it — do not assume), confirm the region really is `[D-heavy]` and
really has no anchor. A clean port — prove-tests present, no heavy oxidation on
hot files, anchors on every `[D-heavy]` region — yields an empty `METHOD GAPS`
block ("no method gap found"), exactly as a faithful module yields no divergence.

## Output format — caveman voice, divergences only

Write the report like a caveman: short fragments, drop articles/filler, no
preamble, no praise, no hedging. **No "verified faithful" list** — report ONLY
divergences (and the coverage log). If a file has no divergence, say "no
divergence found" — do not pad with what you checked.

You STILL re-derive and check every behavior against the reference. You just do
not write the faithful ones down. **Checking mandatory; listing not.**

**Caveman the prose, never the technical tokens.** Keep all `code`, commands,
error strings, `file:line`, reference citations (`ref.c:fn:line`), masks,
offsets, and wire bytes **byte-exact** — a mangled offset is a wrong review. The
caveman style ([why](https://github.com/JuliusBrussee/caveman)) changes how the
report *talks*, not how you *think* or what you verify.

Example — normal vs caveman (same facts, same exact tokens):
> normal: "The poll loop at `init.rs:39` polls 50 times, whereas the reference
> do-while at `util.c:31` polls 51 — one iteration short, narrowing the window."
> caveman: "`init.rs:39` poll 50. ref `util.c:31` do-while poll 51. one short. window tight."

```
DIVERGENCES

CRITICAL  (behavior / bytes / counterpart break)
- `file:line` vs `ref.c:fn:line`. what differ. why bite. how me check (adversarial).

IMPORTANT  (probably behavior. author confirm)
- `file:line` vs `ref.c:fn:line`. what differ. why suspect.

MAYBE CbC / justified  (look like divergence. behavior same. NOT bug)
- `file:line` vs `ref.c:fn:line`. why same bytes. (ask as question, not Critical)

VERDICT
ship/merge? [No | with fixes | Yes]. why short.   (ship = silicon / prod / interop)

NOT REACHED  (reference no find / no read. so sweep no lie "all done")
- ...
```

In a **remediate sweep**, append a SEPARATE block (omit it for a plain
divergence review; never fold gaps into `DIVERGENCES`):

```
METHOD GAPS  (method debt. port faithful now. cost later. NOT divergence)
- MISSING PROVE-TEST. `unit` (ports `ref.c:fn`). no behavior-pin test. no oracle.
- OVER-OXIDIZE HOT FILE. `file:line` [D-heavy] on `ref.c` (hot: N commit/month). resync cost.
- MISSING ANCHOR. `file:line` [D-heavy] region. no `// C: fn() label:`. resync no landing.

(empty -> "no method gap found")
```

## Red flags — you are doing it wrong if

- You verified against the function the **port cited** instead of opening the reference yourself.
- You concluded "faithful" because **the tests are green** / the diff looks like the C.
- You skipped a wait loop because it "obviously polls correctly" (it polls correctly *against the mock*).
- You flagged an idiomatic-Rust rewrite as a bug without checking the bytes on the wire are identical.
- You reported a sweep as complete without listing the modules/references you couldn't reach.
- You padded the report with a "verified faithful" list, preamble, or praise — output is divergences only, caveman voice, no filler.
- You caveman-compressed a `file:line`, a mask, an offset, or a wire byte — compress the *prose*, keep every technical token byte-exact.
- You **skipped class 3 because "there's no hardware pointer here"** — class 3 is *any captured reference* (a checksum/hash over bytes, an object-id, an offset, an index), in any domain. A filesystem/protocol port has class-3 bugs too.
- You decided a lens "doesn't apply to this domain" — all three lenses apply to every port; only the *instance* changes. Find the instance, don't drop the lens.

## Rationalization table

| Excuse | Reality |
|---|---|
| "Tests are green, it's faithful." | Green = matches the mock. The mock shares the port's blind spots. |
| "The comment says it matches `ref.c:81`." | The comment is the author's model. Open the reference and check which *variant* THIS case actually runs. |
| "It's a faithful port, divergences would be obvious." | The expensive ones have no comment and pass every mock test. That's why they reach production. |
| "This Rust doesn't look like the C, so it's unfaithful." | Faithful is about *counterpart-observable* behavior, not textual likeness. Check the bytes (on wire / on disk). |
| "Class 3 is about hardware pointers — N/A here." | Class 3 is *any captured reference*: a checksum over bytes, an object-id, an offset. The referent mutating after capture is the bug — hardware or not. |
| "Re-allocating the ring / re-checksumming after the transform is cleaner." | The reference (device pointer, *or the stored checksum*) was captured over the old bytes. Cleaner code, dangling reference. |
