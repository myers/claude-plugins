# quest-dev Plugin

Meta Quest development toolkit for Claude Code. Provides comprehensive documentation and automatic activity tracking for Quest development sessions.

## What It Includes

### 1. Quest Dev Skill
Comprehensive guide for using the `quest-dev` CLI toolkit:
- Opening URLs with CDP debugging
- Taking screenshots with captions
- Battery monitoring
- Stay-awake workflow automation
- Logcat capture and analysis

Invoke with the skill system: `/quest-dev` or when Claude Code needs Quest development guidance.

### 2. PostToolUse Hook
Automatically keeps Quest awake during active Claude Code sessions by sending SIGUSR1 signals to the `quest-dev stay-awake` process after each tool execution. This resets the idle timer, preventing Quest from sleeping while you work.

## How It Works

1. **Start stay-awake**: Run `quest-dev stay-awake` in your terminal (default 5-minute idle timeout)
2. **Work normally**: As you use Claude Code and tools execute, the hook automatically resets the timer
3. **Auto-sleep**: After 5 minutes of inactivity (no tool executions), Quest automatically restores screen timeout
4. **Manual exit**: Press Ctrl-C in the stay-awake terminal to immediately restore settings

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

- `quest-dev` CLI installed with stay-awake command
- Quest device connected via ADB
- Claude Code with plugin support

## Configuration

The idle timeout can be customized when starting stay-awake:

```bash
# Default: 5 minutes
quest-dev stay-awake

# Custom timeout: 10 minutes
quest-dev stay-awake --idle-timeout 600000

# Short timeout for testing: 10 seconds
quest-dev stay-awake -i 10000
```

## Troubleshooting

**Quest still going to sleep?**
- Check if stay-awake process is running: `ps aux | grep stay-awake`
- Verify PID file exists: `cat ~/.quest-dev-stay-awake.pid`
- Test signal manually: `kill -USR1 $(cat ~/.quest-dev-stay-awake.pid)`

**Hook not working?**
- Verify plugin is installed in Claude Code
- Check hook script is executable: `ls -la $PLUGIN_DIR/hooks/scripts/send-stay-awake-signal.sh`
- Test hook manually: `bash /path/to/send-stay-awake-signal.sh`

## Files

- `.claude-plugin/plugin.json` - Plugin metadata
- `hooks/hooks.json` - PostToolUse hook configuration
- `hooks/scripts/send-stay-awake-signal.sh` - Signal sender script
- `README.md` - This file

## Version

1.0.0
