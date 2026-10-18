"""The worked examples ship their job caches (docs/PLAN-vec.md C6):
load_example copies them, and the tutorial's bootstraps return at once on
the platform they were computed on (Linux x86_64, drvec C: the key holds the
tier and the engine). Rerunning a job reproduces its files byte for byte
there: that is a test too (the flour prices and E1 take minutes on drvec C;
they run with SIMA_SLOW=1)."""
import json
import os
import shutil
import time

import pytest

from sima import jobs
from sima import mcp_server as M
from sima.provenance import platform_tier

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EX = os.path.join(ROOT, "examples")
SPEC = {"flour_prices": dict(purpose="long run", p=2, case="pre"),
        "jenkins_alavi": dict(purpose="long run", p=2, case="2", mixed=True),
        "lutkepohl_e1": dict(purpose="long run", p=2, case="2")}

HERE = platform_tier() == "exact" and jobs.resolve_engine()[0] == "c"
needs_here = pytest.mark.skipif(not HERE, reason="the caches are Linux x86_64's with drvec C "
                                                 "(the key holds the tier and the engine)")


def _fn(f):
    return getattr(f, "fn", f)


def _manifest(name):
    return json.load(open(os.path.join(EX, name, "example.json")))


@pytest.mark.parametrize("name", list(SPEC))
def test_every_cache_is_shipped_whole(name):
    m = _manifest(name)
    assert m.get("jobs"), "the example lists its job cache"
    for rel in m["jobs"]:
        d = os.path.join(EX, name, rel)
        names = set(os.listdir(d))
        assert {"job.json", "result.json"} <= names
        j = json.load(open(os.path.join(d, "job.json")))
        assert j["status"] == "done" and j["id"] == os.path.basename(d)
        assert not any(os.path.isabs(f) for f in j["files"])   # nothing of the machine
        r = json.load(open(os.path.join(d, "result.json")))
        if r["tool"] == "rank_test":
            assert r["B"] >= 499 and {"rank.out", "rank.boot"} <= names


@needs_here
@pytest.mark.parametrize("name", list(SPEC))
def test_the_tutorial_rank_returns_at_once(name, tmp_path, monkeypatch):
    monkeypatch.setenv("SIMA_JOBS_HOME", str(tmp_path / "home"))
    t = _fn(M.load_example)(name, session=f"c_{name}", dest=str(tmp_path / "ex"))
    assert "job cache" in t
    _fn(M.run_gate)(f"c_{name}")
    _fn(M.canonical_analysis)(f"c_{name}")
    _fn(M.prepare_vec)(f"c_{name}", **SPEC[name])
    t0 = time.time()
    out = _fn(M.rank_test)(f"c_{name}", B=499, wait=5)
    assert time.time() - t0 < 30
    assert "B = 499" in out and "Proposed r-hat" in out


def _rerun(name, tmp_path, monkeypatch):
    """Run the cached rank test again, from nothing, and compare the bytes."""
    monkeypatch.setenv("SIMA_JOBS_HOME", str(tmp_path / "home"))
    m = _manifest(name)
    d = tmp_path / "ex"
    for f in m["files"]:
        os.makedirs(d / os.path.dirname(f), exist_ok=True)
        shutil.copy(os.path.join(EX, name, f), d / f)
    files = [str(d / f) for f in m["files"]]
    _fn(M.load_pre)(f"r_{name}", json.dumps(files))
    _fn(M.run_gate)(f"r_{name}")
    _fn(M.canonical_analysis)(f"r_{name}")
    _fn(M.prepare_vec)(f"r_{name}", **SPEC[name])
    _fn(M.rank_test)(f"r_{name}", B=499, wait=0)
    s = M._sess.get(f"r_{name}")
    jid = list(s.rank_jobs.values())[0][0]
    st = jobs.wait(jid, 3 * 3600)
    assert st["status"] == "done"
    ship = [r for r in m["jobs"] if os.path.basename(r) == jid]
    assert ship, f"the rerun's key {jid} is not the shipped cache's"
    for f in ("rank.out", "rank.boot", "result.json"):
        assert open(os.path.join(st["folder"], f), "rb").read() == \
            open(os.path.join(EX, name, ship[0], f), "rb").read(), f


@needs_here
def test_rerunning_the_mixed_case_reproduces_its_bytes(tmp_path, monkeypatch):
    _rerun("jenkins_alavi", tmp_path, monkeypatch)


@needs_here
@pytest.mark.skipif(not os.environ.get("SIMA_SLOW"), reason="minutes on drvec C: SIMA_SLOW=1")
@pytest.mark.parametrize("name", ["flour_prices", "lutkepohl_e1"])
def test_rerunning_the_long_ones_reproduces_their_bytes(name, tmp_path, monkeypatch):
    _rerun(name, tmp_path, monkeypatch)
