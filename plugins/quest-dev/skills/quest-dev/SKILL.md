---
name: quest-dev
description: Meta Quest development toolkit. Use for Quest browser debugging, screenshots, battery monitoring, and keeping Quest awake during development. Provides CDP debugging, ADB utilities, and workflow automation.
allowed-tools: Bash, Read, Grep, Glob, Write
---

# Quest Dev Skill

Command-line toolkit for Meta Quest Browser development via ADB and Chrome DevTools Protocol (CDP).

## Prerequisites

- Meta Quest connected via USB
- ADB installed and in PATH
- Quest in Developer Mode
- USB debugging enabled on Quest

**Quick check:**
```bash
adb devices
```
Should show your Quest device.

## Commands Overview

| Command | Purpose |
|---------|---------|
| `quest-dev open <url>` | Open URL with CDP debugging |
| `quest-dev screenshot <dir>` | Take Quest screenshots |
| `quest-dev battery` | Check battery status |
| `quest-dev stay-awake` | Keep Quest awake during work |
| `quest-dev logcat <action>` | Capture Android logs |

---

## 1. Opening URLs with CDP Debugging

**Opens a URL in Quest browser and sets up Chrome DevTools Protocol port forwarding.**

```bash
quest-dev open <url>
```

### Features

- **Automatic port forwarding**: Sets up CDP on port 9223 (or 9222 for some browsers)
- **Localhost support**: Reverse-forwards localhost URLs so Quest can access your dev server
- **Multi-browser**: Supports Quest Browser, Chrome, Chromium, Edge

### Examples

```bash
# Open a local dev server
quest-dev open http://localhost:3000

# Open a remote URL
quest-dev open https://threejs.org/examples/webxr_vr_cubes.html

# Open in a different browser
quest-dev open https://example.com --browser org.chromium.chrome

# Close all other tabs first
quest-dev open http://localhost:8080 --close-others
```

### Options

- `--browser <package>` (alias `-b`): Browser package name (default: com.oculus.browser)
  - Quest Browser: `com.oculus.browser`
  - Chrome: `com.android.chrome`
  - Chromium: `org.chromium.chrome`
  - Edge: `com.microsoft.emmx`
- `--close-others`: Close all other tabs before opening

### After Opening

CDP is available at `localhost:9223`. Use with cdp-cli:

```bash
# List open pages
cdp-cli list-pages

# Get console messages
cdp-cli list-console

# Execute JavaScript
cdp-cli exec "console.log('Hello from Quest')"
```

---

## 2. Taking Screenshots

**Captures Quest screen and saves to local directory with auto-generated filename.**

```bash
quest-dev screenshot <directory>
```

### Features

- Auto-generated filename: `screenshot-YYYY-MM-DD-HH-MM-SS-offset.jpg`
- Optional caption embedded in JPEG metadata (COM field)
- Pulls from Quest to local machine

### Examples

```bash
# Basic screenshot
quest-dev screenshot ~/Desktop

# Screenshot with caption
quest-dev screenshot ~/screenshots --caption "Three.js XR scene loaded"

# Short alias
quest-dev screenshot . -c "Debug UI visible"
```

### Options

- `--caption <text>` (alias `-c`): Embed caption in JPEG COM metadata

**Best Practice for Claude Code**: Use captions to document progress or bugs for later review.

---

## 3. Battery Status

**Shows Quest battery percentage and charging state in one line.**

```bash
quest-dev battery
```

### Output Format

```
Battery: 87% (not charging)
Battery: 42% (charging)
Battery: 95% (fast charging)
```

**Use Case**: Check battery before long testing sessions, monitor charging status.

---

## 4. Stay Awake (Critical for Development)

**Keeps Quest screen awake during active development sessions with automatic idle timeout.**

```bash
quest-dev stay-awake [--idle-timeout <ms>]
```

### How It Works

1. Sets Quest screen timeout to 24 hours
2. Disables proximity sensor (keeps screen on even when not worn)
3. Monitors for activity via SIGUSR1 signals
4. Automatically restores settings after idle timeout (default: 5 minutes)
5. Child watchdog process ensures cleanup even if parent crashes

### Examples

```bash
# Default: 5-minute idle timeout
quest-dev stay-awake

# Custom timeout: 10 minutes
quest-dev stay-awake --idle-timeout 600000

# Short timeout for testing: 30 seconds
quest-dev stay-awake -i 30000
```

### Options

