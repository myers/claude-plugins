# Myers Plugins

A Claude Code plugin marketplace.

## Installation

Add the marketplace, then install individual plugins:

```
/plugin marketplace add myers/claude-plugins
/plugin install <name>@myers-plugins
```

## Plugins

| Plugin | Description |
|--------|-------------|
| [android-logcat](#android-logcat) | Captures and analyzes Android logcat for Quest/Android debugging. Use when testing APKs, debugging crashes, or analyzing Android logs. |
| [cdp-cli](#cdp-cli) | Chrome DevTools Protocol CLI for inspecting, controlling, and debugging browser pages via CDP. |
| [code-patterns](#code-patterns) | Load opinionated code patterns and conventions for writing and reviewing code. |
| [dev-plan](#dev-plan) | Interactive planning with in-depth requirements interview. |
| [find-block](#find-block) | Blocks the 'find' command in Bash tool and suggests using Glob/Grep tools instead. |
| [fj](#fj) | Forgejo CLI for managing issues, PRs, and project boards. Use when asked to interact with Forgejo repositories. |
| [quest-dev](#quest-dev) | Meta Quest development toolkit. Use for Quest browser debugging, screenshots, battery monitoring, and keeping Quest awake during development. |
| [woodpecker-cli](#woodpecker-cli) | Woodpecker CI CLI for managing pipelines, repos, secrets, and running local builds. |

---

### android-logcat

Captures and analyzes Android logcat for Quest/Android debugging. Use when testing APKs, debugging crashes, or analyzing Android logs. CRITICAL — always capture logs to files before testing, never rely on reading the buffer after a crash.

```
/plugin install android-logcat@myers-plugins
```

### cdp-cli

Chrome DevTools Protocol CLI for inspecting, controlling, and debugging browser pages via CDP. Works with any CDP-compatible browser: desktop Chrome, headless Chrome, Chromium, or Quest Browser.

```
/plugin install cdp-cli@myers-plugins
```

### code-patterns

Load opinionated code patterns and conventions for writing and reviewing code.

```
/plugin install code-patterns@myers-plugins
```

### dev-plan

Interactive planning with in-depth requirements interview.

```
/plugin install dev-plan@myers-plugins
```

### find-block

Blocks the `find` command in Bash tool and suggests using Glob/Grep tools instead, which are optimized for Claude Code. Hook-only plugin (no skill file).

```
/plugin install find-block@myers-plugins
```

### fj

Forgejo CLI for managing issues, PRs, and project boards. Use when asked to interact with Forgejo repositories — creating issues, viewing PRs, managing kanban boards, etc.

```
/plugin install fj@myers-plugins
```

### quest-dev

Meta Quest development toolkit. Use for Quest browser debugging, screenshots, battery monitoring, and keeping Quest awake during development. Provides CDP debugging, ADB utilities, and workflow automation.

```
/plugin install quest-dev@myers-plugins
```

### woodpecker-cli

Woodpecker CI CLI for managing pipelines, repos, secrets, and running local builds. Use when asked to interact with Woodpecker CI.

```
/plugin install woodpecker-cli@myers-plugins
```
