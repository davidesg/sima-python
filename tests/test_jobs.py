"""The job runner (sima.jobs; docs/PLAN-vec.md C2): detached processes that
outlive the server, the content-keyed cache, the slots, cancellation, and the
rule that a partial result is never reported as final. Run on the runner's
own self-test job, so that no engine time is spent (the engine's jobs are in
test_vec.py)."""
import json
import os
import subprocess
import sys
import time

import pytest

from sima import jobs


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMA_JOBS_HOME", str(tmp_path / "home"))
    monkeypatch.delenv("SIMA_JOBS_DIR", raising=False)
    monkeypatch.delenv("SIMA_JOBS_MAX", raising=False)
    f = tmp_path / "data" / "a.pre"
    f.parent.mkdir()
    f.write_text("a file\n")
    return tmp_path, str(f)


def _wait_status(jid, want, seconds=60):
    t0 = time.time()
    while time.time() - t0 < seconds:
        st = jobs.status(jid)
        if st["status"] in want:
            return st
        time.sleep(0.2)
    raise AssertionError(f"job {jid} still {jobs.status(jid)['status']}")


def test_a_job_runs_detached_and_its_result_is_cached(home):
    _tmp, f = home
    jid, state = jobs.submit("_selftest", {"steps": 3, "dt": 0.1}, [f], bootstrap=False)
    assert state == "submitted" and len(jid) == 16
    st = jobs.wait(jid, 60)
    assert st["status"] == "done"
    assert jobs.result(jid) == {"steps": 3, "slots": 1, "workers": 1}
    # one folder per run, next to the first file
    assert st["folder"] == os.path.join(os.path.dirname(f), "sima_jobs", jid)
    # the same key: the stored result, without running
    assert jobs.submit("_selftest", {"steps": 3, "dt": 0.1}, [f], bootstrap=False) == (jid, "cached")


def test_the_key_is_the_content(home):
    tmp, f = home
    jid, _ = jobs.submit("_selftest", {"steps": 1, "dt": 0.0}, [f], bootstrap=False)
    jobs.wait(jid, 60)
    # another argument: another job
    j2, _ = jobs.submit("_selftest", {"steps": 2, "dt": 0.0}, [f], bootstrap=False)
    assert j2 != jid
    # the same content under another name, elsewhere: the same key
    g = tmp / "elsewhere.pre"
    g.write_bytes(open(f, "rb").read())
    k1 = jobs.make_key("t", {}, [f], ("python", "x", ""))[0]
    assert k1 == jobs.make_key("t", {}, [str(g)], ("python", "x", ""))[0]
    # a byte changed: another key
    g.write_text("a file!\n")
    assert k1 != jobs.make_key("t", {}, [str(g)], ("python", "x", ""))[0]
    # the engine, the seed: part of it
    assert k1 != jobs.make_key("t", {}, [f], ("c", "0.13", ""))[0]
    assert k1 != jobs.make_key("t", {}, [f], ("python", "x", ""), seed=7)[0]
    jobs.wait(j2, 60)


def test_never_a_partial_result(home):
    _tmp, f = home
    jid, _ = jobs.submit("_selftest", {"steps": 200, "dt": 0.05}, [f], bootstrap=False)
    st = _wait_status(jid, {"running"})
    with pytest.raises(jobs.JobError, match="no final result"):
        jobs.result(jid)
    assert "result.json" not in os.listdir(st["folder"])
    # progress is counts only
    time.sleep(0.6)
    p = jobs.status(jid)["progress"]
    assert set(p) == {"total", "done", "what", "updated"} and p["done"] < p["total"]
    assert jobs.cancel(jid) == "cancelled"
    assert jobs.status(jid)["status"] == "cancelled"
    with pytest.raises(jobs.JobError):
        jobs.result(jid)
    assert "result.json" not in os.listdir(st["folder"])
    # a cancelled job, asked again, runs again from the start
    j2, state = jobs.submit("_selftest", {"steps": 200, "dt": 0.05}, [f], bootstrap=False)
    assert j2 == jid and state == "submitted"
    jobs.cancel(j2)


