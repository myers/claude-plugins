# quest-dev Skill Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the quest-dev skill doc to the v2.5.0 CLI surface (multi-device, casting, daemon model, XDG paths) and retire the redundant android-logcat plugin.

**Architecture:** Pure documentation work in the `claude-plugins` repo. Part A deletes the android-logcat plugin (directory + marketplace entry + README row). Part B rewrites `plugins/quest-dev/skills/quest-dev/SKILL.md` section by section, verifying each documented command/flag against the live CLI in the sibling `quest-dev` repo. No CLI source changes.

**Tech Stack:** Markdown. Verification via `node build/index.js <cmd> --help` against the built quest-dev CLI at `~/c/chrome-devtools-cli-workspace/quest-dev`, and `grep` over the claude-plugins repo.

## Global Constraints

- Skill repo: `~/c/claude-plugins`. CLI source-of-truth repo: `~/c/chrome-devtools-cli-workspace/quest-dev` at release 2.5.0 (`038fc76`).
- Spec: `docs/superpowers/specs/2026-06-20-quest-dev-skill-refresh-design.md` (in the skill repo). Every documented claim must match CLI source, not the README.
- Preserve verbatim: the `<EXTREMELY-IMPORTANT>` raw-adb gate and the raw-adb danger table in SKILL.md — they are the skill's core value.
- PIN is a *value* requirement, not a flag requirement: document it as satisfiable by `--pin` **or** saved config (`quest-dev config --pin`, `.quest-dev.json`, `~/.config/quest-dev/config.json`), config preferred.
- Git: add explicit filenames (no `git add .`); don't mention test counts; `cd` into the repo, never `git -C`; develop on `main`.
- Version footer target: "Requires quest-dev CLI v2.5.0+. Requires Quest OS v44+."
- The CLI must be built before verification: `cd ~/c/chrome-devtools-cli-workspace/quest-dev && pnpm run build` (already built this session; rebuild only if stale).

---

## Part A — Retire android-logcat

### Task 1: Delete the android-logcat plugin

**Files:**
- Delete: `~/c/claude-plugins/plugins/android-logcat/` (entire directory: `.claude-plugin/plugin.json`, `skills/android-logcat/SKILL.md`, `skills/android-logcat/CAPTURE-GUIDE.md`, `skills/android-logcat/scripts/capture_logcat.sh`)
- Modify: `~/c/claude-plugins/.claude-plugin/marketplace.json` (remove the `android-logcat` object, currently lines 14–19)
- Modify: `~/c/claude-plugins/README.md` (remove the `android-logcat` row, currently line 35)

**Interfaces:**
- Consumes: nothing.
- Produces: a repo with zero remaining `android-logcat` references — Task 2+ are independent of this.

- [ ] **Step 1: Remove the plugin directory**

```bash
cd ~/c/claude-plugins
git rm -r plugins/android-logcat
```

- [ ] **Step 2: Remove the marketplace entry**

Edit `.claude-plugin/marketplace.json` — delete this object (and its trailing comma handling so the array stays valid JSON):

```json
    {
      "name": "android-logcat",
      "source": "./plugins/android-logcat",
      "description": "Captures and analyzes Android logcat for Quest/Android debugging. Use when testing APKs, debugging crashes, or analyzing Android logs.",
      "keywords": ["android", "logcat", "quest", "debugging", "vr"]
    },
```

- [ ] **Step 3: Remove the README row**

Edit `README.md` — delete this table row:

```
| `android-logcat` | Captures and analyzes Android logcat for Quest/Android debugging. Use when testing APKs, debugging crashes, or analyzing Android logs. |
```

- [ ] **Step 4: Verify no references remain and JSON is valid**

Run:
```bash
cd ~/c/claude-plugins
grep -rn "android-logcat" . --exclude-dir=.git --exclude-dir=docs
node -e "JSON.parse(require('fs').readFileSync('.claude-plugin/marketplace.json','utf8')); console.log('marketplace.json OK')"
```
Expected: grep prints nothing (no matches outside `.git`/`docs`); `marketplace.json OK`. The spec under `docs/` may still reference it by design — that's why `docs` is excluded.

- [ ] **Step 5: Commit**

