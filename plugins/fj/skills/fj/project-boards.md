# Project Boards (Kanban)

## View

```bash
fj project list                            # List projects in repo
fj project board                           # Show full board
fj project board "Board Name"              # Specific board
fj project board -v                        # Verbose (assignees, labels)
fj project board -c "In Progress"          # Filter by column
```

## Issue Status

```bash
fj project status <ISSUE_NUM>              # Which column is issue in?
```

## Move Issues

```bash
fj project move <ISSUE_NUM> "To Do"        # Move to column
fj project move <ISSUE_NUM> "Done" --position 1  # Move to top
```

## Known Bug

`fj project add` often fails with "Issue does not belong to project repository" even when correct. Workaround: add issues to projects via the web UI, then use `fj project move` to manage them.

## Important: `-R` does NOT work with project commands

Use `-r owner/repo` instead:
```bash
fj project board -r owner/repo
fj project status 11 -r owner/repo
```
