# Myers Plugins

A Claude Code plugin marketplace with tools for Meta Quest and Android development.

## Installation

```
/plugin marketplace add myers/claude-plugins
```

## Plugins

### android-logcat

Captures and analyzes Android logcat for Quest/Android debugging. Handles Android's ring buffer limitation that fills in seconds on Meta Quest.

```
/plugin install android-logcat@myers-plugins
```

**Key features:**
- Continuous file-based log capture to prevent data loss
- Helper script for start/stop/status commands
- Common analysis patterns for crashes, ANRs, and OpenXR errors

### cdp-quest-dev

Chrome DevTools Protocol debugging for Quest. Use `cdp-cli` and `quest-dev` to inspect, control, and debug browsers on Meta Quest.

```
/plugin install cdp-quest-dev@myers-plugins
```

**Key features:**
- Support for both Quest browser and custom Chromium builds
- Commands: tabs, console, eval, screenshot, network, click, fill
- WebXR debugging workflows
