# Issues

## View

```bash
fj issue view <N>                          # Summary (default: shows body)
fj issue view <N> body                     # Title + body
fj issue view <N> comments                 # All comments
fj issue view <N> comment <IDX>            # Specific comment
```

## Search

```bash
fj issue search "query"                    # By text
fj issue search -s open                    # By state (open/closed/all)
fj issue search -a <user>                  # By assignee
fj issue search -c <user>                  # By creator
fj issue search -l "bug,urgent"            # By labels
```

## Create

```bash
fj issue create "Title" --body "text"
fj issue create "Title" --body-file /path/to/file.md
fj issue create "Title" --assignee user1,user2
fj issue create "Title" --template "Bug Report"
fj issue create --web                      # Open creation page in browser
```

### Image Uploads

Local file paths in markdown `--body` or `--body-file` are automatically uploaded as attachments and their URLs rewritten:
```bash
fj issue create "Bug" --body '![screenshot](./error.png)'
fj issue create "Bug" --body-file report.md   # refs like ![img](./pic.png) in file work too
```

## Edit

Uses subcommand style, NOT flags:

```bash
fj issue edit <N> title "New Title"
fj issue edit <N> body "New body text"
fj issue edit <N> assign <user>
fj issue edit <N> unassign <user>
```

`edit body` does NOT support `--body-file`. For long content:
```bash
fj issue edit <N> body "$(cat /path/to/body.md)"
```

## Edit Comment

```bash
fj issue edit <N> comment <IDX> "edited text"
```

## Comment

```bash
fj issue comment <N> "Comment text"
fj issue comment <N> --body-file /path/to/file.md
```

## Close

```bash
fj issue close <N>
fj issue close <N> -w "Closing because..."   # Close with a comment
```
