# gitea-actions

A `Stop` hook that tells the agent when Gitea Actions CI has gone red, read
through [`gtx`](https://gt.monoloco.net).

A guard nobody runs is not a guard, and a guard nobody *reads* is not a guard
either. A red run can sit on `main` for weeks while running faithfully on every
push. When the agent finishes a turn, this hook checks whether CI is red and, if
so, hands the agent the failure and tells it to launch a subagent. `Stop` is the
event because it is the only one that re-engages the agent with no human typing.

## What it says

```
CI is red on <slug> (<branch>):
  <workflow> run <id> <conclusion>, failing: <jobs>

Launch a subagent to fix it. Logs:
  gtx run view <id> --repo <slug>
  gtx run view <id> --repo <slug> --log-failed

Done when a new run goes green.
```

It states the target behaviour and the completion criterion, and leaves the
diagnosis to the agent. Everything repo-specific in it is discovered, not
configured.

## Discovery

- **Repo.** The git remote whose host matches `gtx config get default.url`,
  `origin` first, so a Gitea remote beside a GitHub `origin` is found. A repo
  with no such remote is skipped. `gtx` runs from the repo's directory with no
  `-R` and makes the same pick. A GitHub or Forgejo repo sharing an
  `owner/repo` with one on Gitea stays silent.
- **Branch** from `git symbolic-ref --short HEAD`.
- **Which runs**: per workflow, the newest `completed` run on that branch. Red is
  any conclusion but `success`, `skipped`, `neutral`, `cancelled`. Cancelled is
  usually `cancel-in-progress` superseding a run, so it is not reported.

## Brakes

A `Stop` hook that re-engages the agent needs hard limits, or a red run
re-nudges forever:

- **Interval.** At most one poll per repo per 10 minutes.
- **Dedupe.** Each set of red run ids is nudged once.
- **Strikes.** Three consecutive nudges without a green, then silence until one.

State lives in `~/.cache/claude-gitea-ci-watch/<slug>.json`, shared by every
session on the machine. That sharing is what makes the interval and the dedupe
hold across concurrent sessions: one session nudging for a run records it, and
the others read the same file and stay quiet. No lock is needed.

## Fail-silent

A broken watcher exits 0: `gtx` missing, erroring, slow (8-second timeout), or
unparseable; the cwd not a git repo; a corrupt cache file. Set `CI_WATCH=0` to
disable it for a session.

## Testing

`tests/test-ci-watch.py`, plain asserts, run it directly. Every brake and
fail-silent path has a test that goes red when that guard is removed. The
decision is a pure function of `(red runs, state) -> (nudge?, state)`, so it
tests without a network; the end-to-end tests put a fake `gtx` on `PATH`.

## Non-goals

- Re-running workflows. Retrying an infrastructure failure buys nothing.
- Any branch but the one checked out.
- Judging *why* CI is red. The agent reads the log; the hook only points at it.
