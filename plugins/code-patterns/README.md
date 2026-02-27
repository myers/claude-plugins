# code-patterns

A Claude Code plugin that provides opinionated code patterns and conventions.

## What it does

The `/code-patterns` skill loads reference material covering coding conventions across Django, Python tooling, database, and frontend topics. Claude uses these patterns when writing new code and flags deviations when reviewing existing code.

## Topics covered

- **Django** — Project structure, settings, auth, models, views, management commands, testing, background tasks, deployment
- **Python Tooling** — uv package management, ruff configuration, prek hooks, bin/ wrapper scripts, Docker Compose
- **Database** — SQLite-first approach, PostgreSQL upgrade path, connection pooling, NOT EXISTS, Subquery, cursor pagination, indexing, raw SQL
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
