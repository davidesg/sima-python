"""sima's job runner: long computations as detached processes, with an on-disk
cache keyed by content (docs/STUDY-vec.md §5.3, docs/PLAN-vec.md C2).

A rank test by parametric bootstrap takes minutes to hours. A stdio MCP server
lives as long as its client, so nothing that runs inside it survives the
client; and the GIL would serialise threads. So each job is its own process,

    python -m sima.jobs run <folder>

started DETACHED by the tool (a new session on POSIX; a detached process group
on Windows), so it outlives the server that started it. The rules:

* **one folder per run**, ``<first file's folder>/sima_jobs/<id>/``: drvec
  writes ``BASE.out`` and two runs in one folder would overwrite each other.
  It holds ``job.json`` (the call, its status, times, versions), ``progress.json``,
  the engine's files (``rank.out``, ``rank.boot``, ``c/`` for drvec C) and
  ``result.json``, the structured result, written LAST and atomically;
* **the cache key** is a sha256 over the tool and its canonical arguments, the
  CONTENT of every input file, the versions of drvec, drvarma and fue, the
  numerical backend, the bootstrap engine, the platform tier and the seed. The
  results are deterministic (fixed seed, one stream), so a key that matches is
  the same computation, not an approximation of it. Same key and a result: it
  is returned without running. Same key and a job running: that job. Anything
  changed: a new run. The id is the key's first 16 hex digits;
* **at most cores - 1 slots at once**, counted with drvec's workers: a job on
  drvec C takes one slot, a job on the Python engine as many as its process
  pool, and the runner passes ``workers=`` explicitly so the pool is not
  counted twice. The rest wait in the queue; a job that ends starts the next;
* **never a partial result as final**: ``result.json`` exists only when the
  run finished; a running job shows its counts, never provisional numbers;
* **cancellation** kills the run's process tree and marks the folder.

The registry of jobs (for ``jobs()`` and the slot count) lives in
``SIMA_JOBS_HOME`` (default ``~/.sima/jobs``): one pointer per job.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import traceback

HEARTBEAT = 2.0          # seconds between the runner's heartbeats
STALE = 45.0             # a heartbeat older than this: the runner is gone
FINAL = ("done", "failed", "cancelled")


class JobError(RuntimeError):
    pass


# --------------------------------------------------------------------------- #
#  places                                                                      #
# --------------------------------------------------------------------------- #

def home():
    d = os.environ.get("SIMA_JOBS_HOME") or os.path.join(os.path.expanduser("~"), ".sima",
                                                         "jobs")
    os.makedirs(os.path.join(d, "registry"), exist_ok=True)
    return d


def budget():
    """The slots: cores - 1 (at least 1); SIMA_JOBS_MAX overrides."""
    env = os.environ.get("SIMA_JOBS_MAX")
    if env:
        return max(1, int(env))
    return max(1, (os.cpu_count() or 2) - 1)


def folder_for(files, job_id):
    base = os.environ.get("SIMA_JOBS_DIR") or os.path.join(
        os.path.dirname(os.path.abspath(files[0])), "sima_jobs")
    return os.path.join(base, job_id)


def _reg(job_id):
    return os.path.join(home(), "registry", f"{job_id}.json")


# --------------------------------------------------------------------------- #
#  files, written atomically (Windows: retry a replace a reader holds)         #
# --------------------------------------------------------------------------- #

def _write_json(path, obj):
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
        fh.write("\n")
    for k in range(50):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:                                # pragma: no cover (Windows)
            time.sleep(0.05 * (k + 1))
    os.replace(tmp, path)


def _read_json(path):
    for k in range(20):
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except FileNotFoundError:
            return None
        except (PermissionError, json.JSONDecodeError):        # being replaced
            time.sleep(0.05 * (k + 1))
    return None


def write_text(path, text):
    """A result file, LF line ends on every platform (bytes reproduce)."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def read_job(folder):
    return _read_json(os.path.join(folder, "job.json"))


def _update_job(folder, **kw):
    j = read_job(folder) or {}
    j.update(kw)
    _write_json(os.path.join(folder, "job.json"), j)
    return j


