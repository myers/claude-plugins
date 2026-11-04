#!/usr/bin/env python3
"""Tests for ci-watch.py.

Plain asserts, no pytest: the hook ships with the plugin and must be testable
wherever the plugin lands.  Run:

    plugins/gitea-actions/tests/test-ci-watch.py

The bar: every brake and every fail-silent path has a test that goes red when
that guard is removed.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "hooks" / "scripts" / "ci-watch.py"

spec = importlib.util.spec_from_file_location("ci_watch", HOOK)
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)

passed = failed = 0


def check(desc, got, want):
    global passed, failed
    if got == want:
        passed += 1
    else:
        failed += 1
        print(f"FAIL {desc}\n  got:  {got!r}\n  want: {want!r}")


def check_true(desc, got):
    check(desc, bool(got), True)


def run(id, conclusion, workflow="ci.yml", status="completed"):
    return {"databaseId": id, "status": status, "conclusion": conclusion,
            "headBranch": "main", "workflowName": workflow, "displayTitle": "x"}


LIST = [run(2004, "", status="in_progress"), run(2003, "failure"),
        run(2002, "success")]

# --- parsing -----------------------------------------------------------------

check("parse: round-trips", ci.parse_runs(json.dumps(LIST)), LIST)
check("parse: empty input", ci.parse_runs(""), [])
check("parse: not json", ci.parse_runs("Error: HTTP 404"), [])
check("parse: not a list", ci.parse_runs('{"a": 1}'), [])
check("parse: rows without an id dropped", ci.parse_runs('[{"status": "x"}, 3]'), [])

# --- picking the red runs ----------------------------------------------------

check("red: skips unfinished, takes newest finished",
      [r["databaseId"] for r in ci.red_runs(LIST)], [2003])
check("red: green newest is not red",
      ci.red_runs([run(5, "success"), run(4, "failure")]), [])
check("red: cancelled is not red", ci.red_runs([run(5, "cancelled")]), [])
check("red: timed_out is red", len(ci.red_runs([run(5, "timed_out")])), 1)
check("red: per workflow, newest first",
      [r["databaseId"] for r in ci.red_runs(
          [run(9, "success", "a.yml"), run(8, "failure", "b.yml"),
           run(7, "failure", "a.yml"), run(6, "failure", "c.yml")])], [8, 6])
check("red: nothing", ci.red_runs([]), [])

RED = ci.red_runs([run(2003, "failure")])
NEWRED = ci.red_runs([run(2006, "failure")])

# --- brake: interval ---------------------------------------------------------

check("interval: inside the window is not due", ci.due({"last_check": 1000}, 1500), False)
check("interval: at the window is due", ci.due({"last_check": 1000}, 1600), True)
check("interval: no state is due", ci.due({}, 1600), True)

# --- decide ------------------------------------------------------------------

nudge, state = ci.decide(RED, {})
check("decide: first red nudges", nudge, True)
check("decide: records the runs", state["last_nudged_runs"], [2003])
check("decide: counts the strike", state["consecutive_nudges"], 1)

msg = ci.message("o/r", "main", RED, {2003: "build, lint"})
check_true("message: names the run", "2003" in msg)
check_true("message: names the repo", "o/r" in msg)
check_true("message: names failing jobs", "build, lint" in msg)
check_true("message: says to launch a subagent", "subagent" in msg.lower())
check_true("message: carries the log command", "--log-failed" in msg)

check("dedupe: same runs stay quiet", ci.decide(RED, state)[0], False)

nudge3, state3 = ci.decide(NEWRED, state)
check("dedupe: a new red run nudges", nudge3, True)
check("dedupe: strike count rises", state3["consecutive_nudges"], 2)

capped = {"last_nudged_runs": [1], "consecutive_nudges": ci.STRIKES}
check("strikes: cap silences the next nudge", ci.decide(NEWRED, capped)[0], False)

nudge_g, gstate = ci.decide([], state3)
check("green: no nudge", nudge_g, False)
check("green: strikes reset", gstate["consecutive_nudges"], 0)
check("green: re-arms after the cap", ci.decide(NEWRED, gstate)[0], True)

# --- slug discovery ----------------------------------------------------------

check("slug: https", ci.slug_from_url("https://gt.monoloco.net/chaos-inc/ws.git"),
      "chaos-inc/ws")
check("slug: ssh", ci.slug_from_url("git@gt.example:o/r.git"), "o/r")
check("slug: unparseable", ci.slug_from_url("not a url"), None)

check("host: https", ci.host_from_url("https://gt.example/o/r.git"), "gt.example")
check("host: config url, no path", ci.host_from_url("https://GT.example"), "gt.example")
check("host: scp-style ssh", ci.host_from_url("git@gt.example:o/r.git"), "gt.example")
check("host: ssh with port", ci.host_from_url("ssh://git@gt.example:2222/o/r.git"),
      "gt.example")
check("host: empty", ci.host_from_url(""), None)

# --- state file --------------------------------------------------------------

with tempfile.TemporaryDirectory() as d:
    os.environ["XDG_CACHE_HOME"] = d
    p = ci.state_path("o/r")
    check_true("state: path is under the cache dir", str(p).startswith(d))
    check("state: missing file reads as empty", ci.load_state("o/r"), {})
    ci.save_state("o/r", {"last_check": 7})
    check("state: round-trips", ci.load_state("o/r")["last_check"], 7)
    p.write_text("{ this is not json")
    check("state: corrupt file reads as empty", ci.load_state("o/r"), {})

# --- the hook end to end -----------------------------------------------------

JOBS = json.dumps({"jobs": [{"name": "build", "conclusion": "failure"},
                            {"name": "fmt", "conclusion": "success"}]})


def run_hook(payload, list_stdout, cache, extra_env=None, list_exit=0):
    """Invoke the hook as the harness does, with a fake `gtx` on PATH."""
    bin_dir = Path(cache) / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    gtx = bin_dir / "gtx"
    gtx.write_text("#!/bin/sh\n"
                   "if [ \"$1\" = config ]; then echo https://gt.example; exit 0; fi\n"
                   "if [ \"$2\" = view ]; then cat <<'EOF'\n" + JOBS + "\nEOF\nexit 0\nfi\n"
                   "cat <<'EOF'\n" + list_stdout + "\nEOF\n"
                   f"exit {list_exit}\n")
    gtx.chmod(0o755)
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["XDG_CACHE_HOME"] = str(cache)
    env.update(extra_env or {})
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                          capture_output=True, text=True, env=env, timeout=30)


with tempfile.TemporaryDirectory() as d:
    repo = Path(d) / "repo"
    repo.mkdir()
    for cmd in (["init", "-q", "-b", "main"],
                ["remote", "add", "origin", "https://gt.example/o/r.git"]):
        subprocess.run(["git", "-C", str(repo)] + cmd, check=True,
                       capture_output=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "--allow-empty",
                    "-m", "x"], check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t",
                        "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t"})

    payload = {"session_id": "s1", "cwd": str(repo)}
    LS = json.dumps(LIST)

    r = run_hook(payload, LS, Path(d) / "c1")
    check("e2e: exits 0", r.returncode, 0)
    out = json.loads(r.stdout)
    check("e2e: blocks", out["decision"], "block")
    check_true("e2e: reason names the red run", "2003" in out["reason"])
    check_true("e2e: reason names the failing job", "build" in out["reason"]
               and "fmt" not in out["reason"])

    r2 = run_hook(payload, "THIS WOULD NOT PARSE", Path(d) / "c1")
    check("e2e: interval suppresses the second run", r2.stdout.strip(), "")

    r3 = run_hook({**payload, "stop_hook_active": True}, LS, Path(d) / "c2")
    check("e2e: stop_hook_active is honoured", r3.stdout.strip(), "")

    r4 = run_hook(payload, LS, Path(d) / "c3", {"CI_WATCH": "0"})
    check("e2e: CI_WATCH=0 disables", r4.stdout.strip(), "")

    # gtx refuses a repo with no remote on its Gitea instance: nonzero exit
    r5 = run_hook(payload, "Error: No git remote matching Gitea instance", Path(d) / "c4",
                  list_exit=1)
    check("e2e: repo not on Gitea is silent", r5.stdout.strip(), "")
    check("e2e: and exits 0", r5.returncode, 0)

    r6 = run_hook(payload, json.dumps([run(5, "success")]), Path(d) / "c5")
    check("e2e: green is silent", r6.stdout.strip(), "")

    r7 = run_hook({"session_id": "s1", "cwd": d}, LS, Path(d) / "c6")
    check("e2e: a non-repo cwd is silent", r7.stdout.strip(), "")
    check("e2e: a non-repo cwd exits 0", r7.returncode, 0)

    def git_in(*cmd):
        subprocess.run(["git", "-C", str(repo)] + list(cmd), check=True,
                       capture_output=True)

    # origin on GitHub, Gitea as a second remote: the slug is the Gitea one
    git_in("remote", "rename", "origin", "gitea")
    git_in("remote", "add", "origin", "https://github.com/gh/other.git")
    r10 = run_hook(payload, LS, Path(d) / "c9")
    check_true("e2e: gitea remote beside a github origin is found",
               "--repo o/r" in r10.stdout and "gh/other" not in r10.stdout)
    check_true("e2e: state keyed on the gitea slug",
               (Path(d) / "c9" / "claude-gitea-ci-watch" / "o__r.json").exists())

    git_in("remote", "remove", "gitea")
    r11 = run_hook(payload, LS, Path(d) / "c10")
    check("e2e: no gitea remote is silent", r11.stdout.strip(), "")
    check("e2e: no gitea remote exits 0", r11.returncode, 0)

    env = dict(os.environ, PATH="/nonexistent", XDG_CACHE_HOME=str(Path(d) / "c7"))
    r8 = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                        capture_output=True, text=True, env=env, timeout=30)
    check("e2e: missing gtx is silent", r8.stdout.strip(), "")
    check("e2e: missing gtx exits 0", r8.returncode, 0)

    env = dict(os.environ, XDG_CACHE_HOME=str(Path(d) / "c8"))
    r9 = subprocess.run([sys.executable, str(HOOK)], input="not json",
                        capture_output=True, text=True, env=env, timeout=30)
    check("e2e: garbage stdin exits 0", r9.returncode, 0)

# --- watched repos: default branch and landed PRs ----------------------------

def wrun(id, conclusion, workflow="ktest.yml", branch="nitro", sha="s", event="push"):
    return {"databaseId": id, "status": "completed", "conclusion": conclusion,
            "headBranch": branch, "workflowName": workflow, "displayTitle": "x",
            "headSha": sha, "event": event}


check("red: a newer skipped run does not hide a red one",
      [r["databaseId"] for r in ci.red_runs(
          [wrun(6605, "skipped"), wrun(6604, "failure", event="schedule")])], [6604])
check("red: by_event keeps a red pull_request run under a green push run",
      [r["databaseId"] for r in ci.red_runs(
          [wrun(9, "success", event="push"), wrun(8, "failure", event="pull_request")],
          by_event=True)], [8])

TRUNK = [wrun(7, "skipped", sha="c3"), wrun(6, "failure", sha="c2", event="schedule"),
         wrun(5, "success", sha="c1", event="schedule"), wrun(4, "success", sha="c0"),
         wrun(3, "failure", branch="iss/x", sha="b1")]
def last_green_in(runs):
    def f(r):
        g = [x for x in runs if x["workflowName"] == r["workflowName"]
             and x["event"] == r["event"] and x["conclusion"] == "success"
             and x["databaseId"] < r["databaseId"]]
        return max(g, key=lambda x: x["databaseId"])["headSha"] if g else None
    return f

tr = ci.trunk_reds(TRUNK, "nitro", last_green_in(TRUNK))
check("trunk: red default-branch run found", [r["databaseId"] for r in tr], [6])
check("trunk: last green comes from the lookup", tr[0]["green_sha"], "c1")
check("trunk: no green", ci.trunk_reds([wrun(6, "failure")], "nitro",
                                       lambda r: None)[0]["green_sha"], None)

NOW = 1_800_000_000
def iso(t):
    from datetime import datetime, timezone
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

PRS = [{"number": 20, "headRefName": "iss/a", "headRefOid": "pa",
        "mergedAt": iso(NOW - 600), "body": ""},
       {"number": 30, "headRefName": "quench/batch/1", "headRefOid": "pb",
        "mergedAt": iso(NOW - 60), "body": "- #12\n- #13"},
       {"number": 19, "headRefName": "iss/old", "headRefOid": "po",
        "mergedAt": iso(NOW - ci.LANDED_WINDOW - 1), "body": ""},
       {"number": 18, "headRefName": "iss/closed", "headRefOid": "pc",
        "mergedAt": None, "body": ""}]
WIDE = [wrun(50, "failure", "landing-gates.yml", "iss/a", "pa", "pull_request"),
        wrun(49, "success", "ktest.yml", "iss/a", "pa", "push"),
        wrun(48, "failure", "landing-gates.yml", "nitro", "pa", "push"),
        wrun(47, "failure", "landing-gates.yml", "quench/batch/1", "pb", "pull_request"),
        wrun(46, "failure", "landing-gates.yml", "iss/old", "po", "pull_request"),
        wrun(45, "failure", "landing-gates.yml", "iss/closed", "pc", "pull_request")]
lr = ci.landed_reds(WIDE, PRS, "nitro", NOW)
check("landed: red runs of PRs merged in the window, not trunk's",
      [r["databaseId"] for r in lr], [50, 47])
check("landed: run carries its PR", lr[0]["pr"]["number"], 20)
check("landed: garbage PR list is empty", ci.landed_reds(WIDE, {"x": 1}, "nitro", NOW), [])

wm = ci.watched_message("o/k", "nitro", tr + lr, {6: "ktest-riscv64"})
check_true("watched msg: lists the landing range",
           "git log --first-parent c1..c2" in wm)
check_true("watched msg: names the landed PR", "#20" in wm)
check_true("watched msg: names batch members", "#12 #13" in wm)
check_true("watched msg: search before filing", "run id before filing" in wm)
check_true("watched msg: failing job", "ktest-riscv64" in wm)

with tempfile.TemporaryDirectory() as d:
    (Path(d) / ci.WATCH_FILE).write_text("# watched\nchaos-inc/asterinas  # kernel\n\n")
    nested = Path(d) / "wt" / "sub"
    nested.mkdir(parents=True)
    check("watch list: read with comments", ci.watch_list(d), ["chaos-inc/asterinas"])
    check("watch list: found from a nested dir", ci.watch_list(nested),
          ["chaos-inc/asterinas"])
with tempfile.TemporaryDirectory() as d:
    check("watch list: none", ci.watch_list(d), [])

# --- watched repos end to end ------------------------------------------------

FAKE = r"""#!/usr/bin/env python3
import json, os, sys
a = sys.argv[1:]
fx = json.load(open(os.environ["FAKE_GTX"]))
if a[:1] == ["config"]: print("https://gt.example"); sys.exit(0)
if a[:2] == ["repo", "view"]: print(json.dumps({"defaultBranchRef": {"name": "nitro"}})); sys.exit(0)
if a[:2] == ["pr", "list"]: print(json.dumps(fx["prs"])); sys.exit(0)
if a[:2] == ["run", "view"]: print(json.dumps({"jobs": [{"name": "boom", "conclusion": "failure"}]})); sys.exit(0)
if a[:2] == ["run", "list"]:
    if "-R" not in a: print("[]"); sys.exit(0)        # the cwd repo's branch: green
    if "-s" in a:                                     # last green of a workflow+event
        ev = a[a.index("-e") + 1]
        print(json.dumps([r for r in fx["trunk"] if r["conclusion"] == "success"
                          and r["event"] == ev])); sys.exit(0)
    print(json.dumps(fx["trunk"] if "-b" in a else fx["wide"])); sys.exit(0)
