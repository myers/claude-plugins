# Project Boards (Kanban)

## View

```bash
fj project list                            # List projects in repo
fj project list -s all                     # Include closed projects
fj project list -o <org>                   # List org projects
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
fj project move <ISSUE_NUM> "Done" -p "Board Name"  # Specify project
```

## Remote Repo Access

Both `-R` (on the parent) and `-r` (on the subcommand) work:
```bash
fj project -R origin board                 # Use git remote
fj project board -r owner/repo             # Use repo path directly
fj project status 11 -r owner/repo
```

## Known Bug

`fj project add` often fails with "Issue does not belong to project repository" even when correct. Workaround: add issues to projects via the web UI, then use `fj project move` to manage them.
