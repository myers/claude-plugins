# woodpecker-cli

Woodpecker CI for Claude Code: a skill that documents the `wp` CLI, and a `Stop`
hook that tells the agent when CI has gone red.

## Skill

`skills/woodpecker-cli/` — pipelines, repo config, secrets, local runs. Invoked
by name or when a task touches Woodpecker.

## The `ci-watch` hook

A guard nobody runs is not a guard — and a guard nobody *reads* is not a guard
either. A red pipeline can sit on `main` for weeks while running faithfully on
every push. This hook closes that gap: when the agent finishes a turn, it checks
whether CI is red and, if so, hands the agent the failure and tells it to launch
a subagent.

`Stop` is the event because it is the only one that re-engages the agent with no
human typing.

### What it says

The whole message. Everything repo-specific in it is discovered, not configured:

```
CI is red on <slug> (<branch>): pipeline <n> <status>, failing: <steps>.

Launch a subagent to fix it. Logs:
  wp pipeline ps <slug> <n>
  wp pipeline log show <slug> <n> <step-id>

Done when a new pipeline goes green.
```

It states the target behaviour and the completion criterion, and leaves the
diagnosis to the agent. It carries no opinion about what broke or how to fix it.

### Discovery, not configuration

- **Slug** from `git remote get-url origin`, scheme and `.git` stripped.
- **Branch** from `git symbolic-ref --short HEAD`.
- **Forge**: the origin's host must match the forge URL Woodpecker has the repo
  registered against (`wp repo show`). A repo that moved forges keeps its slug,
  and Woodpecker keeps its old red pipelines; this skips them.
- **Which run**: the latest pipeline on that branch whose status is settled —
  anything but `pending`, `running`, `created`.

Nothing to configure, and nothing repo-specific in the plugin.

### Brakes

A `Stop` hook that re-engages the agent needs hard limits, or a red pipeline
re-nudges forever:

- **Interval.** At most one poll (`wp repo show` + `wp pipeline ls`) per repo per 10 minutes.
- **Dedupe.** Each pipeline number is nudged exactly once.
- **Strikes.** Three consecutive nudges without a green, then silence until one.

State lives in `~/.cache/claude-ci-watch/<slug>.json`, shared by every session on
the machine. That sharing is what makes the interval and the dedupe hold across
concurrent sessions: one session nudging for pipeline 2003 records it, and the
others read the same file and stay quiet. No lock is needed.

### Fail-silent

**A broken watcher exits 0.** Every failure path returns quietly: `wp` missing,
erroring, unparseable, or slow (an 8-second timeout — `wp` has blocked past 120
seconds in practice); the cwd not a git repo; the repo not registered in
Woodpecker; a corrupt cache file, which the next write repairs.

Set `CI_WATCH=0` to disable it for a session.

### Testing

`tests/test-ci-watch.py` — plain asserts, no pytest, run it directly.
The decision is a pure function of `(wp output, state, now) -> (nudge?, state)`,
so it tests without a network. The bar: **every brake and every fail-silent path
has a test that goes red when that guard is removed.**

One integration test crosses the subprocess boundary with a fake `wp` on `PATH`.

### Non-goals

- CI backends other than Woodpecker.
- Restarting pipelines. Retrying an infrastructure failure buys nothing.
- Any branch but the one checked out.
- Judging *why* CI is red. The agent reads the log; the hook only points at it.
