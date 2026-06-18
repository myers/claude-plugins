# tail-head-block

A Claude Code plugin that blocks piping Bash tool commands to `| tail` or `| head`.

## What it does

Uses a **PreToolUse hook** on the `Bash` tool. If the command contains a pipe to `tail` or `head` (with or without arguments), the hook denies the call and tells the model to run the command in the background and Read the output file instead.

## Why?

`tail` and `head` buffer their input until EOF. For the Claude Code Bash tool, `| tail` on a foreground command means:

- The user sees nothing stream live in their terminal (tail holds every line until the upstream exits).
- The model only receives the filtered last lines at the very end.

A 5-minute build becomes opaque until it's already done — and dumping its full output into the model's context wasn't the goal either. The right answer is to keep the output **out** of model context.

## What to do instead

1. **Re-run the command with `run_in_background: true`.** The harness writes stdout/stderr to a task output file and the user can watch it live in their "N shells" pane.
2. **If the model needs to inspect the output**, use the `Read` tool on the output file. `Read` supports `offset`/`limit`, so partial reads stay cheap. The full output should not be pushed into the LLM context.

For cases where no pipe is actually needed:
- Native limits: `git log -20`, `grep -m 5`, `kubectl get pods --limit 10`
- Line selection: `sed -n 1,20p file`

## Edge cases

The regex `\|[[:space:]]*(tail|head)($|[^[:alnum:]_])` is deliberately conservative:

- Matches: `| tail`, `|tail`, `| tail -5`, `| head -10`, `| tail -f log &`, `cmd | tail -5 | cmd2`
- Skips: `| tailscale`, `| heading`, `/usr/bin/tail`, `git log -20`

False positives on quoted pipe-literals (e.g. `echo "foo | tail bar"`) are accepted — they're rare and easy to rewrite.

## Installation

```bash
/plugin marketplace add myers/claude-plugins
/plugin install tail-head-block@myers-plugins
```

## Plugin structure

```
tail-head-block/
├── .claude-plugin/
│   └── plugin.json
├── hooks/
│   ├── hooks.json
│   └── scripts/
│       └── block-tail-head.sh
└── README.md
```
