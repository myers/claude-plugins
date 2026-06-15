#!/bin/bash
# Tests for block-bg-filter.sh
#
# The hook's contract: read a tool-call JSON on stdin, exit 2 to BLOCK (with a deny
# payload on stderr) or exit 0 to ALLOW. We test it the same way the harness invokes it:
# construct the stdin JSON with `jq -n`, run the hook, and assert on the exit code.
#
# Run:  plugins/bg-output-guard/tests/test-hook.sh
# Exits non-zero if any case fails.

set -u

HOOK="$(cd "$(dirname "$0")/.." && pwd)/hooks/scripts/block-bg-filter.sh"

pass=0
fail=0

# assert <expected: BLOCK|ALLOW> <description> <command> <run_in_background: true|false>
assert() {
  local expected="$1" desc="$2" cmd="$3" bg="$4"
  local json out rc verdict
  json=$(jq -cn --arg c "$cmd" --argjson b "$bg" \
    '{tool_name:"Bash",tool_input:{command:$c,run_in_background:$b}}')
  out=$(printf '%s' "$json" | "$HOOK" 2>/dev/null); rc=$?
  if [[ $rc -eq 2 ]]; then verdict="BLOCK"; else verdict="ALLOW"; fi

  if [[ "$verdict" == "$expected" ]]; then
    pass=$((pass + 1))
    printf '  ok   %-6s %s\n' "$verdict" "$desc"
  else
    fail=$((fail + 1))
    printf '  FAIL want=%s got=%s (rc=%d)  %s\n' "$expected" "$verdict" "$rc" "$desc"
  fi
}

# assert_payload_valid — a blocked command must emit parseable JSON with a deny decision.
assert_payload_valid() {
  local cmd="$1"
  local json out
  json=$(jq -cn --arg c "$cmd" '{tool_name:"Bash",tool_input:{command:$c,run_in_background:true}}')
  out=$(printf '%s' "$json" | "$HOOK" 2>&1)
  if printf '%s' "$out" | python3 -c '
import sys, json
d = json.load(sys.stdin)
assert d["hookSpecificOutput"]["permissionDecision"] == "deny"
' 2>/dev/null; then
    pass=$((pass + 1))
    echo "  ok   PAYLOAD valid deny JSON for: $cmd"
  else
    fail=$((fail + 1))
    echo "  FAIL PAYLOAD invalid/malformed JSON for: $cmd"
  fi
}

echo "Testing $HOOK"
echo

echo "BLOCK: background + trailing filter"
assert BLOCK "bg cargo build | tail"      'cargo build 2>&1 | tail -n 50'  true
assert BLOCK "bg make | grep"             'make | grep error'              true
assert BLOCK "bg cmd | head"              'long-cmd | head -100'           true
assert BLOCK "bg cmd | rg"                'cargo test | rg FAILED'         true
assert BLOCK "bg cmd | wc"                'cargo build | wc -l'            true
assert BLOCK "bg cmd | sed -n"            'make | sed -n 1,20p'            true
assert BLOCK "bg cmd | awk"               'make | awk "/error/"'           true
assert BLOCK "bg cmd | uniq"              'make | uniq'                    true
assert BLOCK "bg cmd | sort"              'make | sort'                    true
assert BLOCK "bg cmd | less"              'make | less'                    true
assert BLOCK "bg | /usr/bin/tail"         'make | /usr/bin/tail -5'        true

echo
echo "ALLOW: foreground (output goes to context; filtering is legit)"
assert ALLOW "fg cargo build | tail"      'cargo build 2>&1 | tail -n 50'  false
assert ALLOW "fg make | grep"             'make | grep error'              false

echo
echo "ALLOW: background, no harmful final filter"
assert ALLOW "bg plain build"             'cargo build'                    true
assert ALLOW "bg ... | tee file"          'cargo build 2>&1 | tee build.log' true
assert ALLOW "bg grep mid-pipe | tee"     'make | grep -v warn | tee build.log' true
assert ALLOW "bg pipe into cargo"         'echo x | cargo run'             true
assert ALLOW "bg no pipe at all"          'make all'                       true

echo
echo "Emitted deny payload is well-formed JSON"
assert_payload_valid 'cargo build 2>&1 | tail -n 50'
assert_payload_valid 'make | grep error'

echo
echo "----------------------------------------"
printf 'passed: %d  failed: %d\n' "$pass" "$fail"
[[ $fail -eq 0 ]]
