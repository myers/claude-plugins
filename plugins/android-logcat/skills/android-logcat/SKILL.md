---
name: android-logcat
description: Captures and analyzes Android logcat for Quest/Android debugging. Use when testing APKs, debugging crashes, or analyzing Android logs. CRITICAL - always capture logs to files before testing, never rely on reading the buffer after a crash.
allowed-tools: Bash, Read, Grep, Glob, Write
---

# Android Logcat Skill

## Critical: Ring Buffer Warning

Android logcat uses a **ring buffer that fills extremely quickly on Meta Quest**. When a crash occurs, critical log messages are often already overwritten before you can read them.

**NEVER** try to read logcat after a crash. **ALWAYS** capture to a file before testing.

## Workflow

### 1. Start Capture BEFORE Testing

```bash
# Using the helper script (logs to ./logs/logcat/ in current workspace)
.claude/skills/android-logcat/scripts/capture_logcat.sh start

# Or manually
mkdir -p logs/logcat
adb logcat -c && adb logcat -v threadtime > logs/logcat/logcat_$(date +%Y%m%d_%H%M%S).txt &
```

### 2. Run Your Test

Install APK, reproduce the crash, etc.

### 3. Stop Capture

```bash
# Using helper script
.claude/skills/android-logcat/scripts/capture_logcat.sh stop

# Or manually: kill the background adb process
```

### 4. Analyze the Captured File

```bash
# Find crashes and fatal errors
grep -i "fatal\|crash\|exception\|died" logs/logcat/*.txt

# OpenXR/WebXR specific
grep -iE "openxr|webxr|xrdevice|vr" logs/logcat/*.txt

# Chromium components
grep -E "cr_" logs/logcat/*.txt
```

## Helper Script Commands

```bash
SCRIPT=".claude/skills/android-logcat/scripts/capture_logcat.sh"

$SCRIPT start          # Start capturing (clears buffer first)
$SCRIPT start "*:W"    # Capture warnings and above only
$SCRIPT stop           # Stop capturing
$SCRIPT status         # Check if capturing, show latest file
```

Log files are saved to `./logs/logcat/` in the current workspace with timestamps.

## Common Analysis Patterns

| What to Find | Command |
|--------------|---------|
| Crashes | `grep -i "fatal\|crash\|exception" logs/logcat/*.txt` |
| ANRs | `grep -i "anr\|not responding" logs/logcat/*.txt` |
| OpenXR errors | `grep -i "openxr.*error\|xr_error" logs/logcat/*.txt` |
| Chromium | `grep "cr_\|chromium" logs/logcat/*.txt` |
| By process | `grep "$(adb shell pidof com.android.chrome)" logs/logcat/*.txt` |

## Quest-Specific Notes

- Ring buffer fills in **seconds** under VR load
- WebXR/OpenXR stack is verbose
- Always use `-v threadtime` format for timestamps
- Capture continuously, analyze after

For detailed reference, see [CAPTURE-GUIDE.md](CAPTURE-GUIDE.md)
