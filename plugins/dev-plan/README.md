# dev-plan

A Claude Code plugin that provides an interactive planning tool with in-depth requirements interviews.

## What it does

The `/dev-plan` command uses Claude Opus to conduct a thorough interview about your project requirements before creating a detailed implementation plan. Instead of making assumptions, it asks deep questions about:

- Technical implementation details
- UI & UX considerations
- Concerns and potential issues
- Tradeoffs between approaches
- Edge cases and requirements

## Usage

```bash
/dev-plan Add user authentication to the app
```

Claude will then interview you with thoughtful, non-obvious questions to fully understand your needs before writing a comprehensive plan.

## Installation

```bash
/plugin install dev-plan@myers-plugins
```
