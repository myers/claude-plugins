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

`-R` selects which git remote to use. It belongs on the parent command (`fj issue`, `fj pr`, `fj project`), NOT on `fj` itself or on the leaf subcommand:

```bash
# CORRECT
fj issue -R origin view 11
fj pr -R origin search -s open
fj project -R origin board

# WRONG
fj -R origin issue view 11
fj pr search -R origin -s open
```

### `body` is a subcommand, not a flag

```bash
# CORRECT - editing issue body
fj issue edit 11 body "new content"

# WRONG
fj issue edit 11 --body "new content"
```

### `--body-file` is only on `create` and `comment`, NOT on `edit body`

```bash
# CORRECT — create and comment support --body-file
fj issue create "Title" --body-file /path/to/body.md
fj issue comment 11 --body-file /path/to/body.md

# WRONG — edit body does NOT have --body-file
fj issue edit 11 body --body-file /path/to/body.md   # Will fail!

# Instead, read the file content and pass it as a positional arg
fj issue edit 11 body "$(cat /path/to/body.md)"
```

### `fj project add` is buggy

`fj project add` often fails with "Issue does not belong to project repository" even when correct. Workaround: add issues to projects via the web UI, then use `fj project move` to manage them.

### Authentication

```bash
fj whoami          # Check current user
fj auth login      # Authenticate
fj auth list       # List logged-in instances
```
