# Pull Requests

## View

```bash
fj pr view <N>                             # Summary
fj pr view <N> body                        # Title + body
fj pr view <N> comments                    # All comments
fj pr view <N> diff                        # Full diff
fj pr view <N> files                       # Changed files list
fj pr view <N> commits                     # Commit list
```

## Search

```bash
fj pr search "query"
fj pr search -s open
fj pr search -a <user>
```

## Create

```bash
fj pr create "Title" --body "text"
fj pr create "Title" --body-file /path/to/file.md
fj pr create --autofill                    # Title/body from commits
fj pr create "WIP: Title"                  # Creates draft PR
fj pr create "Title" --base main --head feature-branch
```

## Edit

```bash
fj pr edit <N> title "New Title"
fj pr edit <N> body "New body"
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
```

## Status & Checkout

```bash
fj pr status <N>                           # CI/merge status
fj pr status <N> --wait                    # Wait for checks
fj pr checkout <N>                         # Checkout PR branch
```
