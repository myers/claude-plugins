# Pipeline Monitoring

## List Pipelines

```bash
woodpecker-cli pipeline ls owner/repo
woodpecker-cli pipeline ls owner/repo --branch main
woodpecker-cli pipeline ls owner/repo --status failure
woodpecker-cli pipeline ls owner/repo --event push
woodpecker-cli pipeline ls owner/repo --limit 10
woodpecker-cli pipeline ls owner/repo --after 2025-01-01T00:00:00Z
woodpecker-cli pipeline ls owner/repo --before 2025-12-31T00:00:00Z
```

## Show Pipeline Details

```bash
woodpecker-cli pipeline show owner/repo <pipeline-number>
woodpecker-cli pipeline show owner/repo              # Latest pipeline (no number)
```

## View Latest Pipeline

```bash
woodpecker-cli pipeline last owner/repo
woodpecker-cli pipeline last owner/repo --branch main
```

## View Logs

```bash
woodpecker-cli pipeline log show owner/repo <pipeline-number>
```

## View Pipeline Steps

```bash
woodpecker-cli pipeline ps owner/repo <pipeline-number>
```

## Check Queue

```bash
woodpecker-cli pipeline queue                        # Show pending pipelines
```
