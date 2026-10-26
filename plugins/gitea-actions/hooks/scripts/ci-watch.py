#!/usr/bin/env python3
"""Stop hook: tell the agent when Gitea Actions CI has gone red.

The Gitea twin of woodpecker-cli's ci-watch.  At the end of a turn this checks,
for each workflow, the latest finished run on the checked-out branch, and when
any is red hands the agent the failure and the commands that show the logs.

The repo is the git remote whose host is gtx's Gitea instance
(`gtx config get default.url`), not necessarily `origin`; a repo with no such
remote is skipped.  `gtx` is run from the repo's own directory without `-R`, so
it makes the same pick.  A GitHub repo that happens to share an `owner/repo`
with one on Gitea never gets reported.

A broken watcher exits 0.  Every failure path here returns quietly rather than
wedging a turn: no `gtx`, no repo, a slow server, unparseable output, a corrupt
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
GTX_TIMEOUT = 8
LIMIT = 20            # runs to ask for; several workflows share the window

# Finished runs whose conclusion is not a failure.  `cancelled` is mostly
# `cancel-in-progress` superseding a run, which is not something to fix.
NOT_RED = {"success", "skipped", "neutral", "cancelled"}
FIELDS = "databaseId,status,conclusion,headBranch,workflowName,displayTitle"


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


def host_from_url(url):
    """Lowercased host of a remote or web URL, without user or port, or None."""
    if not url:
        return None
    url = re.sub(r"^[a-z+]+://", "", url.strip())
    host = re.split(r"[/:]", re.sub(r"^[^/@]+@", "", url), maxsplit=1)[0]
    return host.lower() or None


def gitea_slug(cwd):
    """`owner/repo` of the remote on gtx's Gitea instance, origin first."""
    host = host_from_url(gtx(cwd, "config", "get", "default.url"))
    remotes = (git(cwd, "remote") or "").split()
    if not host or not remotes:
        return None
    remotes.sort(key=lambda r: r != "origin")
    for name in remotes:
        url = git(cwd, "remote", "get-url", name)
        if host_from_url(url) == host:
            return slug_from_url(url)
    return None


# --- state -------------------------------------------------------------------

def state_path(slug):
    cache = os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache")
    return Path(cache) / "claude-gitea-ci-watch" / (slug.replace("/", "__") + ".json")


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

def gtx(cwd, *args):
    try:
        r = subprocess.run(["gtx", *args], cwd=cwd, capture_output=True,
                           text=True, timeout=GTX_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def parse_runs(text):
    """Runs from `gtx run list --json`.  Anything unparseable is dropped."""
    try:
        data = json.loads(text or "")
    except ValueError:
        return []
    if not isinstance(data, list):
        return []
    return [r for r in data
            if isinstance(r, dict) and isinstance(r.get("databaseId"), int)]


def red_runs(runs):
    """Per workflow, the newest finished run; the red ones, newest first."""
    latest = {}
    for r in sorted(runs, key=lambda r: r["databaseId"], reverse=True):
        if r.get("status") == "completed":
            latest.setdefault(r.get("workflowName"), r)
    red = [r for r in latest.values() if r.get("conclusion") not in NOT_RED]
    return sorted(red, key=lambda r: r["databaseId"], reverse=True)


def failing_jobs(cwd, run_id):
    """Names of the jobs that did not pass, best effort."""
    try:
        jobs = json.loads(gtx(cwd, "run", "view", str(run_id), "--json", "jobs")
                          or "")["jobs"]
        return ", ".join(j["name"] for j in jobs
                         if j.get("conclusion") not in NOT_RED)
    except (ValueError, KeyError, TypeError):
        return ""


# --- the decision ------------------------------------------------------------

def decide(red, state):
    """(nudge?, new state).  Pure: no clock, no network, no files."""
    state = dict(state)
    if not red:
        state["consecutive_nudges"] = 0
        state.pop("last_nudged_runs", None)
        return False, state

    ids = sorted(r["databaseId"] for r in red)
    if ids == state.get("last_nudged_runs"):
        return False, state                         # brake: already said so
    if state.get("consecutive_nudges", 0) >= STRIKES:
        return False, state                         # brake: out of strikes

    state["last_nudged_runs"] = ids
    state["consecutive_nudges"] = state.get("consecutive_nudges", 0) + 1
    return True, state


def message(slug, branch, red, jobs):
    lines = [f"CI is red on {slug} ({branch}):"]
    for r in red:
        failing = jobs.get(r["databaseId"])
        lines.append(f"  {r.get('workflowName')} run {r['databaseId']} "
                     f"{r.get('conclusion')}"
                     f"{', failing: ' + failing if failing else ''}")
    first = red[0]["databaseId"]
    lines += ["", "Launch a subagent to fix it. Logs:",
              f"  gtx run view {first} --repo {slug}",
              f"  gtx run view {first} --repo {slug} --log-failed",
              "", "Done when a new run goes green."]
    return "\n".join(lines)


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
    slug = gitea_slug(cwd)
    branch = git(cwd, "symbolic-ref", "--short", "HEAD")
    if not slug or not branch:
        return

    now = int(time.time())
    state = load_state(slug)
    if not due(state, now):
        return

    state["last_check"] = now
    out = gtx(cwd, "run", "list", "-b", branch, "-L", str(LIMIT), "--json", FIELDS)
    red = red_runs(parse_runs(out))
    nudge, state = decide(red, state)
    save_state(slug, state)

    if nudge:
        jobs = {r["databaseId"]: failing_jobs(cwd, r["databaseId"]) for r in red}
        print(json.dumps({"decision": "block",
                          "reason": message(slug, branch, red, jobs)}))


if __name__ == "__main__":
    try:
        main()
    except Exception:                               # a broken watcher exits 0
        pass
