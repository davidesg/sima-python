"""The flour prices end to end through N1c and the C nodes, in both lanes,
with a small bootstrap (docs/PLAN-vec.md C7): the guided lane stops at every
node; the autonomous one decides each, after its evidence, with
record_decision(decided_by="LLM"), and never decides the rank before the
bootstrap's final table. The guion carries the provenance of every step."""
import json
import os
import shutil

import pytest

from sima import jobs
from sima import mcp_server as M

EX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")
B = 19


def _fn(f):
    return getattr(f, "fn", f)


def _open(tmp_path, monkeypatch, name):
    monkeypatch.setenv("SIMA_JOBS_HOME", str(tmp_path / "home"))
    t = _fn(M.load_example)("flour_prices", session=name, dest=str(tmp_path / "ex"))
    assert "Two or more series have d = 1" in t          # the hand-over note, N1c ahead
    return name


def test_the_guided_lane(tmp_path, monkeypatch):
    name = _open(tmp_path, monkeypatch, "glane")
    for call in (lambda: _fn(M.run_gate)(name),):
        assert "N1c" in call()
    c = _fn(M.canonical_analysis)(name)
    assert c.index("prepare_vec") < c.index("identify_matrices")   # the count leads with it
    for t in (_fn(M.prepare_vec)(name, purpose="long run"),
              _fn(M.rank_test)(name, B=B, wait=900)):
        assert "⏸ **Your decision.**" in t
    s = M._sess.get(name)
    # the analyst decides at the pause: here, r = 1 on theory, written as such
    t = _fn(M.estimate_vec)(name, r=1, theory="the analyst: one relation between markets")
    assert "⏸ **Your decision.**" in t
    for t in (_fn(M.test_restriction)(name, weakex="KANSASCITY"), _fn(M.long_run)(name)):
        assert "⏸ **Your decision.**" in t
    t = _fn(M.evaluate)(name, estwin=72, horizon=6)
    assert "CAVEAT, NOT A VETO" in t
    nodes = [e.node for e in s.guion.entries]
    for nd in ("N0", "N1", "N1b", "N1c", "C0", "C1", "C2", "C3", "C5", "C8"):
        assert nd in nodes, nd
    assert not any(e.args.get("decided_by") == "LLM" for e in s.guion.entries)


def test_the_autonomous_lane(tmp_path, monkeypatch):
    name = _open(tmp_path, monkeypatch, "alane")

    def decide(node, decision, reason, evidence, alternatives=""):
        _fn(M.record_decision)(name, node=node, decision=decision, reason=reason,
                               evidence=evidence, alternatives=alternatives,
                               decided_by="LLM")

    _fn(M.run_gate)(name)
    decide("N1", "go on", "the gate passed, every file a fixed point", "difference 1e-13")
    _fn(M.canonical_analysis)(name)
    t = _fn(M.prepare_vec)(name, purpose="long run")
    decide("N1c", "ask the cointegration question; purpose long run",
           "three differenced series, two components near 1", "lam .758 .868 .943")
    # the rank: a job; the node is decided only on job_result's final table
    t = _fn(M.rank_test)(name, B=B, wait=0)
    s = M._sess.get(name)
    jid = list(s.rank_jobs.values())[0][0]
    st = jobs.wait(jid, 900)
    assert st["status"] == "done"
    t = _fn(M.job_result)(jid)
    assert "Proposed r-hat" in t
    from sima import vec
    r_hat, why, _tie = vec.propose_rank(jobs.result(jid))
    r = r_hat if r_hat and 0 < r_hat < 3 else 1
    decide("C1", f"r = {r}", why if r == r_hat else "theory against an exploration (B = 19)",
           f"job {jid}")
    v = _fn(M.estimate_vec)(name, r=r, theory="" if r == r_hat else "the LLM: B = 19 is an "
                            "exploration; one relation is the hypothesis under test")
    assert "# The VEC" in v
    decide("C2", "normalise on KANSASCITY", "the default order", "share in the report")
    _fn(M.test_restriction)(name, weakex="BUFFALO")
    decide("C3", "keep the free VEC", "the LR rejects weak exogeneity", "LR above")
    _fn(M.long_run)(name)
    decide("C5", "read the half-lives", "descriptive", "the model's half-life")
    t = _fn(M.evaluate)(name, estwin=72, horizon=6)
    decide("C8", "the yardstick is a caveat", "purpose long run", "RMSE ratios")
    g = _fn(M.export_guion)(name)
    assert "decision:" in g and "provenance:" in g
    llm = [e for e in s.guion.entries if e.args.get("decided_by") == "LLM"]
    assert [e.node for e in llm] == ["N1", "N1c", "C1", "C2", "C3", "C5", "C8"]
    # every entry carries its provenance; the jobs their engine, key and folder
    assert all(e.prov.get("drvec") and e.prov.get("tier") for e in s.guion.entries)
    c1 = [e for e in s.guion.entries if e.node == "C1" and e.tool == "rank_test"]
    assert all(e.prov.get("key") and e.prov.get("folder") for e in c1)
    # the JSON and the HTML keep it
    j = json.load(open(s.guion.path()))
    assert all("prov" in e and "kind" in e for e in j["entries"])
    html = open(s.guion.html_path(), encoding="utf-8").read()
    assert "PROVENANCE:" in html and "model: VEC" in html
