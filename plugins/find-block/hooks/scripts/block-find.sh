#!/bin/bash
# PreToolUse hook that blocks the 'find' command and suggests Glob/Grep tools instead

# Read the JSON input from stdin
input=$(cat)

# Extract the command using jq
command=$(echo "$input" | jq -r '.tool_input.command // empty')

# Check if this is a find command
if [[ "$command" =~ ^find ]]; then
    cat <<EOF
{
  "decision": "block",
  "reason": "The 'find' command is not allowed.\n\nInstead, use:\n- Glob tool for finding files by pattern (e.g., '**/*.rs')\n- Grep tool for searching code with regex patterns\n\nExamples:\n  Glob: pattern='**/*.txt' - Find all .txt files\n  Grep: pattern='function_name' output_mode='files_with_matches' - Find files containing pattern\n\nThe Glob and Grep tools are optimized for Claude Code and handle permissions correctly."
}
EOF
    exit 2
fi

# Allow other Bash commands
exit 0
