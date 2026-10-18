"""The cointegration tools (docs/PLAN-vec.md C3, C4) on the flour prices, with
a small bootstrap: the checks and refusals, the rank as the only way to a VEC,
the kind tag and the dispatch of the final-stage tools, the restrictions by
LR, the long run, the bands and the yardstick's rule."""
import json
import os
import shutil

import numpy as np
import pytest

from conftest import DATA

from sima import jobs, vec
from sima import mcp_server as M

EX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")
FLOUR = [os.path.join(EX, "flour_prices", "art", f"{c}_m01.pre")
         for c in ("BUFFALO", "MINNEAPOLIS", "KANSASCITY")]
MM = [os.path.join(EX, "jenkins_alavi", "art", f) for f in ("MUSKRAT_m03.pre", "MINK_m02.pre")]
B = 19


def _fn(f):
    return getattr(f, "fn", f)


@pytest.fixture(scope="module")
def flour(tmp_path_factory):
    """The flour session up to the rank test, B = 19 (an exploration)."""
    d = tmp_path_factory.mktemp("flour")
    old = os.environ.get("SIMA_JOBS_HOME")
    os.environ["SIMA_JOBS_HOME"] = str(d / "home")
    files = []
    for f in FLOUR:
        shutil.copy(f, d)
        files.append(str(d / os.path.basename(f)))
    _fn(M.load_pre)("vfl", json.dumps(files))
    _fn(M.run_gate)("vfl")
    _fn(M.canonical_analysis)("vfl")
    yield "vfl", d
    if old is None:
        os.environ.pop("SIMA_JOBS_HOME", None)
    else:
        os.environ["SIMA_JOBS_HOME"] = old


@pytest.fixture(scope="module")
def ranked(flour):
    name, d = flour
    t = _fn(M.prepare_vec)(name, purpose="forecast")
    assert "PURPOSE, recorded: **forecast**" in t
    rt = _fn(M.rank_test)(name, B=B, wait=900)
    assert "## 1 · TABLE" in rt, rt
    return name, rt


def test_prepare_vec_asks_the_purpose_first(flour):
    name, _d = flour
    t = _fn(M.prepare_vec)(name)
    assert "PURPOSE" in t and '"forecast"' in t and '"long run"' in t
    assert M._sess.get(name).vec_spec is None


def test_prepare_vec_proposes_p_from_the_levels(ranked):
    name, _rt = ranked
    s = M._sess.get(name)
    # Tiao and Box's M(l) on the levels: a VAR(2) (the AR rule alone gives 1)
    assert s.vec_spec["p"] == 2 and s.vec_spec["case"] == "pre"
    assert [e.node for e in s.guion.entries if e.tool == "prepare_vec"][-2:] == ["N1c", "C0"]
    assert s.purpose == "forecast"


def test_the_checks_refuse_with_their_reasons():
    from types import SimpleNamespace
    from drvarma.ladder import load
    # d = 2: drvec models I(1) systems only
    m6 = [os.path.join(DATA, "m6", f"M6_{n}.pre") for n in ("EA", "EC")]
    s = SimpleNamespace(series=load(m6), files=m6, gate=None)
    refuse, _w, _f = vec.checks(s)
    assert any("d = 2" in r and "I(1) systems only" in r for r in refuse)
    # a seasonal difference (D > 0): refused, back to art with "multivariante"
    fake = [SimpleNamespace(name=n, model=SimpleNamespace(d=1, D=D)) for n, D in
            (("A", 1), ("B", 0))]
    refuse, _w, _f = vec.checks(SimpleNamespace(series=fake, files=[], gate=None))
    assert any("D = 1" in r and "multivariante" in r for r in refuse)
    # muskrat d = 1 and mink d = 0: the MIXED case is an option, never the default
    s = SimpleNamespace(series=load(MM), files=MM, gate=None)
    refuse, _w, facts = vec.checks(s)
    assert any("mixed=True" in r for r in refuse)
    refuse, _w, facts = vec.checks(s, mixed=True)
    assert not refuse and facts["i0"] == ["MINK"]


