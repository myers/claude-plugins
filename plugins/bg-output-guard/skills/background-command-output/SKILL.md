---
name: background-command-output
description: Use when running a Bash command in the background (run_in_background=true) to understand where its output goes, why you must NOT pipe it through tail/grep/head, and how to retrieve and filter the full log afterward. Covers stdout/stderr capture behavior.
---

# Background Command Output

How output works when a Bash command runs with `run_in_background: true`, and the rules
that keep the full log intact for both you and the user's harness UI.

## The core mechanic

A background command does **not** return its output in the tool result. Instead:

1. The tool call returns immediately with a **task ID** and an **output file path**.
   The output file is the ONLY place the command's output goes.
2. Output is **not** placed in your context automatically.
3. When the command finishes, the harness sends a `<task-notification>` — it tells you
   the command completed and re-points you at the output file. It still does not put the
   contents in your context.
4. To see the output you must **deliberately `Read` the output file** (or read it partway
   through for interim output).

The user sees that same output file in the harness UI. So whatever reaches the file is
what *both* of you can inspect; whatever is discarded before the file is gone for good.

## stdout AND stderr are both captured

Verified empirically: with no redirects, the harness captures **both stdout and stderr**
to the single output file, already interleaved. You do **not** need to add `2>&1` to see
stderr — compiler errors and warnings land in the file automatically.

| Command in background        | What reaches the output file                          |
|------------------------------|-------------------------------------------------------|
| `cargo build`                | stdout + stderr, interleaved (full log)               |
| `cargo build 2>&1`           | same — `2>&1` is redundant for capture, but harmless  |
| `cargo build 2>/dev/null`    | stdout only — **stderr is destroyed** (errors lost!)  |
| `cargo build 2>build.err`    | stdout only — stderr diverted to a separate file      |

## The rule: do NOT filter at the pipe in background mode

**Never** end a background command with a filter that discards lines:

```
# WRONG — only the last 50 lines ever reach the file; the rest of the log is lost
cargo build 2>&1 | tail -n 50        (run_in_background: true)

# WRONG — non-matching lines never reach the file
make | grep error                    (run_in_background: true)
```

There is **zero upside** to filtering at the pipe in background mode, because the output
is going to a file anyway. Filtering there can only destroy data the user would otherwise
see in the UI.

Likewise, do not suppress stderr in background mode (`2>/dev/null`, `2> file`, `&>`):
stderr is where build errors and warnings live, and it's captured for free.

Do **not** wrap a background command in `nohup` (e.g. `nohup cmd &`). The harness already
keeps the process alive and captures its output; `nohup` redirects output to `nohup.out`
and detaches the process so the harness can no longer track or stop it. Run the command
plain with `run_in_background` and let the harness handle detachment and capture.

## The right pattern: run unfiltered, filter the FILE afterward

Let the full output go to the file, then narrow it down once the command completes:

```
# 1. Run unfiltered in the background
cargo build                          (run_in_background: true)
#    -> returns output file path: /.../tasks/<id>.output

# 2. When the <task-notification> arrives, filter the FILE, not the stream:
#    - Read the output file with offset/limit, OR
#    - tail/grep the file path:
tail -n 50 /.../tasks/<id>.output
grep -n 'error\[' /.../tasks/<id>.output
```

This keeps the complete log in the file (and the user's UI) while still giving you just
the slice you need.

## Quick reference

| Goal                          | Don't                          | Do                                        |
|-------------------------------|--------------------------------|-------------------------------------------|
| See the last N lines          | `cmd \| tail -N` in background  | run `cmd`, then `tail -N <output-file>`   |
| Find matching lines           | `cmd \| grep X` in background   | run `cmd`, then `grep X <output-file>`    |
| See errors only               | `cmd 2>/dev/null` in background | run `cmd` (stderr is captured), grep file |
| Capture both streams          | adding `2>&1`                   | nothing — both are captured by default    |
| Keep a long task running      | `nohup cmd &` in background     | run `cmd` plain — the harness keeps it alive |

This is enforced by the `bg-output-guard` plugin's PreToolUse hook, which blocks
output-truncating filter pipes on background Bash commands.
