---
name: faithful-port-review
description: Use when reviewing, finishing, or sweeping a faithful port — code translated from a known-good reference implementation (C driver, protocol, filesystem, algorithm) into Rust or another language — before it merges or runs on real hardware/silicon. Triggers include "faithful port", "ported from FreeBSD/Linux", driver bring-up, a port whose device-free/mock tests are green but is unproven on the real device, sweeping an existing ported codebase for latent reference divergences, or "the diff is the bug".
---

# Faithful-Port Review

A faithful port's **reference is the spec**. Every divergence from the reference
is a bug until a *written* reason says otherwise (fixed, justified in an
exceptions ledger with evidence, or a numbered tracking issue — never just a
plausible-sounding comment).

**Core principle: a green test suite proves the port matches the *mock's*
assumptions, not the *device's*.** Device-free tests are written by the same
person who wrote the port, against the same mental model. They cannot catch a
divergence that both the port and the mock share. **This review is the check the
mock cannot be** — so it is worth running even when every test is green, and
*especially* then.

This review supplements a normal code review (see superpowers
`requesting-code-review`); it does not replace it. Run it as the review stage of
a faithful-port task, before silicon/merge, and as a standalone **sweep** over an
existing ported codebase.

## The one move that defines this review

For every behavior, **re-derive the reference independently — do not trust the
port's own account of it.** The port's doc-comments, commit message, and tests
all encode the author's model. If that model is wrong, they are wrong *together*
and consistently. So:

- Open the reference yourself. Read the actual function, not the port's citation
  of it.
- Ask "does this match the **real device/reference**?" not "does this match the
  cited line / pass the mock?"

## The three recurring bug classes (grounded in real silicon failures)

| Class | What it looks like | Why green tests miss it | The catch |
|---|---|---|---|
| **Mock-masked timing / async** | A poll/wait/retry loop that bails on the first empty result, no inter-poll delay, assumes ordering. | The mock resolves synchronously, so the loop succeeds on pass 1. Real hardware posts the event ms later → instant timeout. | Every wait loop: would this still be correct if the result arrived *later* than the mock delivers it? Compare the loop's wait budget to the reference's. |
| **Wrong reference function** | Port is byte-faithful to reference function `X`; doc-comment cites `X`. But the device's ops-vtable binds `Y`. | The port matches `X` perfectly; tests assert against `X`. Nothing checks that `X` is the function this device runs. | Trace the device's ops struct (bus_ops / file_ops / driver vtable): which function does *this* device install for this op? Verify against `Y`, not the cited `X`. |
| **Hardware-pointer identity / lifetime** | A DMA structure the device caches a pointer to (ring base in a control reg, descriptor-array base, dequeue pointer) gets re-allocated, rebuilt, or moved after the device latched its address. | The mock reads whatever structure you hand it, so a fresh allocation "works". The real device keeps DMAing the *original* address → silent corruption / timeouts. | Any structure whose physical address is programmed into a device register once: confirm it is the *same allocation* for the device's life — moved, never re-allocated. |

These share a root: **the divergence is invisible to a device-free test and has
no confession in the code.** Do not wait for a comment to warn you.

## Checklist

Walk the diff (or the whole module, in sweep mode) and **examine every item** — you
re-derive each behavior from the reference independently. You **report only the
divergences** (see Output format); you do *not* write down the ones you found
faithful. Checking is mandatory; listing the faithful ones is not — "report only
divergences" must never decay into "skim for obvious bugs."

1. **Wait/poll/retry loops** — timing, empty-result handling, ordering vs the real device (class 1).
2. **Op dispatch** — for every register/bus/file op, the function the *device* binds, not the generic/cited one (class 2).
3. **Device-cached pointers** — rings, descriptor arrays, dequeue pointers: same allocation for the device's life (class 3).
4. **Constants & wire bytes** — request codes, masks, offsets, endianness pinned to *literal* reference values (a test asserting against the port's own named constant is circular).
5. **Dropped/added steps** — a "tidy helper" that drops a reference step (a barrier, a re-read, a second write) is a divergence.
6. **Error/edge semantics** — short reads, retries, terminal vs transient errors mapped as the reference maps them.

## Tolerating correct-by-construction oxidation

The faithful-first/oxidize-second method (`docs/faithful-port-method.md`)
deliberately produces a *second* version that **diverges from the C on purpose** —
idiomatic Rust that makes a bug class unrepresentable (typestate, newtype
invariants, RAII, `Result` instead of errno, an iterator instead of an index
loop). **Do not flag a correct-by-construction oxidation as a faithfulness bug.**

Distinguish:
- **Unfaithful divergence (bug):** changes the *behavior / wire bytes / device
  interaction* — a different SETUP packet, a dropped barrier, a re-allocated ring.
- **CbC oxidation (good):** preserves behavior exactly while making illegal states
  unrepresentable — the bytes on the wire and the order of device interactions are
  identical; only the Rust shape changed.

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

CRITICAL  (behavior / wire / device break)
- `file:line` vs `ref.c:fn:line`. what differ. why bite. how me check (adversarial).

IMPORTANT  (probably behavior. author confirm)
- `file:line` vs `ref.c:fn:line`. what differ. why suspect.

MAYBE CbC / justified  (look like divergence. behavior same. NOT bug)
- `file:line` vs `ref.c:fn:line`. why same bytes. (ask as question, not Critical)

VERDICT
silicon/merge? [No | with fixes | Yes]. why short.

NOT REACHED  (reference no find / no read. so sweep no lie "all done")
- ...
```

## Red flags — you are doing it wrong if

- You verified against the function the **port cited** instead of opening the reference yourself.
- You concluded "faithful" because **the tests are green** / the diff looks like the C.
- You skipped a wait loop because it "obviously polls correctly" (it polls correctly *against the mock*).
- You flagged an idiomatic-Rust rewrite as a bug without checking the bytes on the wire are identical.
- You reported a sweep as complete without listing the modules/references you couldn't reach.
- You padded the report with a "verified faithful" list, preamble, or praise — output is divergences only, caveman voice, no filler.
- You caveman-compressed a `file:line`, a mask, an offset, or a wire byte — compress the *prose*, keep every technical token byte-exact.

## Rationalization table

| Excuse | Reality |
|---|---|
| "Tests are green, it's faithful." | Green = matches the mock. The mock shares the port's blind spots. |
| "The comment says it matches usb.c:81." | The comment is the author's model. Open the reference and check which function the device actually binds. |
| "It's a faithful port, divergences would be obvious." | The expensive ones have no comment and pass every device-free test. That's why they reach silicon. |
| "This Rust doesn't look like the C, so it's unfaithful." | Faithful is about device-observable behavior, not textual likeness. Check the wire bytes. |
| "Re-allocating the ring is cleaner." | The device cached the old address. Cleaner code, orphaned hardware pointer. |
