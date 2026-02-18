# Issues

## View

```bash
fj issue view <N>                          # Summary
fj issue view <N> body                     # Title + body
fj issue view <N> comments                 # All comments
fj issue view <N> comment <IDX>            # Specific comment
```

## Search

```bash
fj issue search "query"                    # By text
fj issue search -s open                    # By state
fj issue search -a <user>                  # By assignee
fj issue search -l "bug,urgent"            # By labels
```

## Create

```bash
fj issue create "Title" --body "text"
fj issue create "Title" --body-file /path/to/file.md
fj issue create "Title" --assignee user1,user2
```

## Edit

Note: uses subcommand style, NOT --flags.

```bash
fj issue edit <N> title "New Title"
fj issue edit <N> body "New body text"
fj issue edit <N> body --body-file /path/to/file.md
fj issue edit <N> assign <user>
fj issue edit <N> unassign <user>
```

## Comment

```bash
fj issue comment <N> "Comment text"
fj issue comment <N> --body-file /path/to/file.md
fj issue edit <N> comment <IDX> "edited text"
```

## Close

```bash
fj issue close <N>
```
