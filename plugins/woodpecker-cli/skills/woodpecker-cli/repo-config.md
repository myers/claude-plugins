# Repository Configuration

## View Repository

```bash
woodpecker-cli repo show owner/repo
woodpecker-cli repo ls                               # List all active repos
woodpecker-cli repo ls --org myorg                   # Filter by organization
woodpecker-cli repo ls --all                         # Include inactive repos
```

## Update Repository Settings

```bash
woodpecker-cli repo update owner/repo --timeout 30m
woodpecker-cli repo update owner/repo --visibility public
woodpecker-cli repo update owner/repo --config .woodpecker.yml
woodpecker-cli repo update owner/repo --trusted-network
woodpecker-cli repo update owner/repo --trusted-volumes
woodpecker-cli repo update owner/repo --trusted-security
woodpecker-cli repo update owner/repo --require-approval "forks"
```

## Secrets

All secret commands use `--name` and `--value` flags, NOT positional arguments.

```bash
# List
woodpecker-cli repo secret ls owner/repo

# Show
woodpecker-cli repo secret show owner/repo --name MY_SECRET

# Add
woodpecker-cli repo secret add owner/repo --name MY_SECRET --value "secret-value"
woodpecker-cli repo secret add owner/repo --name MY_SECRET --value "val" --event push --event tag

# Update
woodpecker-cli repo secret update owner/repo --name MY_SECRET --value "new-value"

# Remove
woodpecker-cli repo secret rm owner/repo --name MY_SECRET
```

Organization-level secrets:
```bash
woodpecker-cli org secret ls --org myorg
woodpecker-cli org secret add --org myorg --name MY_SECRET --value "secret-value"
```

## Registries (Docker Auth)

Registry commands use `--hostname`, `--username`, `--password` flags.

```bash
# List
woodpecker-cli repo registry ls owner/repo

# Show
woodpecker-cli repo registry show owner/repo --hostname registry.example.com

# Add
woodpecker-cli repo registry add owner/repo --hostname registry.example.com --username user --password pass

# Update
woodpecker-cli repo registry update owner/repo --hostname registry.example.com --username user --password newpass

# Remove
woodpecker-cli repo registry rm owner/repo --hostname registry.example.com
```

## Cron Jobs

Cron commands use `--name`, `--branch`, `--schedule`, and `--id` flags.

```bash
# List
woodpecker-cli repo cron ls owner/repo

# Show
woodpecker-cli repo cron show owner/repo --id 5

# Add
woodpecker-cli repo cron add owner/repo --name "nightly" --branch main --schedule "0 0 * * *"

# Update
woodpecker-cli repo cron update owner/repo --id 5 --name "nightly" --schedule "0 2 * * *"

# Remove
woodpecker-cli repo cron rm owner/repo --id 5
```

## Other Operations

```bash
woodpecker-cli repo add <forge-remote-id>            # Add repo from forge
woodpecker-cli repo rm owner/repo                    # Remove repo
woodpecker-cli repo repair owner/repo                # Repair webhooks
woodpecker-cli repo chown owner/repo                 # Take ownership
woodpecker-cli repo sync                             # Sync repo list from forge
```
