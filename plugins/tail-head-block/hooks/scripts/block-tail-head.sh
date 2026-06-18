#!/bin/bash
# PreToolUse hook that blocks piping Bash tool commands to `| tail` or `| head`.
#
# Why: tail/head buffer their input until EOF. For the Claude Code Bash tool
# this defeats both views of a running command's progress:
#   - Foreground: the user sees nothing stream live; the model only receives
#     the filtered tail when the command exits.
#   - Background: the user's live shell pane watches the task output file,
#     which stays empty until the command exits.
# The intended fix is not to truncate output into the model's context at all.
# Long-running commands belong in the background; the agent should Read the
# task's output file if it needs to inspect output.

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')

if printf '%s' "$command" | grep -qE '\|[[:space:]]*(tail|head)($|[^[:alnum:]_])'; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Piping Bash tool output to | tail or | head is blocked.\n\nWhy: tail/head buffer their input until EOF, so foreground Bash loses real-time visibility for the user AND delivers only the filtered tail to the model at the end. Truncating large output into the model'"'"'s context is not the goal.\n\nWhat to do instead:\n1. Re-run this command with run_in_background: true. Output is written to a file and the user can watch it live in their shell pane.\n2. If you need to inspect it yourself, Read the output file (supports offset/limit for partial reads) — the full output should NOT be pushed into the LLM context.\n\nExceptions where no pipe is needed at all:\n- Native limits: git log -20, grep -m 5\n- Line selection: sed -n 1,20p file"}}' >&2
  exit 2
fi

exit 0
