# quest-dev Plugin

Meta Quest development toolkit for Claude Code. Provides comprehensive documentation and automatic activity tracking for Quest development sessions.

## What It Includes

### 1. Quest Dev Skill
Comprehensive guide for using the `quest-dev` CLI toolkit:
- Deploying APKs with `quest-dev deploy` (install + launch + crash-check)
- Opening URLs with CDP debugging
- Taking screenshots with captions
- Battery monitoring
- Stay-awake workflow automation
- Logcat capture and analysis

Invoke with the skill system: `/quest-dev` or when Claude Code needs Quest development guidance.

### 2. PreToolUse ADB Guard (`block-adb.sh`)
Blocks raw `adb` commands that should go through the `quest-dev` CLI and tells the agent the correct command instead:
- `adb logcat` → `quest-dev logcat` (Quest's ring buffer overflows in seconds; raw logcat loses crash logs)
- `adb install` / `adb install-multiple` → `quest-dev deploy <apk>` (raw install skips the daemon, stay-awake, app launch, and crash check)

It deliberately does not block `adb uninstall` or `adb shell pm install`. One script handles both checks, so only one process runs per Bash call.

### 3. SessionStart Skill-Load Assertion (`assert-quest-skill.sh`)
Injects a forceful, once-per-session reminder (modeled on superpowers) that any Meta Quest / adb work MUST go through the quest-dev skill. Fires once per session via the SessionStart event — no marker file.

### 4. PostToolUse Hook
Automatically keeps Quest awake during active Claude Code sessions by sending SIGUSR1 signals to the `quest-dev stay-awake` process after each tool execution. This resets the idle timer, preventing Quest from sleeping while you work.

## How It Works

1. **Start stay-awake**: Run `quest-dev stay-awake` (reads PIN from `.quest-dev.json` or `~/.config/quest-dev/config.json`)
2. **Disables autosleep, guardian, and system dialogs** on Quest
3. **Battery monitoring**: Logs battery at 5% intervals, auto-exits at 10% (configurable)
4. **Work normally**: As you use Claude Code and tools execute, the hook automatically resets the idle timer
5. **Auto-restore**: After 5 minutes of inactivity, Quest automatically restores all settings
6. **Manual exit**: Press Ctrl-C to immediately restore settings

## Architecture

```
Claude Code → PostToolUse Hook → Send SIGUSR1 → quest-dev stay-awake → Reset Idle Timer
```

The hook:
- Runs after every tool execution
- Checks if `~/.quest-dev-stay-awake.pid` exists
- Sends SIGUSR1 if process is running
- Cleans up stale PID files
- Never blocks or fails (always exits 0)

## Requirements

- `quest-dev` CLI v2.4.0+ (for `quest-dev deploy`)
- Quest device connected via ADB
- Quest OS v44+
- Meta Store PIN configured
- Claude Code with plugin support

## Configuration

Create `.quest-dev.json` in your project root (or `~/.config/quest-dev/config.json`):

```json
{ "pin": "1234" }
```

Options when starting stay-awake:

```bash
# Default: uses PIN from config, 5-minute idle timeout, 10% battery exit
quest-dev stay-awake

# Explicit PIN
quest-dev stay-awake --pin 1234

# Custom idle timeout: 10 minutes
quest-dev stay-awake --idle-timeout 600000

# Custom low battery threshold
quest-dev stay-awake --low-battery 20

# Check current state
quest-dev stay-awake --status

# Manual restore after unexpected kill
quest-dev stay-awake --disable --pin 1234
```

## Troubleshooting

**Quest still going to sleep?**
- Check if stay-awake process is running: `ps aux | grep stay-awake`
- Verify PID file exists: `cat ~/.quest-dev-stay-awake.pid`
- Test signal manually: `kill -USR1 $(cat ~/.quest-dev-stay-awake.pid)`
- Check property state: `quest-dev stay-awake --status`

**Settings stuck after crash?**
- Restore manually: `quest-dev stay-awake --disable --pin 1234`

**Hook not working?**
- Verify plugin is installed in Claude Code
- Check hook script is executable: `ls -la $CLAUDE_PLUGIN_ROOT/hooks/scripts/send-stay-awake-signal.sh`
- Test hook manually: `bash /path/to/send-stay-awake-signal.sh`

## Files

- `.claude-plugin/plugin.json` - Plugin metadata
- `hooks/hooks.json` - PreToolUse / SessionStart / PostToolUse hook configuration
- `hooks/scripts/block-adb.sh` - PreToolUse ADB guard (logcat + install)
- `hooks/scripts/assert-quest-skill.sh` - SessionStart skill-load assertion
- `hooks/scripts/send-stay-awake-signal.sh` - Signal sender script
- `tests/test-hook.sh` - Hook test suite
- `README.md` - This file

## Version

1.2.0
