#!/bin/bash
# Tests for the quest-dev PreToolUse guard (block-adb.sh) and the SessionStart
# skill-load assertion (assert-quest-skill.sh).
#
# block-adb.sh outcomes:
#   BLOCK - exit 2 with a deny payload (adb logcat, adb install)
#   ALLOW - exit 0, no payload (everything else)
# We invoke the hook the way the harness does: build the stdin JSON with `jq -n`,
# run the hook, classify by exit code.
#
# Run:  plugins/quest-dev/tests/test-hook.sh
# Exits non-zero if any case fails.

set -u

DIR="$(cd "$(dirname "$0")/.." && pwd)"
BLOCK_HOOK="$DIR/hooks/scripts/block-adb.sh"
ASSERT_HOOK="$DIR/hooks/scripts/assert-quest-skill.sh"

pass=0
fail=0

# assert <BLOCK|ALLOW> <description> <command>
assert() {
  local expected="$1" desc="$2" cmd="$3"
  local json out rc verdict
  json=$(jq -cn --arg c "$cmd" '{tool_name:"Bash",tool_input:{command:$c}}')
  out=$(printf '%s' "$json" | "$BLOCK_HOOK" 2>&1); rc=$?
  if [[ $rc -eq 2 ]]; then verdict="BLOCK"; else verdict="ALLOW"; fi
  if [[ "$verdict" == "$expected" ]]; then
    pass=$((pass + 1)); printf '  ok   %-6s %s\n' "$verdict" "$desc"
  else
    fail=$((fail + 1)); printf '  FAIL want=%s got=%s (rc=%d)  %s\n' "$expected" "$verdict" "$rc" "$desc"
  fi
}

# assert_redirect <command> <substring the deny reason must contain>
assert_redirect() {
  local cmd="$1" needle="$2" json out reason
  json=$(jq -cn --arg c "$cmd" '{tool_name:"Bash",tool_input:{command:$c}}')
  out=$(printf '%s' "$json" | "$BLOCK_HOOK" 2>&1)
  reason=$(printf '%s' "$out" | jq -r '.hookSpecificOutput.permissionDecisionReason // empty' 2>/dev/null)
  if [[ -n "$reason" && "$reason" == *"$needle"* ]]; then
    pass=$((pass + 1)); echo "  ok   REDIR  '$cmd' -> mentions '$needle'"
  else
    fail=$((fail + 1)); echo "  FAIL REDIR  '$cmd' deny reason missing '$needle'"
  fi
}

# assert_session_assertion <substring the additionalContext must contain>
assert_session_assertion() {
  local needle="$1" json out ctx
  json=$(jq -cn '{hook_event_name:"SessionStart",source:"startup"}')
  out=$(printf '%s' "$json" | "$ASSERT_HOOK" 2>&1)
  ctx=$(printf '%s' "$out" | jq -r '.hookSpecificOutput.additionalContext // empty' 2>/dev/null)
  if [[ -n "$ctx" && "$ctx" == *"$needle"* ]]; then
    pass=$((pass + 1)); echo "  ok   ASSERT SessionStart context mentions '$needle'"
  else
    fail=$((fail + 1)); echo "  FAIL ASSERT SessionStart context missing '$needle'"
  fi
}

echo "Testing $BLOCK_HOOK"
echo

echo "BLOCK: adb logcat (ring buffer is lost) -> quest-dev logcat"
assert BLOCK "adb logcat"                 'adb logcat'
assert BLOCK "adb -s SERIAL logcat"       'adb -s ABC123 logcat'
assert BLOCK "adb logcat with filter"     'adb logcat *:W'

echo
echo "BLOCK: adb install (bypasses daemon/stay-awake/crash-check) -> quest-dev deploy"
assert BLOCK "adb install apk"            'adb install app.apk'
assert BLOCK "adb install -r apk"         'adb install -r app.apk'
assert BLOCK "adb install-multiple"       'adb install-multiple a.apk b.apk'
assert BLOCK "adb -s X install apk"       'adb -s emulator-5554 install app.apk'
assert BLOCK "adb -d install -r apk"      'adb -d install -r app.apk'

echo
echo "ALLOW: not a deploy/logcat (uninstall, pm install, plain adb, quest-dev itself)"
assert ALLOW "adb uninstall"              'adb uninstall com.foo.bar'
assert ALLOW "adb shell pm install"       'adb shell pm install /data/local/tmp/x.apk'
assert ALLOW "adb devices"               'adb devices'
assert ALLOW "adb shell am start"         'adb shell am start -n com.foo/.Main'
assert ALLOW "quest-dev deploy (correct)" 'quest-dev deploy app.apk'
assert ALLOW "plain build"                'cargo build'

echo
echo "Deny payloads redirect to the right quest-dev command"
assert_redirect 'adb install app.apk' 'quest-dev deploy'
assert_redirect 'adb logcat'          'quest-dev logcat'

echo
echo "SessionStart: forceful skill-load assertion"
assert_session_assertion 'quest-dev'
assert_session_assertion 'MUST'

echo
echo "----------------------------------------"
printf 'passed: %d  failed: %d\n' "$pass" "$fail"
[[ $fail -eq 0 ]]
