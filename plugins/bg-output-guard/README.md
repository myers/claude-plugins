# bg-output-guard

Blocks output-truncating filter pipes on **background** Bash commands so the full log is
preserved in the harness output file — and ships a skill explaining how background command
output works.

## The problem

When a Bash command runs with `run_in_background: true`, its stdout and stderr are written
to a temp output file that the harness UI shows. If the command ends with a filter like
`| tail`, `| grep`, or `| head`, that filter throws away most of the output **before it
reaches the file**. The rest of the log is then lost — from the UI and from any later
inspection — with no upside, since the agent could just as easily filter the file
*afterward*.

## What it does

A **PreToolUse** hook on `Bash`:

- Only acts on **background** commands (`run_in_background: true`). Foreground commands are
  untouched, because their output goes to context where filtering is legitimate.
- Inspects the **final stage** of the pipeline. If it's a known output-destroying filter
  (`tail head grep egrep fgrep rg ag sed awk cut uniq wc sort less more`), the command is
  **blocked** with guidance to run it unfiltered and filter the output file afterward.
- **Allows** `tee` (it writes a full copy) and filters that appear mid-pipeline.

The bundled **`background-command-output` skill** documents the behavior: where background
output goes, that stdout *and* stderr are captured by default, why not to filter at the
pipe, and how to retrieve/filter the full log afterward.

## Installation

```bash
/plugin marketplace add myers/claude-plugins
/plugin install bg-output-guard@myers-plugins
```

## How the right pattern looks

```
# Instead of:  cargo build 2>&1 | tail -n 50   (run_in_background: true)
# Run:
cargo build                                     (run_in_background: true)
# then, when it completes, filter the OUTPUT FILE:
tail -n 50 <output-file>
grep -n 'error' <output-file>
```

## Caveat

The pipe-splitting is a heuristic (it splits on the last top-level `|`), not a full shell
parser. It can be fooled by `|` inside quotes or subshells, but errs toward **allowing**
(false negatives) rather than blocking legitimate commands.

## Tests

`tests/test-hook.sh` exercises the hook by constructing the stdin JSON the harness sends
(via `jq -n`), running the script, and asserting on its exit code (2 = block, 0 = allow).
It exits non-zero if any case fails, so it works as a CI check.

```bash
plugins/bg-output-guard/tests/test-hook.sh
```

## Plugin structure

```
bg-output-guard/
├── .claude-plugin/plugin.json
├── hooks/
│   ├── hooks.json
│   └── scripts/block-bg-filter.sh
├── skills/background-command-output/SKILL.md
├── tests/test-hook.sh
└── README.md
```
