#!/bin/bash
# Claude Code PostToolUse hook - sends activity signal to quest-dev stay-awake
# This script runs after every tool execution to keep Quest awake during active sessions

PID_FILE="$HOME/.quest-dev-stay-awake.pid"

# Exit silently if no stay-awake process
if [ ! -f "$PID_FILE" ]; then
  exit 0
fi

# Read PID and check if process exists
PID=$(cat "$PID_FILE" 2>/dev/null)
if [ -z "$PID" ]; then
  exit 0
fi

if kill -0 "$PID" 2>/dev/null; then
  # Process exists, send SIGUSR1 to reset idle timer
  kill -USR1 "$PID" 2>/dev/null
else
  # Process dead, cleanup stale PID file
  rm -f "$PID_FILE" 2>/dev/null
fi

exit 0  # Always succeed - hook must never block
