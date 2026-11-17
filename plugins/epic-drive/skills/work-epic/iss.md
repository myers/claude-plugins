# work-epic ops: git-issues (`iss`)

Run from the tracker root. `<epic>` is the epic's hex id or slug; `<epic-ref>`
in the dispatch recipe is the epic id.

- **ledger**:
  ```bash
  iss ls --parent <epic> --status all --json \
    | jq -r '.[] | select(.status!="closed" and .status!="abandoned")
            | "\(.created_at) \(.id) \(.status) \(.slug) labels=\(.labels|join(",")) blocks=\([.dependencies[]? | select(.kind=="blocks") | .target] | join(","))"' | sort
  ```
  `blocks=` lists every blocker; check each target's status in the same
  ledger, or with the status check when it is outside. The epic's hex id works
  as `--parent` — never `iss show <epic>` for its slug (`iss show <epic> --json
  | jq -r .slug` gets it without the body). `--json` without the `jq`
  projection dumps every ticket's `body` and `comments` into your context —
  always project. Never run `iss ready`, in any form: it is a whole-workspace
  dump.
- **bar**: `iss dep progress <epic>`.
- **status check**: `iss show <id> --json | jq -r '"\(.status) \(.labels)"'`.
  (`iss show <id> | tail -5` prints the body's tail and no status — it fails
  the check and leaks what you must not read.)
- **sync**: push each code repo the worker touched, then `iss push origin`.
- **file a follow-up**: `iss new --parent <epic> …` (the worker does this).
- **HITL rows**: labels `ready-for-human`, `wayfinder:grilling`,
  `wayfinder:prototype`.