```bash
cd ~/c/claude-plugins
git add -A plugins/android-logcat .claude-plugin/marketplace.json README.md
git commit -m "chore: retire android-logcat plugin (subsumed by quest-dev logcat)"
```

---

## Part B — quest-dev SKILL.md refresh

All Part B tasks edit the one file `~/c/claude-plugins/plugins/quest-dev/skills/quest-dev/SKILL.md`. Tasks are split by section so a reviewer can accept/reject each independently. Commit after each task.

### Task 2: Frontmatter + Commands Overview table

**Files:**
- Modify: `~/c/claude-plugins/plugins/quest-dev/skills/quest-dev/SKILL.md` (frontmatter `description`, lines ~1–5; Commands Overview table, lines ~36–46)

**Interfaces:**
- Consumes: nothing.
- Produces: the canonical command list later tasks document in detail. Command names used everywhere downstream: `deploy`, `open`, `screenshot`, `cast-screenshot`, `battery`, `start`, `stop`, `ping`, `stay-awake`, `logcat`, `device`, `config`, `setup-cast`.

- [ ] **Step 1: Confirm the live command list**

Run:
```bash
cd ~/c/chrome-devtools-cli-workspace/quest-dev
node build/index.js --help 2>&1 | sed -n '/Commands:/,/Options:/p'
```
Expected: lists screenshot, cast-screenshot, open, logcat, battery, start, stay-awake, deploy, stop, ping, config, setup-cast. (`device` is registered but may not appear in the top help block — confirm with `node build/index.js device --help`.)

- [ ] **Step 2: Update the frontmatter description**

Extend the `description:` field to mention multi-device and casting. Replace the existing description with:

```yaml
description: Use whenever a task touches a Meta Quest / Quest 3 / Quest headset or runs adb against it — deploying an APK, capturing logcat, taking screenshots, casting the VR view, debugging the Quest browser over CDP, checking battery, controlling several headsets at once, or keeping the headset awake. Raw adb can wedge the Quest's VR power stack; this skill provides the safe quest-dev equivalents (deploy, logcat, screenshot, cast, stay-awake) and a per-device daemon so multiple Quests never collide.
```

Leave `allowed-tools: Bash, Read, Grep, Glob, Write` unchanged.

- [ ] **Step 3: Replace the Commands Overview table**

Replace the existing table with the full 13-command surface:

```markdown
| Command | Purpose |
|---------|---------|
| `quest-dev deploy <apk>` | Install + launch + crash-check an APK (use instead of `adb install`) |
| `quest-dev open <url>` | Open URL in Quest browser with CDP port forwarding |
| `quest-dev screenshot <dir>` | Take a Quest screenshot, pull it locally |
| `quest-dev cast-screenshot <dir>` | Capture a per-eye/stereo VR frame from the cast daemon |
| `quest-dev battery` | Show battery percentage and charging state |
| `quest-dev start` | Start the per-device daemon (stay-awake + casting dashboard) |
| `quest-dev stay-awake` | Keep the Quest awake during work (via daemon) |
| `quest-dev stop` | Stop the daemon (restores Quest settings) |
| `quest-dev ping` | Reset the daemon's idle timer during a long session |
| `quest-dev logcat <action>` | Capture Android logs (`start`/`stop`/`status`/`tail`) |
| `quest-dev device <action>` | Manage device aliases + inspect ports (`set`/`list`/`rm`/`info`) |
| `quest-dev config` | Save defaults (PIN, ports, timeouts) |
| `quest-dev setup-cast [source]` | Extract the casting APK from Meta Quest Developer Hub |
```

- [ ] **Step 4: Verify**

Run:
```bash
grep -c "quest-dev " ~/c/claude-plugins/plugins/quest-dev/skills/quest-dev/SKILL.md
```
Expected: a count reflecting all 13 commands present in the table (≥13). Visually confirm every command name from Step 1 appears.

- [ ] **Step 5: Commit**

```bash
cd ~/c/claude-plugins
git add plugins/quest-dev/skills/quest-dev/SKILL.md
git commit -m "docs(quest-dev): refresh frontmatter + full command overview"
```

### Task 3: Daemon model + Multi-device sections (new)

