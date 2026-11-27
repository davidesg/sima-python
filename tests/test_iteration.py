"""Package B (26-nov-2026): the iteration in one answer, as art packs it —
the specification, the estimated model, the diagnosis and the reformulation,
always stated; observation t of the trial run (one portmanteau cell is not
structure); observation i (structure's refits in parallel)."""
import pytest
import tempfile
import warnings

import numpy as np

import sima.mcp_server as M
from sima import envelope as E
from sima import evidence
from sima import parallel
from sima import session as S

_fn = lambda f: getattr(f, "fn", f)                      # noqa: E731


@pytest.fixture(autouse=True)
def _jobs_aside(tmp_path, monkeypatch):
    """structure's refits run as a job (BUG-0021): its folder out of tests/data."""
    monkeypatch.setenv("SIMA_JOBS_DIR", str(tmp_path / "jobs"))
    monkeypatch.setenv("SIMA_JOBS_HOME", str(tmp_path / "home"))


def _ja(name, lane="guided"):
    warnings.simplefilter("ignore")
    _fn(M.load_example)("jenkins_alavi", session=name, dest=tempfile.mkdtemp(), lane=lane)
    _fn(M.run_gate)(name)
    _fn(M.identify_cross)(name)
    return name


def test_estimate_packs_the_iteration():
    n = _ja("it_pack")
    t = _fn(M.estimate)(n, 1, 0)
    assert isinstance(t, str)                           # figures off (conftest)
    order = ["# Iteration · N3 + N4", "### The specification", "### The estimated model",
             "### The diagnosis — Jenkins and Alavi", "CHECKING, as Jenkins and Alavi",
             E.SHOWS, "**The diagnosis.**", E.CONCLUSIONS, "**The reformulation**",
             E.DECISION, E.STOP]
    pos = [t.index(x) for x in order]
    assert pos == sorted(pos)
    assert '`estimate(name="it_pack", p=1, q=0)`' in t
    s = S.get(n)
    n3, n4 = s.guion.entries[-2:]
    assert (n3.node, n4.node) == ("N3", "N4") and n4.args.get("in") == "estimate"
    # the iteration's decision stays on the estimate's own step
    assert [e.node for e in s.guion.pending()] == ["N3"]


def test_the_reformulation_is_always_stated():
    n = _ja("it_ref")
    t = _fn(M.estimate)(n, 1, 0)
    # the muskrat's 1908 residual, 3.9 s.d.: art first, in levels
    assert "1. the large residual at 1908" in t
    assert "art: suggest_intervention_form(...)" in t
    t0 = _fn(M.estimate)(n, 0, 0)
    assert "**The reformulation**" in t0


def test_the_autonomous_lane_records_the_reformulation():
    n = _ja("it_auto", lane="autonomous")
    t = _fn(M.estimate)(n, 1, 0)
    assert E.STOP not in t and "Autonomous lane." in t
    assert "**The reformulation**" in t


def test_the_guided_lane_shows_the_diagnosis_figures(monkeypatch):
    monkeypatch.setenv("SIMA_FIGURES", "1")
    monkeypatch.setattr(M._viewer, "show", lambda p: None)
    n = _ja("it_fig")
    out = _fn(M.estimate)(n, 1, 0)
    assert isinstance(out, list) and out[0].type == "text"
    assert "# Iteration · N3 + N4" in out[0].text
    assert sum(c.type == "image" for c in out) >= 2


def test_one_portmanteau_cell_is_not_structure():
    """(t) white noise with one cell at p < 0.05 out of m^2: not structure."""
    m, n, K = 4, 200, 12
    for seed in range(200):
        a = np.random.default_rng(seed).standard_normal((n, m))
        _, f = evidence.ja_checking(a, np.eye(m), list("ABCD"), K, 1,
                                    lambda t: (1900 + t, 1), npq=1)
        if f["significant_Q"] and not f["bonferroni_Q"] and f["n_beyond"] <= f["expected"] + 1:
            break
    else:
        raise AssertionError("no seed with a single chance cell")
    assert f["q_df"] == K - 1
    assert not f["structure"]


def test_real_structure_is_still_structure():
    rng = np.random.default_rng(1)
    e = rng.standard_normal((300, 2))
    a = e.copy()
    a[1:, 0] += 0.6 * e[:-1, 1]                          # B leads A by one step
    _, f = evidence.ja_checking(a, np.eye(2), ["A", "B"], 6, 1, lambda t: (1900 + t, 1))
    assert f["structure"] and ("A", "B") in f["bonferroni_Q"]


def test_structure_refits_in_parallel_the_same_numbers(monkeypatch):
    n = _ja("it_par")
    _fn(M.estimate)(n, 1, 0)
    s = S.get(n)
    keys = [k for k in [s.current[:5] + (M._zeros(["AR1[MINK<-MUSKRAT]"]),) + s.current[6:],
                        s.current[:5] + (M._zeros(["AR1[MUSKRAT<-MINK]"]),) + s.current[6:]]]
    specs = [M._ladder_spec(s, k) for k in keys]
    par = parallel.fit_many(specs, 2)
    ser = parallel.fit_many(specs, 1)
    for a, b in zip(par, ser):
        assert not isinstance(a, Exception), a
        assert a.result.logL == b.result.logL
    monkeypatch.setenv("SIMA_WORKERS", "2")
    t = _fn(M.structure)(n)
    assert "refit(s) by exact ML on 2 process(es)" in t
    # the second call reuses every fit
    assert "0 refit(s)" in _fn(M.structure)(n) or "reused" in _fn(M.structure)(n)
