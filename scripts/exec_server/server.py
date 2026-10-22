#!/usr/bin/env python3
"""
signal-lab-exec v0.2: a restricted MCP server for Cowork, run inside WSL (decisions/0064 follow-up, DRAFT).

Stdlib only (newline-delimited JSON-RPC over stdio), so it needs no new dependency and no lockfile change.

  repo_state   git status, HEAD, ahead count, whether a nightly run is live, whether the one-run lock is held
  git_read     status | log | diff | show | rev-parse | rev-list | ls-files | check-ignore  (read only)
  start_job    kind=unattended|make, target from allow.json; make targets that make numbers or change records
               need task=<HANDOFF id> (detached; log under results/audit/_cowork/)
  job_status   running / rc / elapsed / log line count
  job_tail     the last lines of a job's log, only for targets in allow.json tail_ok
  commit       paths matching allow.json commit_paths (lane 1 and 2), only after a passing check newer than every
               changed file in the tree (code paths: check-scoped), the message citing a HANDOFF task or a decision.
               No amend.
  push         `git push origin main` (never forced), only for a HANDOFF task whose text says to push, after a
               passing check newer than HEAD. A non-fast-forward is rejected by git and reported, not worked around.

What may run is DATA, not code: scripts/exec_server/allow.json (owner-edited; its directory is protected).
Audits, `make clean|lock|install`, anything that pulls with credentials, and the plumbing (scripts/nightly/,
scripts/exec_server/, .claude/, CLAUDE.md, params/, vetoes/, SUBSTRATE.md) are outside it by design.
Refused everywhere: any argument naming data/raw, data/snapshots, .env or a key (scripts/nightly/guard.py's own
pattern, imported, not copied). It will not start while results/audit/_nightly/RUNNING is under 5 minutes old, and
it takes the same flock as scripts/unattended.sh. If guard.py or allow.json cannot be read, every call fails closed.
"""

from __future__ import annotations

import fcntl
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

REPO = Path(os.environ.get("SIGNAL_LAB_REPO", os.getcwd())).resolve()
LOCK = Path(os.environ.get("SIGNAL_LAB_LOCK", str(Path.home() / ".locks" / "signal-lab.lock")))
JOBS = REPO / "results" / "audit" / "_cowork"
VERIFIED = (
    REPO / "results" / "audit" / "_cowork_verified"
)  # <sha of a commit made by `commit`> -> the check job it rested on
RUNNING = REPO / "results" / "audit" / "_nightly" / "RUNNING"
ALLOW = REPO / "scripts" / "exec_server" / "allow.json"

ENV = dict(os.environ)
ENV.update(
    OMP_NUM_THREADS="1",
    OPENBLAS_NUM_THREADS="1",
    MKL_NUM_THREADS="1",  # decisions/0048
    GIT_TERMINAL_PROMPT="0",
)
ENV.setdefault("UV_PROJECT_ENVIRONMENT", str(Path.home() / ".venvs" / "signal-lab"))

GIT_READ = {"status", "log", "diff", "show", "rev-parse", "rev-list", "ls-files", "check-ignore"}
GIT_BAD_FLAGS = re.compile(
    r"^(--output|--no-index|-c$|--exec|--ext-diff|--textconv|-O|--open-files)"
)
OWNER_ONLY = re.compile(
    r"^(SUBSTRATE\.md|params/|vetoes/)"
)  # hard-coded: allow.json cannot widen this
CITES = re.compile(r"(HANDOFF task \d+|decisions/\d{4}|OWNER-QUEUE)")
CHECKS = {"unattended-check", "unattended-check-scoped", "unattended-check-full"}
MAX_LINES, MAX_CHARS = 300, 30000


def allow() -> dict:
    """Read at every call, so the owner's edit takes effect without a restart. Missing or broken: fail closed."""
    a = json.loads(ALLOW.read_text())
    for k in (
        "unattended",
        "make_readonly",
        "make_task",
        "tail_ok",
        "commit_paths",
        "protected_paths",
    ):
        if not isinstance(a.get(k), list):
            raise ValueError(f"allow.json: {k} must be a list")
    return a