# --------------------------------------------------------------------------- #
#  the key                                                                     #
# --------------------------------------------------------------------------- #

def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def resolve_engine(seed=None, bootstrap=True):
    """The bootstrap engine drvec's engine="auto" picks: drvec C when a
    matching binary is found and the seed is the C's, else the Python port.
    -> ("c", "0.13", source) or ("python", drvec's version, "")."""
    from .provenance import _version
    if not bootstrap:
        return ("python", _version("drvec"), "")
    want = (os.environ.get("DRVEC_ENGINE") or "auto").lower()
    if seed is None and want in ("auto", "c"):
        try:
            from drvec import c_engine
            b = c_engine.find()
            return ("c", b.version, b.source)
        except Exception:                                      # noqa: BLE001
            pass
    return ("python", _version("drvec"), "")


def make_key(tool, args, files, engine, seed=None, extra_files=()):
    from .provenance import _version, drvarma_backend, platform_tier
    payload = {"tool": tool, "args": args,
               "files": [digest(f) for f in files],
               "extra_files": [digest(f) for f in extra_files],
               "versions": {k: _version(k) for k in ("drvec", "drvarma", "fue")},
               "backend": drvarma_backend(),
               "engine": f"{engine[0]} {engine[1]}",
               "tier": platform_tier(), "seed": seed}
    return hashlib.sha256(canonical(payload).encode()).hexdigest(), payload


# --------------------------------------------------------------------------- #
#  liveness and the process tree                                               #
# --------------------------------------------------------------------------- #

def _pid_alive(pid):
    if not pid:
        return False
    if sys.platform == "win32":                                # pragma: no cover
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, int(pid))             # QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = k.GetExitCodeProcess(h, ctypes.byref(code))
        k.CloseHandle(h)
        return bool(ok) and code.value == 259                  # STILL_ACTIVE
    try:                                   # our own child, ended: reap it (no zombie)
        done, _st = os.waitpid(int(pid), os.WNOHANG)
        if done:
            return False
    except (ChildProcessError, OSError):
        pass
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    # a zombie (ended, not yet reaped by its parent) is not running
    try:
        with open(f"/proc/{int(pid)}/stat") as fh:
            return fh.read().split(")")[-1].split()[0] != "Z"
    except OSError:
        return True


def alive(folder, j=None):
    """Is the run of this folder still going? Its process exists and its
    heartbeat is recent (a runner just started gets the grace period)."""
    j = j or read_job(folder) or {}
    if not _pid_alive(j.get("pid")):
        return False
    hb = os.path.join(folder, "heartbeat")
    t = os.path.getmtime(hb) if os.path.exists(hb) else j.get("started", 0)
    return time.time() - t < STALE


def _kill_tree(pid):
    if not pid:
        return
    if sys.platform == "win32":                                # pragma: no cover
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    import signal
    try:
        pg = os.getpgid(int(pid))
    except ProcessLookupError:
        return
    for sig, wait in ((signal.SIGTERM, 3.0), (signal.SIGKILL, 2.0)):
        try:
            os.killpg(pg, sig)
        except ProcessLookupError:
            return
        t0 = time.time()
        while time.time() - t0 < wait and _pid_alive(pid):
            time.sleep(0.1)
        if not _pid_alive(pid):
            return


def _spawn(folder):
    """The runner, DETACHED: it survives the server and its client."""
    log = open(os.path.join(folder, "runner.log"), "ab")
    cmd = [sys.executable, "-m", "sima.jobs", "run", folder]
    kw = dict(stdin=subprocess.DEVNULL, stdout=log, stderr=log, close_fds=True,
              cwd=folder)
    try:
        if sys.platform == "win32":                            # pragma: no cover
            flags = (subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                     | getattr(subprocess, "CREATE_NO_WINDOW", 0))
            try:
                return subprocess.Popen(cmd, creationflags=flags | 0x01000000, **kw)
            except OSError:                    # the job object forbids the breakaway
                return subprocess.Popen(cmd, creationflags=flags, **kw)
        return subprocess.Popen(cmd, start_new_session=True, **kw)
    finally:
        log.close()


