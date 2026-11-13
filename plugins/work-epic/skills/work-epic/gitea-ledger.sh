#!/usr/bin/env bash
# Ledger + progress bar for a Gitea epic. Run inside the repo clone.
# Usage: gitea-ledger.sh <epic>  — an issue number (its milestone is the epic) or a milestone title.
# One row per open issue, oldest first, then the bar. Never prints bodies.
set -euo pipefail
epic=$1
epic_issue=0
ms=$(gtx issue view "$epic" --json milestone 2>/dev/null | jq -r '.milestone.title // empty' || true)
if [[ $epic =~ ^[0-9]+$ && -n $ms ]]; then epic_issue=$epic; else ms=$epic; fi
repo=$(git remote get-url origin | sed -E 's#\.git$##; s#.*[:/]([^/]+/[^/]+)$#\1#')

issues=$(gtx issue list --state all -L 1000 -m "$ms" --json number,state,title,assignees,labels \
  | jq --argjson skip "$epic_issue" '[.[] | select(.number != $skip)]')
total=$(jq length <<<"$issues")
closed=$(jq '[.[] | select(.state != "OPEN")] | length' <<<"$issues")

jq -r 'sort_by(.number)[] | select(.state == "OPEN")
       | [.number, ([.assignees[]?.login] | join(",") | if . == "" then "-" else . end),
          ([.labels[]?.name] | join(",") | if . == "" then "-" else . end), .title] | @tsv' <<<"$issues" |
while IFS=$'\t' read -r n who labels title; do
  blocks=$(gtx api "repos/$repo/issues/$n/dependencies" | jq -r --arg ms "$ms" \
    '[.[] | select(.state == "open") | "\(.number)" + (if (.milestone.title // "") == $ms then "" else "@outside" end)] | join(",")')
  printf '%s\topen\tassignee=%s\tblocks=%s\tlabels=%s\t%s\n' "$n" "$who" "$blocks" "$labels" "$title"
done

width=20 filled=0 pct=0
if (( total > 0 )); then filled=$(( closed * width / total )); pct=$(( closed * 100 / total )); fi
bar=$(printf '%*s' "$filled" '' | tr ' ' '#')$(printf '%*s' $((width - filled)) '' | tr ' ' '-')
printf '[%s] %d/%d (%d%%) - %s\n' "$bar" "$closed" "$total" "$pct" "$ms"
