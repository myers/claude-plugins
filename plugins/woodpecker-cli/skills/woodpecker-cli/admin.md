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

Secrets available to all repos. Uses `--name`/`--value` flags, not positional args.

```bash
woodpecker-cli admin secret ls
woodpecker-cli admin secret add --name MY_SECRET --value "secret-value"
woodpecker-cli admin secret rm --name MY_SECRET
```

## Global Registries

Docker registries available to all repos. Uses `--hostname`/`--username`/`--password` flags.

```bash
woodpecker-cli admin registry ls
woodpecker-cli admin registry add --hostname registry.example.com --username user --password pass
woodpecker-cli admin registry rm --hostname registry.example.com
```
