"""The third identification form: the echelon VARMA on route V
(drvarma docs/ECHELON_PLAN.md §2.3) -- identify_echelon and
estimate(indices=). A simulated system with known indices (1, 0):

    y1 = .6 y1(-1) + a1 + .4 a1(-1) + .3 a2(-1)
    y2 = .5 (y1 - a1) + a2

i.e. A_0 = [[1, 0], [-.5, 1]]: y2 has no dynamics of its own, only a
contemporaneous term on y1."""
import re

import numpy as np
import pytest

from sima import mcp_server as M


def _fn(tool):
    return getattr(tool, "fn", tool)


@pytest.fixture(scope="module")
def ech(tmp_path_factory):
    from drvarma import echelon as E
    from drvarma.datasets import simulate_varma
    A = np.zeros((2, 2, 2)); Mm = np.zeros((2, 2, 2))
    A[0] = [[1.0, 0.0], [-0.5, 1.0]]
    A[1] = [[-0.6, 0.0], [0.0, 0.0]]
    Mm[0] = A[0]
    Mm[1] = [[0.4, 0.3], [0.0, 0.0]]
    phi, theta = E.standard(A, Mm)
    y = simulate_varma(phi=phi, theta=theta, sigma=np.array([[1.0, 0.3], [0.3, 1.0]]),
                       n=400, burnin=300, seed=21, freq=1).data + 50.0
    d = tmp_path_factory.mktemp("ech")
    path = d / "ech10.csv"
    np.savetxt(path, y, delimiter=",", header="y1,y2", comments="", fmt="%.10f")
    _fn(M.load_data)("e10", str(path), freq=1, start="1000")
    _fn(M.characterize)("e10", set="y1: lam=1, d=0; y2: lam=1, d=0")
    _fn(M.write_specs)("e10")
    assert "GATE: PASSED" in _fn(M.run_gate)("e10")
    return d


def test_identify_echelon_finds_the_indices(ech):
    t = _fn(M.identify_echelon)("e10", max_index=2)
    assert "Chosen by SC: y1 1, y2 0" in t
    assert 'estimate(name="e10", indices="1, 0")' in t
    assert "order of the series is part of the form" in t
    g = M._sess.get("e10").guion.entries[-1]
    assert "identify_echelon" in str(g)


def test_identify_echelon_says_its_sample(ech):
    """BUG-0005: max_index moves the common sample; the report says on how many."""
    for k in (1, 2):
        t = _fn(M.identify_echelon)("e10", max_index=k)
        m = re.search(r"T = (\d+) of the (\d+) observations", t)
        assert m, t
        assert f"max_index = {k}" in t
        assert int(m.group(2)) - int(m.group(1)) >= k


def test_estimate_fits_the_echelon_form(ech):
    e = _fn(M.estimate)("e10", indices="1, 0")
    assert "ROUTE V — the ECHELON FORM with Kronecker indices (y1 1, y2 0)" in e
    assert "ESTIMATED: echelon form, Kronecker indices (1, 0)" in e
    s = M._sess.get("e10")
    assert s.current[6] == (1, 0)
    L = s.fits[s.current]
    assert L.start_used.startswith("echelon")
    x = dict(zip(L.result.names, L.result.x))
    se = dict(zip(L.result.names, L.result.std_errors))
    assert abs(x["AR0[y2<-y1]"] - 0.5) < 3 * se["AR0[y2<-y1]"]
    assert abs(x["phi_y1[B^1]"] - 0.6) < 3 * se["phi_y1[B^1]"]
    assert [n for n in L.result.names if "<-" in n] == ["AR0[y2<-y1]", "MA1[y1<-y2]"]
    # the specs: y1 with a free AR(1)/MA(1), y2 with none
    assert [x.orders() for x in L.series] == [(1, 1), (0, 0)]


def test_the_tools_after_estimate_know_the_form(ech):
    _fn(M.estimate)("e10", indices="1, 0")
    st = _fn(M.structure)("e10")
    assert "y1 -> y2" in st                    # AR0[y2<-y1] is y1 entering y2
    ev = _fn(M.evaluate)("e10", estwin=300, horizon=2, indices="1, 0")
    assert "THE YARDSTICK — ECHELON (1, 0) (full cov)" in ev
    sim = _fn(M.simplify)("e10", t=50.0)       # everything cross is |t| < 50
    assert 'indices="1, 0"' in sim


def test_what_is_refused(ech):
    assert "give 2, one per series" in _fn(M.estimate)("e10", indices="1")
    assert "leave them at 0" in _fn(M.estimate)("e10", 2, 2, indices="1, 0")
    assert "not a list of integers" in _fn(M.estimate)("e10", indices="one, zero")


def test_a_seasonal_row_factor_on_route_u():
    """Route U with seasonal models (the IPC .pre files: AR(3) x annual AR(1),
    AR(1), annual AR(1)): the annual factors multiply their whole rows
    (drvarma echelon stage 4), and estimate checks them by the LR against
    the same rows with the factor's restriction dropped, which starts at
    the fit's own likelihood."""
    import json
    import os
    d = os.path.join(os.path.dirname(__file__), "data")
    _fn(M.load_pre)("ipc_e", json.dumps([os.path.join(d, f"IPC_{c}_ext.pre")
                                         for c in ("DE", "ES", "FR")]))
    assert "GATE: PASSED" in _fn(M.run_gate)("ipc_e")
    t = _fn(M.identify_echelon)("ipc_e")
    assert "the search ran on each row filtered by them" in t
    assert "IPC_DE, IPC_FR" in t
    assert "pass 1: (" in t and "factors of the univariate models" in t
    e = _fn(M.estimate)("ipc_e", indices="1, 1, 1")
    assert "factors of IPC_DE, IPC_FR multiply their whole rows" in e
    assert "THE ROW FACTOR'S CHECK" in e
    s = M._sess.get("ipc_e")
    L = s.fits[s.current]
    assert "Phi_IPC_DE[B^12]" in L.result.names and "phi_IPC_DE[B^2]" not in L.result.names
    ft = L.factor_check
    assert ft["logL_start"] == pytest.approx(ft["logL"], abs=1e-5)
    assert ft["df"] > 0 and ft["lr"] >= -1e-6
    assert any(g.tool == "factor_test" for g in s.guion.entries)
