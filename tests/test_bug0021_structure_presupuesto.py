"""BUG-0021: structure says its cost first and does not start beyond the
budget, and its refits run as a detached job that survives the client."""
import json
import os

import pytest

import sima.mcp_server as M
from sima import jobs, session as S

D = os.path.join(os.path.dirname(__file__), "..", "bugs", "BUG-0018-repro")


@pytest.fixture
def par(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMA_JOBS_DIR", str(tmp_path / "jobs"))
    monkeypatch.setenv("SIMA_JOBS_HOME", str(tmp_path / "home"))
    n = "b21t"
    M.load_pre(n, json.dumps([os.path.join(D, f) for f in ("IPC_m07.pre", "IPI_m07.pre")]))
    M.run_gate(n)
    M.estimate(n, p=1, q=0)
    return n


def test_mas_alla_del_presupuesto_no_empieza(par):
    s = S.get(par)
    s.fits[s.current].sima_seconds = 1e5
    t = M.structure(par)
    assert t.startswith("structure NOT STARTED") or "structure NOT STARTED" in t
    assert "max_seconds=0" in t
    assert len(s.fits) == 1                       # nothing was fitted


def test_los_reajustes_son_un_trabajo(par):
    s = S.get(par)
    t = M.structure(par, wait=0)
    if "a JOB, running detached" in t:            # not finished at once: its id
        jid = t.split("job id: `")[1].split("`")[0]
        st = jobs.wait(jid, 120)
        assert st["status"] == "done", st
        from sima.mcp_vec import job_result
        assert "STRUCTURE'S REFITS" in job_result(jid)
        t = M.structure(par)                      # the same call reads the job
    assert "LR =" in t and "refit(s) by exact ML" in t
    assert len(s.fits) > 1
