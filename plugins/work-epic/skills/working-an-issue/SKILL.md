---
name: working-an-issue
description: Use when dispatching a subagent (or working as one) to do focused work — research, implementation, design, triage — on a single tracker issue (git-issues `iss` or Gitea `gtx`) and report the outcome back on the issue itself. Triggers on "iss", "git-issues", "gtx", "Gitea", "issue", or "ticket" in the dispatch.
---

# Working an issue

The issue is the deliverable. Your closing comment and status change are the
artifact a human or the next subagent will see. Everything else you did is
invisible. Match the recipe below or the work doesn't count.

## Pick the tracker

The dispatch names the tracker. Use its column in the table below for every
command; the rest of this skill uses the operation names.

| Operation | git-issues (`iss`, run from the tracker root) | Gitea (`gtx`, run from the repo clone) |
|---|---|---|
| **read** (body and every comment) | `iss show <id>` | `gtx issue view <n> --comments` |
| **claim** | `iss update <id> --claim` | `gtx issue edit <n> --add-assignee @me` |
| **comment** (body on stdin) | `iss comment <id> -F -` | `gtx issue comment <n> --body-file -` |
| **close** | `iss close <id>` | `gtx issue close <n>` |
| **block** | `iss block <id> --reason "…"` | leave open; Findings says what blocks it (Gitea has no blocked status) |
| **file a follow-up** | `iss new --parent <epic> …` | `gtx issue create --milestone "<title>" …`, following the child-ticket convention in `docs/agents/issue-tracker.md` |

If the dispatch does not name a tracker, the repo's `CLAUDE.md` or
`docs/agents/issue-tracker.md` does. Do not guess.

### Attribution

- **git-issues:** if the orchestrator set `ISS_ACTOR=<your-name>` (or told you
  to pass `--actor <name>`), use it on every claim / comment / close.
  Parallel subagents share one `git config user.name`; the override is the
  only way a reader can tell who did what. Precedence: `--actor` >
  `ISS_ACTOR` > `git config user.name`. If neither was set, don't invent one.
  If the comment landed under the wrong actor, pass `--actor` explicitly on a
  corrective comment.
- **Gitea:** attribution does not apply; every `gtx` write lands under the
  authenticated user.

## What "done" looks like

You produced **two things on the issue**, in this order:

1. **A closing comment** matching the recipe below.
2. **A status change** — closed if the work is complete, or blocked / left
   open with the comment explaining why if not.

**Read** after you finish must show both, or you are not done.

## Closing-comment recipe

The comment is exactly these four sections, in this order, with these
headings. Fill each one. None are optional. Order is the contract.

````
## Findings

<What you learned. Quote sources. Link file paths with line numbers
(file_path:line). If you ran code, say what and what it told you.
This is the substance.>

## Recommendation

<One paragraph. The thing the next person should do based on Findings.>

## Confidence

<low | medium | high>. Then one sentence of why that level.

## Open follow-ups

<Bulleted list. New issues you filed (with their ids), questions you
hit that need their own ticket, or "none.">
````

Send the body on stdin so multi-line content works, using the **comment**
command from the table (`iss` shown):

```bash
cat <<'EOF' | iss comment <id> -F -
## Findings
...
## Recommendation
...
## Confidence
medium. <why>
## Open follow-ups
- none.
EOF
```

## REQUIRED steps

- [ ] **Read** the issue end-to-end before starting. The body AND every
      comment are context; the latest comment may carry direction the body
      doesn't.
- [ ] Do the work. Throwaway code goes under `experiments/<topic>/` (unless
      the repo's `CLAUDE.md` names another place), never at the root. Strip
      nested `.git/` and `.jj/` from experiment subdirs before committing
      (`find experiments/<topic> -name ".git" -exec rm -rf {} +`; same for
      `.jj`).
- [ ] Post the closing comment using the recipe above.
- [ ] Complete → **close**. Blocked on something concrete → **block**. Truly
      incomplete and not blocked → leave open; Findings MUST say why.
- [ ] **Read** again. Verify the new comment is at the bottom and, if
      applicable, the status changed. If not, fix it.

## Boundary

- Do not edit the issue title or body. Comments only.
- Do not edit the body's checklist. If acceptance criteria are met, the
  closing status change is the signal — not editing `[ ]` to `[x]`.
- Do not modify other issues unless your findings genuinely change them.
  When you must, leave a cross-link comment; do not edit their bodies.
- Do not push — no `git push`, no `iss push`. The orchestrator decides when;
  the one exception is a branch push its brief explicitly asks you for.
- Do not close issues that aren't yours.

## Return value to the orchestrator

After the recipe steps land on the issue, summarize back to the dispatcher
under 200 words: the verdict, the issue id you closed (or left open and why),
and any follow-ups you filed.

## Common mistakes

| Mistake | Fix |
|---|---|
| Comment uses your own headings instead of the four-section recipe | Rewrite using the exact recipe headings; the recipe is the contract |
| Restated the body's checklist as `[x]` inside the comment | Delete that section; the status change is the only signal needed |
| "Comment landed" in the return value but issue still open | **Close** it, or explain in Findings why not |
| Confidence implied by tone but not stated | Add the `## Confidence` line with one of `low`/`medium`/`high` |
| Did the work, wrote a great writeup, never posted it | The comment IS the artifact; nothing else counts |
| Ran `iss` commands against a Gitea issue, or `gtx` against git-issues | Use the column for the tracker the dispatch named |
