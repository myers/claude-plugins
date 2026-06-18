---
name: executing-plans
description: Use when you have a written implementation plan to execute in a separate session with review checkpoints
---

<!-- myers-superpowers: AskUserQuestion mandate -->
## Asking the user questions — MANDATORY PATTERN

**This fork of superpowers requires the `AskUserQuestion` tool for every user-facing choice.**

Whenever this skill tells you to "ask", "offer options", "present approaches", "get approval", "confirm", "pick", or otherwise solicit a decision from your human partner, and the answer space is enumerable as 2-4 distinct options:

- You MUST invoke the `AskUserQuestion` tool.
- Each question gets a short header (≤12 chars), a complete question ending with "?", and 2-4 options. Each option has a 1-5 word label and a one-sentence description explaining what it means or the tradeoff it implies.
- If you recommend one option, put it first and suffix its label with " (Recommended)".
- Do NOT output the question as prose followed by "which do you prefer?", "A/B/C?", or a numbered list — the harness will not surface prose choices as structured selections, and typing "1" can be read as a grading response, not an answer.
- Use `multiSelect: true` only when answers genuinely compose (e.g. "which checks do you want to run?").
- If the tool is not yet loaded in your environment, use `ToolSearch` with `select:AskUserQuestion` to load it before invoking.

**Narrow exceptions (ask as prose):**
- Genuinely open-ended questions with no enumerable answer space ("what does success look like for this feature?").
- One-word confirmations where the user has already been shown the concrete artifact being confirmed and "yes/no" is adequate.

This rule overrides any instruction in this skill that says to "ask one question at a time" as plain text — interpret every such instruction as "call AskUserQuestion with one question at a time".

# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

**Note:** Tell your human partner that Superpowers works much better with access to subagents. The quality of its work will be significantly higher if run on a platform with subagent support (such as Claude Code or Codex). If subagents are available, use superpowers:subagent-driven-development instead of this skill.

## The Process

### Step 1: Load and Review Plan
1. Read plan file
2. Review critically - identify any questions or concerns about the plan
3. If concerns: Raise them with your human partner before starting
4. If no concerns: Create TodoWrite and proceed

### Step 2: Execute Tasks

For each task:
1. Mark as in_progress
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as completed

### Step 3: Complete Development

After all tasks complete and verified:
- Announce: "I'm using the finishing-a-development-branch skill to complete this work."
- **REQUIRED SUB-SKILL:** Use superpowers:finishing-a-development-branch
- Follow that skill to verify tests, present options, execute choice

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** - stop and ask.

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications
- Reference skills when plan says to
- Stop when blocked, don't guess
- Never start implementation on main/master branch without explicit user consent

## Integration

**Required workflow skills:**
- **superpowers:using-git-worktrees** - REQUIRED: Set up isolated workspace before starting
- **superpowers:writing-plans** - Creates the plan this skill executes
- **superpowers:finishing-a-development-branch** - Complete development after all tasks
