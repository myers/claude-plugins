#!/usr/bin/env bash
# PreToolUse hook: block raw adb commands that must go through the quest-dev CLI.
#
# One script, so only one process runs per Bash call. Two cases are blocked:
#   1. adb logcat        -> quest-dev logcat   (Quest's ring buffer overflows in
#                           seconds under VR load; raw logcat loses crash logs)
#   2. adb install[-multiple] -> quest-dev deploy <apk>   (raw install skips the
#                           daemon, stay-awake, app launch, and crash check)
#
# Deliberately NOT blocked: 'adb uninstall', 'adb shell pm install' (the regex
# requires install to follow adb + optional global flags, so 'shell pm' breaks
# the match; 'uninstall' starts with 'un', not 'install').

set -u

input=$(cat)
command=$(printf '%s' "$input" | jq -r '.tool_input.command // empty')

SKILL_REF="If there is even a 1% chance this session involves Meta Quest work, STOP and load the quest-dev skill (Skill tool: quest-dev) before running adb -- it is not optional."

deny() {
  # printf %b interprets the \n escapes in the message into real newlines.
  local reason; reason=$(printf '%b' "$1")
  jq -n --arg r "$reason" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}' >&2
  exit 2
}

# adb logcat (incl. 'adb -s SERIAL logcat')
if [[ "$command" =~ adb[[:space:]]((-[a-zA-Z]+[[:space:]]+[^[:space:]]+[[:space:]]+)*)?((-[a-zA-Z]+[[:space:]]+)*)logcat ]]; then
  deny "adb logcat is blocked. Quest's ring buffer overflows in seconds under VR load, so application logs are lost before you can read them. Use quest-dev logcat, which captures to persistent files in ./logs/logcat/ instead.\n\nCommands:\n  quest-dev logcat start                  # Start capture (clears buffer first)\n  quest-dev logcat start --filter \"*:W\"   # Warnings and above only\n  quest-dev logcat tail                   # Live tail of capture\n  quest-dev logcat stop                   # Stop and show file path\n\n${SKILL_REF}"
fi

# adb install / adb install-multiple (incl. global flags like '-s SERIAL', '-d', '-e')
if [[ "$command" =~ adb[[:space:]]((-[a-zA-Z]+[[:space:]]+[^[:space:]]+[[:space:]]+)*)?((-[a-zA-Z]+[[:space:]]+)*)install([-[:space:]]|$) ]]; then
  deny "adb install is blocked. Use 'quest-dev deploy <apk>' instead -- it auto-starts the daemon, enables stay-awake, installs, launches the app, and checks for an immediate crash. A bare 'adb install' skips all of that and can leave the Quest in a bad state.\n\n  quest-dev deploy path/to/app.apk\n\n${SKILL_REF}"
fi

exit 0
