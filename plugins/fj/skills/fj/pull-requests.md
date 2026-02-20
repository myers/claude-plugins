# Pull Requests

## View

```bash
fj pr view <N>                             # Summary
fj pr view <N> body                        # Title + body
fj pr view <N> comments                    # All comments
fj pr view <N> diff                        # Full diff
fj pr view <N> files                       # Changed files list
fj pr view <N> commits                     # Commit list
fj pr view <N> labels                      # Labels on the PR
```

## Search

```bash
fj pr search "query"
fj pr search -s open                       # By state (open/closed/all)
fj pr search -a <user>                     # By assignee
fj pr search -c <user>                     # By creator
fj pr search -l "bug,urgent"               # By labels
```

## Create

```bash
fj pr create "Title" --body "text"
fj pr create "Title" --body-file /path/to/file.md
fj pr create -A                            # Autofill title/body from commits
fj pr create "WIP: Title"                  # Creates draft PR
fj pr create "Title" --base main --head feature-branch
fj pr create "Title" --assignee user1,user2
fj pr create --web                         # Open creation page in browser
```

### Image Uploads

Local file paths in markdown `--body` or `--body-file` are automatically uploaded as attachments and their URLs rewritten:
```bash
fj pr create "Title" --body '![before-after](./screenshot.png)'
```

## Edit

Uses subcommand style:

```bash
fj pr edit <N> title "New Title"
fj pr edit <N> body "New body"
fj pr edit <N> labels                      # Edit labels
```

`edit body` does NOT support `--body-file`. For long content:
```bash
fj pr edit <N> body "$(cat /path/to/body.md)"
```

## Comment

```bash
fj pr comment <N> "Comment text"
fj pr comment <N> --body-file /path/to/file.md
```

## Merge

```bash
fj pr merge <N>                            # Default merge
fj pr merge <N> -M squash -d               # Squash + delete branch
fj pr merge <N> -M rebase -d               # Rebase + delete branch
fj pr merge <N> -t "Merge title" -m "Merge body"
```

## Status & Checkout

```bash
fj pr status <N>                           # CI/merge status
fj pr status <N> --wait                    # Wait for checks
fj pr checkout <N>                         # Checkout PR branch
fj pr checkout <N> --branch-name my-branch # Custom branch name
```
