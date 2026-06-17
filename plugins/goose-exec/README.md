# goose-exec

Delegate plan **execution** to [goose](https://github.com/block/goose) — a headless coding
agent you've configured to run a cheaper model (e.g. DeepSeek) — while Claude stays the
**orchestrator and reviewer**.

The idea: Claude is expensive but excellent at planning and reviewing; a cheaper model in
goose is fine at grinding through implementation. So Claude writes/approves the plan, then
dispatches `goose run` per task, reviews the diff (spec compliance → code quality), and only
moves on once tests pass.

Key piece: **follow-up commands in the same goose context** via named, resumable sessions
(`goose run -r -n <name> -t "..."`), so rework and next sub-steps keep goose's memory of what
it just did.

> goose's model/provider setup (pointing it at DeepSeek) is out of scope for this skill — it
> assumes goose is already configured.

## Installation

```
/plugin install goose-exec@myers-plugins
```

## Files

- `skills/goose-exec/SKILL.md` — the workflow: division of labor, the per-task loop, and
  continuing the same goose session.
- `skills/goose-exec/templates.md` — copy-paste prompt scaffolds (dispatch, rework, task files).
