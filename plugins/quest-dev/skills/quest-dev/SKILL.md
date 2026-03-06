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
87% not charging
42% charging
95% fast charging
```

**Use Case**: Quick battery check. For continuous monitoring, `quest-dev stay-awake` automatically reports battery at 5% intervals.

---

## 4. Stay Awake (Critical for Development)

**Keeps Quest awake during active development sessions. Disables autosleep, guardian boundary, and system dialogs. Monitors battery and auto-exits on low charge.**

```bash
quest-dev stay-awake [--pin <pin>] [--idle-timeout <ms>] [--low-battery <percent>]
```

### How It Works

1. Disables autosleep, guardian, and system dialogs on Quest
2. Wakes the Quest screen
3. Monitors battery every 60 seconds, logging at 5% boundaries (95%, 90%, 85%...)
4. Auto-exits and restores settings at low battery (default: 10%)
5. Monitors for activity via SIGUSR1 signals with idle timeout
6. Child watchdog process ensures cleanup even if parent is killed (TaskStop, terminal close, etc.)

### PIN Configuration

The PIN is your Meta Store PIN for the logged-in account. It can be provided via:

1. `--pin <pin>` CLI flag (highest priority)
2. `.quest-dev.json` in current directory: `{ "pin": "1234" }`
3. `~/.config/quest-dev/config.json` (same format, fallback)

### Examples

```bash
# Using PIN from config file
quest-dev stay-awake

# Explicit PIN
quest-dev stay-awake --pin 1234

# Custom idle timeout: 10 minutes
quest-dev stay-awake --idle-timeout 600000

# Custom low battery threshold
quest-dev stay-awake --low-battery 20

# Check current property values
quest-dev stay-awake --status

# Manually restore all properties (if process was killed)
quest-dev stay-awake --disable --pin 1234
```

### Options

- `--pin <pin>`: Meta Store PIN (or set in config files)
- `--idle-timeout <ms>` (alias `-i`): Idle timeout in milliseconds (default: 300000 = 5 minutes)
- `--low-battery <percent>`: Exit when battery drops to this level (default: 10)
- `--status`: Show current property values and exit
- `--disable`: Manually restore all test properties and exit

### Behavior

- **Active sessions**: As long as Claude Code tools execute, Quest stays awake (hooks send SIGUSR1)
- **Idle detection**: After configured timeout with no activity, automatically exits and restores settings
- **Battery monitoring**: Logs battery at every 5% boundary crossing; auto-exits at low threshold (not charging only)
- **Manual exit**: Press Ctrl-C to immediately restore settings
- **Crash protection**: Child watchdog process detects parent death and restores settings to prevent battery drain

### Integration with Claude Code

This plugin includes a PostToolUse hook that automatically signals stay-awake after each tool execution. Just run `quest-dev stay-awake` once and it will stay active during your entire Claude Code session.

**Recommended Workflow:**
```bash
# Terminal 1: Start stay-awake (PIN from .quest-dev.json)
quest-dev stay-awake

