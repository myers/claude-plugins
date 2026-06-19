# quest-dev ADB guard + forceful skill-load assertion

**Date:** 2026-06-19
**Plugin:** `plugins/quest-dev` (bump `1.1.0` → `1.2.0`)

## Problem

Raw `adb` commands bypass the `quest-dev` CLI and can wedge the Quest (it has a
layered VR power-management stack). The skill already documents this, but nothing
*enforces* it, and `adb install` is still listed as "safe" even though
`quest-dev deploy <apk>` is the correct path (it auto-starts the daemon, enables
stay-awake, installs, launches, and crash-checks). There is also no forceful
nudge to load the skill when an agent starts Quest work.

Verified facts (2026-06-19):
- Correct plugin-root env var is `${CLAUDE_PLUGIN_ROOT}`; `$PLUGIN_DIR` is unsupported.
  (Already fixed on `main`.)
- `@myerscarpenter/quest-dev` is at `2.4.0`; the deploy command is
  **`quest-dev deploy <apk>`** — there is no `quest-dev install`.
- superpowers achieves once-per-session injection with a **SessionStart hook**
  (matcher `startup|clear|compact`), no marker file.

## Components

### 1. `block-adb.sh` (PreToolUse, Bash) — one consolidated block script
Replaces `block-adb-logcat.sh`. Reads stdin JSON once, extracts
`.tool_input.command`, and denies (JSON `permissionDecision:deny` + exit 2) for:
- **`adb logcat`** (incl. `adb -s SERIAL logcat`) → redirect to `quest-dev logcat`.
- **`adb install` / `adb install-multiple`** (incl. target flags like
  `-s SERIAL`, `-d`, `-e`) → redirect to `quest-dev deploy <apk>`.

Must NOT match: `adb uninstall`, `adb shell pm install`, or the literal word
`install`/`logcat` inside quotes or a path. Everything else exits 0.
One script = one process per Bash call (perf).

### 2. `assert-quest-skill.sh` (SessionStart) — forceful skill-load assertion
Modeled on `superpowers:using-superpowers`. Matcher `startup|clear|compact`.
Emits `hookSpecificOutput.additionalContext` (SessionStart) with a forceful,
superpowers-styled assertion: if there is even a 1% chance the session involves
Meta Quest / `adb` work, the agent MUST load the `quest-dev` skill before running
any adb/quest command. Fires once per session by virtue of the event — no marker.

### 3. SKILL.md changes
- Add an `<EXTREMELY-IMPORTANT>` preamble + a "Red Flags" rationalization table
  near the top (superpowers style).
- Move `adb install -r <apk>` out of the "safe to run directly" list into the
  "dangerous → use quest-dev" table, pointing at `quest-dev deploy <apk>`.
- Strengthen the `description:` frontmatter as a strong activation trigger.

### 4. Wiring / meta
- `hooks.json`: point PreToolUse at `block-adb.sh`; add the SessionStart hook.
- README: document both hooks and the deploy redirect.
- `plugin.json`: `1.2.0`.

## Testing (TDD)

### Hooks — `plugins/quest-dev/tests/test-hook.sh`
Bash `assert <BLOCK|ALLOW> <desc> <command>` harness (modeled on
`plugins/bg-output-guard/tests/test-hook.sh`). Cases:
- BLOCK: `adb logcat`, `adb -s SERIAL logcat`, `adb install app.apk`,
  `adb install-multiple a.apk b.apk`, `adb -s X install app.apk`,
  `adb -d install -r app.apk`.
- ALLOW: `adb uninstall com.foo`, `adb shell pm install /data/x.apk`,
  `adb devices`, `echo "adb install in a comment"`, `quest-dev deploy app.apk`.
- PAYLOAD: blocked commands emit valid deny JSON pointing at the right
  `quest-dev` command.
- SessionStart: running `assert-quest-skill.sh` emits `additionalContext`
  containing the "MUST load the quest-dev skill" assertion.

### Skill — `/writing-skills`
Drive the SKILL.md edits through the writing-skills methodology (baseline →
edit → verify the forceful framing reads correctly and triggers).

## Out of scope / cleanup
- Drop the obsolete `stash@{0}` (already merged into `main`).
- `send-stay-awake-signal.sh` (PostToolUse) unchanged.

## Git
Commit directly to `main` (per request).
