# Python Tooling

## Package Management

### uv for Python Dependencies

Use `uv` instead of pip/poetry:

```bash
# Install dependencies
uv sync

# Add a dependency
uv add package-name

# Run with uv
uv run ./manage.py runserver
```

### pyproject.toml Configuration

```toml
[project]
requires-python = ">=3.13,<4.0"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.metadata]
allow-direct-references = true  # For git dependencies

[dependency-groups]
dev = [
    "pytest>=8.4.1",
    "pytest-django>=4.11.1",
    "factory-boy>=3.3.3",
    # ...
]
```

---

## Code Quality

### Ruff Configuration

```toml
# pyproject.toml
[tool.ruff]
target-version = "py313"
line-length = 88

[tool.ruff.lint]
select = [
    "E4", "E402", "E7", "E9",  # pycodestyle
    "F",                       # Pyflakes
    "I",                       # isort
    "UP",                      # pyupgrade
    "B",                       # flake8-bugbear
    "C4",                      # flake8-comprehensions
    "PIE",                     # flake8-pie
    "PLC0415",                 # import outside top-level
    "SIM",                     # flake8-simplify
]

ignore = [
    "E501",   # Line too long (handled by formatter)
    "SIM108", # Use ternary operator (often less readable)
]

[tool.ruff.lint.per-file-ignores]
"**/tests/**" = ["B905", "PLC0415"]  # Allow in tests
"**/migrations/**" = ["E501", "F401"]
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.12.8
    hooks:
      - id: ruff-format
      - id: ruff-check
        args: [--fix]
```

---

## Development Tooling

### Wrapper Scripts

Create `bin/` scripts that load `.env` and use `uv run`:

```bash
#!/usr/bin/env bash
# bin/manage

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $DIR/..

if [ -e .env ]; then
    set -a
    source <(cat .env | sed -e '/^#/d;/^\s*$/d' -e "s/'/'\\\''/g" -e "s/=\(.*\)/='\1'/g")
    set +a
fi

exec uv run ./manage.py "$@"
```

```bash
#!/usr/bin/env bash
# bin/test
# ... same .env loading ...
exec uv run pytest -n auto "$@"
```

### Docker Compose for Services

Run PostgreSQL and other services via Docker:

```yaml
services:
  postgres:
    image: postgres:15.13
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: myapp
      POSTGRES_PASSWORD: myapp
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U myapp -d myapp"]
```

### SQL Logging Middleware

Toggle-able SQL logging for debugging:

```python
# settings.py
if os.getenv("DJANGO_SQL_LOGGING", "true").lower() == "true":
    MIDDLEWARE.insert(0, "web.middleware.SQLLoggingMiddleware")
```
