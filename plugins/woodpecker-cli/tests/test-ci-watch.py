#!/usr/bin/env python3
"""Tests for ci-watch.py.

Plain asserts, no pytest: the hook ships with the plugin and must be testable
wherever the plugin lands.  Run:

    plugins/woodpecker-cli/tests/test-ci-watch.py

The bar the README sets: every brake and every fail-silent path has a test that
goes red when that guard is removed.
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


LS = """\
NUMBER  STATUS    EVENT  BRANCH  MESSAGE
2004    running   push   main    still going
2003    failure   push   main    broke it
2002    success   push   main    fine
"""


# --- parsing -----------------------------------------------------------------

rows = ci.parse_pipelines(LS)
check("parse: three rows", len(rows), 3)
check("parse: number is an int", rows[0]["number"], 2004)
check("parse: status", rows[1]["status"], "failure")
check("parse: branch", rows[1]["branch"], "main")

check("parse: empty input", ci.parse_pipelines(""), [])
check("parse: header only", ci.parse_pipelines("NUMBER  STATUS\n"), [])
check("parse: wp warn json ignored",
      ci.parse_pipelines('{"level":"warn","message":"update"}\n' + LS), rows)
check("parse: ragged line ignored", ci.parse_pipelines("garbage\n"), [])

# --- picking the run ---------------------------------------------------------

check("pick: skips unsettled, takes newest settled",
      ci.pick(rows, "main")["number"], 2003)
check("pick: other branch has none", ci.pick(rows, "wip"), None)
check("pick: nothing settled", ci.pick(ci.parse_pipelines(
    "NUMBER  STATUS   EVENT  BRANCH  MESSAGE\n2004    running  push   main    x\n"
), "main"), None)

GREEN = ci.parse_pipelines(
    "NUMBER  STATUS   EVENT  BRANCH  MESSAGE\n2005    success  push   main    ok\n")
RED = ci.parse_pipelines(
    "NUMBER  STATUS   EVENT  BRANCH  MESSAGE\n2003    failure  push   main    bad\n")
KILLED = ci.parse_pipelines(
    "NUMBER  STATUS  EVENT  BRANCH  MESSAGE\n2003    killed  push   main    bad\n")

# --- brake: interval ---------------------------------------------------------

check("interval: inside the window is not due", ci.due({"last_check": 1000}, 1500), False)
check("interval: at the window is due", ci.due({"last_check": 1000}, 1600), True)
check("interval: no state is due", ci.due({}, 1600), True)

# --- decide ------------------------------------------------------------------

nudge, state = ci.decide(ci.pick(RED, "main"), {}, "o/r", "main")
check_true("decide: first red nudges", nudge)
check("decide: records the pipeline", state["last_nudged_pipeline"], 2003)
check("decide: counts the strike", state["consecutive_nudges"], 1)
check_true("decide: message names the pipeline", "2003" in nudge)
check_true("decide: message names the repo", "o/r" in nudge)
check_true("decide: message says to launch a subagent", "subagent" in nudge.lower())
check_true("decide: message carries the log command", "wp pipeline log show" in nudge)

# brake: dedupe
nudge2, _ = ci.decide(ci.pick(RED, "main"), state, "o/r", "main")
check("dedupe: same pipeline stays quiet", nudge2, None)

# a new red pipeline is new information
NEWRED = ci.parse_pipelines(
    "NUMBER  STATUS   EVENT  BRANCH  MESSAGE\n2006    failure  push   main    again\n")
nudge3, state3 = ci.decide(ci.pick(NEWRED, "main"), state, "o/r", "main")
check_true("dedupe: a new red pipeline nudges", nudge3)
check("dedupe: strike count rises", state3["consecutive_nudges"], 2)

# brake: strikes
capped = {"last_nudged_pipeline": 1, "consecutive_nudges": ci.STRIKES}
nudge4, _ = ci.decide(ci.pick(NEWRED, "main"), capped, "o/r", "main")
check("strikes: cap silences the next nudge", nudge4, None)

# green clears everything
_, gstate = ci.decide(ci.pick(GREEN, "main"), state3, "o/r", "main")
check("green: no nudge", ci.decide(ci.pick(GREEN, "main"), state3, "o/r", "main")[0], None)
check("green: strikes reset", gstate["consecutive_nudges"], 0)
nudge5, _ = ci.decide(ci.pick(NEWRED, "main"), gstate, "o/r", "main")
check_true("green: re-arms after the cap", nudge5)

# a killed pipeline is red too
check_true("killed counts as red", ci.decide(ci.pick(KILLED, "main"), {}, "o/r", "main")[0])

# --- slug discovery ----------------------------------------------------------

check("slug: https", ci.slug_from_url("https://fj.monoloco.net/chaos-inc/ws.git"),
      "chaos-inc/ws")
check("slug: https without .git", ci.slug_from_url("https://github.com/myers/cp"),
      "myers/cp")
check("slug: ssh", ci.slug_from_url("git@github.com:myers/claude-plugins.git"),
      "myers/claude-plugins")
check("slug: ssh url form", ci.slug_from_url("ssh://git@host:2222/o/r.git"), "o/r")
check("slug: trailing slash", ci.slug_from_url("https://host/o/r/"), "o/r")
check("slug: unparseable", ci.slug_from_url("not a url"), None)
check("slug: empty", ci.slug_from_url(""), None)

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


def run_hook(payload, wp_stdout, cache, extra_env=None):
    """Invoke the hook as the harness does, with a fake `wp` on PATH."""
    bin_dir = Path(cache) / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    wp = bin_dir / "wp"
    wp.write_text("#!/bin/sh\ncat <<'WPEOF'\n" + wp_stdout + "WPEOF\n")
    wp.chmod(0o755)
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["XDG_CACHE_HOME"] = str(cache)
    env.update(extra_env or {})
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                       capture_output=True, text=True, env=env, timeout=30)
    return r


with tempfile.TemporaryDirectory() as d:
    repo = Path(d) / "repo"
    repo.mkdir()
    for cmd in (["init", "-q", "-b", "main"],
                ["remote", "add", "origin", "https://fj.monoloco.net/o/r.git"]):
        subprocess.run(["git", "-C", str(repo)] + cmd, check=True,
                       capture_output=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "--allow-empty",
                    "-m", "x"], check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t",
                        "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t"})

    payload = {"session_id": "s1", "cwd": str(repo)}

    r = run_hook(payload, LS, Path(d) / "c1")
    check("e2e: exits 0", r.returncode, 0)
    out = json.loads(r.stdout)
    check("e2e: blocks", out["decision"], "block")
    check_true("e2e: reason names the red pipeline", "2003" in out["reason"])

    # second run inside the interval: silent, and it must not call wp at all
    r2 = run_hook(payload, "THIS WOULD NOT PARSE", Path(d) / "c1")
    check("e2e: interval suppresses the second run", r2.stdout.strip(), "")
    check("e2e: still exits 0", r2.returncode, 0)

    # the harness's own loop guard
    r3 = run_hook({**payload, "stop_hook_active": True}, LS, Path(d) / "c2")
    check("e2e: stop_hook_active is honoured", r3.stdout.strip(), "")

    # opt out
    r4 = run_hook(payload, LS, Path(d) / "c3", {"CI_WATCH": "0"})
    check("e2e: CI_WATCH=0 disables", r4.stdout.strip(), "")

    # fail-silent: wp says something unparseable
    r5 = run_hook(payload, "total nonsense\n", Path(d) / "c4")
    check("e2e: unparseable wp output is silent", r5.stdout.strip(), "")
    check("e2e: and still exits 0", r5.returncode, 0)

    # fail-silent: green CI
    r6 = run_hook(payload, "NUMBER  STATUS   EVENT  BRANCH  MESSAGE\n"
                           "2005    success  push   main    ok\n", Path(d) / "c5")
    check("e2e: green is silent", r6.stdout.strip(), "")

    # fail-silent: not a git repo
    r7 = run_hook({"session_id": "s1", "cwd": d}, LS, Path(d) / "c6")
    check("e2e: a non-repo cwd is silent", r7.stdout.strip(), "")
    check("e2e: a non-repo cwd exits 0", r7.returncode, 0)

    # fail-silent: no wp on PATH
    env = dict(os.environ, PATH="/nonexistent", XDG_CACHE_HOME=str(Path(d) / "c7"))
    r8 = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                        capture_output=True, text=True, env=env, timeout=30)
    check("e2e: missing wp is silent", r8.stdout.strip(), "")
    check("e2e: missing wp exits 0", r8.returncode, 0)

    # fail-silent: garbage on stdin
    env = dict(os.environ, XDG_CACHE_HOME=str(Path(d) / "c8"))
    r9 = subprocess.run([sys.executable, str(HOOK)], input="not json",
                        capture_output=True, text=True, env=env, timeout=30)
    check("e2e: garbage stdin exits 0", r9.returncode, 0)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
