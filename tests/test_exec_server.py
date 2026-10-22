"""
signal-lab-exec (decisions/0065): the restricted MCP server Cowork uses inside WSL.

One stateful session over real JSON-RPC against a throwaway git repo (a fake `make`, a fake
`scripts/unattended.sh`, a local bare remote). Nothing here reads data/ or calls a model; the server under
test is scripts/exec_server/server.py with the repo's own allow.json and scripts/nightly/guard.py.
"""

from __future__ import annotations

import fcntl
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER = REPO_ROOT / "scripts" / "exec_server" / "server.py"
ALLOW = REPO_ROOT / "scripts" / "exec_server" / "allow.json"
GUARD = REPO_ROOT / "scripts" / "nightly" / "guard.py"


def test_one_session_end_to_end(tmp_path):
    T = tmp_path
    repo = T / "repo"
    for d in (
        "scripts/nightly",
        "scripts/exec_server",
        "decisions",
        "params",
        "src",
        "docs",
        "results/audit/_nightly",
    ):
        (repo / d).mkdir(parents=True)
    env = {
        **os.environ,
        "SIGNAL_LAB_REPO": str(repo),
        "SIGNAL_LAB_LOCK": str(T / "lock"),
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }

    def git(*a, cwd=repo):
        return subprocess.run(
            ["git", *a], cwd=cwd, capture_output=True, text=True, env=env
        ).stdout.strip()

    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(T / "remote.git")], check=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    shutil.copy(GUARD, repo / "scripts/nightly/guard.py")
    shutil.copy(ALLOW, repo / "scripts/exec_server/allow.json")
    (repo / "Makefile").write_text(
        "governance:\n\t@echo gov-ok\ninspect-raw:\n\t@echo SECRET-ROW-1\ntest-fast:\n\t@echo ok\n"
    )
    (repo / "scripts/unattended.sh").write_text('#!/bin/sh\necho "unattended $1 ok"\n')
    (repo / "HANDOFF.md").write_text("hi\n")
    (repo / "params/p.yaml").write_text("x\n")
    (repo / ".gitignore").write_text("results/\n")
    git("add", "-A")
    git("commit", "-qm", "init")
    git("remote", "add", "origin", str(T / "remote.git"))
    git("push", "-q", "origin", "main")

    p = subprocess.Popen(
        [sys.executable, str(SERVER)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        env=env,
    )
    n = [0]
    fails: list[str] = []

    def rpc(method, params=None, notify=False):
        m = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            m["params"] = params
        if not notify:
            n[0] += 1
            m["id"] = n[0]
        p.stdin.write(json.dumps(m) + "\n")
        p.stdin.flush()
        return None if notify else json.loads(p.stdout.readline())

    def call(name, **a):
        r = rpc("tools/call", {"name": name, "arguments": a})["result"]
        return r.get("isError", False), r["content"][0]["text"]

    def check(label, cond, detail=""):
        if not cond:
            fails.append(f"{label} | {detail[:160]}")

    def wait(jid):
        d = {}
        for _ in range(200):
            d = json.loads(call("job_status", id=jid)[1])
            if d["rc"] is not None:
                return d
            time.sleep(0.1)
        return d

    def job(kind, target, **kw):
        e, t = call("start_job", kind=kind, target=target, **kw)
        return e, t, (t.split()[1] if not e else None)

    try:
        r = rpc(
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "t", "version": "0"},
            },
        )
        check("initialize echoes the version", r["result"]["protocolVersion"] == "2025-03-26")
        rpc("notifications/initialized", notify=True)
        names = sorted(t["name"] for t in rpc("tools/list")["result"]["tools"])
        check(
            "seven tools",
            names
            == sorted(
                ["repo_state", "git_read", "start_job", "job_status", "job_tail", "commit", "push"]
            ),
            str(names),
        )
        check("repo_state", not call("repo_state")[0])
        for bad in (
            ["push"],
            ["reset", "--hard"],
            ["log", "--output=/tmp/x"],
            ["show", "HEAD:data/raw/x.xlsx"],
            ["diff", "--no-index", "a", "b"],
            ["-c", "core.pager=x", "log"],
        ):
            check("git_read refuses " + " ".join(bad), call("git_read", args=bad)[0])
        for k, tg in (
            ("make", "audit"),
            ("unattended", "audit"),
            ("make", "audit-lean"),
            ("make", "clean"),
            ("make", "lock"),
            ("make", "jpmaqs-pull"),
            ("shell", "ls"),
        ):
            check(f"start_job refuses {k} {tg}", call("start_job", kind=k, target=tg)[0])
        e, t, j1 = job("make", "governance")
        check("governance starts without a task", not e, t)
        check("governance rc 0", wait(j1)["rc"] == 0)
        check("tail shows a tail_ok target", "gov-ok" in call("job_tail", id=j1)[1])
        e, t, _ = job("make", "inspect-raw")
        check("inspect-raw needs a task id", e and "task=" in t, t)
        e, t, j2 = job("make", "inspect-raw", task=65)
        check("inspect-raw starts with a task id", not e, t)
        wait(j2)
        tl = call("job_tail", id=j2)[1]
        check("inspect-raw rows are never shown", "SECRET-ROW-1" not in tl and "refused" in tl, tl)
        check("the task id is recorded", json.loads(call("job_status", id=j2)[1]).get("task") == 65)
        (repo / "decisions/0001.md").write_text("rec\n")
        e, t = call("commit", paths=["decisions/0001.md"], message="records: x HANDOFF task 9")
        check("no check, no commit", e and "newer" in t, t)
        e, t, j3 = job("unattended", "check")
        check("unattended check rc 0", wait(j3)["rc"] == 0)
        e, t = call("commit", paths=["decisions/0001.md"], message="records: x")
        check("a commit must cite its authority", e and "cite" in t, t)
        for badp in (
            "params/p.yaml",
            "../x",
            "/etc/passwd",
            "data/raw/a.xlsx",
            "decisions/none.md",
            "scripts/nightly/guard.py",
            "scripts/exec_server/allow.json",
            "CLAUDE.md",
            ".claude/settings.json",
            "tests/test_nightly.py",
            "tests/test_exec_server.py",
            "pyproject.toml",
            "SUBSTRATE.md",
        ):
            check(
                "commit refuses " + badp,
                call("commit", paths=[badp], message="m HANDOFF task 1")[0],
            )
        e, t = call("commit", paths=["decisions/0001.md"], message="records: x\n\n(HANDOFF task 9)")
        check("a records commit after a check", not e and "committed" in t, t)
        check("HEAD is that commit", git("log", "-1", "--format=%s") == "records: x")
        (repo / "src/a.py").write_text("x = 1\n")
        e, t = call("commit", paths=["src/a.py"], message="src: a (HANDOFF task 10)")
        check("code needs check-scoped, not check", e and "check-scoped" in t, t)
        e, t, j4 = job("unattended", "check-scoped")
        check("check-scoped rc 0", wait(j4)["rc"] == 0)
        e, t = call("commit", paths=["src/a.py"], message="src: a (HANDOFF task 10)")
        check("a code commit after check-scoped", not e, t)
        (repo / "OWNER-QUEUE.md").write_text("q\n")
        e, t = call("commit", paths=["OWNER-QUEUE.md"], message="records OWNER-QUEUE")
        check("a change newer than every check blocks", e, t)
        e, t = call("push", task=11)
        check("push needs a task that says to push", e and "does not say" in t, t)
        with (repo / "HANDOFF.md").open("a") as f:
            f.write("\n### 12. A pushing task\n\nThen `git push origin main`.\n\n## Done\n")
        e, t, j5 = job("unattended", "check")
        wait(j5)
        time.sleep(1.2)  # the check ends well BEFORE the commit, as in real use (decisions/0065)
        e, t = call(
            "commit",
            paths=["HANDOFF.md", "OWNER-QUEUE.md"],
            message="handoff: task 12 written (HANDOFF task 12)",
        )
        check("commit handoff and queue", not e, t)
        e, t = call("push", task=12)
        check("a fast-forward push", not e and "rc=0" in t, t)
        remote_head = subprocess.run(
            ["git", "--git-dir", str(T / "remote.git"), "rev-parse", "main"],
            capture_output=True,
            text=True,
        ).stdout.strip()
        check("the remote has HEAD", git("rev-parse", "HEAD") == remote_head)
        git("commit", "--allow-empty", "-qm", "direct")  # a commit made outside the server
        e, t = call("push", task=12)
        check("an outside commit needs a check after it", e and "start_job a check" in t, t)
        time.sleep(1.1)
        e, t, jx = job("unattended", "check")
        wait(jx)
        e, t = call("push", task=12)
        check("a check started after it lets it go", not e and "rc=0" in t, t)
        subprocess.run(
            ["git", "clone", "-q", str(T / "remote.git"), str(T / "other")], check=True, env=env
        )
        subprocess.run(
            "echo z > z.txt && git add z.txt && git commit -qm other && git push -q origin main",
            shell=True,
            check=True,
            cwd=T / "other",
            env=env,
        )
        (repo / "docs/n.md").write_text("n\n")
        e, t, j6 = job("unattended", "check")
        wait(j6)
        e, t = call("commit", paths=["docs/n.md"], message="docs: n (HANDOFF task 12)")
        check("a local commit ahead of a diverged remote", not e, t)
        e, t, j7 = job("unattended", "check")
        wait(j7)
        e, t = call("push", task=12)
        check(
            "a non-fast-forward push is reported, not forced",
            "rc=0" not in t and "Not worked around" in t,
            t,
        )
        other = subprocess.run(
            ["git", "--git-dir", str(T / "remote.git"), "log", "-1", "--format=%s", "main"],
            capture_output=True,
            text=True,
        ).stdout.strip()
        check("the remote was not overwritten", other == "other")
        (repo / "results/audit/_nightly/RUNNING").write_text("x")
        check(
            "RUNNING fresh blocks start_job", call("start_job", kind="make", target="governance")[0]
        )
        check(
            "RUNNING fresh blocks commit",
            call("commit", paths=["docs/n.md"], message="m HANDOFF task 1")[0],
        )
        check("RUNNING fresh blocks push", call("push", task=12)[0])
        (repo / "results/audit/_nightly/RUNNING").unlink()
        fd = os.open(T / "lock", os.O_CREAT | os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX)
        e, t, j8 = job("make", "governance")
        check("a held lock gives rc 75 for make", wait(j8)["rc"] == 75)
        check(
            "a held lock refuses unattended",
            call("start_job", kind="unattended", target="check")[0],
        )
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
        a = json.loads((repo / "scripts/exec_server/allow.json").read_text())
        a["make_readonly"] = []
        (repo / "scripts/exec_server/allow.json").write_text(json.dumps(a))
        check(
            "an allow.json edit takes effect without a restart",
            call("start_job", kind="make", target="governance")[0],
        )
        (repo / "scripts/exec_server/allow.json").write_text("{ not json")
        check("fails closed on a broken allow.json", call("git_read", args=["status"])[0])
        (repo / "scripts/nightly/guard.py").rename(repo / "scripts/nightly/guard.py.bak")
        check("fails closed without guard.py", call("git_read", args=["status"])[0])
    finally:
        p.stdin.close()
        p.wait(timeout=10)
    assert not fails, "\n".join(fails)