def _guard():
    p = REPO / "scripts" / "nightly" / "guard.py"
    spec = importlib.util.spec_from_file_location("nightly_guard", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # a missing guard fails closed: the server will not answer calls
    return mod


def forbidden(text: str) -> bool:
    return bool(_guard().FORBIDDEN.search(text))


def sh(argv, timeout=120):
    r = subprocess.run(argv, cwd=REPO, env=ENV, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr)


def clip(text: str) -> str:
    lines = text.splitlines()
    cut = len(lines) > MAX_LINES or len(text) > MAX_CHARS
    out = "\n".join(lines[-MAX_LINES:] if cut else lines)[-MAX_CHARS:]
    return ("[clipped to the last part]\n" if cut else "") + out


def nightly_live() -> bool:
    try:
        return time.time() - RUNNING.stat().st_mtime < 300
    except OSError:
        return False


def lock_held() -> bool:
    try:
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(LOCK, os.O_CREAT | os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(fd, fcntl.LOCK_UN)
            return False
        except OSError:
            return True
        finally:
            os.close(fd)
    except OSError:
        return True  # cannot tell: fail toward not starting


def job_dirs():
    return sorted(p for p in JOBS.glob("*") if p.is_dir()) if JOBS.exists() else []


def job_info(d: Path) -> dict:
    meta = json.loads((d / "meta.json").read_text())
    rcf = d / "rc"
    rc = int(rcf.read_text().strip()) if rcf.exists() and rcf.read_text().strip() else None
    alive = False
    if rc is None:
        try:
            os.kill(meta["pid"], 0)
            alive = True
        except OSError:
            alive = False
    log = d / "log"
    n = sum(1 for _ in log.open("rb")) if log.exists() else 0
    end = rcf.stat().st_mtime if rc is not None else None
    return {
        **meta,
        "id": d.name,
        "rc": rc,
        "running": alive,
        "log_lines": n,
        "ended_at": end,
        "elapsed_s": round((end or time.time()) - meta["started_at"]),
    }


def _q(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"


def _is_id(x) -> bool:
    return isinstance(x, int) or (isinstance(x, str) and x.isdigit())


# ---------------------------------------------------------------- tools


def t_repo_state(_a):
    _, status = sh(["git", "status", "--short"])
    _, head = sh(["git", "log", "-1", "--format=%h %s"])
    _, ahead = sh(["git", "rev-list", "--count", "origin/main..HEAD"])
    jobs = [job_info(d) for d in job_dirs()[-3:]]
    return json.dumps(
        {
            "head": head.strip(),
            "ahead_of_origin_main": ahead.strip(),
            "status": status.splitlines(),
            "nightly_run_live": nightly_live(),
            "lock_held": lock_held(),
            "index_lock": (REPO / ".git" / "index.lock").exists(),
            "recent_jobs": [{k: j[k] for k in ("id", "rc", "running", "elapsed_s")} for j in jobs],
        },
        indent=1,
    )


def t_git_read(a):
    args = a.get("args")
    if not isinstance(args, list) or not args or not all(isinstance(x, str) for x in args):
        raise ValueError(
            'args must be a non-empty list of strings, e.g. ["log", "-5", "--oneline"]'
        )
    if args[0] not in GIT_READ:
        raise ValueError(f"git {args[0]} is not allowed; allowed: {sorted(GIT_READ)}")
    for x in args[1:]:
        if GIT_BAD_FLAGS.match(x):
            raise ValueError(f"flag {x} is not allowed")
    if forbidden(" ".join(args)):
        raise ValueError(
            "refused: the arguments name vendor data or a secret (scripts/nightly/guard.py)"
        )
    rc, out = sh(["git", "--no-pager", *args])
    return f"rc={rc}\n{clip(out)}"


def t_start_job(a):
    al = allow()
    kind, target, task = a.get("kind"), a.get("target"), a.get("task")
    if kind == "unattended" and target in al["unattended"]:
        argv, name = ["bash", "scripts/unattended.sh", target], f"unattended-{target}"
    elif kind == "make" and (target in al["make_readonly"] or target in al["make_task"]):
        if target in al["make_task"] and not _is_id(task):
            raise ValueError(
                f"make {target} makes numbers or changes records: pass task=<the HANDOFF task id> "
                "that authorizes it (it is recorded with the job)."
            )
        argv, name = ["flock", "-n", "-E", "75", str(LOCK), "make", target], f"make-{target}"
    else:
        raise ValueError(
            "not allowed; see allow.json. unattended: "
            + str(al["unattended"])
            + "; make: "
            + str(al["make_readonly"] + al["make_task"])
            + ". Audits run on the nightly worker."
        )
    if nightly_live():
        raise ValueError(
            "a nightly run is live (RUNNING under 5 minutes old); Cowork starts nothing meanwhile"
        )
    for d in job_dirs():
        j = job_info(d)
        if j["running"]:
            raise ValueError(f"job {j['id']} is still running; one at a time")
    if lock_held() and kind == "unattended":
        raise ValueError(f"another run holds {LOCK}")
    d = (
        JOBS / f"{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}-{name}"
    )  # microseconds: two jobs in one second must not collide
    d.mkdir(parents=True)
    script = f"{' '.join(map(_q, argv))} > {_q(str(d / 'log'))} 2>&1; echo $? > {_q(str(d / 'rc'))}"
    p = subprocess.Popen(
        ["sh", "-c", script],
        cwd=REPO,
        env=ENV,
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    (d / "meta.json").write_text(
        json.dumps(
            {
                "name": name,
                "kind": kind,
                "target": target,
                "pid": p.pid,
                "task": task,
                "started_at": time.time(),
            }
        )
    )
    return f"started {d.name} (pid {p.pid}). Poll with job_status."


def _find(jid):
    d = JOBS / str(jid)
    if not (d / "meta.json").exists():
        raise ValueError(f"no such job {jid!r}")
    return d


def t_job_status(a):
    if a.get("id"):
        return json.dumps(job_info(_find(a["id"])), indent=1)
    return json.dumps(
        [
            {k: j[k] for k in ("id", "rc", "running", "elapsed_s", "log_lines")}
            for j in map(job_info, job_dirs()[-8:])
        ],
        indent=1,
    )


def t_job_tail(a):
    d = _find(a.get("id"))
    j = job_info(d)
    if j["target"] not in allow()["tail_ok"]:
        return (
            f"refused: {j['target']} is not in allow.json tail_ok (its log may hold vendor rows or values). "
            f"rc={j['rc']}, {j['log_lines']} log lines. Read what it wrote under results/ with the file tools."
        )
    n = max(1, min(int(a.get("lines", 40)), MAX_LINES))
    log = d / "log"
    lines = log.read_text(errors="replace").splitlines()[-n:] if log.exists() else []
    return f"rc={j['rc']} running={j['running']}\n" + clip("\n".join(lines))


def _changed_mtimes():
    """mtimes of every tracked-modified and untracked file (ignored files excluded)."""
    _, out = sh(["git", "status", "--porcelain", "-z"])
    res = []
    for ent in out.split("\0"):
        if len(ent) > 3 and (REPO / ent[3:]).is_file():
            res.append((REPO / ent[3:]).stat().st_mtime)
    return res


def _passing(names, since):
    return [
        j
        for j in map(job_info, job_dirs())
        if j["name"] in names and j["rc"] == 0 and (j["ended_at"] or 0) >= since
    ]


def t_commit(a):
    paths, msg = a.get("paths"), a.get("message")
    if not isinstance(paths, list) or not paths or not all(isinstance(x, str) for x in paths):
        raise ValueError("paths must be a non-empty list of repo-relative paths")
    if not isinstance(msg, str) or not msg.strip():
        raise ValueError("message is required")
    if not CITES.search(msg):
        raise ValueError(
            "the message must cite its authority: 'HANDOFF task N', 'decisions/NNNN' or 'OWNER-QUEUE'"
        )
    if nightly_live():
        raise ValueError("a nightly run is live; Cowork edits and commits nothing meanwhile")
    if (REPO / ".git" / "index.lock").exists():
        raise ValueError(".git/index.lock exists; not touching the index")
    al = allow()
    allowed = [re.compile(x) for x in al["commit_paths"]]
    protected = [re.compile(x) for x in al["protected_paths"]]
    code = False
    for p in paths:
        norm = os.path.normpath(p).replace("\\", "/")
        if os.path.isabs(p) or norm.startswith("..") or norm == ".":
            raise ValueError(f"{p!r}: repo-relative paths only")
        if OWNER_ONLY.match(norm):
            raise ValueError(f"{p}: owner-only path (SUBSTRATE section 2)")
        if any(r.match(norm) for r in protected):
            raise ValueError(f"{p}: protected plumbing (allow.json protected_paths)")
        if not any(r.match(norm) for r in allowed):
            raise ValueError(f"{p}: matches no allow.json commit_paths entry")
        if forbidden(norm):
            raise ValueError(f"{p}: names vendor data or a secret")
        if not (REPO / norm).exists():
            raise ValueError(f"{p}: does not exist")
        if re.match(r"^(src|scripts|tests)/|^build\.mk$", norm):
            code = True
    _, staged = sh(["git", "diff", "--cached", "--name-only"])
    if staged.strip():
        raise ValueError(
            "something is already staged: " + ", ".join(staged.split()[:6]) + ". Not mixing it in."
        )
    bar = max(_changed_mtimes() + [(REPO / p).stat().st_mtime for p in paths])
    need = {"unattended-check-scoped"} if code else CHECKS
    if not _passing(need, bar):
        raise ValueError(
            ("code paths need" if code else "records need")
            + f" a passing {sorted(need)} job newer than "
            "every changed file in the tree. start_job it first."
        )
    ok = _passing(need, bar)[-1]
    rc, out = sh(["git", "add", "--", *paths])
    if rc:
        raise RuntimeError("git add failed: " + clip(out))
    rc, out = sh(["git", "commit", "-m", msg], timeout=180)
    if rc:
        sh(["git", "reset", "-q", "--", *paths])  # leave the index as it was found
        raise RuntimeError("git commit failed (index restored): " + clip(out))
    _, head = sh(["git", "log", "-1", "--format=%h %s"])
    _, full = sh(["git", "rev-parse", "HEAD"])
    VERIFIED.mkdir(parents=True, exist_ok=True)
    (VERIFIED / full.strip()).write_text(ok["id"])  # the push gate reads this
    return f"committed {head.strip()} on {ok['id']}. Not pushed."


def t_push(a):
    task = a.get("task")
    if not _is_id(task):
        raise ValueError("task=<HANDOFF task id> is required")
    if nightly_live():
        raise ValueError("a nightly run is live")
    text = (REPO / "HANDOFF.md").read_text(errors="replace")
    m = re.search(rf"^### {int(task)}\. .*?(?=^### \d+\. |^## )", text, re.S | re.M)
    if not m or "git push origin main" not in m.group(0):
        raise ValueError(
            f"HANDOFF task {int(task)} does not say 'git push origin main'. "
            "Pushing needs a task that says so."
        )
    _, dirty = sh(["git", "status", "--porcelain", "--untracked-files=no"])
    if dirty.strip():
        raise ValueError(
            "tracked files are modified; commit or discard them first: "
            + " ".join(dirty.split()[:8])
        )
    # The check comes BEFORE the commit (check, commit, push), so "a check newer than HEAD" would refuse every
    # honest push. HEAD may go if `commit` made it after a passing check (its marker), or if a passing check
    # started at least a whole second after it (for a commit made elsewhere, e.g. by Claude Code).
    _, full = sh(["git", "rev-parse", "HEAD"])
    _, ts = sh(["git", "log", "-1", "--format=%ct"])
    after = [
        j
        for j in map(job_info, job_dirs())
        if j["name"] in CHECKS and j["rc"] == 0 and j["started_at"] >= float(ts.strip()) + 1
    ]
    if not (VERIFIED / full.strip()).exists() and not after:
        raise ValueError(
            "HEAD was not committed through this server after a passing check, and no passing check "
            "has started since it: start_job a check, then push"
        )
    if lock_held():
        raise ValueError(f"another run holds {LOCK}")
    rc, out = sh(
        ["git", "push", "origin", "main"], timeout=180
    )  # fixed argv: never forced, never another branch
    _, head = sh(["git", "rev-parse", "--short", "HEAD"])
    tail = "" if rc == 0 else "\nNot worked around: report it (CLAUDE.md)."
    return f"push rc={rc} (HEAD {head.strip()})\n{clip(out)}{tail}"


TOOLS = {
    "repo_state": (
        t_repo_state,
        "Git status, HEAD, ahead count, nightly-run and lock state, recent jobs.",
        {},
    ),
    "git_read": (
        t_git_read,
        "Read-only git: status, log, diff, show, rev-parse, rev-list, ls-files, check-ignore.",
        {"args": {"type": "array", "items": {"type": "string"}}},
    ),
    "start_job": (
        t_start_job,
        "Start a detached job; kind=unattended|make, target per allow.json; task=<HANDOFF id> "
        "for targets that make numbers or change records.",
        {"kind": {"type": "string"}, "target": {"type": "string"}, "task": {"type": "integer"}},
    ),
    "job_status": (
        t_job_status,
        "Status of one job (id) or the last eight.",
        {"id": {"type": "string"}},
    ),
    "job_tail": (
        t_job_tail,
        "Last lines of a job's log (only for targets in allow.json tail_ok).",
        {"id": {"type": "string"}, "lines": {"type": "integer"}},
    ),
    "commit": (
        t_commit,
        "Commit allow.json paths after a passing check newer than every changed file; the message "
        "must cite a HANDOFF task or decision.",
        {"paths": {"type": "array", "items": {"type": "string"}}, "message": {"type": "string"}},
    ),
    "push": (
        t_push,
        "git push origin main for a HANDOFF task that says to push, after a passing check newer than HEAD.",
        {"task": {"type": "integer"}},
    ),
}


def schema(props):
    return {"type": "object", "properties": props, "additionalProperties": False}


def handle(msg: dict):
    method, mid = msg.get("method"), msg.get("id")
    if mid is None:
        return None  # a notification
    if method == "initialize":
        ver = (msg.get("params") or {}).get("protocolVersion", "2024-11-05")
        return {
            "protocolVersion": ver,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "signal-lab-exec", "version": "0.2-draft"},
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {
            "tools": [
                {"name": n, "description": d, "inputSchema": schema(p)}
                for n, (_, d, p) in TOOLS.items()
            ]
        }
    if method == "tools/call":
        p = msg.get("params") or {}
        fn = TOOLS.get(p.get("name"))
        if not fn:
            return {
                "content": [{"type": "text", "text": f"unknown tool {p.get('name')!r}"}],
                "isError": True,
            }
        try:
            _guard()  # fail closed if guard.py cannot be loaded
            allow()  # ... or allow.json
            return {"content": [{"type": "text", "text": fn[0](p.get("arguments") or {})}]}
        except Exception as e:  # noqa: BLE001 - every failure is reported to the caller, never raised
            return {
                "content": [{"type": "text", "text": f"{type(e).__name__}: {e}"}],
                "isError": True,
            }
    raise LookupError(method)


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        try:
            res = handle(msg)
            if res is not None:
                print(json.dumps({"jsonrpc": "2.0", "id": msg["id"], "result": res}), flush=True)
        except LookupError as e:
            print(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": msg.get("id"),
                        "error": {"code": -32601, "message": f"method not found: {e}"},
                    }
                ),
                flush=True,
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
