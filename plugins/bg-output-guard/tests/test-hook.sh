#!/bin/bash
# Tests for block-bg-filter.sh
#
# The hook has three outcomes:
#   BLOCK - exit 2 with a deny payload on stderr (known filters, stderr suppression)
#   WARN  - exit 0 but emits a non-blocking additionalContext note (other pipes/redirects)
#   ALLOW - exit 0 with no output (clean commands, foreground, tee, 2>&1)
# We test it the same way the harness invokes it: construct the stdin JSON with `jq -n`,
# run the hook, and classify by exit code + whether a payload was emitted.
#
# Run:  plugins/bg-output-guard/tests/test-hook.sh
# Exits non-zero if any case fails.

set -u

HOOK="$(cd "$(dirname "$0")/.." && pwd)/hooks/scripts/block-bg-filter.sh"

pass=0
fail=0

# assert <expected: BLOCK|WARN|ALLOW> <description> <command> <run_in_background: true|false>
assert() {
  local expected="$1" desc="$2" cmd="$3" bg="$4"
  local json out rc verdict
  json=$(jq -cn --arg c "$cmd" --argjson b "$bg" \
    '{tool_name:"Bash",tool_input:{command:$c,run_in_background:$b}}')
  # Capture stdout+stderr together so we can see WARN's additionalContext payload.
  out=$(printf '%s' "$json" | "$HOOK" 2>&1); rc=$?
  if [[ $rc -eq 2 ]]; then
    verdict="BLOCK"
  elif printf '%s' "$out" | grep -q 'additionalContext'; then
    verdict="WARN"
  else
    verdict="ALLOW"
  fi

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
echo "BLOCK: background + stderr suppression (errors live on stderr)"
assert BLOCK "bg cmd 2>/dev/null"         'cargo build 2>/dev/null'        true
assert BLOCK "bg cmd 2> file"             'cargo build 2> errors.txt'      true
assert BLOCK "bg cmd &>/dev/null"         'cargo build &>/dev/null'        true
assert BLOCK "bg cmd >&/dev/null"         'cargo build >&/dev/null'        true

echo
echo "ALLOW: foreground (output goes to context; filtering is legit)"
assert ALLOW "fg cargo build | tail"      'cargo build 2>&1 | tail -n 50'  false
assert ALLOW "fg make | grep"             'make | grep error'              false
assert ALLOW "fg cmd 2>/dev/null"         'cargo build 2>/dev/null'        false

echo
echo "ALLOW: background, clean (no pipe, no redirect)"
assert ALLOW "bg plain build"             'cargo build'                    true
assert ALLOW "bg no pipe at all"          'make all'                       true
assert ALLOW "bg 2>&1 only (merges)"      'cargo build 2>&1'               true

echo
echo "WARN: background pipe/redirect that isn't blocked or clean"
assert WARN  "bg ... | tee file"          'cargo build 2>&1 | tee build.log' true
assert WARN  "bg grep mid-pipe | tee"     'make | grep -v warn | tee build.log' true
assert WARN  "bg pipe into cargo"         'echo x | cargo run'             true
assert WARN  "bg redirect > file"         'cargo build > build.log'        true
assert WARN  "bg redirect >> file"        'cargo build >> build.log'       true

echo
echo "ALLOW: pipe/redirect tokens that live INSIDE quotes (not real operators)"
assert ALLOW "bg | tail in quotes"        'echo "please | tail the log"'   true
assert ALLOW "bg 2>/dev/null in quotes"   'echo "2>/dev/null is just text"' true
assert ALLOW "bg | grep in single quotes" "printf 'see | grep here\n'"     true
assert ALLOW "bg redirect in quotes only" 'echo "write to > file please"'  true
# Mixed: quoted operator-noise must not hide a REAL trailing filter.
assert BLOCK "bg quoted | + real | tail"  'echo "pipe | inside" | tail'    true
assert BLOCK "bg quoted regex + | head"   'grep "a|b" file | head'         true
assert BLOCK "bg quoted 2>&1 + real 2>/d" 'echo "x 2>&1" 2>/dev/null'      true

echo
echo "Emitted deny payload is well-formed JSON"
assert_payload_valid 'cargo build 2>&1 | tail -n 50'
assert_payload_valid 'make | grep error'
assert_payload_valid 'cargo build 2>/dev/null'

echo
echo "----------------------------------------"
printf 'passed: %d  failed: %d\n' "$pass" "$fail"
[[ $fail -eq 0 ]]
