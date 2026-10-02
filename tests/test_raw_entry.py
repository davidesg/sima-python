"""The raw-data entry (docs/STUDY-raw-entry.md): load_data and characterize."""
import os

import numpy as np
import pytest

from sima import mcp_server as M
from sima import raw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLOUR = os.path.join(ROOT, "examples", "flour_prices", "data", "flour_prices.csv")
MM = os.path.join(ROOT, "examples", "jenkins_alavi", "data", "mink_muskrat.csv")


def _fn(tool):
    return getattr(tool, "fn", tool)


# ── the table ────────────────────────────────────────────────────────────────

def test_dates_and_frequency_are_read():
    names, data, dates = raw.read_table(FLOUR)
    assert names == ["Buffalo", "Minneapolis", "KansasCity"] and data.shape == (100, 3)
    assert raw.infer_start(dates, 12) == (1972, 8)
    t = _fn(M.load_data)("r_fl", FLOUR)
    assert "monthly, 1972.08 - 1980.11" in t
    t = _fn(M.load_data)("r_mm", MM)
    assert "annual, 1850 - 1911" in t


def test_a_numeric_csv_without_header_keeps_its_first_row(tmp_path):
    """The old sima's BUG: the first row was dropped as a header."""
    p = tmp_path / "x.csv"
    rng = np.random.default_rng(1)
    x = 10 + rng.random((40, 2))
    np.savetxt(p, x, delimiter=",")
    names, data, dates = raw.read_table(str(p))
    assert dates is None and data.shape == (40, 2) and data[0, 0] == pytest.approx(x[0, 0])
    assert "Say the frequency" in _fn(M.load_data)("r_x", str(p))
    assert "Say the first date" in _fn(M.load_data)("r_x", str(p), freq=4)
    assert "quarterly" in _fn(M.load_data)("r_x", str(p), freq=4, start="2000Q1")


def test_missing_values_are_refused_with_where(tmp_path):
    p = tmp_path / "m.csv"
    rows = ["date,A,B"] + [f"{2000 + i},{1 + i},{2 + i}" for i in range(40)]
    rows[5] = "2004,,6"
    p.write_text("\n".join(rows))
    t = _fn(M.load_data)("r_m", str(p))
    assert "Cannot load" in t and "A row 5" in t


# ── the characterization ─────────────────────────────────────────────────────

def test_flour_characterization():
    _fn(M.load_data)("r_fl2", FLOUR)
    t = _fn(M.characterize)("r_fl2")
    for h in ("## 1 · TABLE", "## 2 · WHAT IT SHOWS", "## 3 · CONCLUSIONS",
              "## 4 · DECISION", "⏸"):
        assert h in t
    ch = M._sess.get_raw("r_fl2").chars
    assert [(c["lam"], c["d"], c["harmonics"]) for c in ch] == [(0.0, 1, False)] * 3
    assert "3 series are differenced" in t and 'canonical_analysis(name="r_fl2")' in t


def test_each_series_keeps_its_own_and_the_analyst_can_change_it():
    """Mink and muskrat: different d (0 and 1), no consensus. The engine
    proposes levels for the mink (opposite signs: the domain decides); the
    analyst sets logs, as Jenkins and Alavi."""
    _fn(M.load_data)("r_mm2", MM)
    t = _fn(M.characterize)("r_mm2")
    ch = {c["name"]: c for c in M._sess.get_raw("r_mm2").chars}
    assert ch["mink"]["d"] == 0 and ch["muskrat"]["d"] == 1 and ch["muskrat"]["lam"] == 0.0
    assert "they differ here" in t
    t = _fn(M.characterize)("r_mm2", set="mink: lam=0")
    assert ch["mink"]["lam"] == 0.0
    assert "Changed by the analyst: mink: lam = 0" in t
    assert "the series are mink, muskrat" in _fn(M.characterize)("r_mm2", set="otter: d=1")
    assert "lambda is 0" in _fn(M.characterize)("r_mm2", set="mink: lam=0.5")
    g = M._sess.get_raw("r_mm2").guion.entries
    assert [e.node for e in g] == ["N0r", "N0c", "N0c"]


def test_canonical_analysis_on_raw_levels_is_the_ladders():
    """The same lambdas as from the .pre files (test_tiao_box), before any
    model; the menu speaks of characterize, not of the .pre."""
    _fn(M.load_data)("r_fl3", FLOUR)
    assert "Characterize the series first" in _fn(M.canonical_analysis)("r_fl3")
    _fn(M.characterize)("r_fl3")
    c = _fn(M.canonical_analysis)("r_fl3")
    assert "1  0.758    0.870" in c and "3  0.943    0.971" in c
    assert 'characterize(name="r_fl3", set="SERIES: d=0")' in c
    assert "it is the analyst's, in characterize" in c


# ── route U ──────────────────────────────────────────────────────────────────

def test_route_u_builds_the_seed_and_opens_the_ladder(tmp_path):
    """Muskrat and mink from the raw table: the models art's engine ranks
    first, with the provenance in every .pre, the gate repeating it, and the
    guion going on from the raw entry."""
    import shutil
    shutil.copy(MM, tmp_path)
    _fn(M.load_data)("u_mm", str(tmp_path / "mink_muskrat.csv"))
    assert "Characterize the series first" in _fn(M.build_univariate)("u_mm")
    _fn(M.characterize)("u_mm", set="mink: lam=0")
    t = _fn(M.build_univariate)("u_mm")
    assert "mink: (0,0)  AR(2)" in t and "muskrat: (1,0)  AR(2)" in t
    assert "not reviewed in art" in t and "run_gate" in t
    pre = tmp_path / "mink_muskrat_sima" / "mink_u.pre"
    assert raw.PROVENANCE in pre.read_text()
    # the mean starts at the series' mean: not a unit root carrying the level
    s = M._sess.get("u_mm")
    phi, _theta, mu, _f = s.series[0].polynomials()
    assert abs(sum(phi)) < 0.8 and mu == pytest.approx(1079, abs=5)
    g = _fn(M.run_gate)("u_mm")
    assert "GATE: PASSED" in g and "not reviewed in art: mink, muskrat" in g
    assert "the analysts' models" not in g
    assert [e.node for e in s.guion.entries] == ["N0r", "N0c", "N0u", "N0", "N1"]
    assert "exist and are kept" in _fn(M.build_univariate)("u_mm")


