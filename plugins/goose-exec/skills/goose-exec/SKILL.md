---
name: goose-exec
description: Delegate execution of an approved implementation plan to goose (a headless coding agent configured to run a cheaper model such as DeepSeek) while Claude stays the orchestrator and reviewer. Use after a plan is written/approved to implement plan tasks cheaply, dispatching goose per task and reviewing its work before moving on. Covers running goose headless, capturing output, and continuing follow-up commands in the SAME goose session/context.
allowed-tools: Bash, Read, Write, Edit
---

# Executing Plans with goose

The expensive model (Claude) is good at **planning and reviewing**. A cheaper model
running inside **goose** is good at **grinding through implementation**. This skill keeps
Claude as the orchestrator/reviewer and hands the actual code-writing to `goose run`.

> goose's model/provider configuration (e.g. pointing it at DeepSeek) is **out of scope** —
> assume goose is already configured. This skill only covers *driving* goose to execute a plan.

## Division of labor

| Role | Who | Does |
|------|-----|------|
| Plan | Claude | Brainstorm, design, write the task list (e.g. via superpowers / dev-plan) |
| Execute | goose | Write/edit code for one task at a time |
| Review | Claude | Inspect the diff: spec compliance, then code quality |
| Rework | goose | Fix issues — **in the same goose session** so it keeps context |
| Verify | Claude | Run tests/build before declaring a task done |

Claude never writes the implementation itself. It dispatches goose, reads the resulting
diff, and decides: accept, rework, or revert.

## The core invocation

goose runs headless with `goose run` (the goose analog of `claude -p`):

```bash
goose run -t "INSTRUCTIONS" -q            # prompt inline, quiet (response only on stdout)
goose run -i task.md -q                   # prompt from a file
echo "INSTRUCTIONS" | goose run -i - -q   # prompt from stdin
```

Useful flags:

| Flag | Purpose |
|------|---------|
| `-t, --text` | Inline instructions |
| `-i, --instructions <file>` | Instructions from a file; `-i -` reads stdin |
| `-q, --quiet` | Print only the model response to stdout |
| `-n, --name <name>` | Name the session (so you can resume it) |
| `-r, --resume` | Resume a previous run/session |
| `--output-format text\|json\|stream-json` | `json` for parseable results in scripts |
| `-s, --interactive` | Drop into interactive mode after the run (don't use for headless) |

## Continuing in the SAME goose context (the important part)

A fresh `goose run` starts with **no memory** of previous runs. To send a follow-up command
that builds on what goose just did — corrections, the next sub-step, "now also handle X" —
**name the session and resume it**:

```bash
# 1. Start the task in a NAMED session
goose run -n task-3 -t "Implement task 3 from plan.md: add the /healthz endpoint." -q

# 2. Send a follow-up into that SAME session — goose still has all prior context
goose run -r -n task-3 -t "Good. Now add a test for the 503 case you just wrote." -q

# 3. Keep going as many times as needed — same name, same context each time
goose run -r -n task-3 -t "The test fails because the timeout is 5s not 3s. Fix it." -q
```

`-r -n <name>` resumes the named session and appends your new instruction to its existing
conversation, so goose remembers the files it touched and the decisions it made. Without
`-r -n`, each call is a blank slate.

- Resume by ID instead of name if you prefer: `goose run -r --session-id 20251108_1 -t "..."`.
- Use one session name **per plan task** (e.g. `task-3`), not one giant session for the whole
  plan — this keeps each task's context focused (the same "fresh context per task" idea that
  subagent-driven development uses), while still letting you iterate within a task.

## The per-task loop

For each task in the approved plan:

1. **Checkpoint** so a bad run is reversible. Commit current state, or note it:
   ```bash
   git add -A && git commit -m "checkpoint before task 3" || true
   ```

2. **Dispatch goose** in a named session. Give it the *task*, not the whole plan, plus the
   acceptance criteria. For long runs, prefer `run_in_background: true` and read the output
   file when the task notification arrives (don't pipe goose through `tail`/`grep`):
   ```bash
   goose run -n task-3 -i task-3.md -q
   ```

3. **Review the diff** — Claude does this, in two stages:
   ```bash
   git --no-pager diff
   ```
   - **Spec compliance:** does the diff actually satisfy the task's acceptance criteria?
   - **Code quality:** correctness, edge cases, naming, no stray debug code, follows repo
     conventions.

4. **Decide:**
   - ✅ **Accept** → run tests/build to verify, then commit and go to the next task.
   - 🔁 **Rework** → send the specific findings back into the **same** session:
     ```bash
     goose run -r -n task-3 -t "Review found 2 issues: (1) ... (2) ... Fix both, don't touch anything else." -q
     ```
     Then re-review. Loop until it passes or you decide to revert.
   - ↩️ **Revert** → if goose went off the rails, throw the work away and re-dispatch with a
     sharper prompt:
     ```bash
     git checkout -- . && git clean -fd     # back to the checkpoint
     ```

5. **Verify before done** — Claude runs the project's tests/linter/build. A passing goose
   self-report is not enough; confirm it yourself.

See `templates.md` for copy-paste prompt scaffolds (dispatch, rework, per-task instruction file).

## Writing good goose task prompts

goose is the implementer, so the prompt must be self-contained:

- **One task at a time.** Don't hand goose the whole plan; give it the current task plus just
  enough surrounding context (relevant files, the interface it must match).
- **State acceptance criteria explicitly** — what "done" means and how it'll be checked.
- **Constrain blast radius** — "only modify files under `src/api/`", "don't change the
  public signature of `foo()`".
- **Tell it to run the tests** it can, but rely on Claude's verification as the gate.

## Guardrails

- **goose edits the working tree directly.** Always checkpoint with git before a run so you can
  revert. Review the diff before trusting it.
- **Don't filter goose's output through `tail`/`grep`** when running in the background — let the
  full log reach the output file, then read/filter the file (see the `bg-output-guard` skill).
- **Don't use `-s/--interactive`** for orchestrated execution — it blocks waiting for a human.
- **Trust but verify.** The whole point is offloading cost, so the review and test steps are
  where Claude earns its keep — never skip them.