**Files:**
- Modify: `~/c/claude-plugins/plugins/quest-dev/skills/quest-dev/SKILL.md` (insert two new sections after Commands Overview, before the per-command sections)

**Interfaces:**
- Consumes: command names from Task 2.
- Produces: the `--device` ref forms, `$QUEST_DEVICE`, resolution order, and `device` subcommand semantics that per-command tasks (4–7) reference instead of re-explaining.

- [ ] **Step 1: Confirm resolution order and device subcommand from source**

Run:
```bash
cd ~/c/chrome-devtools-cli-workspace/quest-dev
sed -n '1,60p' src/daemon/resolve.ts
node build/index.js device --help 2>&1 | head -5
```
Expected: `resolve.ts` shows precedence `--device → $QUEST_DEVICE → config.device → sole connected device`; `device` accepts `set | list | rm | info`. (Spec gap table cites `daemon/resolve.ts` and `index.ts:696`.)

- [ ] **Step 2: Insert the Daemon Model section**

Add after the Commands Overview table:

```markdown
## Daemon Model

`start`, `stay-awake`, `deploy`, and `logcat` are backed by a single **per-device
daemon**, keyed on the Quest's stable hardware serial. The daemon binds an
OS-assigned HTTP port and exposes a deterministic per-serial CDP port, so two
Quests (or two agents) never collide.

- First command that needs it auto-starts the daemon.
- `quest-dev ping` resets its idle timer — run it during a long session so the
  daemon doesn't idle out.
- `quest-dev stop` shuts the daemon down and restores Quest settings.
```

- [ ] **Step 3: Insert the Multi-device section**

Add immediately after the Daemon Model section:

```markdown
## Multiple Devices

Every command targets one device. Select it with the global `--device <ref>` flag,
where `<ref>` is an **alias**, a raw **address** (`127.0.0.1:5555`,
`quest3.home.arap:5555`), or a **serial**. Or set `QUEST_DEVICE` once per shell:

```bash
export QUEST_DEVICE=quest3
quest-dev stay-awake
quest-dev open http://localhost:3000/
```

**Resolution order:** `--device` → `$QUEST_DEVICE` → saved `config.device` → the single
connected device (if exactly one). With one Quest connected, no flag is needed.

**Aliases** (for devices whose address moves — SSH tunnel vs. `*.home.arap` on the LAN):

```bash
quest-dev device set quest3 127.0.0.1:5555        # connects, records the serial
quest-dev device set quest3 quest3.home.arap:5555 # later, after it moved
quest-dev device list                             # alias, address, serial, daemon state
quest-dev device info quest3                       # serial, address, daemon/CDP/cast ports, stay-awake, battery
quest-dev device info quest3 --json                # agent-friendly
quest-dev device rm quest3
```

The alias maps to a current address; the hardware serial keeps each device's daemon,
logs, and ports consistent across moves. Two agents driving two headsets just set a
different `$QUEST_DEVICE` (or `--device`) — per-serial state means no cross-talk.
```

- [ ] **Step 4: Verify the documented device actions match the CLI**

Run:
```bash
cd ~/c/chrome-devtools-cli-workspace/quest-dev
node build/index.js device set 2>&1 | head -2   # usage error confirms the verb exists
```
Expected: a `Usage: quest-dev device set <alias> <address>` message (verb recognized). Confirm `list`, `rm`, `info` likewise appear in `device --help` choices.

- [ ] **Step 5: Commit**

```bash
cd ~/c/claude-plugins
git add plugins/quest-dev/skills/quest-dev/SKILL.md
git commit -m "docs(quest-dev): add daemon model + multi-device sections"
```

### Task 4: stay-awake section (corrected flags, PIN sources, XDG path)

**Files:**
- Modify: `~/c/claude-plugins/plugins/quest-dev/skills/quest-dev/SKILL.md` (the stay-awake section)

**Interfaces:**
- Consumes: PIN-source rule and daemon model from Tasks 2–3.
- Produces: the corrected flag set used by the Common Workflows task (8): `--pin`, `--idle-timeout`, `--low-battery`, `--unplugged-timeout`, `--off`, `--status`.

- [ ] **Step 1: Confirm the live flag set**

