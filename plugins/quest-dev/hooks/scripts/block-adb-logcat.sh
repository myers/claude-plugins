#!/bin/bash
# PreToolUse hook that blocks 'adb logcat' and directs to quest-dev logcat

# Read the JSON input from stdin
input=$(cat)

# Extract the command using jq
command=$(echo "$input" | jq -r '.tool_input.command // empty')

# Match adb logcat, including with flags like adb -s SERIAL logcat
if [[ "$command" =~ adb[[:space:]]((-[a-zA-Z]+[[:space:]]+[^[:space:]]+[[:space:]]+)*)?((-[a-zA-Z]+[[:space:]]+)*)logcat ]]; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"adb logcat is blocked. Quest'"'"'s ring buffer overflows in seconds under VR load, so application logs are lost before you can read them. Use quest-dev logcat which captures to persistent files instead.\n\nCommands:\n  quest-dev logcat start                  # Start capture (clears buffer first)\n  quest-dev logcat start --filter \"*:W\"   # Warnings and above only\n  quest-dev logcat status                 # Check if capturing\n  quest-dev logcat tail                   # Live tail of capture\n  quest-dev logcat stop                   # Stop and show file path\n\nLogs saved to ./logs/logcat/. See CAPTURE-GUIDE.md in the android-logcat plugin for details."}}' >&2
  exit 2
fi

# Allow other commands
exit 0
