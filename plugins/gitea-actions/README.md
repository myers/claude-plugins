# gitea-actions

A `Stop` hook that tells the agent when Gitea Actions CI has gone red, read
through [`gtx`](https://gt.monoloco.net). The Gitea twin of `woodpecker-cli`'s
`ci-watch`; see that README for the reasoning behind the design.

## What it says

```
CI is red on <slug> (<branch>):
  <workflow> run <id> <conclusion>, failing: <jobs>

Launch a subagent to fix it. Logs:
  gtx run view <id> --repo <slug>
  gtx run view <id> --repo <slug> --log-failed

Done when a new run goes green.
```

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

- **Interval.** At most one poll per repo per 10 minutes.
- **Dedupe.** Each set of red run ids is nudged once.
- **Strikes.** Three consecutive nudges without a green, then silence until one.

State lives in `~/.cache/claude-gitea-ci-watch/<slug>.json`, shared by every
session on the machine.

## Fail-silent

A broken watcher exits 0: `gtx` missing, erroring, slow (8-second timeout), or
unparseable; the cwd not a git repo; a corrupt cache file. Set `CI_WATCH=0` to
disable it (this also disables `woodpecker-cli`'s hook).

## Testing

`tests/test-ci-watch.py`, plain asserts, run it directly. Every brake and
fail-silent path has a test that goes red when that guard is removed.