Run:
```bash
cd ~/c/chrome-devtools-cli-workspace/quest-dev
node build/index.js stay-awake --help 2>&1 | sed -n '/Options:/,$p'
```
Expected flags present: `--pin`, `--idle-timeout`/`-i`, `--low-battery`, `--unplugged-timeout`, `--off`, `--status`. Confirm `--disable` is **absent** (renamed to `--off`).

- [ ] **Step 2: Confirm the PID path and PIN resolution from source**

Run:
```bash
cd ~/c/chrome-devtools-cli-workspace/quest-dev
sed -n '100,106p' src/commands/stay-awake.ts   # stayAwakePidPath uses runtimeDir()
sed -n '17,23p' src/utils/paths.ts             # runtimeDir(): XDG_RUNTIME_DIR or state/run
sed -n '68,82p' src/utils/config.ts            # loadPin: --pin → config.pin → exit
```
Expected: PID file is `runtimeDir()/stay-awake-<serial>.pid`; `runtimeDir()` = `$XDG_RUNTIME_DIR/quest-dev/` or `~/.local/state/quest-dev/run/` (macOS); PIN resolves `--pin → config.pin`.

- [ ] **Step 3: Rewrite the stay-awake section body**

Replace the section's flag list, PIN docs, and PID/troubleshooting paths with:

```markdown
Keeps the Quest awake by turning off autosleep, guardian, dialogs, and proximity via
the Meta Scriptable Testing API. Runs through the per-device daemon and spawns a
watchdog so settings are restored even if the parent dies.

```bash
quest-dev stay-awake            # PIN from saved config
quest-dev stay-awake --pin 1234 # explicit PIN
quest-dev stay-awake --status   # show current protection state, change nothing
quest-dev stay-awake --off      # restore protections and exit
```

**PIN** — a PIN value is required (your Meta Store PIN). Provide it via `--pin`, or
save it once so you never pass the flag again (preferred):

```bash
quest-dev config --pin 1234     # → ~/.config/quest-dev/config.json
# or .quest-dev.json in the project: { "pin": "1234" }
```

**Flags:**

- `--pin <pin>` — Meta Store PIN (or saved config, above)
- `--idle-timeout <ms>` (`-i`) — exit after inactivity (default 300000 = 5 min)
- `--low-battery <percent>` — exit when battery hits this level, unplugged (default 10)
- `--unplugged-timeout <ms>` — exit after this long unplugged (default 300000; `0`
  disables; brief unplugs are forgiven)
- `--off` — restore all protections and exit
- `--status` — print current protection state and exit

**Activity signaling** — reset the idle timer from another process. The PID file is
per-serial under the XDG runtime dir:

```bash
kill -USR1 $(cat "$XDG_RUNTIME_DIR/quest-dev/stay-awake-<serial>.pid")
# macOS / no XDG_RUNTIME_DIR: ~/.local/state/quest-dev/run/stay-awake-<serial>.pid
```

A PostToolUse hook in this plugin signals stay-awake automatically after each tool
runs, so a single `quest-dev stay-awake` stays active for the whole session.

Requires Quest OS v44+.
```

- [ ] **Step 4: Verify no stale path/flag remains in the section**

