# quest-dev skill refresh (v2.5.0) + retire android-logcat

**Date:** 2026-06-20
**Status:** Approved
**Scope:** Documentation refresh of an existing skill + retirement of a redundant plugin. No CLI code changes.

## Goal

Bring `plugins/quest-dev/skills/quest-dev/SKILL.md` up to date with the quest-dev CLI
v2.5.0 surface (multi-device, casting, daemon model, XDG paths), correcting every claim
against the CLI source — not the README, which has its own drift. Retire the
`android-logcat` plugin, which v2.5.0's `quest-dev logcat` fully subsumes.

Every claim in the gap table below was verified against source in
`~/c/chrome-devtools-cli-workspace/quest-dev/src/` at commit `038fc76` (release 2.5.0).

## Part A — Retire `android-logcat`

The `android-logcat` plugin (a standalone `capture_logcat.sh` wrapper) is fully replaced
by `quest-dev logcat` (start/stop/status/tail, same `logs/logcat/` concept, same grep
patterns). Worse, it instructs raw `adb shell pidof` — exactly the raw-adb pattern the
quest-dev skill forbids. Keeping it invites the failure mode quest-dev exists to prevent.

**Retirement (hard delete + marketplace):**

1. `git rm -r plugins/android-logcat/`
2. Remove the `android-logcat` object from `.claude-plugin/marketplace.json` (lines 14–19,
   the `{ "name": "android-logcat", ... }` entry).
3. Remove the `android-logcat` row from the plugin table in `README.md` (line 35).
4. Commit.

## Part B — quest-dev SKILL.md refresh

### Gap table (every row source-verified)

| Current SKILL.md | Source reality (file:line) | Action |
|---|---|---|
| Commands: deploy, open, screenshot, battery, stay-awake, logcat | Missing `start`, `stop`, `ping`, `cast-screenshot`, `setup-cast`, `device`, `config` (`index.ts` command table) | Add |
| No multi-device concept | Global `--device <alias\|address\|serial>`; `$QUEST_DEVICE`; `config.device`. Resolution: `--device → $QUEST_DEVICE → config.device → sole connected device` (`daemon/resolve.ts`, README §Multiple devices) | New section |
| No `device` subcommand | `device set/list/rm/info`, `--json`, reports serial/daemonPort/cdpPort/castPort/stayAwake/battery (`index.ts:696`, `commands/device.ts`) | Add |
| stay-awake `--disable` | Flag renamed to `--off`; `--status` retained (`index.ts:354`) | Fix |
| stay-awake flags pin/idle/low-battery | Adds `--unplugged-timeout` (default 300000ms, `0` disables, forgives brief unplugs) (`stay-awake.ts:172`, `index.ts:350`) | Add |
| stay-awake = foreground process | Daemon-delegated: `stay-awake` enables via daemon; direct path kept only for `--off`/`--status` fallback. `start` and `deploy` also enable it (`index.ts:332`) | Reframe |
| `--pin` required | Confirmed: `loadPin()` feeds the Scriptable Testing API to set/restore protections (`stay-awake.ts:91,166,221`). README dropped `--pin` from its list; source keeps it | Keep `--pin` |
| PID file `~/.quest-dev-stay-awake.pid` | `runtimeDir()/stay-awake-<serial>.pid` = `$XDG_RUNTIME_DIR/quest-dev/`, or `~/.local/state/quest-dev/run/` when `XDG_RUNTIME_DIR` unset (macOS) (`paths.ts:17`, `stay-awake.ts:103`) | Fix |
| logcat actions start/stop/status/**tail** (all equal) | start/stop/status are daemon-delegated; `tail` is a pre-yargs `tail(1)` pass-through forwarding `-f`, `-n N` (`index.ts:204–222`) | Fix tail semantics |
| Logs in `./logs/logcat/` | `$XDG_STATE_HOME/quest-dev/logcat/<serial>/` with a `latest.txt` symlink (README §Logcat, `paths.ts`) | Fix |
| screenshot `<directory>` + `--caption` | Correct: positional is `directory`, auto-filename, `-c/--caption` embeds JPEG COM (`commands/screenshot.ts`). (README's file-path example is the README's drift.) | Keep |
| No casting | `setup-cast [source]` extracts the cast APK from MQDH; `cast-screenshot <dir>` grabs a per-eye/stereo VR frame; `start` serves a dashboard (`index.ts:722`, `commands/cast-screenshot.ts`, README §Casting Setup) | New section |
| `--browser` default `com.oculus.browser`, `--close-others` | Correct (`index.ts:185`) | Keep |
| Raw-adb danger table | Still valid and the skill's core value | Keep |
| Version footer "v2.4.0+" | 2.5.0 | Bump to 2.5.0+ |

### Rewritten skill structure

Preserve the EXTREMELY-IMPORTANT raw-adb gate and the danger table verbatim — they are the
skill's reason to exist. Layer the new surface on top:

1. **Frontmatter** — extend `description` to mention multi-device + casting; `allowed-tools` unchanged.
2. **EXTREMELY-IMPORTANT raw-adb gate** — keep as-is.
3. **Prerequisites** — keep; note Wi-Fi via `adb connect` is supported.
4. **Commands Overview** — expand the table to all 13 user-facing commands.
5. **Daemon model** (new, short) — one per-device daemon backs `start`/`stay-awake`/`deploy`/`logcat`;
   `ping` resets its idle timer, `stop` shuts it down. OS-assigned HTTP port; deterministic per-serial CDP port.
6. **Multi-device** (new) — `--device` ref forms, `$QUEST_DEVICE`, resolution order, and `device set/list/rm/info`.
7. **Per-command sections** — deploy, open, screenshot, battery,
   stay-awake (corrected: `--pin`, `--idle-timeout`, `--low-battery`, `--unplugged-timeout`, `--off`, `--status`; daemon-delegated; XDG PID path),
   logcat (start/stop/status daemon-delegated + `tail` as `tail(1)` pass-through; XDG log path + `latest.txt`),
   casting (setup-cast / cast-screenshot / dashboard).
8. **XDG paths reference** (new) — runtime/state/config/data locations from `paths.ts`.
9. **Raw-adb danger table** — keep.
10. **Version footer** → "Requires quest-dev CLI v2.5.0+. Requires Quest OS v44+."

## Out of scope

- No changes to the quest-dev CLI source.
- No changes to quest-dev plugin hooks (`block-adb.sh`, `assert-quest-skill.sh`, `send-stay-awake-signal.sh`) — out of scope unless a hook references a path the refresh corrects (none found).
- No rewrite of the README in the CLI repo.

## Verification

- Re-run `node build/index.js <cmd> --help` for any command whose flags are documented, to confirm the skill matches the live CLI.
- Confirm no remaining repo references to `android-logcat` after deletion (`grep -rn android-logcat`).