# --------------------------------------------------------------------------- #
#  the queue                                                                   #
# --------------------------------------------------------------------------- #

class _Lock:
    """A cross-process lock on the registry: an exclusive directory."""

    def __init__(self, timeout=20.0):
        self.path = os.path.join(home(), "lock")
        self.timeout = timeout

    def __enter__(self):
        t0 = time.time()
        while True:
            try:
                os.mkdir(self.path)
                return self
            except FileExistsError:
                try:
                    if time.time() - os.path.getmtime(self.path) > 30.0:
                        os.rmdir(self.path)             # a holder that died
                        continue
                except OSError:
                    continue
                if time.time() - t0 > self.timeout:
                    raise JobError("the job registry is locked: " + self.path)
                time.sleep(0.05)

    def __exit__(self, *exc):
        try:
            os.rmdir(self.path)
        except OSError:
            pass


def _registry():
    """{id: folder} of every job registered, the gone ones dropped."""
    d = os.path.join(home(), "registry")
    out = {}
    for f in sorted(os.listdir(d)):
        if not f.endswith(".json"):
            continue
        r = _read_json(os.path.join(d, f)) or {}
        folder = r.get("folder")
        if folder and os.path.exists(os.path.join(folder, "job.json")):
            out[f[:-5]] = folder
        else:
            try:
                os.remove(os.path.join(d, f))
            except OSError:
                pass
    return out


def _register(job_id, folder):
    _write_json(_reg(job_id), {"folder": os.path.abspath(folder)})


def _settle(folder, j):
    """A run marked running whose process is gone ended without a result:
    say so (it was killed, or crashed), never leave it 'running'."""
    if j and j.get("status") == "running" and not alive(folder, j):
        if os.path.exists(os.path.join(folder, "result.json")):
            j = _update_job(folder, status="done")
        else:
            j = _update_job(folder, status="failed", ended=time.time(),
                            error="the run's process ended without a result "
                                  "(killed, or it crashed): see runner.log")
    return j


def pump():
    """Start queued jobs while slots are free (oldest first)."""
    started = []
    with _Lock():
        used, queued = 0, []
        for jid, folder in _registry().items():
            j = _settle(folder, read_job(folder))
            if not j:
                continue
            if j["status"] == "running":
                used += int(j.get("slots", 1))
            elif j["status"] == "queued":
                queued.append((j.get("created", 0), jid, folder, j))
        cap = budget()
        for _t, jid, folder, j in sorted(queued):
            need = int(j.get("slots", 1))
            if used and used + need > cap:
                continue
            proc = _spawn(folder)
            _update_job(folder, status="running", pid=proc.pid, started=time.time())
            used += need
            started.append(jid)
    return started


def submit(tool, args, files, *, seed=None, bootstrap=True, extra_files=(), label="",
           session=""):
    """Queue a job, or find it. -> (job_id, state), state "cached" (a finished
    result with this key), "running"/"queued" (that job), or "submitted"."""
    files = [os.path.abspath(f) for f in files]
    engine = resolve_engine(seed, bootstrap)
    key, payload = make_key(tool, args, files, engine, seed, extra_files)
    jid = key[:16]
    folder = folder_for(files, jid)
    os.makedirs(folder, exist_ok=True)
    with _Lock():
        j = _settle(folder, read_job(folder))
        if j and j.get("key") == key:
            if j["status"] == "done" and os.path.exists(os.path.join(folder, "result.json")):
                _register(jid, folder)
                return jid, "cached"
            if j["status"] in ("queued", "running"):
                _register(jid, folder)
                return jid, j["status"]
        # a new run (or a failed/cancelled one again): a clean folder
        for f in os.listdir(folder):
            p = os.path.join(folder, f)
            shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) else os.remove(p)
        slots = 1 if engine[0] == "c" or not bootstrap else budget()
        _write_json(os.path.join(folder, "job.json"), {
            "id": jid, "key": key, "payload": payload, "tool": tool, "args": args,
            "files": files, "extra_files": [os.path.abspath(f) for f in extra_files],
            "seed": seed, "engine": list(engine), "slots": slots,
            "workers": 1 if engine[0] == "c" else slots, "label": label,
            "session": session, "status": "queued", "created": time.time()})
        _register(jid, folder)
    pump()
    return jid, "submitted"