def test_the_mixed_case_goes_in_y1(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMA_JOBS_HOME", str(tmp_path / "home"))
    files = []
    for f in MM:
        shutil.copy(f, tmp_path)
        files.append(str(tmp_path / os.path.basename(f)))
    _fn(M.load_pre)("vmm", json.dumps(files))
    _fn(M.run_gate)("vmm")
    t = _fn(M.prepare_vec)("vmm", purpose="long run", p=2, case="2")
    assert "REFUSED" in t and "mixed=True" in t
    t = _fn(M.prepare_vec)("vmm", purpose="long run", p=2, case="2", mixed=True)
    assert "THE MIXED CASE" in t and "r >= 1" in t
    assert M._sess.get("vmm").vec_spec["order"] == ["MUSKRAT", "MINK"]
    # without a rank test the VEC is refused; on theory it is fitted, MINK in Y1
    assert "No finished rank test" in _fn(M.estimate_vec)("vmm", r=1)
    t = _fn(M.estimate_vec)("vmm", r=1, theory="mink is I(0) in its own model")
    assert "beta is normalised on MINK" in t and "ADOPTED ON THEORY" in t
    # B2 = 0 is the ladder's mixed-d model: tested by LR
    t = _fn(M.test_restriction)("vmm", fixb2="0")
    assert "every entry of B2 = 0" in t and "df 1" in t


def test_the_rank_table_and_its_rules(ranked):
    name, rt = ranked
    assert "parametric bootstrap" in rt and f"B = {B}" in rt
    assert "an EXPLORATION, not a verdict" in rt           # B < 199
    assert "none (case 3/pre: bootstrap only)" in rt       # no table for case pre
    assert "Proposed r-hat" in rt and "PROPOSES" in rt
    assert "PROVENANCE:" in rt and "cache key" in rt and "run folder" in rt
    s = M._sess.get(name)
    e = [e for e in s.guion.entries if e.node == "C1" and "final" in e.evidence][-1]
    assert e.prov["key"] and e.prov["engine"] and e.prov["drvec"]
    # the same call again: the cache, at once
    import time
    t0 = time.time()
    assert _fn(M.rank_test)(name, B=B) .startswith("# The cointegration rank")
    assert time.time() - t0 < 15


def test_the_rank_files_and_the_result(ranked):
    name, _rt = ranked
    s = M._sess.get(name)
    jid = list(s.rank_jobs.values())[0][0]
    st = jobs.status(jid)
    assert sorted(f for f in os.listdir(st["folder"]) if f.endswith((".out", ".boot",
                                                                      "result.json"))) == \
        ["rank.boot", "rank.out", "result.json"]
    res = jobs.result(jid)
    assert res["B"] == B and len(res["comparisons"]) == 2
    assert all(c["ok"] + c["simfail"] + c["fitfail"] == B for c in res["comparisons"])
    assert res["provenance"]["engine"] in ("c", "python")
    assert "elapsed" not in res["provenance"]["extra"]      # nothing that varies run to run
    # job_status / job_result
    assert "status: DONE" in _fn(M.job_status)(jid)
    assert "# The cointegration rank" in _fn(M.job_result)(jid)
    assert jid in _fn(M.jobs_list)(name)


def test_no_vec_without_the_bootstrap_or_theory(ranked):
    name, _rt = ranked
    s = M._sess.get(name)
    res = jobs.result(list(s.rank_jobs.values())[0][0])
    r_hat, _why, _tie = vec.propose_rank(res)
    other = 2 if r_hat != 2 else 1
    t = _fn(M.estimate_vec)(name, r=other)
    assert "THEORY" in t and "ESTIMATED" not in t and s.current_kind() == "VARMA"
    assert "r = 0 is no VEC" in _fn(M.estimate_vec)(name, r=0)
    assert "r must be in 1..2" in _fn(M.estimate_vec)(name, r=3)


@pytest.fixture(scope="module")
def vecfit(ranked):
    name, _rt = ranked
    t = _fn(M.estimate_vec)(name, r=1, theory="the law of one price, tested here")
    assert "# The VEC — rank r = 1" in t, t
    return name, t


def test_the_vec_report(vecfit):
    name, t = vecfit
    assert "beta is normalised on KANSASCITY" in t
    assert "Estimated Parameters and Standard Deviations" in t      # the .out, verbatim
    assert "NOT CITABLE" in t and "Wald" in t
    assert "Beside beta-hat: the canonical analysis" in t
    s = M._sess.get(name)
    assert s.current_kind() == "VEC"
    e = [e for e in s.guion.entries if e.tool == "estimate_vec"][-1]
    assert e.kind == "VEC" and "on theory" in e.decision
    assert e.prov["drvec_provenance"]["engine"] == "python"   # no bootstrap in a fit


def test_the_kind_tag_dispatches(vecfit):
    import drvec
    name, _t = vecfit
    s = M._sess.get(name)
    # reorder refuses on a VEC: another order is another fit
    assert "REFUSED on a VEC" in _fn(M.reorder)(name, '["KANSASCITY", "BUFFALO", "MINNEAPOLIS"]')
    assert "the current model is a VEC" in _fn(M.check_residuals)(name)[0]
    assert "the current model is a VEC" in _fn(M.simplify)(name)
    assert "IMPULSE RESPONSES OF THE LEVELS" in _fn(M.impulse_response)(name, horizon=8)
    assert "OF THE LEVELS" in _fn(M.variance_decomposition)(name, horizon=8)
    # the forecast is drvarma's forecaster on the VEC in levels
    f = _fn(M.forecast)(name, horizon=4)
    assert "forecast_given" in f
    vf = s.vec_fits[s.vec_current]
    fc = drvec.to_levels_varma(vf.fit).forecast(4)
    assert f"{fc[0]['level'][0]:.4f}" in f
    # a VARMA estimated makes the VARMA current; estimate_vec again (cached), the VEC
    _fn(M.estimate)(name, p=1, q=0)
    assert s.current_kind() == "VARMA"
    assert "IMPULSE RESPONSES (orthogonalised" in _fn(M.impulse_response)(name, horizon=4,
                                                                          bands=False)
    _fn(M.estimate_vec)(name, r=1, theory="the law of one price, tested here")
    assert s.current_kind() == "VEC"


def test_restrictions_by_lr(vecfit):
    name, _t = vecfit
    s = M._sess.get(name)
    base = s.vec_fits[s.vec_current]
    t = _fn(M.test_restriction)(name, weakex="BUFFALO")
    assert "LR =" in t and "df 1" in t and "NOT CITABLE" in t
    rv = [v for k, v in s.vec_fits.items() if v.restriction.get("weakex") == "BUFFALO"][0]
    lr = 2 * (base.fit.loglik - rv.fit.loglik)
    assert f"LR = {lr:.4f}" in t
    assert "needs a VALUE" in _fn(M.test_restriction)(name, fixb2="true")
    assert "not in the nabla Y2 block" in _fn(M.test_restriction)(name, fixb2row="KANSASCITY=0")
    assert s.vec_current == base.key                       # not adopted


def test_the_long_run(vecfit):
    name, _t = vecfit
    t = _fn(M.long_run)(name)
    assert "theta" in t and "TEXTBOOK" in t and "MODEL's" in t and "Gonzalo and Ng" in t
    s = M._sess.get(name)
    vf = s.vec_fits[s.vec_current]
    lr = vec.long_run(vf, 60, 12)
    assert np.allclose(lr["theta"], -np.asarray(vf.fit.beta2))
    assert lr["gn"]["trans_long_run_max"] < 1e-3            # transitory: no long-run effect
    sh = np.asarray(lr["gn"]["share_permanent"])
    assert np.all((sh >= -1e-12) & (sh <= 1 + 1e-12))


def test_the_irf_bands_are_a_bootstrap_job(vecfit):
    name, _t = vecfit
    assert "at least 20" in _fn(M.irf_bands)(name, N=10)
    t = _fn(M.irf_bands)(name, N=20, wait=900)
    assert "IRF BANDS" in t, t
    t = _fn(M.impulse_response)(name, horizon=4)
    assert "parametric bootstrap's 90 %" in t and "[" in t
    out = _fn(M.plot_impulse_response)(name, horizon=8)
    assert any(getattr(x, "type", "") == "image" for x in out)


def test_the_sweep(vecfit):
    name, _t = vecfit
    t = _fn(M.sweep)(name, p="1,2", wait=600)
    assert "p=1 case pre" in t and "p=2 case pre" in t and "done" in t


def test_the_yardstick_rule_follows_the_purpose(vecfit):
    name, _t = vecfit
    s = M._sess.get(name)
    t = _fn(M.evaluate)(name, estwin=72, horizon=6)
    assert "# The yardstick for the VEC (C8)" in t and "SAME origins" in t
    assert "a VETO" in t                                    # purpose: forecast
    s.purpose = "long run"
    t = _fn(M.evaluate)(name, estwin=72, horizon=6)
    assert "CAVEAT, NOT A VETO" in t
    s.purpose = "forecast"
    e = [e for e in s.guion.entries if e.node == "C8"][-1]
    assert e.kind == "VEC"


def test_the_rank_figure(vecfit):
    name, _t = vecfit
    out = _fn(M.plot_rank_bootstrap)(name)
    assert any(getattr(x, "type", "") == "image" for x in out)
    s = M._sess.get(name)
    assert s.guion.entries[-1].node == "C1"


def test_the_refused_options_are_never_offered():
    import asyncio
    tools = {t.name: t for t in asyncio.run(M.mcp.list_tools())}
    assert "rungs" not in tools and "export_tables" not in tools
    for t in tools.values():
        props = set(((t.inputSchema or {}).get("properties") or {}))
        assert not props & {"warma", "mawarma", "specs", "matest", "artest", "rankadm",
                            "m", "writeres", "writeinp", "eval", "noladder", "rungs"}, t.name
    assert {"prepare_vec", "rank_test", "estimate_vec", "test_restriction", "add_exogenous",
            "long_run", "irf_bands", "sweep", "plot_rank_bootstrap", "job_status",
            "job_result", "job_cancel", "jobs"} <= set(tools)


def test_no_tie_flagged_below_the_exploration_threshold():
    """At B < 199 the rank is an exploration and the tie rule is silent; from
    B = 199 a p-value within two Monte Carlo errors of 5 % is a tie
    (decided 2026-10-18)."""
    def res(b):
        return {"M": 2, "B": b, "comparisons": [
            {"h0": 0, "cv": [3.0, 4.0, 6.0], "lr": 4.1, "pvalue": 0.06, "ok": b, "B": b}]}
    assert vec.propose_rank(res(19))[2] == []
    assert vec.propose_rank(res(199))[2] == [0]
