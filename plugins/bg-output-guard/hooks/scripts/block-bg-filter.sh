#!/bin/bash
# PreToolUse hook: block output-truncating filter pipes on BACKGROUND Bash commands.
#
# Rationale: when a Bash command runs with run_in_background=true, its stdout/stderr
# go to a temp output file that the harness UI shows. A trailing "| tail", "| grep",
# "| head" etc. pre-filters at the pipe, so only the truncated result ever reaches the
# file -- the rest of the log is lost for both the UI and any later inspection. There is
# no upside to filtering at the pipe in background mode: the agent can Read the output
# file with offset/limit, or grep/tail the FILE once the command completes, keeping the
# full log intact. So we forbid the filter and tell the agent to filter the file instead.
#
# Only the FINAL stage of the pipeline is checked -- a filter mid-pipeline (e.g. feeding
# a later "tee file.log") does not truncate the final output, and "tee" is explicitly
# allowed because it writes a full copy.
#
# This is a heuristic, not a full shell parser: it splits on the last top-level "|" and
# can be fooled by "|" inside quotes/subshells. It errs toward ALLOWING (false negatives)
# rather than blocking legitimate commands.

SKILL_REF="For the full explanation (where background output goes, stdout/stderr capture, the right patterns), use the 'bg-output-guard:background-command-output' skill."

deny() {
  # deny <reason text>
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}' "$1" >&2
  exit 2
}

warn() {
  # warn <context text> -- non-blocking note, command still runs.
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"%s"}}'  "$1"
  exit 0
}

input=$(cat)

command=$(echo "$input" | jq -r '.tool_input.command // empty')
background=$(echo "$input" | jq -r '.tool_input.run_in_background // false')

# Only police background commands. Foreground output goes to context, where filtering
# is a legitimate way to keep the result small.
if [[ "$background" != "true" ]]; then
  exit 0
fi

# --- Block tier 1: trailing filter pipe ---------------------------------------
# Isolate the final pipe stage: everything after the last "|".
# (Heuristic; does not account for "|" inside quotes.)
if [[ "$command" == *"|"* ]]; then
  last_stage="${command##*|}"
  # Trim leading whitespace, then take the first word (the command name),
  # stripping any leading path.
  last_stage="${last_stage#"${last_stage%%[![:space:]]*}"}"
  read -r first_word _rest <<<"$last_stage"
  first_word="${first_word##*/}"

  # Filters that discard or collapse lines when used as the final stage of a pipe.
  # "tee" is intentionally NOT here: it writes a full copy.
  case "$first_word" in
    tail|head|grep|egrep|fgrep|rg|ag|sed|awk|cut|uniq|wc|sort|less|more)
      deny "Background command blocked: '| ${first_word}' truncates the output before it reaches the log file.\n\nWhen a command runs in the background, its full output is written to a temp file that the harness UI shows you. Filtering at the pipe (| ${first_word}) throws away the rest of the log BEFORE it hits that file -- so it is gone from the UI and from any later inspection, with no upside.\n\nInstead: run the command WITHOUT the trailing filter so the full log goes to the output file, then filter the FILE once it completes:\n  - Read the output file with offset/limit, or\n  - grep / tail the output file path, e.g.  tail -n 50 <output-file>  or  grep ERROR <output-file>\n\n(tee is allowed -- it writes a full copy. A filter mid-pipeline that still writes full output downstream is fine.)\n\n${SKILL_REF}"
      ;;
  esac
fi

# --- Block tier 2: stderr suppression -----------------------------------------
# stderr is captured to the output file by default; build errors and warnings live
# there. Redirecting it away (2>/dev/null, 2> file) or merging both streams to
# elsewhere (&> , >& ) destroys that. "2>&1" merely MERGES stderr into stdout (which
# still goes to the file) and is explicitly allowed -- so strip it before matching.
no_merge="${command//2>&1/}"
if [[ "$no_merge" =~ 2\>[^\&] ]] || [[ "$no_merge" =~ 2\>$ ]] \
   || [[ "$no_merge" =~ \&\> ]] || [[ "$no_merge" =~ \>\& ]]; then
  deny "Background command blocked: it redirects stderr away from the log (e.g. 2>/dev/null, 2> file, &>, >&).\n\nIn background mode the harness captures BOTH stdout and stderr to the output file automatically. stderr is where build errors and warnings live -- suppressing or diverting it removes exactly the lines you most want in the log, with no upside.\n\nInstead: run the command WITHOUT the stderr redirect. Both streams are captured for free; filter the output FILE afterward if you need to narrow it down. (2>&1 is fine -- it merges stderr into stdout, which still reaches the file.)\n\n${SKILL_REF}"
fi

# --- Warn tier: any other pipe or output redirect -----------------------------
# Not blocked, but a pipe or output redirect in background mode may still divert or
# reshape output that would otherwise land in the log file verbatim. Nudge, don't block.
# "2>&1" is already stripped into $no_merge and is harmless on its own.
if [[ "$command" == *"|"* ]] || [[ "$no_merge" =~ \>\>? ]]; then
  warn "Heads-up: this background command contains a pipe or output redirect. In background mode the full output is captured to a log file the user can see -- any pipe or redirect may reshape or divert what reaches that file. If you only meant to narrow the output, prefer running it plain and filtering the output FILE afterward. Proceeding anyway.\n\n${SKILL_REF}"
fi

exit 0
