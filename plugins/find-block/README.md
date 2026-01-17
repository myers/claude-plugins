# find-block

A Claude Code plugin that blocks the `find` command and suggests using the optimized Glob and Grep tools instead.

## What it does

This plugin uses a **PreToolUse hook** to intercept Bash commands before execution. When Claude attempts to use the `find` command, the hook blocks it and provides helpful guidance on using Claude Code's native tools:

- **Glob tool** - For finding files by pattern (e.g., `**/*.rs`)
- **Grep tool** - For searching code with regex patterns

## Why?

The Glob and Grep tools are optimized for Claude Code and handle permissions correctly. They're faster and more reliable than shell-based `find` commands.

## Installation

Add the marketplace and install the plugin:

```bash
/plugin marketplace add myers/claude-plugins
/plugin install find-block@myers-plugins
```

Or install from local path during development:

```bash
/plugin marketplace add ./path/to/claude-plugins
/plugin install find-block@myers-plugins
```

## Plugin structure

```
find-block/
├── .claude-plugin/
│   └── plugin.json         # Plugin manifest
├── hooks/
│   ├── hooks.json          # Hook configuration
│   └── scripts/
│       └── block-find.sh   # PreToolUse hook script
└── README.md
```

## How it works

The hook receives JSON input via stdin containing the tool name and command. It parses the command using `jq` and checks if it starts with `find`. If so, it outputs a structured JSON response to stderr with `permissionDecision: "deny"` and exits with code 2 to block execution.
