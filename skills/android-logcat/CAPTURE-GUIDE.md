# Android Logcat Capture Guide

## Why File Capture is Mandatory on Quest

### The Ring Buffer Problem

Android's logcat uses a kernel ring buffer with limited size. On Meta Quest devices:

- The buffer fills in **seconds** under VR workload
- WebXR/OpenXR generates high log volume
- When a crash occurs, critical messages are often already overwritten
- Reading logcat *after* a crash typically shows only post-crash recovery logs

### The Race Condition

```
[App crashes] → [Crash logs written] → [System recovery logs flood buffer] → [You run adb logcat] → [Crash logs gone]
```

This happens in milliseconds. You **cannot** reliably read crash logs after the fact on Quest.

### The Solution

Capture logs **continuously** to a file on the PC during testing. The file has no size limit - nothing is lost.

---

## Capture Patterns

### Basic Crash Debugging

```bash
# 1. Start capture
.claude/skills/android-logcat/scripts/capture_logcat.sh start

# 2. Install and launch
out/Quest/bin/chrome_public_apk run 'https://example.com'

# 3. Reproduce crash

# 4. Stop capture
.claude/skills/android-logcat/scripts/capture_logcat.sh stop

# 5. Analyze
grep -i "fatal\|crash\|exception" logs/logcat/latest.txt
```

### Performance Analysis

For performance issues, capture warnings and above to reduce noise:

```bash
.claude/skills/android-logcat/scripts/capture_logcat.sh start "*:W"
```

### WebXR/OpenXR Issues

Focus on XR-related tags:

```bash
# Capture everything, filter during analysis
.claude/skills/android-logcat/scripts/capture_logcat.sh start

# Later, analyze XR specifically
grep -iE "openxr|webxr|xrdevice|vr|immersive" logs/logcat/latest.txt
```

---

## Filtering Strategies

### By Priority Level

| Filter | Meaning |
|--------|---------|
| `*:V` | Verbose (all) |
| `*:D` | Debug and above |
| `*:I` | Info and above |
| `*:W` | Warning and above |
| `*:E` | Error and above |
| `*:F` | Fatal only |

### By Tag

```bash
# Only chromium, silence everything else
adb logcat chromium:V *:S

# Multiple tags
adb logcat chromium:V OpenXR:V *:S
```

### By Process (after identifying PID)

```bash
# Get Chrome's PID
adb shell pidof com.android.chrome

# Filter by PID
adb logcat --pid=12345
```

---

## Common Tags for Quest/Chromium

### Chromium Tags

| Tag Pattern | Component |
|-------------|-----------|
| `cr_*` | Chromium components |
| `chromium` | General chromium |
| `WebXR` | WebXR implementation |
| `OpenXR` | OpenXR backend |

### Quest/VR Tags

| Tag | Component |
|-----|-----------|
| `VrApi` | Quest VR API |
| `OVR*` | Oculus VR components |
| `OpenXR` | OpenXR runtime |
| `XrRuntime` | XR runtime |

### System Tags

| Tag | Component |
|-----|-----------|
| `AndroidRuntime` | Java crashes |
| `DEBUG` | Native crashes |
| `ActivityManager` | App lifecycle |
| `WindowManager` | Display/window issues |

---

## Analysis Commands

### Find Crashes

```bash
# Java crashes (exceptions)
grep -i "exception\|fatal exception" logs/logcat/latest.txt

# Native crashes (segfaults, etc)
grep -A 20 "DEBUG.*signal\|SIGABRT\|SIGSEGV" logs/logcat/latest.txt

# ANRs
grep -B 5 -A 20 "ANR in\|not responding" logs/logcat/latest.txt
```

### Find Errors by Component

```bash
# OpenXR errors
grep -i "openxr.*error\|xr_error\|XR_ERROR" logs/logcat/latest.txt

# Chromium errors
grep -E "cr_.*E \|chromium.*error" logs/logcat/latest.txt

# GPU/Graphics errors
grep -i "egl\|gles\|gpu.*error\|graphics" logs/logcat/latest.txt
```

### Extract Stack Traces

```bash
# Java stack trace (follows "at " pattern)
grep -A 50 "FATAL EXCEPTION" logs/logcat/latest.txt | grep -E "^\s+at |Caused by:"

# Native stack trace
grep -A 30 "backtrace:" logs/logcat/latest.txt
```

### Timeline Analysis

The `-v threadtime` format includes timestamps:

```
12-13 10:15:32.123  1234  5678 I chromium: Message here
```

```bash
# Extract timestamp and message for timeline
awk '{print $1, $2, $6, $7}' logs/logcat/latest.txt | grep -i error
```

---

## Troubleshooting

### "No Android device connected"

```bash
# Check connection
adb devices

# If Quest not listed, on Quest:
# Settings → Developer → USB debugging → Allow
```

### Log file is empty

```bash
# Verify adb is working
adb shell echo test

# Check if logcat process is running
ps aux | grep "adb logcat"
```

### Missing logs from before capture started

Logs before you started capturing are **gone**. The ring buffer was already overwritten. This is why you must start capture **before** testing.

### Log file too large

Use filtering to reduce size:

```bash
# Warnings and above
.claude/skills/android-logcat/scripts/capture_logcat.sh start "*:W"

# Specific tag only
.claude/skills/android-logcat/scripts/capture_logcat.sh start "chromium:V *:S"
```
