---
name: fj
description: Forgejo CLI for managing issues, PRs, and project boards. Use when asked to interact with Forgejo repositories — creating issues, viewing PRs, managing kanban boards, etc.
allowed-tools: Bash, Read, Write
---

# Forgejo CLI (fj)

`fj` is a CLI client for Forgejo (a Gitea fork). Use it instead of `gh` when working with Forgejo repositories.

## Task Reference Files

Read the relevant topic file(s) based on what the agent needs to do:

- **issues.md** — View, search, create, edit, comment on, and close issues
- **pull-requests.md** — View, search, create, edit, merge PRs; check CI status
- **project-boards.md** — View kanban boards, move issues between columns, check status
- **repos.md** — View repo info, README, browse, create repos

## Important Quirks (Always Read)

### The `-R` flag goes AFTER the subcommand group

```bash
# CORRECT
fj issue -R origin view 11
fj pr -R origin view 5

# WRONG
fj -R origin issue view 11
```

### `fj project` subcommands do NOT accept `-R`

Use `-r owner/repo` instead:
```bash
fj project board -r owner/repo
fj project status 11 -r owner/repo
```

### `body` is a subcommand, not a flag

```bash
# CORRECT - editing issue body
fj issue edit 11 body "new content"
fj issue edit 11 body --body-file /path/to/file.md

# WRONG
fj issue edit 11 --body "new content"
```

### Use `--body-file` for multiline content

When the content is more than a line or two, write it to a file first:
```bash
fj issue edit 11 body --body-file /path/to/body.md
```

### `fj project add` is buggy

`fj project add` often fails with "Issue does not belong to project repository" even when correct. Workaround: add issues to projects via the web UI, then use `fj project move` to manage them.

### Authentication

```bash
fj whoami          # Check current user
fj auth login      # Authenticate
```