- `--idle-timeout <ms>` (alias `-i`): Idle timeout in milliseconds (default: 300000 = 5 minutes)

### Behavior

- **Active sessions**: As long as Claude Code tools execute, Quest stays awake (hooks send SIGUSR1)
- **Idle detection**: After configured timeout with no activity, automatically exits and restores settings
- **Manual exit**: Press Ctrl-C to immediately restore original settings
- **Crash protection**: Child watchdog process detects parent death and restores settings

### Integration with Claude Code

This plugin includes a PostToolUse hook that automatically signals stay-awake after each tool execution. Just run `quest-dev stay-awake` once and it will stay active during your entire Claude Code session.

**Recommended Workflow:**
```bash
# Terminal 1: Start stay-awake
quest-dev stay-awake

# Terminal 2: Work in Claude Code
claude -c
# Quest stays awake automatically while you work
# After 5 minutes of no activity, Quest returns to normal
```

### Troubleshooting

**Quest still sleeping?**
- Verify stay-awake is running: `ps aux | grep stay-awake`
- Check PID file: `cat ~/.quest-dev-stay-awake.pid`
- Test signal manually: `kill -USR1 $(cat ~/.quest-dev-stay-awake.pid)`

**Can't start (already running)?**
- Another instance is active: `kill $(cat ~/.quest-dev-stay-awake.pid)`

---

## 5. Logcat Capture

**Captures Android logcat to files. CRITICAL: Always start before testing to avoid losing crash logs.**

```bash
quest-dev logcat <action>
```

### Actions

| Action | Description |
|--------|-------------|
| `start` | Start capturing (clears buffer first) |
| `stop` | Stop capturing and show file info |
| `status` | Check if capturing, show file path |
| `tail` | Live tail of current capture |

### Examples

```bash
# Start capturing before testing
quest-dev logcat start

# Capture only warnings and above
quest-dev logcat start --filter "*:W"

# Capture only Chromium logs
quest-dev logcat start --filter "chromium:V *:S"

# Check capture status
quest-dev logcat status

# Watch logs live
quest-dev logcat tail

# Stop when done
quest-dev logcat stop
```

### Options

- `--filter <expression>`: Logcat filter expression
  - `*:W` - Warnings and above only
  - `chromium:V *:S` - Chromium verbose, silence everything else
  - `*:E` - Errors only

### Log Files

Saved to `./logs/logcat/` with timestamped filenames: `logcat_YYYY-MM-DD_HH-MM-SS.txt`

### Analysis After Capture

```bash
# Find crashes
grep -i "fatal\|crash\|exception" logs/logcat/*.txt

# WebXR/OpenXR errors
grep -iE "openxr|webxr|xrdevice" logs/logcat/*.txt

# Chromium errors
grep -E "cr_.*error|chromium.*error" logs/logcat/*.txt
```

**CRITICAL**: Android's ring buffer fills in seconds on Quest. Always capture to file BEFORE reproducing bugs or crashes.

---

## Common Workflows

### Full Development Session

```bash
# 1. Check connection
adb devices

# 2. Start stay-awake
quest-dev stay-awake

# Terminal 2: Start log capture
quest-dev logcat start

# 3. Open your dev server
quest-dev open http://localhost:3000

# 4. Work in Claude Code
# (Quest stays awake via hooks)

# 5. Take progress screenshots
quest-dev screenshot ~/Desktop -c "Feature X implemented"

# 6. Check battery periodically
quest-dev battery

# 7. When done, stop logs
quest-dev logcat stop

# 8. Ctrl-C stay-awake to restore Quest settings
```

### Quick Testing

```bash
# Open URL and start testing
quest-dev open http://localhost:8080 --close-others

# Use CDP to debug
cdp-cli list-console
```

### Bug Reproduction

```bash
# Start logging FIRST
quest-dev logcat start

# Reproduce the bug in Quest

# Capture evidence
quest-dev screenshot ~/bugs -c "Crash before rendering"

# Stop logging
quest-dev logcat stop

# Analyze logs
grep -i "crash\|fatal" logs/logcat/*.txt
```

---

## Tips

1. **Always run stay-awake**: Quest sleeping mid-test is frustrating
2. **Capture logs early**: Ring buffer overwrites quickly
3. **Use captions**: Screenshots with context are invaluable
4. **Check battery**: VR drains fast, especially during development
5. **Close other tabs**: Use `--close-others` to avoid CDP confusion

## Version

Requires quest-dev CLI with stay-awake idle timeout support (v1.1.0+)