def folder_of(job_id):
    r = _read_json(_reg(job_id))
    if not r:
        raise JobError(f"no job '{job_id}' (jobs() lists them)")
    return r["folder"]


def status(job_id):
    """The job's state, its progress and times; never its provisional numbers."""
    folder = folder_of(job_id)
    j = _settle(folder, read_job(folder))
    if j is None:
        raise JobError(f"job '{job_id}': its folder {folder} has no job.json")
    if j["status"] == "queued":
        pump()
        j = read_job(folder)
    prog = _read_json(os.path.join(folder, "progress.json")) or {}
    t0 = j.get("started") or j.get("created")
    t1 = j.get("ended") or time.time()
    return {"id": job_id, "status": j["status"], "tool": j["tool"], "label": j.get("label", ""),
            "folder": folder, "progress": prog, "engine": j.get("engine"),
            "elapsed": (t1 - t0) if j.get("started") else 0.0,
            "error": j.get("error", ""), "slots": j.get("slots", 1),
            "session": j.get("session", ""), "seed": j.get("seed"), "key": j.get("key")}


def result(job_id):
    """The FINAL result, or JobError: a partial result is never returned."""
    folder = folder_of(job_id)
    j = _settle(folder, read_job(folder))
    if not j or j["status"] != "done":
        raise JobError(f"job {job_id} is {j['status'] if j else 'unknown'}: "
                       "there is no final result yet")
    r = _read_json(os.path.join(folder, "result.json"))
    if r is None:
        raise JobError(f"job {job_id}: done but result.json is missing ({folder})")
    return r


def cancel(job_id):
    folder = folder_of(job_id)
    with _Lock():
        j = _settle(folder, read_job(folder))
        st = j["status"]
        if st in FINAL:
            return st
        if st == "running":
            _kill_tree(j.get("pid"))
        try:
            os.remove(os.path.join(folder, "result.json"))     # never half a result
        except OSError:
            pass
        _update_job(folder, status="cancelled", ended=time.time())
    pump()
    return "cancelled"


def wait(job_id, seconds):
    """Poll up to `seconds`; -> the final status or the current one."""
    t0 = time.time()
    while True:
        st = status(job_id)
        if st["status"] in FINAL or time.time() - t0 >= seconds:
            return st
        time.sleep(0.25)


def all_jobs():
    out = []
    for jid in _registry():
        try:
            out.append(status(jid))
        except JobError:
            pass
    return sorted(out, key=lambda s: (s["status"] not in ("running", "queued"), s["id"]))


# --------------------------------------------------------------------------- #
#  progress, as the run reports it                                             #
# --------------------------------------------------------------------------- #

class Progress:
    """The rank test's progress: per comparison r -> r + 1, the replications
    done and their statuses. Written at most twice a second, and when a
    comparison completes. Counts only: no provisional critical value."""

    def __init__(self, folder, B, comparisons):
        self.path = os.path.join(folder, "progress.json")
        self.B = int(B)
        self.c = {str(h): {"done": 0, "ok": 0, "simfail": 0, "fitfail": 0}
                  for h in comparisons}
        self.t = 0.0
        self.write(force=True)

    def __call__(self, b, rep):
        h = str(getattr(rep, "h0", 0))
        c = self.c.setdefault(h, {"done": 0, "ok": 0, "simfail": 0, "fitfail": 0})
        c["done"] += 1
        st = getattr(rep, "status", "ok")
        c[st] = c.get(st, 0) + 1
        self.write(force=c["done"] >= self.B)

    def write(self, force=False):
        now = time.time()
        if force or now - self.t >= 0.5:
            self.t = now
            _write_json(self.path, {"B": self.B, "comparisons": self.c, "updated": now})


