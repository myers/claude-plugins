---
name: dev-plan
description: Interactive planning with in-depth requirements interview
model: opus
---

# Planning Request

$ARGUMENTS

# Your Task

1. **First**: Use the `EnterPlanMode` tool to enter plan mode. This will ask the user for permission to switch modes.

2. **Then**: Interview me in detail using the AskUserQuestion tool about literally anything: technical implementation, UI & UX, concerns, tradeoffs, etc. but make sure the questions are not obvious. Be very in-depth and continue interviewing me continually until the requirements are fully understood.

3. **Finally**: Write the plan to the plan filename given by the system alert. Use the `ExitPlanMode` tool when the plan is complete and ready for user approval.
