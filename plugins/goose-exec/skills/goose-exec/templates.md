# goose-exec prompt templates

Copy-paste scaffolds for driving goose through a plan. Fill in the `<...>` parts.

## Per-task instruction file (`task-N.md`)

Write the task to a file and pass it with `-i`. Keeps the prompt out of the shell and
versionable.

```markdown
# Task <N>: <short title>

## Goal
<one or two sentences on what to build>

## Context
- Relevant files: <paths>
- Interface/contract to match: <signatures, schema, API shape>
- Conventions: <link or note repo conventions to follow>

## Do
- <concrete step>
- <concrete step>

## Acceptance criteria
- <observable, checkable outcome>
- <e.g. `pytest tests/test_health.py` passes>

## Constraints
- Only modify files under <dir>.
- Do NOT change <thing that must stay stable>.
- Run the relevant tests when done and report the result.
```

Dispatch it in a named session:

```bash
goose run -n task-<N> -i task-<N>.md -q
```

## Inline dispatch

```bash
goose run -n task-<N> -t "Implement task <N>: <goal>. Only touch <dir>. \
Acceptance: <criteria>. Run <test cmd> when done." -q
```

## Rework (same session, keeps context)

```bash
goose run -r -n task-<N> -t "Review found these issues:
1. <issue + where>
2. <issue + where>
Fix exactly these. Don't change anything else. Re-run <test cmd>." -q
```

## Follow-up / next sub-step (same session)

```bash
goose run -r -n task-<N> -t "That works. Now also <next thing>, consistent with what you just wrote." -q
```

## Long run in the background

Let the full log reach the output file; read it when the task notification arrives.

```bash
# run_in_background: true
goose run -n task-<N> -i task-<N>.md -q
# then Read the output file, and:
git --no-pager diff
```

## Machine-readable result (for scripted loops)

```bash
goose run -n task-<N> -i task-<N>.md --output-format json -q > task-<N>.result.json
```
