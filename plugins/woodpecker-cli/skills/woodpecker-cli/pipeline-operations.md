# Pipeline Operations

## Create a Pipeline

Trigger a new pipeline from a branch:
```bash
woodpecker-cli pipeline create owner/repo --branch main
woodpecker-cli pipeline create owner/repo --branch main --var KEY=value
woodpecker-cli pipeline create owner/repo --branch main --var KEY1=val1 --var KEY2=val2
```

## Start / Restart a Pipeline

```bash
woodpecker-cli pipeline start owner/repo <pipeline-number>
woodpecker-cli pipeline start owner/repo <pipeline-number> -p KEY=value
```

## Stop a Pipeline

```bash
woodpecker-cli pipeline stop owner/repo <pipeline-number>
```

## Kill a Pipeline (Force)

```bash
woodpecker-cli pipeline kill owner/repo <pipeline-number>
```

## Deploy

Trigger a deployment event:
```bash
woodpecker-cli pipeline deploy owner/repo <pipeline-number> <environment>
woodpecker-cli pipeline deploy owner/repo <pipeline-number> production
woodpecker-cli pipeline deploy owner/repo <pipeline-number> staging -p KEY=value
```

## Approve / Decline

For pipelines requiring manual approval:
```bash
woodpecker-cli pipeline approve owner/repo <pipeline-number>
woodpecker-cli pipeline decline owner/repo <pipeline-number>
```

## Purge Pipelines

```bash
woodpecker-cli pipeline purge owner/repo
woodpecker-cli pipeline purge owner/repo --older-than 720h   # Older than 30 days
woodpecker-cli pipeline purge owner/repo --keep-min 20       # Keep at least 20 (default: 10)
woodpecker-cli pipeline purge owner/repo --branch main       # Only purge this branch
woodpecker-cli pipeline purge owner/repo --dry-run           # Preview what would be deleted
```

## Purge Logs

```bash
woodpecker-cli pipeline log purge owner/repo <pipeline-number>
```
