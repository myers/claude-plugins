---
name: fj
description: Forgejo CLI for managing issues, PRs, and project boards. Use when asked to interact with Forgejo repositories — creating issues, viewing PRs, managing kanban boards, etc.
allowed-tools: Bash, Read, Write
---

# Forgejo CLI (fj)

`fj` is a CLI client for Forgejo (a Gitea fork). Use it instead of `gh` when working with Forgejo repositories.

## Quick Reference

### Authentication

```bash
fj whoami          # Check current user
fj auth login      # Authenticate
```

### Issues

```bash
# View
fj issue view <N>                          # Summary
fj issue view <N> body                     # Title + body
fj issue view <N> comments                 # All comments
fj issue view <N> comment <IDX>            # Specific comment

# Search
fj issue search "query"                    # By text
fj issue search -s open                    # By state
fj issue search -a <user>                  # By assignee
fj issue search -l "bug,urgent"            # By labels

# Create
fj issue create "Title" --body "text"
fj issue create "Title" --body-file /path/to/file.md
fj issue create "Title" --assignee user1,user2

# Edit (note: subcommand style, NOT --flags)
fj issue edit <N> title "New Title"
fj issue edit <N> body "New body text"
fj issue edit <N> body --body-file /path/to/file.md
fj issue edit <N> assign <user>
fj issue edit <N> unassign <user>

# Comment
fj issue comment <N> "Comment text"
fj issue comment <N> --body-file /path/to/file.md
fj issue edit <N> comment <IDX> "edited text"

# Close
fj issue close <N>
```

### Pull Requests

```bash
# View
fj pr view <N>                             # Summary
fj pr view <N> body                        # Title + body
fj pr view <N> comments                    # All comments
fj pr view <N> diff                        # Full diff
fj pr view <N> files                       # Changed files list
fj pr view <N> commits                     # Commit list

# Search
fj pr search "query"
fj pr search -s open
fj pr search -a <user>

# Create
fj pr create "Title" --body "text"
fj pr create "Title" --body-file /path/to/file.md
fj pr create --autofill                    # Title/body from commits
fj pr create "WIP: Title"                  # Creates draft PR
fj pr create "Title" --base main --head feature-branch

# Edit
fj pr edit <N> title "New Title"
fj pr edit <N> body "New body"

# Comment
fj pr comment <N> "Comment text"
fj pr comment <N> --body-file /path/to/file.md

# Merge
fj pr merge <N>                            # Default merge
fj pr merge <N> -M squash -d               # Squash + delete branch
fj pr merge <N> -M rebase -d               # Rebase + delete branch

# Status & checkout
fj pr status <N>                           # CI/merge status
fj pr status <N> --wait                    # Wait for checks
fj pr checkout <N>                         # Checkout PR branch
```

### Project Boards (Kanban)

```bash
# View
fj project list                            # List projects in repo
fj project board                           # Show full board
fj project board "Board Name"              # Specific board
fj project board -v                        # Verbose (assignees, labels)
fj project board -c "In Progress"          # Filter by column

# Issue status
fj project status <ISSUE_NUM>              # Which column is issue in?

# Move issues
fj project move <ISSUE_NUM> "To Do"        # Move to column
fj project move <ISSUE_NUM> "Done" --position 1  # Move to top

# Note: fj project add has a bug — use the web UI to add issues to projects
```

### Repositories

```bash
fj repo view                               # Current repo info
fj repo readme                             # View README
fj repo browse                             # Open in browser
fj repo create "name"                      # Create new repo
```

## Important Quirks

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

When the content is more than a line or two, write it to a temp file first:
```bash
# Write content to temp file, then use --body-file
echo "Long body content here..." > /tmp/body.md
fj issue edit 11 body --body-file /tmp/body.md
```

### `fj project add` is buggy

`fj project add` often fails with "Issue does not belong to project repository" even when correct. Workaround: add issues to projects via the web UI, then use `fj project move` to manage them.
