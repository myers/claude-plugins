---
name: cdp-cli
description: Chrome DevTools Protocol CLI for inspecting, controlling, and debugging browser pages via CDP.
allowed-tools: Bash, Read
---

# cdp-cli — Chrome DevTools Protocol CLI

A command-line tool for inspecting and controlling browser pages via the Chrome DevTools Protocol (CDP). Works with any CDP-compatible browser: desktop Chrome, headless Chrome, Chromium, or Quest Browser.

## Installation

```bash
npm install -g @myerscarpenter/cdp-cli
```

## Connecting

cdp-cli connects to a browser's CDP endpoint. By default it uses `http://localhost:9222`.

### Desktop Chrome / Headless

Launch Chrome with remote debugging enabled:

```bash
# Desktop Chrome
google-chrome --remote-debugging-port=9222

# Headless
google-chrome --headless --remote-debugging-port=9222
```

Then use cdp-cli with the default port:

```bash
cdp-cli tabs
```

### Custom Port

```bash
cdp-cli --cdp-url http://localhost:9225 tabs
```

### Meta Quest Browser

Quest Browser uses port 9223 via ADB forwarding:

```bash
adb forward tcp:9223 localabstract:chrome_devtools_remote
cdp-cli --cdp-url http://localhost:9223 tabs
```

### Chromium on Quest (custom builds)

Chromium uses a PID-specific socket:

```bash
# Find the socket
adb shell cat /proc/net/unix | grep chrome_devtools_remote

# Forward it
PID=$(adb shell pidof org.chromium.chrome)
adb forward tcp:9225 localabstract:chrome_devtools_remote_$PID

cdp-cli --cdp-url http://localhost:9225 tabs
```

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `tabs` | List open pages | `cdp-cli tabs` |
| `new [url]` | Open new tab | `cdp-cli new "https://example.com"` |
| `go <page> <action>` | Navigate (URL/back/forward/reload) | `cdp-cli go "My Page" reload` |
| `close <page>` | Close tab | `cdp-cli close "Old Tab"` |
| `console <page>` | View console messages | `cdp-cli console "My App"` |
| `eval <page> <expr>` | Run JavaScript | `cdp-cli eval "My App" "document.title"` |
| `screenshot <page> <file>` | Save screenshot | `cdp-cli screenshot 0 shot.png` |
| `network <page>` | View network requests | `cdp-cli network "My App"` |
| `click <page> [selector]` | Click element | `cdp-cli click "My App" "#submit"` |
| `fill <page> <value> [sel]` | Fill input | `cdp-cli fill "Login" "user@example.com"` |

`<page>` can be a page ID (number) or substring of the page title.

## Common Workflows

### Inspect a Running Page

```bash
cdp-cli tabs                          # Find the page
cdp-cli console "My App"             # Check console output
cdp-cli eval "My App" "location.href" # Get current URL
cdp-cli screenshot "My App" shot.png  # Capture screenshot
```

### Monitor Console During Testing

```bash
cdp-cli console "My App" | grep -i error
```

### Automate Form Interaction

```bash
cdp-cli fill "Login" "user@example.com" "#email"
cdp-cli fill "Login" "password123" "#password"
cdp-cli click "Login" "#submit"
```

## See Also

**quest-dev** plugin — Meta Quest development toolkit with `quest-dev open` for launching URLs on Quest with automatic CDP port forwarding, screenshots, stay-awake, and logcat capture.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No pages found" | Check the browser is running with `--remote-debugging-port` |
| Connection refused | Verify the port matches what the browser is listening on |
| Wrong browser | Check which port/socket you forwarded |
| Empty console | Console capture starts when you connect — messages before that are lost |
