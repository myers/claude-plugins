#!/usr/bin/env python3
"""Stop hook: tell the agent when Gitea Actions CI has gone red.

At the end of a turn this checks, for each workflow, the latest finished run on
the checked-out branch, and when any is red hands the agent the failure and the
commands that show the logs.

The repo is the git remote whose host is gtx's Gitea instance
(`gtx config get default.url`), not necessarily `origin`; a repo with no such
remote is skipped.  `gtx` is run from the repo's own directory without `-R`, so
it makes the same pick.  A GitHub repo that happens to share an `owner/repo`
with one on Gitea never gets reported.

A repo can also name other repos to watch in a tracked `.ci-watch` file (one
`owner/repo` per line, `#` comments), found in the cwd or any directory above
it, so a session in a nested worktree reads its workspace's list.  For each
watched repo the hook checks the default branch (newest finished run per
workflow, which catches a red nightly) and the runs of PRs merged into it in
the last LANDED_WINDOW seconds (which catches an informational job that went
red after the PR landed).  The nudge names the landing range or the PR.

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
from datetime import datetime
from pathlib import Path

INTERVAL = 600        # seconds between polls, per repo, across all sessions
STRIKES = 3           # consecutive nudges without a green before going quiet
GTX_TIMEOUT = 8
LIMIT = 20            # runs to ask for; several workflows share the window
WIDE_LIMIT = 100      # repo-wide runs scanned for landed PRs' runs
PR_LIMIT = 20         # recently closed PRs scanned for landings
LANDED_WINDOW = 12 * 3600  # how long a landed PR's runs stay watched
DEADLINE = 20         # seconds; the harness kills the hook at 30
# ponytail: checked between watched repos only; one repo whose gtx calls all
# stall (8 s each) can still reach 30 s. Pass a remaining budget if that bites.
WATCH_FILE = ".ci-watch"

# Finished runs whose conclusion is not a failure.  `cancelled` is mostly
# `cancel-in-progress` superseding a run, which is not something to fix.
NOT_RED = {"success", "skipped", "neutral", "cancelled"}
FIELDS = ("databaseId,status,conclusion,headBranch,workflowName,displayTitle,"
          "headSha,event")


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


def red_runs(runs, by_event=False):
    """Per workflow, the newest finished run; the red ones, newest first.

    A `skipped` run ran nothing, so it never hides the result before it (a
    quench fast-forward's all-skipped push run sits on top of the nightly).
    `by_event` keys on (workflow, event), so a PR's green push run does not
    hide its red pull_request run.
    """
    latest = {}
    for r in sorted(runs, key=lambda r: r["databaseId"], reverse=True):
        if r.get("status") == "completed" and r.get("conclusion") != "skipped":
            key = (r.get("workflowName"), r.get("event") if by_event else None)
            latest.setdefault(key, r)
    red = [r for r in latest.values() if r.get("conclusion") not in NOT_RED]
    return sorted(red, key=lambda r: r["databaseId"], reverse=True)


def failing_jobs(cwd, run_id, slug=None):
    """Names of the jobs that did not pass, best effort."""
    repo = ["-R", slug] if slug else []
    try:
        jobs = json.loads(gtx(cwd, "run", "view", str(run_id), *repo,
                              "--json", "jobs") or "")["jobs"]
        return ", ".join(j["name"] for j in jobs
                         if j.get("conclusion") not in NOT_RED)
    except (ValueError, KeyError, TypeError):
        return ""


# --- watched repos ------------------------------------------------------------

def watch_list(cwd):
    """Slugs from the nearest `.ci-watch` at or above `cwd`."""
    for d in [Path(cwd).resolve(), *Path(cwd).resolve().parents]:
        try:
            text = (d / WATCH_FILE).read_text()
        except OSError:
            continue
        return [ln.split("#")[0].strip() for ln in text.splitlines()
                if "/" in ln.split("#")[0]]
    return []


def json_of(text):
    try:
        return json.loads(text or "")
    except ValueError:
        return None


def epoch(iso):
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
    except (AttributeError, ValueError):
        return None


def trunk_reds(runs, default, last_green):
    """Red default-branch runs, each with `last_green(run)`: the sha of the
    newest older success of the same workflow and event, or None."""
    red = red_runs([r for r in runs if r.get("headBranch") == default], by_event=True)
    for r in red:
        r["green_sha"] = last_green(r)
    return red


def landed_reds(runs, prs, default, now):
    """Red runs of PRs merged into `default` in the last LANDED_WINDOW."""
    landed = {}
    for pr in prs if isinstance(prs, list) else []:
        t = epoch(pr.get("mergedAt")) if isinstance(pr, dict) else None
        if t is not None and now - t <= LANDED_WINDOW and pr.get("headRefOid"):
            landed[pr["headRefOid"]] = pr
    runs = [r for r in runs
            if r.get("headSha") in landed and r.get("headBranch") != default]
    red = []
    for sha, pr in landed.items():                  # each PR's runs on their own
        for r in red_runs([r for r in runs if r["headSha"] == sha], by_event=True):
            red.append({**r, "pr": pr})
    return sorted(red, key=lambda r: r["databaseId"], reverse=True)


def poll_watched(cwd, slug, now):
    """Red runs on `slug`'s default branch and on its recently landed PRs."""
    repo = json_of(gtx(cwd, "repo", "view", "-R", slug, "--json", "defaultBranchRef"))
    try:
        default = repo["defaultBranchRef"]["name"]
    except (TypeError, KeyError):
        return None
    trunk = parse_runs(gtx(cwd, "run", "list", "-R", slug, "-b", default,
                           "-L", str(LIMIT), "--json", FIELDS))
    prs = json_of(gtx(cwd, "pr", "list", "-R", slug, "-s", "closed", "-B", default,
                      "-L", str(PR_LIMIT), "--json",
                      "number,headRefName,headRefOid,mergedAt,body"))
    wide = parse_runs(gtx(cwd, "run", "list", "-R", slug, "-L", str(WIDE_LIMIT),
                          "--json", FIELDS))
    def last_green(r):
        # Asked per red run: a daily nightly falls out of any fixed run window.
        greens = [g for g in parse_runs(gtx(
            cwd, "run", "list", "-R", slug, "-b", default, "-w", r.get("workflowName") or "",
            "-e", r.get("event") or "", "-s", "success", "-L", "5", "--json", FIELDS))
            if g["databaseId"] < r["databaseId"]]
        return max(greens, key=lambda g: g["databaseId"])["headSha"] if greens else None

    return default, (trunk_reds(trunk, default, last_green)
                     + landed_reds(wide, prs, default, now))


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


def watched_message(slug, default, red, jobs):
    lines = [f"CI is red after landing on {slug} ({default}):"]
    for r in red:
        failing = jobs.get(r["databaseId"])
        head = (f"  {r.get('workflowName')} run {r['databaseId']} "
                f"{r.get('conclusion')} ({r.get('event')})"
                f"{', failing: ' + failing if failing else ''}")
        pr = r.get("pr")
        if pr:
            head += f", on landed PR #{pr.get('number')} ({pr.get('headRefName')})"
            members = re.findall(r"#(\d+)", pr.get("body") or "") \
                if str(pr.get("headRefName", "")).startswith("quench/batch/") else []
            if members:
                head += ", batch members " + " ".join("#" + m for m in members)
            lines.append(head)
            continue
        lines.append(head)
        red_sha = r.get("headSha") or "?"
        if r.get("green_sha"):
            lines.append(f"    landed since last green: git log --first-parent "
                         f"{r['green_sha']}..{red_sha}")
        else:
            lines.append(f"    red at {red_sha}; no green run of this workflow in its "
                         f"{r.get('event')} history on {default}")
    first = red[0]["databaseId"]
    lines += ["", "Search the tracker for a ticket naming the run id before filing "
              "one. Then launch a subagent to fix it. Logs:",
              f"  gtx run view {first} --repo {slug}",
              f"  gtx run view {first} --repo {slug} --log-failed",
              "", "Done when a new run goes green."]
    return "\n".join(lines)


# --- entry point -------------------------------------------------------------

def check_branch(cwd, now):
    """The original check: the checked-out branch of the cwd repo."""
    slug = gitea_slug(cwd)
    branch = git(cwd, "symbolic-ref", "--short", "HEAD")
    if not slug or not branch:
        return None
    state = load_state(slug)
    if not due(state, now):
        return None
    state["last_check"] = now
    out = gtx(cwd, "run", "list", "-b", branch, "-L", str(LIMIT), "--json", FIELDS)
    red = red_runs(parse_runs(out))
    nudge, state = decide(red, state)
    save_state(slug, state)
    if not nudge:
        return None
    jobs = {r["databaseId"]: failing_jobs(cwd, r["databaseId"]) for r in red}
    return message(slug, branch, red, jobs)


def check_watched(cwd, slug, now):
    """Default branch and landed PRs of a repo named in `.ci-watch`."""
    key = slug + "#watch"                           # apart from branch state
    state = load_state(key)
    if not due(state, now):
        return None
    state["last_check"] = now
    polled = poll_watched(cwd, slug, now)
    if polled is None:
        save_state(key, state)
        return None
    default, red = polled
    nudge, state = decide(red, state)
    save_state(key, state)
    if not nudge:
        return None
    jobs = {r["databaseId"]: failing_jobs(cwd, r["databaseId"], slug) for r in red}
    return watched_message(slug, default, red, jobs)


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
    start = time.monotonic()
    now = int(time.time())
    reasons = [check_branch(cwd, now)]
    for slug in watch_list(cwd):
        if time.monotonic() - start > DEADLINE:
            break                                   # next turn picks it up
        reasons.append(check_watched(cwd, slug, now))
    reasons = [r for r in reasons if r]
    if reasons:
        print(json.dumps({"decision": "block", "reason": "\n\n".join(reasons)}))


if __name__ == "__main__":
    try:
        main()
    except Exception:                               # a broken watcher exits 0
        pass