Run:
```bash
grep -nE "\-\-disable|~/\.quest-dev-stay-awake\.pid|~/\.config/quest-dev/config\.json" ~/c/claude-plugins/plugins/quest-dev/skills/quest-dev/SKILL.md
```
Expected: no `--disable`; no `~/.quest-dev-stay-awake.pid`. (`~/.config/quest-dev/config.json` may still legitimately appear as a PIN/config location — that's fine.)

- [ ] **Step 5: Commit**

```bash
cd ~/c/claude-plugins
git add plugins/quest-dev/skills/quest-dev/SKILL.md
git commit -m "docs(quest-dev): correct stay-awake flags, PIN sources, XDG PID path"
```

### Task 5: logcat section (tail pass-through, XDG log path)

**Files:**
- Modify: `~/c/claude-plugins/plugins/quest-dev/skills/quest-dev/SKILL.md` (the logcat section)

**Interfaces:**
- Consumes: daemon model from Task 3.
- Produces: the corrected logcat usage referenced by Common Workflows (Task 8).

- [ ] **Step 1: Confirm actions and tail semantics from source**

Run:
```bash
cd ~/c/chrome-devtools-cli-workspace/quest-dev
sed -n '204,222p' src/index.ts        # action choices start/stop/status; tail short-circuit note
grep -n "latest.txt\|logcat/" README.md | head
```
Expected: `choices: ['start','stop','status']`; comment explaining `tail` is a pre-yargs `tail(1)` pass-through; logs at `$XDG_STATE_HOME/quest-dev/logcat/<serial>/` with a `latest.txt` symlink.

- [ ] **Step 2: Rewrite the logcat section body**

Replace the actions table and examples with:

```markdown
Captures Android logcat through the per-device daemon. The Quest ring buffer fills in
seconds under VR load — always `start` before reproducing a bug.

```bash
quest-dev logcat start                 # clears the buffer, starts capturing
quest-dev logcat start --filter "*:W"  # warnings and above only
quest-dev logcat status                # capturing? which file?
quest-dev logcat stop                  # stop, print file + size
```

**`tail` is a pure `tail(1)` pass-through** over the current capture file — it forwards
its arguments straight to `tail`:

```bash
quest-dev logcat tail          # last 10 lines (tail default)
quest-dev logcat tail -f       # stream until Ctrl-C
quest-dev logcat tail -n 500   # last 500 lines, then exit (good for scripts)
```

**Log files** live under `$XDG_STATE_HOME/quest-dev/logcat/<serial>/` (default
`~/.local/state/quest-dev/logcat/<serial>/`), with a `latest.txt` symlink to the
active capture. Filters use standard logcat syntax (`*:W`, `chromium:V *:S`, `*:E`).

After capture, grep the file for crashes/WebXR/Chromium errors as usual:

```bash
grep -iE "fatal|crash|exception" "$(readlink -f ~/.local/state/quest-dev/logcat/<serial>/latest.txt)"
```
```

- [ ] **Step 3: Verify no stale `./logs/logcat/` claim and tail is documented as pass-through**

Run:
```bash
grep -n "\./logs/logcat/\|Live tail" ~/c/claude-plugins/plugins/quest-dev/skills/quest-dev/SKILL.md
grep -n "tail(1)\|XDG_STATE_HOME\|latest.txt" ~/c/claude-plugins/plugins/quest-dev/skills/quest-dev/SKILL.md
```
Expected: first grep prints nothing (old `./logs/logcat/` path and "Live tail" phrasing gone); second grep confirms the new terms are present.

- [ ] **Step 4: Commit**

```bash
cd ~/c/claude-plugins
git add plugins/quest-dev/skills/quest-dev/SKILL.md
git commit -m "docs(quest-dev): correct logcat tail pass-through + XDG log path"
```

### Task 6: Casting section (new: setup-cast, cast-screenshot, dashboard)

**Files:**
- Modify: `~/c/claude-plugins/plugins/quest-dev/skills/quest-dev/SKILL.md` (insert a new Casting section)

**Interfaces:**
- Consumes: daemon model (`start` serves the dashboard) from Task 3.
- Produces: casting usage referenced by Common Workflows (Task 8).

- [ ] **Step 1: Confirm casting commands from source**

Run:
```bash
cd ~/c/chrome-devtools-cli-workspace/quest-dev
node build/index.js setup-cast --help 2>&1 | head -15
node build/index.js cast-screenshot --help 2>&1 | head -8
sed -n '320,328p' src/index.ts   # `start` prints Dashboard URL + cast/start curl
```
Expected: `setup-cast [source]` accepts `.app`/`.dmg`/`.exe.zip`/dir and auto-detects MQDH; `cast-screenshot <directory>` captures a per-eye/stereo VR frame; `start` serves a dashboard and a `POST /cast/start` endpoint.

- [ ] **Step 2: Insert the Casting section** (place it after the screenshot section)

```markdown
## Casting

quest-dev can cast the Quest's live VR view to your computer. This needs a casting APK
that ships inside Meta Quest Developer Hub (MQDH).

**One-time setup** — extract the APK from MQDH (auto-detected on macOS if installed):

```bash
quest-dev setup-cast                                            # auto-detect MQDH
quest-dev setup-cast "/Applications/Meta Quest Developer Hub.app"
quest-dev setup-cast ~/Downloads/MetaQuestDeveloperHub.dmg      # .dmg
quest-dev setup-cast ~/Downloads/Meta-Quest-Developer-Hub.exe.zip  # Windows (needs 7z)
```

The APK is cached at `~/.local/share/quest-dev/` and auto-installed on the Quest when
casting starts. Download MQDH from https://developer.oculus.com/meta-quest-developer-hub.

**Start casting** — the daemon serves a dashboard and a cast endpoint:

```bash
quest-dev start                          # prints Dashboard URL + cast/start curl
curl -X POST http://localhost:<port>/cast/start
```

**Grab a VR frame** — unlike `screenshot` (compositor view), `cast-screenshot` writes a
validated per-eye/stereo JPEG from the cast stream:

```bash
quest-dev cast-screenshot ~/Desktop
```
```

- [ ] **Step 3: Verify**

Run:
```bash
grep -n "setup-cast\|cast-screenshot\|Dashboard" ~/c/claude-plugins/plugins/quest-dev/skills/quest-dev/SKILL.md
```
Expected: all three terms present in the new section.

- [ ] **Step 4: Commit**

```bash
cd ~/c/claude-plugins
git add plugins/quest-dev/skills/quest-dev/SKILL.md
git commit -m "docs(quest-dev): add casting section (setup-cast, cast-screenshot, dashboard)"
```

### Task 7: XDG paths reference + version footer; preserve danger table

**Files:**
- Modify: `~/c/claude-plugins/plugins/quest-dev/skills/quest-dev/SKILL.md` (add XDG paths reference; bump version footer; confirm danger table + EXTREMELY-IMPORTANT gate intact)

**Interfaces:**
- Consumes: path facts already used in Tasks 4–6.
- Produces: nothing downstream (final content task).

- [ ] **Step 1: Confirm the four XDG roots from source**

Run:
```bash
cd ~/c/chrome-devtools-cli-workspace/quest-dev
sed -n '16,42p' src/utils/paths.ts
```
Expected: `runtimeDir` (XDG_RUNTIME_DIR or state/run), `stateDir` (XDG_STATE_HOME or `~/.local/state`), `configDir` (XDG_CONFIG_HOME or `~/.config`), `dataDir` (XDG_DATA_HOME or `~/.local/share`), all under an `quest-dev` subdir.

- [ ] **Step 2: Add the XDG paths reference** (place it just before the raw-adb danger table)

```markdown
## Where State Lives (XDG)

| What | Location |
|------|----------|
| Daemon registry + PID files | `$XDG_RUNTIME_DIR/quest-dev/` (or `~/.local/state/quest-dev/run/` on macOS) |
| Logcat output | `$XDG_STATE_HOME/quest-dev/logcat/<serial>/` (default `~/.local/state/quest-dev/logcat/<serial>/`) |
| Aliases + config | `$XDG_CONFIG_HOME/quest-dev/` (default `~/.config/quest-dev/`) |
| Casting APK | `$XDG_DATA_HOME/quest-dev/` (default `~/.local/share/quest-dev/`) |
```

- [ ] **Step 3: Bump the version footer**

Replace the existing version footer with:

```markdown
## Version

Requires quest-dev CLI v2.5.0+. Requires Quest OS v44+.
```

- [ ] **Step 4: Confirm the EXTREMELY-IMPORTANT gate and danger table survived all edits**

Run:
```bash
grep -c "EXTREMELY-IMPORTANT" ~/c/claude-plugins/plugins/quest-dev/skills/quest-dev/SKILL.md
grep -n "Do Not Bypass quest-dev With Raw ADB\|automation_enable\|prox_close" ~/c/claude-plugins/plugins/quest-dev/skills/quest-dev/SKILL.md
```
Expected: `EXTREMELY-IMPORTANT` count ≥ 2 (open + close tags); the danger-table heading and at least the `automation_enable`/`prox_close` rows still present.

- [ ] **Step 5: Commit**

```bash
cd ~/c/claude-plugins
git add plugins/quest-dev/skills/quest-dev/SKILL.md
git commit -m "docs(quest-dev): add XDG paths reference, bump version footer to 2.5.0+"
```

### Task 8: Common Workflows + final consistency sweep

**Files:**
- Modify: `~/c/claude-plugins/plugins/quest-dev/skills/quest-dev/SKILL.md` (Common Workflows section + whole-file sweep)

**Interfaces:**
- Consumes: every corrected command/flag from Tasks 2–7.
- Produces: nothing downstream.

- [ ] **Step 1: Update the Common Workflows examples**

Ensure every workflow example uses current commands/flags: `stay-awake` (no `--disable`), `logcat start/stop` + `tail -n`, `deploy`, `cast-screenshot`/`setup-cast` where relevant, and a multi-device example using `$QUEST_DEVICE`. Replace any `--disable` with `--off` and any `./logs/logcat/` with the XDG path or `latest.txt`. Add one multi-device workflow:

```markdown
### Two Quests at once

```bash
quest-dev device set left  127.0.0.1:5555
quest-dev device set right 127.0.0.1:5557

QUEST_DEVICE=left  quest-dev stay-awake
QUEST_DEVICE=right quest-dev stay-awake
QUEST_DEVICE=left  quest-dev logcat start
QUEST_DEVICE=right quest-dev open http://localhost:3000/
# per-serial daemons/ports — the two sessions never collide
```
```

- [ ] **Step 2: Whole-file stale-term sweep**

Run:
```bash
grep -nE "\-\-disable|~/\.quest-dev-stay-awake\.pid|\./logs/logcat/|Live tail|v2\.4\.0" ~/c/claude-plugins/plugins/quest-dev/skills/quest-dev/SKILL.md
```
Expected: **no output**. Any hit is a stale reference — fix it in place.

- [ ] **Step 3: Cross-check every documented command against the live CLI**

Run:
```bash
cd ~/c/chrome-devtools-cli-workspace/quest-dev
for c in deploy open screenshot cast-screenshot battery start stay-awake stop ping logcat device config setup-cast; do
  echo "== $c =="; node build/index.js "$c" --help 2>&1 | sed -n '/Options:/,$p' | grep -E "^\s+--" | head -8
done
```
Expected: for each command, the flags documented in SKILL.md are a subset of the flags the CLI reports. Note any flag in the doc that the CLI doesn't list and remove/fix it.

- [ ] **Step 4: Commit**

```bash
cd ~/c/claude-plugins
git add plugins/quest-dev/skills/quest-dev/skills 2>/dev/null; git add plugins/quest-dev/skills/quest-dev/SKILL.md
git commit -m "docs(quest-dev): refresh common workflows incl. multi-device; final consistency sweep"
```

---

## Self-Review

**Spec coverage** — every spec item maps to a task:
- Part A retirement (delete dir + marketplace + README) → Task 1.
- Frontmatter + Commands Overview → Task 2.
- Daemon model + Multi-device (`--device`, `$QUEST_DEVICE`, resolution order, `device set/list/rm/info`) → Task 3.
- stay-awake (`--off`, `--unplugged-timeout`, PIN sources, XDG PID path, daemon-delegated) → Task 4.
- logcat (`tail` pass-through, XDG log path + `latest.txt`) → Task 5.
- Casting (setup-cast, cast-screenshot, dashboard) → Task 6.
- XDG paths reference + version footer + preserve gate/danger table → Task 7.
- Common Workflows refresh incl. multi-device + final sweep → Task 8.
- screenshot "keep as-is" → no change needed (correctly left untouched).

**Placeholder scan** — no TBD/TODO; every edit shows the literal markdown to write; every verify step has an exact command and expected result.

**Type/name consistency** — command names (`--off` not `--disable`; `cast-screenshot`; `device set/list/rm/info`; `setup-cast`) are used identically across Tasks 2–8. PID path phrasing (`runtimeDir()` / `$XDG_RUNTIME_DIR/quest-dev/`) matches between Tasks 4 and 7. Log path (`$XDG_STATE_HOME/quest-dev/logcat/<serial>/` + `latest.txt`) matches between Tasks 5 and 7.

**Note for executor:** Tasks 2–8 all modify the same file; run them in order and re-read the file before each edit (the line numbers in the spec are pre-edit and will drift).