def test_route_u_on_the_flour_prices(tmp_path):
    """Buffalo comes out a random walk (no parameters) in a five-way tie; the
    gate passes on it; the other two are the example's MA(1)s."""
    import shutil
    shutil.copy(FLOUR, tmp_path)
    _fn(M.load_data)("u_fl", str(tmp_path / "flour_prices.csv"))
    _fn(M.characterize)("u_fl")
    t = _fn(M.build_univariate)("u_fl")
    assert "Buffalo: (1,0)  WN" in t and "none (a random walk)" in t
    assert "Minneapolis: (1,0)  MA(1)" in t and "-0.2508" in t
    assert "GATE: PASSED" in _fn(M.run_gate)("u_fl")


# ── route V: the gas furnace, as Tiao and Box ────────────────────────────────

GAS = os.path.join(ROOT, "tests", "data", "gas_furnace.csv")


@pytest.fixture(scope="module")
def gas_v(tmp_path_factory):
    """Series J from the raw table, in levels (d = 0, lambda = 1), route V."""
    import shutil
    d = tmp_path_factory.mktemp("gas")
    shutil.copy(GAS, d)
    _fn(M.load_data)("v_gf", str(d / "gas_furnace.csv"), freq=1, start="1000")
    _fn(M.characterize)("v_gf", set="InputGasRate: d=0; CO2: lam=1, d=0")
    t = _fn(M.write_specs)("v_gf")
    return d, t


def test_route_v_opens_on_specifications(gas_v):
    d, t = gas_v
    assert "ROUTE V" in t and "No univariate models enter the system" in t
    assert raw.V_PROVENANCE in (d / "gas_furnace_sima" / "CO2_v.inp").read_text()
    g = _fn(M.run_gate)("v_gf")
    assert "GATE: PASSED" in g and "Route V: the files are specifications" in g
    assert "the analysts' models" not in g


def test_route_v_identification_is_tiao_and_box(gas_v):
    """M(l) from the raw table is their Table 12(b); method 2 is not read."""
    i = _fn(M.identify_matrices)("v_gf", nlags=11)
    assert "ROUTE V — the vector first" in i
    assert "METHOD 2 — not in route V" in i and "R_k(a):" not in i
    assert "1649.7" in i and "665.1" in i
    assert "(a) Tiao and Box's order: M(l) is significant up to l = 6" in i
    assert "cross AR of order" not in i


def test_route_v_full_var6(gas_v):
    """The full VAR(6) by exact ML: each series' own AR(6) with the cross
    terms; Tiao and Box's (5.6) phi_1 = 1.93, phi_2 = -1.20 for the input; the
    CO2 receives the gas at lag 3 (the delay); no feedback from CO2 to gas. It
    is close to the least-squares VAR(6) of the stepwise table."""
    from drvarma.identification_mv import stepwise_ar
    assert "route V has none" in _fn(M.estimate)("v_gf", 1, 1, cross="residual")
    e = _fn(M.estimate)("v_gf", 6, 0)
    assert "ROUTE V — the full VARMA(6,0)" in e
    s = M._sess.get("v_gf")
    L = s.fits[s.current]
    names = list(L.result.names)
    x = dict(zip(names, L.result.x))
    t = dict(zip(names, np.asarray(L.result.x) / np.asarray(L.result.std_errors)))
    assert x["phi_InputGasRate[B^1]"] == pytest.approx(1.93, abs=0.03)
    assert x["phi_InputGasRate[B^2]"] == pytest.approx(-1.20, abs=0.03)
    assert t["AR3[CO2<-InputGasRate]"] < -2.0
    assert all(abs(t[f"AR{k}[InputGasRate<-CO2]"]) < 2.0 for k in range(1, 7))
    data = np.genfromtxt(GAS, delimiter=",", skip_header=1)
    P = stepwise_ar(data, 6)["Phi_all"][5]          # LS, (l, i, j)
    assert x["phi_InputGasRate[B^1]"] == pytest.approx(P[0, 0, 0], abs=0.05)
    assert x["AR3[CO2<-InputGasRate]"] * 100 == pytest.approx(P[2, 1, 0] * 100, abs=5)


def test_route_v_yardstick_is_built_for_n5_only(gas_v):
    """The univariates come from route U's builder and never enter the system;
    the VAR(6) forecasts the CO2 better (the input helps), not the gas."""
    d, _t = gas_v
    ev = _fn(M.evaluate)("v_gf", 6, 0, 200, horizon=3)
    assert "ROUTE V: the yardstick is univariate models built by route U's builder" in ev
    assert (d / "gas_furnace_sima" / "CO2_u.pre").exists()
    s = M._sess.get("v_gf")
    cand, diag = list(s.evaluations.values())[-1]
    assert cand[("CO2", 3)]["RMSE"] < 0.8 * diag[("CO2", 3)]["RMSE"]
    assert all(f.endswith("_v.inp") for f in s.files)
