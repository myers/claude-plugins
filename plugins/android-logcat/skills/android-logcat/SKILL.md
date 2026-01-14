---
name: android-logcat
description: Captures and analyzes Android logcat for Quest/Android debugging. Use when testing APKs, debugging crashes, or analyzing Android logs. CRITICAL - always capture logs to files before testing, never rely on reading the buffer after a crash.
allowed-tools: Bash, Read, Grep, Glob, Write
---

# Android Logcat Skill

## Critical: Ring Buffer Warning

Android logcat uses a **ring buffer that fills extremely quickly on Meta Quest**. When a crash occurs, critical log messages are often already overwritten before you can read them.

**NEVER** try to read logcat after a crash. **ALWAYS** capture to a file before testing.

## Required: Use the Helper Script

**YOU MUST use the capture_logcat.sh helper script** - it handles buffer clearing, PID tracking, and file management correctly.

First, find the script location:
```bash
# Find the installed script
LOGCAT_SCRIPT=$(find ~/.claude -name "capture_logcat.sh" -path "*/android-logcat/*" 2>/dev/null | head -1)
echo "Script: $LOGCAT_SCRIPT"
```

## Workflow

### 1. Start Capture BEFORE Testing

```bash
$LOGCAT_SCRIPT start
```

This clears the ring buffer and starts capturing to `./logs/logcat/` with a timestamped filename.

### 2. Run Your Test

Install APK, reproduce the crash, etc.

### 3. Stop Capture

```bash
$LOGCAT_SCRIPT stop
```

Shows the log file path, size, and line count.

### 4. Analyze the Captured File

```bash
# Find crashes and fatal errors
grep -i "fatal\|crash\|exception\|died" logs/logcat/*.txt

# OpenXR/WebXR specific
grep -iE "openxr|webxr|xrdevice|vr" logs/logcat/*.txt

# Chromium components
grep -E "cr_" logs/logcat/*.txt
```

## Script Commands Reference

```bash
$LOGCAT_SCRIPT start          # Start capturing (clears buffer first)
$LOGCAT_SCRIPT start "*:W"    # Capture warnings and above only
$LOGCAT_SCRIPT stop           # Stop capturing
$LOGCAT_SCRIPT status         # Check if capturing, show latest file
$LOGCAT_SCRIPT tail           # Live tail of current capture
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
