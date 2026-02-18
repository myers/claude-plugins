# Server Administration

Requires admin privileges on the Woodpecker server.

## Log Level

```bash
woodpecker-cli admin log-level                       # Get current log level
woodpecker-cli admin log-level debug                 # Set log level
```

## User Management

```bash
woodpecker-cli admin user ls
woodpecker-cli admin user show <username>
woodpecker-cli admin user add <username>
woodpecker-cli admin user rm <username>
```

## Organization Management

```bash
woodpecker-cli admin org ls
```

## Global Secrets

Secrets available to all repos:
```bash
woodpecker-cli admin secret ls
woodpecker-cli admin secret add <name> <value>
woodpecker-cli admin secret rm <name>
```

## Global Registries

Docker registries available to all repos:
```bash
woodpecker-cli admin registry ls
woodpecker-cli admin registry add <address> <username> <password>
woodpecker-cli admin registry rm <address>
```
