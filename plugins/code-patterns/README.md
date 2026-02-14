# code-patterns

A Claude Code plugin that provides opinionated code patterns and conventions for Django projects.

## What it does

The `/code-patterns` skill loads reference material covering Django, Python tooling, database, and frontend conventions. Claude uses these patterns when writing new code and flags deviations when reviewing existing code.

## Topics covered

- **Django** — Project structure, settings, auth, models, views, management commands, testing, background tasks, deployment
- **Python Tooling** — uv package management, ruff configuration, pre-commit hooks, bin/ wrapper scripts, Docker Compose
- **Database** — PostgreSQL connection pooling, NOT EXISTS, Subquery, cursor pagination, indexing, raw SQL
- **Frontend** — Hotwired (Turbo + Stimulus), Vite asset bundling

## Usage

```
/code-patterns
```

Then ask Claude to write or review code — it will apply the loaded conventions automatically.

## Installation

```bash
/plugin install code-patterns@myers-plugins
```
