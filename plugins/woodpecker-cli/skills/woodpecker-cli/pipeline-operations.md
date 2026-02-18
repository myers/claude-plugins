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
```

## Purge Logs

```bash
woodpecker-cli pipeline log purge owner/repo <pipeline-number>
```