sys.exit(1)
"""


def run_watch(cwd, cache, fixture):
    bin_dir = Path(cache) / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    (bin_dir / "gtx").write_text(FAKE)
    (bin_dir / "gtx").chmod(0o755)
    fx = Path(cache) / "fx.json"
    fx.write_text(json.dumps(fixture))
    env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}",
               XDG_CACHE_HOME=str(cache), FAKE_GTX=str(fx))
    return subprocess.run([sys.executable, str(HOOK)],
                          input=json.dumps({"session_id": "s", "cwd": str(cwd)}),
                          capture_output=True, text=True, env=env, timeout=30)


import time as _time
REAL_NOW = int(_time.time())
with tempfile.TemporaryDirectory() as d:
    ws = Path(d) / "ws"
    ws.mkdir()
    subprocess.run(["git", "-C", str(ws), "init", "-q", "-b", "main"], check=True)
    subprocess.run(["git", "-C", str(ws), "remote", "add", "origin",
                    "https://gt.example/o/ws.git"], check=True)
    (ws / ci.WATCH_FILE).write_text("o/k\n")
    green = {"trunk": [wrun(5, "success")], "prs": [], "wide": []}

    red_trunk = dict(green, trunk=[wrun(7, "success", sha="c2", event="push"),
                                   wrun(6, "failure", sha="c2", event="schedule"),
                                   wrun(5, "success", sha="c1", event="schedule")])
    r = run_watch(ws, Path(d) / "w1", red_trunk)
    check("watch e2e: exits 0", r.returncode, 0)
    out = json.loads(r.stdout or "{}")
    check("watch e2e: red trunk nudges once", out.get("reason", "").count("run 6 "), 1)
    check_true("watch e2e: trunk nudge has the range", "c1..c2" in out.get("reason", ""))
    r = run_watch(ws, Path(d) / "w1", red_trunk)
    check("watch e2e: interval holds for the watched repo", r.stdout.strip(), "")

    red_pr = dict(green, prs=[{"number": 21, "headRefName": "iss/b", "headRefOid": "pb",
                               "mergedAt": iso(REAL_NOW - 300), "body": ""}],
                  wide=[wrun(60, "failure", "landing-gates.yml", "iss/b", "pb",
                             "pull_request")])
    r = run_watch(ws, Path(d) / "w2", red_pr)
    out = json.loads(r.stdout or "{}")
    check("watch e2e: red landed PR nudges once", out.get("reason", "").count("#21"), 1)
    check_true("watch e2e: names the failing job", "boom" in out.get("reason", ""))

    r = run_watch(ws, Path(d) / "w3", green)
    check("watch e2e: all green is silent", r.stdout.strip(), "")

    (ws / ci.WATCH_FILE).unlink()
    r = run_watch(ws, Path(d) / "w4", red_trunk)
    check("watch e2e: no watch file, no watched nudge", r.stdout.strip(), "")

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