def test_cancel_kills_the_process(home):
    _tmp, f = home
    jid, _ = jobs.submit("_selftest", {"steps": 500, "dt": 0.05}, [f], bootstrap=False)
    _wait_status(jid, {"running"})
    pid = jobs.read_job(jobs.folder_of(jid))["pid"]
    assert jobs._pid_alive(pid)
    jobs.cancel(jid)
    t0 = time.time()
    while jobs._pid_alive(pid) and time.time() - t0 < 10:
        time.sleep(0.1)
    assert not jobs._pid_alive(pid)


def test_a_failure_is_said_and_has_no_result(home):
    _tmp, f = home
    jid, _ = jobs.submit("_selftest", {"steps": 1, "dt": 0.0, "fail": True}, [f],
                         bootstrap=False)
    st = jobs.wait(jid, 60)
    assert st["status"] == "failed" and "asked to fail" in st["error"]
    with pytest.raises(jobs.JobError):
        jobs.result(jid)


def test_the_slots_queue_the_rest(home, monkeypatch):
    _tmp, f = home
    monkeypatch.setenv("SIMA_JOBS_MAX", "1")
    a, _ = jobs.submit("_selftest", {"steps": 8, "dt": 0.1}, [f], bootstrap=False)
    b, _ = jobs.submit("_selftest", {"steps": 2, "dt": 0.1}, [f], bootstrap=False)
    assert jobs.status(a)["status"] == "running"
    assert jobs.status(b)["status"] == "queued"
    # the job that ends starts the next one (no server needed)
    assert jobs.wait(b, 60)["status"] == "done"
    assert jobs.status(a)["status"] == "done"


def test_a_python_engine_job_takes_its_workers_as_slots(home, monkeypatch):
    _tmp, f = home
    monkeypatch.setenv("SIMA_JOBS_MAX", "3")
    monkeypatch.setenv("DRVEC_ENGINE", "python")
    jid, _ = jobs.submit("_selftest", {"steps": 1, "dt": 0.0}, [f], bootstrap=True)
    assert jobs.wait(jid, 60)["status"] == "done"
    assert jobs.result(jid) == {"steps": 1, "slots": 3, "workers": 3}


SERVER = r"""
import os, sys
from sima import jobs
jid, state = jobs.submit("_selftest", {"steps": 15, "dt": 0.2}, [sys.argv[1]], bootstrap=False)
print(jid, flush=True)
os._exit(0)          # the server ends at once, as a client that closes
"""


def test_a_job_survives_the_server(home, tmp_path):
    """The process that submitted the job ends right away; the job goes on
    and finishes, and another process reads its result."""
    _tmp, f = home
    script = tmp_path / "server.py"
    script.write_text(SERVER)
    out = subprocess.run([sys.executable, str(script), f], capture_output=True, text=True,
                         env=dict(os.environ), timeout=120)
    assert out.returncode == 0, out.stderr
    jid = out.stdout.split()[0]
    st = jobs.wait(jid, 120)
    assert st["status"] == "done", st
    assert jobs.result(jid)["steps"] == 15


def test_a_dead_run_is_not_left_running(home):
    """A run whose process is gone, with no result: failed, said so."""
    _tmp, f = home
    jid, _ = jobs.submit("_selftest", {"steps": 500, "dt": 0.05}, [f], bootstrap=False)
    folder = _wait_status(jid, {"running"})["folder"]
    pid = jobs.read_job(folder)["pid"]
    jobs._kill_tree(pid)                    # not through cancel: it just dies
    st = _wait_status(jid, {"failed"}, 30)
    assert "without a result" in st["error"]


def test_the_runner_writes_lf_files(home):
    tmp, _f = home
    p = tmp / "x.txt"
    jobs.write_text(str(p), "a\nb\n")
    assert open(p, "rb").read() == b"a\nb\n"
    jobs._write_json(str(tmp / "x.json"), {"b": 1, "a": [1, 2]})
    assert b"\r\n" not in open(tmp / "x.json", "rb").read()
    assert json.load(open(tmp / "x.json")) == {"a": [1, 2], "b": 1}
