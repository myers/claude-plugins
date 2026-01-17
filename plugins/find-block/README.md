# find-block

A Claude Code plugin that blocks the `find` command and suggests using the optimized Glob and Grep tools instead.

## What it does

This plugin uses a PreToolUse hook to intercept Bash commands before execution. When Claude attempts to use the `find` command, the hook blocks it and provides helpful guidance on using Claude Code's native tools:

- **Glob tool** - For finding files by pattern (e.g., `**/*.rs`)
- **Grep tool** - For searching code with regex patterns

## Why?

The Glob and Grep tools are optimized for Claude Code and handle permissions correctly. They're faster and more reliable than shell-based `find` commands.

## Installation

```bash
claude /install github:myers/claude-plugins/plugins/find-block
```
