#!/usr/bin/env python3
"""Stop hook: tell the agent when Woodpecker CI has gone red.

A guard nobody reads is not a guard.  A red pipeline can run faithfully on every
push for weeks with nobody looking, so at the end of a turn this checks the
latest settled pipeline for the checked-out branch and, when it is red, hands
the agent the failure and the two commands that show the logs.

Everything repo-specific is discovered from git, so the hook carries no
configuration and works in any repo registered with Woodpecker.

A broken watcher exits 0.  Every failure path here returns quietly rather than
wedging a turn: no `wp`, no repo, a slow server, unparseable output, a corrupt
cache.  Set CI_WATCH=0 to switch it off for a session.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

INTERVAL = 600        # seconds between polls, per repo, across all sessions
STRIKES = 3           # consecutive nudges without a green before going quiet
WP_TIMEOUT = 8        # `wp` has blocked past 120s in practice
LIMIT = 10            # pipelines to ask for; the branch filter needs headroom

# Statuses that mean "not finished yet" -- no verdict to report.
UNSETTLED = {"pending", "running", "created", "blocked"}
# Settled statuses that are not a failure.  `declined` and `skipped` mean the
# run never happened, which is not something an agent can fix.
NOT_RED = {"success", "skipped", "declined"}


# --- discovery ---------------------------------------------------------------

def git(cwd, *args):
    try:
        r = subprocess.run(["git", "-C", str(cwd), *args],
                           capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def slug_from_url(url):
    """`owner/repo` from any remote URL spelling, or None."""
    if not url:
        return None
    url = url.strip().rstrip("/")
    url = re.sub(r"\.git$", "", url)
    url = re.sub(r"^[a-z+]+://", "", url)          # https://, ssh://
    url = re.sub(r"^[^/@]+@", "", url)             # git@host
    url = url.replace(":", "/", 1) if ":" in url.split("/")[0] else url
    parts = [p for p in url.split("/") if p]
    if len(parts) < 3:                             # host + owner + repo
        return None
    return "/".join(parts[-2:])


# --- state -------------------------------------------------------------------

def state_path(slug):
    cache = os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache")
    return Path(cache) / "claude-ci-watch" / (slug.replace("/", "__") + ".json")


def load_state(slug):
    try:
        return json.loads(state_path(slug).read_text())
    except (OSError, ValueError):
        return {}


def save_state(slug, state):
    p = state_path(slug)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(state))
    except OSError:
        pass


def due(state, now):
    return now - state.get("last_check", 0) >= INTERVAL


# --- polling -----------------------------------------------------------------

def parse_pipelines(text):
    """Rows from a `wp pipeline ls` table.  Anything unparseable is dropped."""
    rows = []
    for line in (text or "").splitlines():
        if not line.strip() or line.lstrip().startswith("{"):
            continue                                # wp's warn lines are JSON
        parts = line.split(None, 4)
        if len(parts) < 4 or not parts[0].isdigit():
            continue                                # header, or not a row
        rows.append({"number": int(parts[0]), "status": parts[1],
                     "event": parts[2], "branch": parts[3],
                     "message": parts[4] if len(parts) > 4 else ""})
    return rows


def pick(rows, branch):
    """The newest settled run on this branch."""
    for row in rows:
        if row["branch"] == branch and row["status"] not in UNSETTLED:
            return row
    return None


def wp(*args):
    try:
        r = subprocess.run(["wp", "--disable-update-check", *args],
                           capture_output=True, text=True, timeout=WP_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def failing_steps(slug, number):
    """Names of the steps that did not pass, best effort."""
    out = wp("pipeline", "ps", slug, str(number))
    if not out:
        return ""
    names, name = [], None
    for line in out.splitlines():
        if line.startswith("Step:"):
            name = line.split(":", 1)[1].strip()
        elif line.startswith("State:") and name:
            if line.split(":", 1)[1].strip() not in NOT_RED:
                names.append(name)
            name = None
    return ", ".join(names)


# --- the decision ------------------------------------------------------------

def decide(row, state, slug, branch):
    """(nudge text or None, new state).  Pure: no clock, no network, no files."""
    state = dict(state)
    if row is None:
        return None, state

    if row["status"] in NOT_RED:
        state["consecutive_nudges"] = 0
        state.pop("last_nudged_pipeline", None)
        return None, state

    if row["number"] == state.get("last_nudged_pipeline"):
        return None, state                          # brake: already said so
    if state.get("consecutive_nudges", 0) >= STRIKES:
        return None, state                          # brake: out of strikes

    state["last_nudged_pipeline"] = row["number"]
    state["consecutive_nudges"] = state.get("consecutive_nudges", 0) + 1
    return message(slug, branch, row, "<step-id>"), state


def message(slug, branch, row, steps):
    return (
        f"CI is red on {slug} ({branch}): "
        f"pipeline {row['number']} {row['status']}"
        f"{', failing: ' + steps if steps and steps != '<step-id>' else ''}.\n\n"
        f"Launch a subagent to fix it. Logs:\n"
        f"  wp pipeline ps {slug} {row['number']}\n"
        f"  wp pipeline log show {slug} {row['number']} <step-id>\n\n"
        f"Done when a new pipeline goes green."
    )


# --- entry point -------------------------------------------------------------

def main():
    if os.environ.get("CI_WATCH") == "0":
        return
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        payload = {}
    if payload.get("stop_hook_active"):
        return                                      # the harness's loop guard

    cwd = payload.get("cwd") or os.getcwd()
    slug = slug_from_url(git(cwd, "remote", "get-url", "origin"))
    branch = git(cwd, "symbolic-ref", "--short", "HEAD")
    if not slug or not branch:
        return

    now = int(time.time())
    state = load_state(slug)
    if not due(state, now):
        return

    state["last_check"] = now
    out = wp("pipeline", "ls", slug, "--limit", str(LIMIT))
    row = pick(parse_pipelines(out), branch)
    nudge, state = decide(row, state, slug, branch)
    save_state(slug, state)

    if nudge:
        steps = failing_steps(slug, row["number"])
        print(json.dumps({"decision": "block",
                          "reason": message(slug, branch, row, steps)}))


if __name__ == "__main__":
    try:
        main()
    except Exception:                               # a broken watcher exits 0
        pass
