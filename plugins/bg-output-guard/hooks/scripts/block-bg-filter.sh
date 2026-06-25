#!/usr/bin/env bash
# PreToolUse hook: block output-truncating filter pipes on BACKGROUND Bash commands.
#
# Rationale: when a Bash command runs with run_in_background=true, the harness already
# captures its full stdout+stderr to a temp output file AND returns that file's path in
# the tool result. The agent should LEAN ON that capture -- Read the file with
# offset/limit, or grep/tail the path once the command completes -- rather than reshape
# the stream on the way in or roll its own log file. Two failure modes we police:
#   1. Truncation: a trailing "| tail"/"| grep"/"| head" pre-filters at the pipe, so only
#      the lossy result reaches the file -- the rest is gone for the UI and later inspection.
#   2. Duplication: "> myfile 2>&1" rebuilds the combined console log the harness already
#      made, and leaves the harness's own output file (the one the UI shows) EMPTY --
#      reducing visibility, not adding it.
# Both have no upside in background mode, so we block the clear cases and warn the rest,
# always pointing the agent back to the output-file path it was handed.
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

# Build a "skeleton" of the command with the CONTENTS of quoted strings blanked out, so
# that pipes/redirects appearing inside quotes (e.g. echo "use | tail") are not mistaken
# for real shell operators. Each quoted run is replaced by a single 'Q' placeholder: that
# preserves surrounding structure (echo "x"|tail still shows the pipe) while removing any
# operator characters that lived inside the quotes. Done char-by-char in awk so single and
# double quotes nest correctly. This is still a heuristic (no escaped-quote / heredoc
# handling), but it removes the most common false-positive: operator-looking text in args.
skeleton=$(printf '%s' "$command" | awk '
{
  out=""; q=""
  n=length($0)
  for (i=1;i<=n;i++){
    c=substr($0,i,1)
    if (q==""){
      if (c=="\""||c=="\x27"){ q=c; out=out "Q" }   # opening quote -> one placeholder
      else out=out c
    } else {
      if (c==q){ q="" }                              # closing quote -> drop char
      # else: inside quotes, drop the char entirely
    }
  }
  print out
}')

# All operator detection below runs against $skeleton, not the raw $command. The matched
# filter NAME also comes from the skeleton, so it is never quoted text.

# is_filter <name> -> 0 if name is a line-discarding/collapsing filter, else 1.
# "tee" and "cat" are NOT filters: they pass the full stream through.
is_filter() {
  case "$1" in
    tail|head|grep|egrep|fgrep|rg|ag|sed|awk|cut|uniq|wc|sort|less|more) return 0 ;;
    *) return 1 ;;
  esac
}

# stage_cmd <pipe stage> -> the effective command name of that stage: leading whitespace
# trimmed, any leading path stripped, and wrapper words (env/command/builtin/xargs/nice/
# stdbuf/time/sudo) skipped so e.g. "env tail" reports "tail". Wrappers may themselves take
# options; we skip leading words that are wrappers or look like flags until we hit the real
# command. (xargs CMD runs CMD per input -- treat CMD as the effective command.)
stage_cmd() {
  local s="$1" w
  # shellcheck disable=SC2086
  set -- $s                                   # word-split the stage
  while [[ $# -gt 0 ]]; do
    w="${1##*/}"
    case "$w" in
      env|command|builtin|exec|nice|stdbuf|time|sudo|xargs)
        shift; continue ;;                    # wrapper -> look at the next word
      -*)
        shift; continue ;;                    # a flag/option -> skip
      *)
        printf '%s' "$w"; return ;;
    esac
  done
}

# --- Block tier 0: nohup detaches the process from the harness ----------------
# nohup makes the process ignore SIGHUP and, when stdout is not a tty (always the case
# here), redirects output to ./nohup.out -- diverting it away from the harness's output
# file. It is almost always paired with "&" to double-background, spawning a detached
# child the harness can neither track nor stop while the task "completes" instantly. In
# background mode the harness ALREADY manages the process lifecycle and captures output
# to the log file, so nohup has no upside and destroys both. Match "nohup" as a command
# word (a leading path like /usr/bin/nohup is covered by the [^[:alnum:]_] boundary).
if [[ "$skeleton" =~ (^|[^[:alnum:]_])nohup([[:space:]]|$) ]]; then
  deny "Background command blocked: it uses 'nohup'.\n\nnohup makes the process ignore SIGHUP and, when stdout is not a terminal (it never is here), redirects output to ./nohup.out -- so the real output never reaches the harness log file. It is almost always paired with '&', double-backgrounding into a detached process the harness can neither track nor stop, while the task reports completion immediately.\n\nIn background mode the harness already keeps the process alive and captures BOTH stdout and stderr to the output file for you. nohup defeats that with no upside.\n\nInstead: run the command plain with run_in_background -- drop 'nohup' (and the trailing '&'). The harness handles detachment and output capture; Read the output file or filter it once the command completes.\n\n${SKILL_REF}"
fi

