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

A **PreToolUse** hook on `Bash` that only acts on **background** commands
(`run_in_background: true`) — foreground commands are untouched, since their output goes to
context where filtering is legitimate. It has three tiers:

1. **Block — trailing filter pipe.** If the final stage of the pipeline is a known
   output-destroying filter (`tail head grep egrep fgrep rg ag sed awk cut uniq wc sort
   less more`), the command is denied with guidance to run it unfiltered and filter the
   output file afterward. `tee` (writes a full copy) and mid-pipeline filters are allowed.
2. **Block — stderr suppression.** If the command diverts stderr away from the log
   (`2>/dev/null`, `2> file`, `&>`, `>&`), it's denied — stderr is captured to the log file
   for free and is where build errors and warnings live. `2>&1` (merges into stdout) is
   allowed.
3. **Warn — any other pipe or output redirect.** A non-blocking note (the command still
   runs) reminding that pipes/redirects in background mode may reshape what reaches the log.

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

## Caveats

The matcher is a heuristic, not a full shell parser. Before checking for operators it
blanks out the contents of single- and double-quoted strings, so operator-looking text in
arguments (`echo "use | tail"`, `grep "a|b"`) is **not** mistaken for a real pipe or
redirect. It does not handle every shell construct, though:

- **Known false negatives (truncation slips through):** a filter that isn't the final pipe
  stage is missed — e.g. `cmd | tail | cat` is allowed because `cat`, not `tail`, is last.
  Wrapper forms like `cmd | env tail` or `cmd | command tail` also evade the name match.
  These are honest-mistake bypasses, not adversarial concerns — the hook guards a habit,
  not an attacker.
- **Not handled:** escaped quotes (`\"`), heredocs, and `|`/redirects produced by
  subshell/`eval` expansion. Escaped-quote edge cases can still misfire in either
  direction.

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
