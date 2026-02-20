# Repositories

## View

```bash
fj repo view                               # Current repo info
fj repo view owner/repo                    # Specific repo
fj repo readme                             # View README
fj repo browse                             # Open in browser
```

## Create

```bash
fj repo create "name"                      # Create new repo
fj repo create "name" -d "Description"     # With description
fj repo create "name" -P                   # Create as private
fj repo create "name" -p                   # Create + push current branch
fj repo create "name" -r origin            # Create + add as remote
```