# --- Block tier 1: the final pipe stage is a filter ---------------------------
# We block only when the LAST stage truncates -- that is the unambiguous case where the
# filtered (lossy) stream is exactly what reaches the log. Wrapper words (env/command/
# xargs/...) are stripped so "| env tail" is caught. A filter that is NOT the final stage
# -- e.g. "| tail | cat" or "| grep -v noise | tee file" -- is structurally indistinguishable
# from a legitimate noise-filter-then-tee, so by design it falls through to the warn tier
# (the user's call: warn, don't block, so the agent still learns its harness keeps the full
# log). This means "| tail | cat" is a KNOWN, warned bypass rather than a hard block.
if [[ "$skeleton" == *"|"* ]]; then
  final=$(stage_cmd "${skeleton##*|}")
  if is_filter "$final"; then
    deny "Background command blocked: '| ${final}' truncates the output before it reaches the log file.\n\nWhen a command runs in the background, its full output is written to a temp file that the harness UI shows you. Filtering at the pipe (| ${final}) throws away the rest of the log BEFORE it hits that file -- so it is gone from the UI and from any later inspection, with no upside.\n\nYou do not need to capture this yourself: the harness ALREADY wrote the full stdout+stderr to a file AND returned its path to you in the tool result (the 'Output is being written to: <path>' line). Use that path.\n\nInstead: run the command WITHOUT the trailing filter, then read or filter the harness output FILE once it completes:\n  - Read the output file with offset/limit, or\n  - grep / tail that path, e.g.  tail -n 50 <output-file>  or  grep ERROR <output-file>\n\n${SKILL_REF}"
  fi
fi

# --- Block tier 2: stderr suppression -----------------------------------------
# stderr is captured to the output file by default; build errors and warnings live
# there. Redirecting it away (2>/dev/null, 2> file) or merging both streams to
# elsewhere (&> , >& ) destroys that. "2>&1" merely MERGES stderr into stdout (which
# still goes to the file) and is explicitly allowed -- so strip it before matching.
no_merge="${skeleton//2>&1/}"
if [[ "$no_merge" =~ 2\>[^\&] ]] || [[ "$no_merge" =~ 2\>$ ]] \
   || [[ "$no_merge" =~ \&\> ]] || [[ "$no_merge" =~ \>\& ]]; then
  deny "Background command blocked: it redirects stderr away from the log (e.g. 2>/dev/null, 2> file, &>, >&).\n\nIn background mode the harness captures BOTH stdout and stderr to the output file automatically. stderr is where build errors and warnings live -- suppressing or diverting it removes exactly the lines you most want in the log, with no upside.\n\nInstead: run the command WITHOUT the stderr redirect. Both streams are captured for free; filter the output FILE afterward if you need to narrow it down. (2>&1 is fine -- it merges stderr into stdout, which still reaches the file.)\n\n${SKILL_REF}"
fi

# --- Block tier 3: building your own combined console log (>FILE plus 2>&1) ---
# "cmd > some.log 2>&1" merges stderr into stdout and sends the whole console
# stream to a file the AGENT chose. That is exactly what the harness already does
# in background mode: it writes the full stdout+stderr to its output file and hands
# back that file's path in the tool result. So this redirect is pure duplication --
# and worse, it leaves the harness's OWN output file (the one the UI shows the user)
# empty, reducing visibility instead of adding it. High-precision signature, low
# false-positive: a 2>&1 merge together with a ">" redirect to a real file (a
# deliverable like "> backup.sql" is almost never paired with 2>&1, and "> /dev/null"
# is a deliberate discard -- both excluded here). The agent's pull toward its own
# file is ergonomic (a predictable name to grep later); the fix is to remind it the
# harness path is already provided, not to let it roll its own.
if [[ "$skeleton" == *"2>&1"* ]] && [[ "$no_merge" =~ \>\>?[[:space:]]*([^[:space:]|\&\;\<\>]+) ]]; then
  tgt="${BASH_REMATCH[1]}"
  if [[ "$tgt" != "/dev/null" ]]; then
    deny "Background command blocked: it builds its own combined console log (> ${tgt} ... 2>&1).\n\nMerging stderr into stdout and redirecting it to a file is EXACTLY what the harness already does for a background command -- it captures the full stdout+stderr to an output file and returns that file's path to you in the tool result (the 'Output is being written to: <path>' line). Your redirect just duplicates that, and it leaves the harness's own output file -- the one the user sees in the UI -- empty. So it reduces visibility with no upside.\n\nYou already have the file you want: it is the path in the tool result. Run the command plain (drop '> ${tgt}' and the '2>&1'), then Read or grep/tail that path once it completes. If you want a stable name, the tool-result path is stable for the life of the task -- reference it directly.\n\n${SKILL_REF}"
  fi
fi

# --- Warn tier: any other pipe or output redirect -----------------------------
# Not blocked, but a pipe or output redirect in background mode may still divert or
# reshape output that would otherwise land in the log file verbatim. Nudge, don't block.
# "2>&1" is already stripped into $no_merge and is harmless on its own.
if [[ "$skeleton" == *"|"* ]] || [[ "$no_merge" =~ \>\>? ]]; then
  warn "Heads-up: this background command contains a pipe or output redirect. In background mode the harness already captures the full stdout+stderr to an output file and returns its path to you in the tool result ('Output is being written to: <path>') -- so you usually do NOT need a redirect of your own. A pipe or redirect here may reshape or divert what reaches that file, and if you are redirecting just to capture a log, you are duplicating the harness and emptying the file the user sees. If you only meant to narrow the output, run it plain and grep/tail that returned path afterward. Proceeding anyway.\n\n${SKILL_REF}"
fi

exit 0
