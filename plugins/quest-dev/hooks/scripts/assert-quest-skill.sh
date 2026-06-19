#!/bin/bash
# SessionStart hook: forcefully assert that any Meta Quest work goes through the
# quest-dev skill. Modeled on superpowers' SessionStart injection -- fires once
# per session by virtue of the event, so no marker file is needed.

set -u
cat >/dev/null  # drain stdin (SessionStart payload); we don't need it

read -r -d '' ASSERTION <<'EOF'
<EXTREMELY-IMPORTANT>
Meta Quest development discipline:

If there is even a 1% chance that what you are about to do touches a Meta Quest
device -- running adb, deploying an APK, taking a screenshot, reading logs,
debugging the Quest browser, or keeping the headset awake -- you ABSOLUTELY MUST
load the quest-dev skill FIRST (Skill tool: quest-dev) and operate from it.

This is not optional. Raw adb commands bypass the quest-dev daemon and can wedge
the Quest's layered VR power-management stack, requiring a reboot. The skill
documents which commands are safe and which have quest-dev equivalents
(quest-dev deploy / logcat / screenshot / stay-awake).

Red flags that mean STOP and load the skill:
  "It's just one adb command"        -> load the skill.
  "I'll deploy with adb install"     -> use quest-dev deploy; load the skill.
  "I just need the logs quickly"     -> use quest-dev logcat; load the skill.
  "I know how adb works"             -> the Quest's power stack is the trap; load it.
</EXTREMELY-IMPORTANT>
EOF

jq -n --arg c "$ASSERTION" \
  '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$c}}'
exit 0
