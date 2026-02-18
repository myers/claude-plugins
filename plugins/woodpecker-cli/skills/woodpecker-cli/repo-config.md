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

```bash
# List
woodpecker-cli repo secret ls owner/repo

# Show
woodpecker-cli repo secret show owner/repo <name>

# Add
woodpecker-cli repo secret add owner/repo <name> <value>

# Update
woodpecker-cli repo secret update owner/repo <name> <value>

# Remove
woodpecker-cli repo secret rm owner/repo <name>
```

Organization-level secrets:
```bash
woodpecker-cli org secret ls <org>
woodpecker-cli org secret add <org> <name> <value>
```

## Registries (Docker Auth)

```bash
woodpecker-cli repo registry ls owner/repo
woodpecker-cli repo registry add owner/repo <address> <username> <password>
woodpecker-cli repo registry update owner/repo <address> <username> <password>
woodpecker-cli repo registry rm owner/repo <address>
woodpecker-cli repo registry show owner/repo <address>
```

## Cron Jobs

```bash
woodpecker-cli repo cron ls owner/repo
woodpecker-cli repo cron show owner/repo <cron-id>
woodpecker-cli repo cron add owner/repo <name> <schedule> <branch>
woodpecker-cli repo cron update owner/repo <cron-id> --name "nightly" --schedule "0 0 * * *"
woodpecker-cli repo cron rm owner/repo <cron-id>
```

## Other Operations

```bash
woodpecker-cli repo add <forge-remote-id>            # Add repo from forge
woodpecker-cli repo rm owner/repo                    # Remove repo
woodpecker-cli repo repair owner/repo                # Repair webhooks
woodpecker-cli repo chown owner/repo                 # Take ownership
woodpecker-cli repo sync                             # Sync repo list from forge
```