# Terminal 2: Work in Claude Code
claude -c
# Quest stays awake automatically while you work
# Battery status logged at 5% intervals
# After 5 minutes of no activity, Quest returns to normal
```

### Troubleshooting

**Quest still sleeping?**
- Verify stay-awake is running: `ps aux | grep stay-awake`
- Check PID file: `cat ~/.quest-dev-stay-awake.pid`
- Test signal manually: `kill -USR1 $(cat ~/.quest-dev-stay-awake.pid)`

**Can't start (already running)?**
- Another instance is active: `kill $(cat ~/.quest-dev-stay-awake.pid)`

**Settings stuck after unexpected kill?**
If stay-awake is killed without cleanup (kill -9, power loss), manually restore:
```bash
quest-dev stay-awake --disable --pin 1234
```
Or check current state:
```bash
quest-dev stay-awake --status
```

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

# 2. Start stay-awake (PIN from .quest-dev.json)
quest-dev stay-awake

# Terminal 2: Start log capture
quest-dev logcat start

# 3. Open your dev server
quest-dev open http://localhost:3000

# 4. Work in Claude Code
# (Quest stays awake via hooks, battery monitored automatically)

# 5. Take progress screenshots
quest-dev screenshot ~/Desktop -c "Feature X implemented"

# 6. When done, stop logs
quest-dev logcat stop

# 7. Ctrl-C stay-awake to restore Quest settings
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

## See Also

**cdp-cli** plugin — General-purpose Chrome DevTools Protocol CLI for inspecting, controlling, and debugging any CDP-compatible browser. Use after `quest-dev open` to interact with pages via console, eval, screenshot, network, click, and fill commands.

## CRITICAL: Do Not Bypass quest-dev With Raw ADB Commands

**The following raw ADB commands will put the Quest into a broken state requiring a reboot.** Always use `quest-dev` commands instead — they handle enable/disable pairing and cleanup properly.

### Never run these directly:

| Dangerous Command | Why | Use Instead |
|---|---|---|
| `adb shell am broadcast -a com.oculus.vrpowermanager.automation_enable` | Conflicts with stay-awake's enable/disable pairing; leaves automation stuck on | `quest-dev stay-awake` |
| `adb shell am broadcast -a com.oculus.vrpowermanager.prox_close` | Conflicts with stay-awake proximity management | `quest-dev stay-awake` |
| `adb shell am broadcast -a com.oculus.vrpowermanager.automation_disable` | Conflicts with stay-awake cleanup | `quest-dev stay-awake --disable` |
| `adb shell svc power stayon true` | Conflicts with Quest VR power management layer | `quest-dev stay-awake` |
| `adb shell settings put system screen_off_timeout ...` | Conflicts with stay-awake timeout management | `quest-dev stay-awake` |
| `adb shell settings put global stay_on_while_plugged_in ...` | Conflicts with Quest VR power management | `quest-dev stay-awake` |
| `adb shell input keyevent KEYCODE_WAKEUP` | Unreliable; use stay-awake which handles wake properly | `quest-dev stay-awake` |
| `adb shell am force-stop com.oculus.guardian` | Breaks VR shell state; guardian restarts in broken loop | `quest-dev stay-awake` (disables guardian) |
| `adb shell am force-stop com.oculus.metacam` | Breaks screenshot service; can't restart without reboot | `quest-dev screenshot` |
| `adb shell am force-stop com.oculus.os.clearactivity` | Breaks VR shell state | Don't touch this |
| `adb shell am startservice ... com.oculus.metacam` | Leaves metacam in broken background state | `quest-dev screenshot` |
| `adb shell content call --uri content://com.oculus.rc ...` | Scriptable Testing API — stay-awake manages this | `quest-dev stay-awake` |

### What IS safe to run directly:

- `adb install -r <apk>` — install your app
- `adb shell am start -n <component>` — launch your app
- `adb shell am force-stop <your.app.package>` — stop YOUR app only
- `adb shell pidof <package>` — check if a process is running
- `adb shell dumpsys activity activities | grep <package>` — check foreground state
- `adb shell dumpsys power` — read-only power state inspection
- `adb shell screencap` — raw screenshot (shows compositor, not VR content)
- `adb connect / disconnect` — ADB connection management
- `echo "command" | nc -u -w1 <ip> <port>` — UDP commands to your app

### Root Cause

The Quest has a **layered power management system**: Android's standard power manager sits underneath Meta's VR power manager (`vrpowermanager`), which uses the Scriptable Testing API (`content://com.oculus.rc`). Sending commands at the wrong layer (e.g., `svc power stayon` at Android level while stay-awake manages the VR level) creates conflicts where the layers disagree about screen/proximity state. Force-stopping system services like `guardian` or `metacam` can leave the VR shell in an unrecoverable state that only a reboot fixes.

---

## Tips

1. **Always run stay-awake**: Quest sleeping mid-test is frustrating
2. **Configure PIN once**: Put `{ "pin": "1234" }` in `.quest-dev.json` to avoid typing it every time
3. **Capture logs early**: Ring buffer overwrites quickly
4. **Use captions**: Screenshots with context are invaluable
5. **Battery is monitored**: stay-awake logs battery at 5% intervals and auto-exits at 10%
6. **Close other tabs**: Use `--close-others` to avoid CDP confusion
7. **Never bypass quest-dev**: Raw ADB power/proximity/guardian commands break the Quest (see above)

## Version

Requires quest-dev CLI v1.3.0+. Requires Quest OS v44+.