class Ticks:
    """A progress that counts steps (the IRF bootstrap, a sweep's cells)."""

    def __init__(self, folder, total, what):
        self.path = os.path.join(folder, "progress.json")
        self.total, self.what, self.done, self.t = int(total), what, 0, 0.0
        self.write(True)

    def __call__(self, *_a):
        self.done += 1
        self.write(self.done >= self.total)

    def write(self, force=False):
        now = time.time()
        if force or now - self.t >= 0.5:
            self.t = now
            _write_json(self.path, {"total": self.total, "done": self.done, "what": self.what,
                                    "updated": now})


def progress_text(st):
    """'k of B, comparison r -> r + 1' and the rate, from a status."""
    p = st.get("progress") or {}
    if "comparisons" in p:
        B = p["B"]
        parts = []
        done_total = 0
        for h, c in sorted(p["comparisons"].items(), key=lambda kv: int(kv[0])):
            h = int(h)
            done_total += c["done"]
            fin = " (finished)" if c["done"] >= B else ""
            parts.append(f"comparison r = {h} -> {h + 1}: replication {c['done']} of {B}"
                         f" (ok {c.get('ok', 0)}, simfail {c.get('simfail', 0)}, "
                         f"fitfail {c.get('fitfail', 0)}){fin}")
        total = B * max(1, len(p["comparisons"]))
        txt = "\n".join("  " + x for x in parts)
        el = st.get("elapsed") or 0.0
        if done_total and st["status"] == "running" and el > 0:
            left = el / done_total * (total - done_total)
            txt += f"\n  elapsed {el / 60:.1f} min; about {left / 60:.1f} min left at this rate"
        return txt
    if "total" in p:
        el = st.get("elapsed") or 0.0
        return (f"  {p['what']}: {p['done']} of {p['total']}"
                + (f"; elapsed {el / 60:.1f} min" if el else ""))
    if st.get("status") == "done":
        return "  finished"
    return "  (no progress reported yet)"


# --------------------------------------------------------------------------- #
#  the runner                                                                  #
# --------------------------------------------------------------------------- #

def _heartbeat(folder, stop):
    hb = os.path.join(folder, "heartbeat")
    while not stop.is_set():
        try:
            with open(hb, "w") as fh:
                fh.write(str(time.time()))
        except OSError:
            pass
        stop.wait(HEARTBEAT)


def _selftest(job, folder):
    """A job that sleeps and counts: the runner's own tests (no engine)."""
    a = job["args"]
    tk = Ticks(folder, a.get("steps", 5), "selftest steps")
    for _k in range(int(a.get("steps", 5))):
        time.sleep(float(a.get("dt", 0.2)))
        tk()
    if a.get("fail"):
        raise RuntimeError("asked to fail")
    return {"steps": int(a.get("steps", 5)), "slots": job["slots"],
            "workers": job["workers"]}


def _tools():
    from . import vec
    return {"_selftest": _selftest, "rank_test": vec.job_rank_test,
            "irf_bands": vec.job_irf_bands, "fit_cell": vec.job_fit_cell}


def run(folder):
    folder = os.path.abspath(folder)
    j = read_job(folder)
    if j is None or j.get("status") in FINAL:
        return 0
    _update_job(folder, status="running", pid=os.getpid(),
                started=j.get("started") or time.time())
    stop = threading.Event()
    threading.Thread(target=_heartbeat, args=(folder, stop), daemon=True).start()
    code = 0
    try:
        res = _tools()[j["tool"]](j, folder)
        if (read_job(folder) or {}).get("status") == "cancelled":
            return 0
        _write_json(os.path.join(folder, "result.json"), res)
        _update_job(folder, status="done", ended=time.time())
    except BaseException as e:                                 # noqa: BLE001
        code = 1
        tb = traceback.format_exc()
        sys.stderr.write(tb)
        if (read_job(folder) or {}).get("status") != "cancelled":
            _update_job(folder, status="failed", ended=time.time(),
                        error=f"{type(e).__name__}: {e}")
    finally:
        stop.set()
        try:
            pump()
        except Exception:                                      # noqa: BLE001
            pass
    return code


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) == 2 and argv[0] == "run":
        return run(argv[1])
    sys.stderr.write("usage: python -m sima.jobs run <folder>\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
