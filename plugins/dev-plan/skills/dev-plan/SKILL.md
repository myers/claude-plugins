---
name: dev-plan
description: Interactive planning with in-depth requirements interview
model: opus
---

# Planning Request

$ARGUMENTS

# Your Task

1. **First**: Check that the git working tree is clean (no uncommitted changes). If there are uncommitted changes, warn the user and ask how they want to proceed before continuing.

2. **Branch**: Ask the user if this work should be done on a new branch. Suggest a descriptive branch name based on the planning request (e.g., `feature/add-auth-flow`, `fix/login-redirect`). Let the user accept, modify, or decline.

3. **Enter plan mode**: Use the `EnterPlanMode` tool to enter plan mode. This will ask the user for permission to switch modes.

4. **Interview**: Interview me in detail using the AskUserQuestion tool about literally anything: technical implementation, UI & UX, concerns, tradeoffs, etc. but make sure the questions are not obvious. Be very in-depth and continue interviewing me continually until the requirements are fully understood.

5. **Finally**: Write the plan to the plan filename given by the system alert. Use the `ExitPlanMode` tool when the plan is complete and ready for user approval.
