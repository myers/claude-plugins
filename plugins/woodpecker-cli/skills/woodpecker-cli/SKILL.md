---
name: woodpecker-cli
description: Woodpecker CI CLI for managing pipelines, repos, secrets, and running local builds. Use when asked to interact with Woodpecker CI.
allowed-tools: Bash, Read, Write
---

# Woodpecker CI CLI

`woodpecker-cli` is the CLI client for Woodpecker CI (a lightweight CI/CD engine). Use it to manage pipelines, repositories, secrets, and run local builds.

## Task Reference Files

Read the relevant topic file(s) based on what the agent needs to do:

- **pipeline-monitoring.md** — List pipelines, view status, read logs, check queue
- **pipeline-operations.md** — Create, start, stop, deploy, approve/decline pipelines
- **repo-config.md** — View/update repos, manage secrets, registries, and cron jobs
- **local-dev.md** — Execute pipelines locally, lint configuration files
- **admin.md** — Server administration, user/org management, global secrets/registries

## Common Patterns

### Repository Argument

Most commands take `<repo-id|repo-full-name>` — use the full name like `owner/repo`:
```bash
woodpecker-cli pipeline ls owner/repo
woodpecker-cli repo show owner/repo
```

### Output Formatting

```bash
--output table                    # Default table output
--output json                     # JSON output (useful for parsing)
--output-no-headers               # Omit table headers
```

### Authentication Context

Woodpecker CLI supports multiple server contexts:
```bash
woodpecker-cli context ls         # List all contexts
woodpecker-cli context use <name> # Switch context
woodpecker-cli info               # Show current user info
```

Configure via environment variables or `woodpecker-cli setup`:
- `WOODPECKER_SERVER` — Server URL
- `WOODPECKER_TOKEN` — Auth token
