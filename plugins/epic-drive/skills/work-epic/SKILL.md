---
name: work-epic
description: Use when asked to drive, finish, work through, or clear an epic (a git-issues parent, a Gitea milestone, or a map issue) by delegating its issues to subagents, one at a time, until it is done. Triggers on "work the epic", "drive the epic", "finish epic", "clear this epic", or an epic id/milestone with no single-ticket scope.
---

# Work an epic

You are the controller. Subagents do the work; you hold only the epic's
bookkeeping. **Your context is the scarce resource — spend it on the ledger,
never on ticket bodies.**

## Tracker operations

The loop names five operations — **ledger**, **bar**, **status check**,
**sync**, **file a follow-up** — and the tracker decides the commands. Read
exactly one ops file before kickoff:

- git-issues (`iss`, the repo has `iss` initialized) → [`iss.md`](iss.md)
- Gitea (`gtx`, the repo's `docs/agents/issue-tracker.md` says Gitea) →
  [`gitea.md`](gitea.md)

## Kickoff (once)

Run the **ledger** and the **bar**. That is the whole read; the ledger's
projection never includes bodies or comments.

**The drive is the whole epic, plus its blockers.** Every open issue under
the epic is in scope, including the follow-ups workers file under it
mid-drive, and so is every outside ticket that holds one of them (see **An
outside blocker is in scope**). The denominator grows as workers file, so the
bar can move backwards (two closes against eight new leaves read as
32% → 30%); that is the drive working, not a regression.

Then tell the user, verbatim and paste-able:

```
/goal Work epic <epic-name> to done: every issue under it, including follow-ups filed during the drive, and every outside ticket blocking one, is closed or abandoned, and the epic body's own acceptance checklist is verified. Follow the work-epic skill — one issue per fresh subagent, controller reads no ticket bodies.
```

Say it keeps you working across turns without re-prompting, then start round 1.

## The loop

1. Re-run the **ledger**. Pick the oldest open leaf whose `blocks=`
   targets are all closed, or the outside blocker holding a leaf (see **An
   outside blocker is in scope**). Ties → lowest id. A claimed or
   `in-progress` row is a prior session's unfinished ticket — dispatch it
   like any other; its comments tell the subagent where it stopped. A
   **HITL** row (the ops file names its labels) needs the human: skip it and
   name it in the round's report.
2. Dispatch ONE fresh subagent (not a fork) with the dispatch recipe below.
   Record its handle and end your turn. If a goal continuation wakes you
   before its result, follow **Waiting for a worker** below.
3. On its return, run the **status check** to confirm the state actually
   moved. Then **sync**: push each repo the worker touched, plus the tracker
   where the ops file says it needs one — the tracker is the loop's state; an
   unsynced close is a lost round.
4. Run the **bar**. Print it VERBATIM — it ends in ` - <epic-name>`; a bar
   with no name does not say which epic. Go to 1.

Serial by default: parallel subagents in one checkout collide on git, and you
cannot tell whether two tickets touch disjoint files without reading their
bodies. Lanes in separate worktrees are the exception (see **Parallel lanes**).

**Done** = the ledger shows no open row except HITL ones, every outside
blocker worked this drive is closed, AND the epic body's own acceptance
checklist checks out. Read the epic body once, at that point — not before.
Report the bar's raw fraction and name any HITL or abandoned rows that keep
it under 100%.

## Waiting for a worker

**Wait on notifications.** After dispatch or resume, the next controller
action is triggered by the worker's completion, an actionable handoff or
blocker, or new user instructions. Routine progress messages need no response.

If an active goal wakes the controller early, use one long, interruptible
notification wait: in Codex, `collaboration.wait_agent({"timeout_ms":3600000})`,
or the longest interval the tool and higher-priority instructions allow.
The worker's message or new user input interrupts the wait. Avoid short
timeouts that repeatedly wake the controller merely to wait again.

A timeout means only that no notification arrived. Continue waiting on the
same worker, silently; it is not evidence of a stalled job or a reason to
restart work. Automatic goal continuations are not worker completion signals.

While waiting, do not poll process lists, test logs, agent status, or issue
status, and do not send recurring "still waiting" commentary or final replies.
Check final gate summaries when the worker reports completion. Use a targeted
recovery check only after an explicit failure/missing-handle signal or a user
request to investigate. This controller wait does not replace the worker's
responsibility to await its own gates before reporting.

## Dispatch prompt recipe

The prompt is exactly these lines, in this order. It is a pointer, not a
briefing.

```
Work issue <id>. Tracker: <tracker>, run from <tracker root>; its CLAUDE.md says where the code lives.
Load these skills first: subagent-working-a-git-issues-issue, plus every skill this repo's CLAUDE.md requires for work of this shape.
Read it yourself: the issue with its comments, then the epic <epic-ref> — the epic carries method and corrections from prior children.
Gates before close: every gate this repo's CLAUDE.md and the epic body require for a change of this shape. Classify your own change against them. A gate that came back red goes in your report even if a re-run went green.
Do not push. File any new gaps as tickets under <epic-ref>; touch no other issue. A gate that is red on the unmodified base is not "pre-existing" — it is a stop-the-line defect: file it at priority 0 under the subsystem epic it belongs to, never let it ride inside this commit, and do not close this ticket past a red final run.
Do not end your turn while a suite or build is running: wait for its Summary in the foreground (a Monitor or an until-loop on the captured output file), then finish the gates.
Report back under 150 words, then stop: verdict, the id you closed or left open and why, follow-up ids filed, and for each red gate: which gate, whether it was your own in-flight edit or red on the unmodified base, and what fixed it. Ask no questions; print no `Next up:` line and no progress bar — the controller owns the loop.
<one line for constraints scoped to this session that CLAUDE.md cannot know — commit trailers, a pinned toolchain — or omit the line>
```

Only `<id>`, `<tracker>` (`git-issues` or `Gitea`), `<tracker root>`,
`<epic-ref>` (the ops file says its form) and the session line are yours to
fill. Every other word is fixed text — copy it. The subagent reads the
ticket, the epic, and the repo's CLAUDE.md; you do not read them for it, so
you cannot name its skills, its gates, or its code repo. Repo-standing
conventions (git staging, scratch dirs, commit style) are not session
constraints — the subagent reads those.

## Parallel lanes (only when the human asks for them)

The loop above is serial. When the human rules a drive parallel (lanes in
separate worktrees, each on its own CPU slice), the controller writes common
briefs and runs each lane through the plugin's review loop:

- Coder brief: copy [`coder-brief.md`](coder-brief.md), fill its **Project
  specifics** from the project's epic-drive doc.
- Planner brief, for a ticket too big for one coder or one that keeps coming
  back partial: copy [`planner-brief.md`](planner-brief.md) the same way.
- Code, coverage check, fresh review and fix rounds per lane: the
  `/epic-drive:review-loop` workflow. Its args shape is in the plugin README.

## Escalation

| Subagent came back with | You do |
|---|---|
| Closed | Next round. |
| Closed, red gate was its own in-flight edit, fixed before commit, final run green | Next round. That is the TDD loop working. |
| Any gate red on the unmodified base (what used to be reported as "pre-existing") | **Stop the line.** The red is the next round's ticket, at priority 0, ahead of the epic; nothing merges or pushes until it is green, except the fix for that red. Never brief the next worker with a "known-red" list. |
| Closed, but the *final* run of any gate is red, or the report cannot say whether a red was own-edit or on the unmodified base | **Stop the loop.** Its verdict does not override its own evidence; the human decides. |
| Blocked, concrete reason | Leave blocked, next round. Note it. If the reason is an open ticket outside the epic, that ticket is a round (see **An outside blocker is in scope**). |
| Stopped mid-work, no report (a stray sentence, no verdict) | **Resume that same agent**, do not re-dispatch: its worktree is dirty and a fresh agent cannot tell whose edits those are. Send it the recipe's report line again. |
| Open, work incomplete, worktree clean | Re-dispatch once with its own comment as the pointer. Still open → escalate. |
| A conflict between two stated policies, or a call it says needs a human | **Stop the loop.** One paragraph to the user. Do not resolve it by reading the ticket yourself. |

Ledger comes back empty — the epic has no children at all, or every open row
is HITL? **Stop the loop.** An empty epic is the one other time reading the
epic body is correct: it will say why (often "spike first, the spike's output
is the ticket list"). Quote that to the user and ask whether to file the
first ticket. Do not file it yourself, and do not dispatch a subagent against
the epic id.

**An outside blocker is in scope.** A leaf is held only by open
`blocks=` targets outside this epic, or a worker reports it blocked on an
outside ticket. Work that blocker as a round of its own:
- Dispatch the recipe with `<id>` set to the blocker. Set `<epic-ref>` to the
  blocker's own epic, so its follow-ups file there.
- If the blocker is itself held by another outside ticket, recurse.
- Once it closes, the held leaf is dispatchable again. It has priority over
  an older free leaf, because it is the reason the round ran.
- Name the outside ticket to the user in that round's report.

## Common mistakes

| Mistake | Fix |
|---|---|
| Dispatch prompt restates the ticket's gap, scope, or acceptance criteria | Delete it. Line 3 of the recipe already points there. |
| Dispatch prompt lists the repo's git/scratch/commit conventions | Delete it. The subagent reads CLAUDE.md. |
| Ran a workspace-wide ready/list query | The scoped **ledger** already carries `blocks=`. |
| Read any body — a ticket's, a sibling's, the epic's — to pick the next dispatch | The ledger row is the whole answer: oldest open leaf, `blocks=` says why one is not ready. The epic body is read once, at the done-check. |
| Bar went *down* and you called it a regression | Workers file follow-ups under the epic; they join the drive. Keep working until the ledger is empty. |
| Stopped with follow-ups still open, calling them "the next drive" | Follow-ups filed under the epic are this drive. Work them. |
| Bar hits 100%, declared done | The epic body's acceptance checklist has non-leaf items. Verify them. |
| Held the loop's state in your head | The tracker is the state. Re-read the ledger every round. |
| Skipped a claimed or `in-progress` leaf as "someone else's" | It is a stalled ticket. Dispatch it; the subagent reads its comments. |
| Dispatched a HITL ticket (grilling, prototype, ready-for-human) | A subagent cannot speak for the human. Skip it; name it to the user. |
| A worker built the self-contained part of a ticket (a helper, a buffer API) and reported the coupled core as "remaining" | That is a partial ticket, not progress to bank. Re-dispatch once, naming the missing items by their upstream symbols. If it comes back partial again, the ticket is cut wrong: dispatch a planner to split it core-first, with the hard part in the first slice and a prerequisite check by struct field. |
| A ticket's comments show the same "remaining" list across several rounds | Each round is doing the easy half. Stop re-dispatching it as-is; plan the split first. |
| A goal continuation became a short-wait/status-update loop | Follow **Waiting for a worker**: one long interruptible notification wait, with no status polling or recurring waiting replies. |
