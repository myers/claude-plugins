# work-epic ops: Gitea (`gtx`)

Run from the repo clone; `gtx` infers the repo from `origin`. The epic is a
**milestone**. The user may name it by the milestone title or by an issue
number whose milestone it is (a wayfinder map or an epic issue). That issue
is the epic body, and is excluded from the ledger. With a bare milestone, the
milestone description is the epic body. `<epic-ref>` in the dispatch recipe
is `milestone "<title>"` (plus `, epic issue #<n>` when there is one).

- **ledger** and **bar**, in one call:
  ```bash
  ${CLAUDE_SKILL_DIR}/gitea-ledger.sh <issue-number | "milestone title">
  ```
  One row per open issue, oldest first:
  `<n> open assignee=<login|-> blocks=<open blockers> labels=<…> <title>`.
  `blocks=` already lists only *open* blockers, so an empty `blocks=` is
  unblocked; `<n>@outside` is a blocker in another milestone (see **An
  outside blocker is in scope**). The last line is the bar. Gitea has no
  `in-progress` state: an assignee is the claim.
- **status check**: `gtx issue view <n> --json state,labels --jq '"\(.state) \([.labels[].name])"'`.
- **sync**: push each code repo the worker touched. The tracker is the Gitea
  server, so there is nothing else to push.
- **file a follow-up**: `gtx issue create --milestone "<title>" …`, following
  any child-ticket convention in the repo's `docs/agents/issue-tracker.md`
  (the worker does this).
- **HITL rows**: labels `ready-for-human`, `wayfinder:grilling`,
  `wayfinder:prototype`. A wayfinder map's tickets are mostly HITL; this loop
  works its `wayfinder:research` and AFK `wayfinder:task` rows, and the
  implementation milestones that come after the map.
- **Blocked**: Gitea has no blocked status. A blocked worker leaves the issue
  open with a comment saying why; its report tells you.
