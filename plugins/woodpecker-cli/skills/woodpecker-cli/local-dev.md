# Local Development

## Lint Pipeline Config

Validate a pipeline configuration file:
```bash
woodpecker-cli lint                                  # Lint .woodpecker.yaml in cwd
woodpecker-cli lint path/to/.woodpecker.yaml
woodpecker-cli lint --strict                         # Treat warnings as errors
```

## Execute Pipeline Locally

Run a pipeline on the local machine without pushing to the server:
```bash
# Basic local execution
woodpecker-cli exec .woodpecker.yaml

# Run from local directory (uses local files instead of cloning)
woodpecker-cli exec --local

# With secrets
woodpecker-cli exec --secrets SECRET_NAME="value"
woodpecker-cli exec --secrets-file secrets.yaml

# With volumes mounted
woodpecker-cli exec --volumes /host/path:/container/path

# With environment variables
woodpecker-cli exec --env MY_VAR=value

# Set timeout
woodpecker-cli exec --timeout 30m

# Choose backend
woodpecker-cli exec --backend-engine docker          # Docker (default)
woodpecker-cli exec --backend-engine local           # Run directly on host
```

### Docker Backend Options

```bash
woodpecker-cli exec --backend-docker-host /var/run/docker.sock
woodpecker-cli exec --backend-docker-network my-network
woodpecker-cli exec --backend-docker-volumes /shared:/shared
```

### Override Metadata

Useful for testing pipeline behavior with specific metadata:
```bash
woodpecker-cli exec --commit-branch feature-x
woodpecker-cli exec --pipeline-event pull_request
woodpecker-cli exec --commit-message "test: my commit"
woodpecker-cli exec --repo owner/repo
```
