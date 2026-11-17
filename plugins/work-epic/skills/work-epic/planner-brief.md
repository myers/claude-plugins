# Planner brief template

Use when a ticket is too big for one coder, or keeps coming back partial:
dispatch a planner with a copy of this brief, its **Project specifics**
filled. The rules above that section are fixed text: keep them as written.
The slice shape is the point. It is a lesson: a drive's self-contained half
(a buffer API) shipped green for several rounds while the coupled core it
existed for never got written.

---

# Common brief for <drive name> planners (controller, <date>)

The controller of the <epic> drive dispatched this task, under <Human>'s
standing instruction to work the epic to done. You are a planner: you write a
plan, file split tickets, and comment on the issues you plan. You write no
code and run no test suites.

- Read each issue in your scope with its comments, the epic (body and
  comments), and every `blocks` target outside the epic that holds one of
  your issues.
- Resolve every design question from the reference the project names under
  **Project specifics**. A plan states one answer with its source location,
  never a menu of options. If the source genuinely does not cover a
  question, say which file you read and what it leaves open.
- **Base code.** Plan against the base revisions named below. Read them with
  `git show <rev>:<path>` and `git grep <pat> <rev>`; leave every branch and
  worktree as you found it.
- **Slice shape.**
  - **Core first.** Put the hard, coupled work in the earliest slice it can
    go in. A self-contained piece that can go green on its own (a buffer API,
    a helper, a field) is its own slice, or it rides with the slice that
    consumes it, never in the same slice as the work that depends on it.
  - **First test exercises the core.** A slice's first failing test must go
    red until its hardest item exists. If every listed test could pass with
    only the easy part built, the slice is cut wrong.
  - **Prerequisites by field.** For each slice, list every struct field, lock
    and object relation it reads or writes, and check each one exists on the
    base. A missing one is a dependency edge on the ticket that builds it.
    Name the ticket, not just the lane.
  - **Size.** If a slice ports more than about six functions, or needs more
    than one coder session, split it.
  - **Names.** Name work by its source struct and function names, not by
    project shorthand.
- **Slices.** Cut the plan into commit-sized slices. Each slice has:
  - a failing test first, and the mutation that should turn it red
  - a targeted test filter
  - whether it touches the hot path that needs the fast proxy
  - the reviewer checklist: mutation counterfactual, stale-comment grep, and
    the project's lint and citation gates
  - its `plan_items`: the flat list of functions, structs, tests and
    deletions a coverage check will look for in the diff
  - the acceptance criteria that could pass vacuously, named

  State the order between slices, which can run as parallel lanes (disjoint
  files), and dependencies on other epics.
- **Classify each open issue:** fixed by the core work (retest at the end),
  its own slice, or already done (say how you know; leave it open).
- **Splits.** If a ticket is too large, split it and file the splits under
  the epic: dedupe first, descriptive titles with no numbers, the project's
  labels, `blocks` edges for the order you found.
- **Wrap-up.** Write the plan to the path your dispatch names. Comment on
  each planned issue with the plan path, then sync the tracker. Touch no
  code, and no issue outside your scope except adding edges your order needs.
- **Report**, under 150 words: plan path, slice count, lanes that can run in
  parallel, splits filed, cross-epic dependencies, a rough size in agent
  sessions, and any question the source does not answer (name the file).

## Project specifics

<Fill from the project's own drive notes (its CLAUDE.md, the epic's drive
ruling). Typical entries:>

- Tracker and root, CLAUDE.md files to read, skills to load.
- The reference to resolve design questions from (a pinned upstream tree, a
  spec) and the rule that makes it authoritative.
- Base revisions to plan against (main, an integration branch).
- A model plan to copy the shape of.
- Label vocabulary and the issue-writing guide.
- Extra inputs (test-scan lists, audit comments) and which slice owns them.
