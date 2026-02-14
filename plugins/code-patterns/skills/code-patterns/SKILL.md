---
name: code-patterns
description: Load opinionated code patterns and conventions for writing and reviewing Django project code
allowed-tools: Glob, Read
---

# Code Patterns

Load and apply the project's opinionated code patterns and conventions.

## Loading Instructions

1. Use Glob to find all `*.md` files in this skill's directory (excluding this SKILL.md)
2. Read each topic file to load the full conventions

The topic files are:
- **django.md** — Project structure, settings, auth, models, views, commands, testing, background tasks, deployment
- **python-tooling.md** — Package management (uv), code quality (ruff), development tooling (bin/ scripts, Docker)
- **database.md** — Connection pooling, query patterns (NOT EXISTS, Subquery), cursor pagination, indexing, raw SQL
- **frontend.md** — Hotwired (Turbo + Stimulus), Vite asset bundling

## Usage Modes

### Writing Code
When writing new code, follow these patterns automatically. Don't mention them unless the user asks why something was done a certain way.

### Reviewing Code
When reviewing code, flag deviations from these patterns as suggestions. Explain what the convention is and why it exists.

## Key Opinions (Quick Reference)

1. **PostgreSQL only** — No SQLite support, enforced in settings
2. **uv for package management** — Not pip, poetry, or pipenv
3. **Function-based views** — Simpler than class-based views
4. **Composable filter functions** — Not Django Filter or custom filter classes
5. **pytest functions, not TestCase classes** — Better parallel execution
6. **factory-boy for test data** — Not fixtures or manual creation
7. **Global login required** — Secure by default, opt-out for public views
8. **Skinny models, views, and commands** — Business logic in service modules
9. **Cursor pagination** — Better for large datasets than offset
10. **Raw SQL when beneficial** — Don't fight the ORM for complex queries
11. **Connection pooling** — psycopg pool, not CONN_MAX_AGE
12. **Ruff for linting and formatting** — Not black, isort, flake8 separately
13. **Pre-commit hooks** — Enforce quality on every commit
14. **Vite for assets** — Not webpack or Django's built-in static
15. **Hotwired for frontend** — Not React/Vue SPA
16. **Management commands as orchestrators** — Parse args, display output, delegate logic
