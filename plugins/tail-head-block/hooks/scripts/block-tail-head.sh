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
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Blocked: | tail and | head in the Bash tool.\n\nNext call: Bash with run_in_background: true (no pipe). Then if you need to inspect output: Read the output file (offset/limit supported). This keeps output out of your context and lets the user watch it live."}}' >&2
  exit 2
fi

exit 0
