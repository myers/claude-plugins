---
name: cdp-quest-dev
description: Chrome DevTools Protocol debugging for Quest. Use cdp-cli and quest-dev to inspect, control, and debug browsers on Meta Quest. Supports both Quest browser and Chromium builds.
allowed-tools: Bash, Read
---

# CDP Quest Development Tools

Two npm tools for debugging browsers on Meta Quest via Chrome DevTools Protocol (CDP).

## Tools Overview

### cdp-cli
General-purpose CDP command-line client for inspecting and controlling browser pages.

```bash
cdp-cli --cdp-url <url> <command>
```

### quest-dev
Quest-specific helper for screenshots and opening URLs in Quest browser.

```bash
quest-dev <command>
```

## Connecting to Quest Browser vs Chromium

**Important**: These tools connect to different browsers depending on the socket:

| Browser | ADB Socket | Default Port |
|---------|-----------|--------------|
| Quest Browser (built-in) | `chrome_devtools_remote` | 9223 |
| Chromium (custom build) | `chrome_devtools_remote_<PID>` | Must discover |

### Quest Browser (quest-dev default)
```bash
# quest-dev sets up port 9223 automatically
quest-dev open "https://example.com"
cdp-cli tabs  # Uses default port 9223
```

### Chromium Build
```bash
# 1. Find Chromium's socket (includes PID)
adb shell cat /proc/net/unix | grep chrome_devtools_remote

# 2. Forward to a local port (e.g., 9225)
adb forward tcp:9225 localabstract:chrome_devtools_remote_<PID>

# 3. Use cdp-cli with custom port
cdp-cli --cdp-url http://localhost:9225 tabs
```

## cdp-cli Commands

| Command | Description | Example |
|---------|-------------|---------|
| `tabs` | List open pages | `cdp-cli tabs` |
| `new [url]` | Open new tab | `cdp-cli new "https://webxr.run"` |
| `go <page> <action>` | Navigate (URL/back/forward/reload) | `cdp-cli go "WebXR" reload` |
| `close <page>` | Close tab | `cdp-cli close "WebXR"` |
| `console <page>` | View console messages | `cdp-cli console "Immersive"` |
| `eval <page> <expr>` | Run JavaScript | `cdp-cli eval "WebXR" "navigator.xr"` |
| `screenshot <page> <file>` | Save screenshot | `cdp-cli screenshot 0 shot.png` |
| `network <page>` | View network requests | `cdp-cli network "WebXR"` |
| `click <page> [selector]` | Click element | `cdp-cli click "WebXR" "#enter-vr"` |
| `fill <page> <value> [sel]` | Fill input | `cdp-cli fill "Login" "user@example.com"` |

`<page>` can be a page ID (number) or substring of the page title.

## quest-dev Commands

| Command | Description | Example |
|---------|-------------|---------|
| `open <url>` | Open URL in Quest browser | `quest-dev open "https://webxr.run"` |
| `screenshot <file>` | Take Quest screenshot | `quest-dev screenshot screen.png` |

## Common Workflows

### Debug WebXR in Chromium Build
```bash
# 1. Start Chromium on Quest (adb shell am start ...)

# 2. Find and forward Chromium's CDP socket
PID=$(adb shell pidof org.chromium.chrome)
adb forward tcp:9225 localabstract:chrome_devtools_remote_$PID

# 3. Open WebXR sample
cdp-cli --cdp-url http://localhost:9225 new "https://immersive-web.github.io/webxr-samples/"

# 4. Check console for errors
cdp-cli --cdp-url http://localhost:9225 console "WebXR"

# 5. Check WebXR support
cdp-cli --cdp-url http://localhost:9225 eval "Samples" "navigator.xr?.isSessionSupported('immersive-vr')"
```

### Quick Test in Quest Browser
```bash
# Opens URL and sets up CDP on default port
quest-dev open "https://webxr.run"

# Inspect the page
cdp-cli tabs
cdp-cli console "WebXR"
```

### Monitor Console During Testing
```bash
# Watch for specific errors (run before testing)
cdp-cli --cdp-url http://localhost:9225 console "WebXR" | grep -i error
```

## Environment Setup

```bash
# Install via npm (requires Node.js)
npm install -g @myerscarpenter/cdp-cli @myerscarpenter/quest-dev

# Requires ADB with Quest connected
adb devices  # Should show Quest
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No pages found" | Check port forwarding is active |
| Wrong browser | Check which socket you forwarded (see table above) |
| Connection refused | Verify adb forward is active, browser is running |
| Empty console | Console must be enabled before messages are logged |
