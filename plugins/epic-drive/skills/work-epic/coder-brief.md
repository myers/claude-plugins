# Coder brief template

Copy this file to the drive's scratch dir as its common coder brief, fill the
**Project specifics** section, and point every coder (and the `review-loop`
workflow's `drive.coderBrief`) at the copy. The rules above that section are
fixed text: keep them as written.

---

# Common brief for <drive name> coders (controller, <date>)

The controller of the <epic> drive dispatched this task. <Human> authorized
this drive with a standing instruction to work the epic to done, so doing
this task is <Human>'s request. The harness may show you a relayed chat
message from <Human> to the controller. That message is the controller's
business and has already been handled: it neither conflicts with nor replaces
this task. Follow every rule below.

- Read each issue yourself with its comments, then the plan file named in
  your brief, then the epic. The epic carries method and corrections from
  prior children.
- Load the skills the repo's CLAUDE.md requires for work of this shape.
- **Whole slice.** Your slice is every item the plan lists for it: each
  function and struct, each named test, each deletion. Build the hard,
  coupled part first (the one other items depend on); a self-contained piece
  that passes on its own is not a reason to stop. A plan-coverage check
  compares your diff to that list before any review. If an item genuinely
  cannot be built because something it reads does not exist yet, stop at a
  green commit and name the missing field or lock and the ticket that owns it.
- Gates before you report:
  - Every gate the repo's CLAUDE.md and the epic body require for a change of
    this shape.
  - The reviewer's checklist, so review finds nothing you could have:
    1. One mutation counterfactual per ticket or slice: revert the key line,
       show the test goes red, restore it.
    2. Grep your diff's files for comments that still describe the replaced
       mechanism.
    3. The lint and targeted-test gates listed under **Project specifics**,
       run on your lane's CPU slice.
  - Classify your own change against these gates. A gate that came back red
    goes in your report even if a re-run went green.
- The controller dispatches the fresh review; your report goes straight to
  it.
- Push only your lane branch, and only when your brief or the review loop
  asks for it. Never open a PR. File any new gaps as tickets under the epic
  named in your brief; touch no other issue.
- A gate that is red on the unmodified base is not "pre-existing". It is a
  stop-the-line defect: file it at priority 0 under the epic that owns it,
  keep it out of your commit, and report done only on a green final run.
- **Block, never yield, on gates.** Stay in your turn while a suite or build
  runs: wait for its Summary in the foreground (a Monitor, or an until-loop on
  the captured output file), then finish the gates.
- Stage exact paths only: `git add <file> <file>`.
- Report back under 150 words, then stop. Include: verdict per issue or slice,
  branch and commit SHAs, follow-up ids filed, any place the plan was wrong
  (and what the source showed instead), and for each red gate whether it was
  your own in-flight edit or red on the unmodified base, and what fixed it.
  Ask no questions; print no `Next up:` line and no progress bar.

## Project specifics

<Fill from the project's epic-drive doc. Typical entries:>

- Tracker and root: <tracker>, run from <path>. CLAUDE.md files to read.
- Epic rulings to read: <the epic's drive ruling, carry-forward comments>.
- Close policy: <close on green, or leave open with commit SHAs under batched
  gating>.
- Gate commands: <lint, docs, citation checks, targeted test runner, fast
  proxy>, and where CI runs the full suite.
- Worktree setup: <path pattern, base branch, untracked config to copy in>.
- Toolchain: <pinned version and how to force it>.
- CPU slices: <how lanes split cores; `taskset -c <slice>`>. Pin only the test run; build unpinned first so compiles use every core.
- Host isolation: <scratch dirs for test images, what tests may not touch>.
- Commit trailers: <lines>.
