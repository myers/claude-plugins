#!/bin/bash
# Android Logcat Capture Script
# Usage: capture_logcat.sh start [filter] | stop | status
#
# CRITICAL: Always start capture BEFORE testing on Quest.
# The ring buffer fills in seconds and you WILL lose crash logs.

# Use local directory relative to workspace root
LOG_DIR="${LOG_DIR:-logs/logcat}"
PID_FILE="$LOG_DIR/.logcat_pid"
LOGFILE_LINK="$LOG_DIR/latest.txt"

case "$1" in
  start)
    # Check for existing capture
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
      echo "Already capturing. Use 'stop' first."
      exit 1
    fi

    # Check ADB connection
    if ! adb devices | grep -q "device$"; then
      echo "No Android device connected. Check ADB."
      exit 1
    fi

    mkdir -p "$LOG_DIR"
    LOGFILE="$LOG_DIR/logcat_$(date +%Y%m%d_%H%M%S).txt"

    # Clear the buffer first - critical for Quest
    adb logcat -c

    echo "Starting capture to: $LOGFILE"
    echo "Ring buffer cleared."

    if [ -n "$2" ]; then
      echo "Filter: $2"
      adb logcat -v threadtime "$2" > "$LOGFILE" 2>&1 &
    else
      adb logcat -v threadtime > "$LOGFILE" 2>&1 &
    fi

    echo $! > "$PID_FILE"
    ln -sf "$(basename "$LOGFILE")" "$LOGFILE_LINK"

    echo "Capturing (PID: $!)"
    echo ""
    echo "Now run your test. When done: $0 stop"
    ;;

  stop)
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        echo "Capture stopped (PID: $PID)"
      else
        echo "Capture process already ended"
      fi
      rm "$PID_FILE"

      # Show file info
      if [ -L "$LOGFILE_LINK" ]; then
        LATEST=$(readlink "$LOGFILE_LINK")
        if [ -f "$LOG_DIR/$LATEST" ]; then
          SIZE=$(du -h "$LOG_DIR/$LATEST" | cut -f1)
          LINES=$(wc -l < "$LOG_DIR/$LATEST")
          echo ""
          echo "Log file: $LOG_DIR/$LATEST"
          echo "Size: $SIZE ($LINES lines)"
        fi
      fi
    else
      echo "No capture in progress"
    fi
    ;;

  status)
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
      echo "Capturing (PID: $(cat $PID_FILE))"
      if [ -L "$LOGFILE_LINK" ]; then
        LATEST=$(readlink "$LOGFILE_LINK")
        if [ -f "$LOG_DIR/$LATEST" ]; then
          SIZE=$(du -h "$LOG_DIR/$LATEST" | cut -f1)
          LINES=$(wc -l < "$LOG_DIR/$LATEST")
          echo "File: $LOG_DIR/$LATEST"
          echo "Size: $SIZE ($LINES lines)"
        fi
      fi
    else
      echo "Not capturing"
      if [ -d "$LOG_DIR" ]; then
        echo ""
        echo "Recent logs:"
        ls -lht "$LOG_DIR"/*.txt 2>/dev/null | head -5
      fi
    fi
    ;;

  tail)
    # Live tail of current capture
    if [ -L "$LOGFILE_LINK" ] && [ -f "$LOG_DIR/$(readlink "$LOGFILE_LINK")" ]; then
      tail -f "$LOG_DIR/$(readlink "$LOGFILE_LINK")"
    else
      echo "No active log file"
    fi
    ;;

  *)
    echo "Android Logcat Capture"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  start [filter]  Start capturing (clears buffer first)"
    echo "  stop            Stop capturing and show file info"
    echo "  status          Check capture status"
    echo "  tail            Live tail of current capture"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Capture all logs"
    echo "  $0 start '*:W'              # Warnings and above"
    echo "  $0 start 'chromium:V *:S'   # Only chromium tag"
    echo ""
    echo "Log directory: $LOG_DIR"
    ;;
esac
