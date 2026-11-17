# work-epic

Drive an epic to done by delegating its issues to subagents, with the
controller's context spent on the ledger and never on ticket bodies.

- **`work-epic` skill** (`skills/work-epic/`): the controller loop. Ledger,
  pick the oldest unblocked leaf, dispatch one fresh subagent with a fixed
  pointer prompt, check, sync, bar, repeat. Ops files for git-issues (`iss`)
  and Gitea (`gtx`, with `gitea-ledger.sh`).
- **`working-an-issue` skill** (`skills/working-an-issue/`): what each
  dispatched subagent follows on its one issue, for either tracker: read,
  claim, do the work, post the four-section closing comment, change status.
- **Brief templates** (`skills/work-epic/coder-brief.md`,
  `planner-brief.md`): the project-independent rules for parallel-lane coders
  and planners (whole slice, core first, first test exercises the core,
  prerequisites by struct field, findings fixed-or-notfixed, reviewer
  checklist, block-not-yield on gates, report format, exact-path staging).
  Each ends in a **Project specifics** section the controller fills from the
  project's own drive notes.
- **`review-loop` workflow** (`workflows/review-loop.js`, run as
  `/work-epic:review-loop`): per lane item, optionally code the slice, check
  the diff covers the plan (sending a partial slice back to the coder, twice
  at most), then a fresh-context review, and fix plus re-review until APPROVE
  or the round limit. After a REJECT, items with `code` get the coverage check
  again; plan items still missing go to a continuation coder before the fix
  round.

## Install and update

```
/plugin marketplace add myers/claude-plugins
/plugin install work-epic@myers-plugins
```

Update with `/plugin marketplace update myers-plugins`, then reinstall or
restart so the new version loads.

## review-loop args

Pass an object (or a bare `items` array, with no drive settings):

```json
{
  "drive": {
    "preamble": "Text that opens every agent prompt: who dispatched it, the human's authorization, tracker and root.",
    "coderBrief": "/abs/path/to/filled/coder-brief.md",
    "epic": "epic-slug-for-follow-ups",
    "reviewSkills": ["work-epic:working-an-issue", "c-to-rust-superpowers:faithful-port-review"],
    "reviewRead": "the epic's drive ruling and fixture rules",
    "reviewChecks": ["every fixture in an upstream-reachable state"],
    "gates": ["cargo clippy --workspace --all-targets -- -D warnings", "taskset -c {cpus} cargo nextest run -p <touched crates>"],
    "ci": "Push the head with git push -f origin <branch>, find its run, wait in the foreground, gate on it.",
    "cpus": "0-7",
    "maxRounds": 3,
    "reviewModel": "opus"
  },
  "items": [
    {
      "key": "lane-a",
      "branch": "issue/lane-a",
      "worktree": "/abs/wt/lane-a",
      "base": "main or a sha",
      "code": "Slice text for the coder; omit to start at review",
      "commits": "commit list for review; derived from the coder when omitted",
      "issues": "slug-one, slug-two",
      "plan": "/abs/path/plan.md, slice C1",
      "plan_items": ["dbuf_dirty", "dbuf_dirty_record_t", "test dirty_record_on_dn_dbufs"],
      "focus": "anything the reviewer must judge specifically",
      "startFix": { "head": "sha", "blocking": ["finding text"] },
      "cpus": "8-15",
      "drive": { "maxRounds": 2 }
    }
  ]
}
```

Every `drive` field is optional; an item's `drive` overrides it for that
item. `{cpus}` in a gate becomes the item's slice. With `plan_items`, the
coverage check and the reviewer look for exactly that list; without it, the
checker derives the list from `code` and `plan`.

Each item returns `{key, branch, verdict, head, rounds, blocking, summary}`,
where `verdict` is `APPROVE`, `REJECT` (rounds ran out), `INCOMPLETE` (the
coder twice shipped a partial slice; `blocking` lists the missing items) or
`ERROR`.
