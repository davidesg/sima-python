"""The engine's route V (drvarma 0.4.0, the C's -route v): the univariate
models go through the gate as on route U, and past it each series' regular
ARMA is replaced by a free AR(p)/MA(q). In sima: load_pre(route="V"). The
session's files, the yardstick and the deterministic terms are the
univariates'. (The first route V, write_specs, was retired in 0.2.5.)"""
import glob
import json
import os

import pytest

import sima.mcp_server as M
from sima import status

pytest.importorskip("drvarma")
from drvarma.ladder import Ladder          # noqa: E402

pytestmark = pytest.mark.skipif(
    "route" not in Ladder.__init__.__code__.co_varnames,
    reason="needs drvarma >= 0.4.0 (route='v')")

HERE = os.path.dirname(os.path.abspath(__file__))
JA = sorted(glob.glob(os.path.join(HERE, "..", "examples", "jenkins_alavi", "art",
                                   "*.pre")))
assert len(JA) == 2, "the muskrat and mink models of examples/jenkins_alavi/art"


def _fn(tool):
    return getattr(tool, "fn", tool)


@pytest.fixture(scope="module")
def v():
    t = _fn(M.load_pre)("rv", json.dumps(JA), route="V")
    g = _fn(M.run_gate)("rv")
    return t, g


def test_the_load_says_the_route_and_keeps_the_univariate_files(v):
    t, g = v
    s = M._sess.get("rv")
    assert s.route == "V" and not s.v and M._engine_v(s)
    assert [os.path.basename(f) for f in s.files] == ["MINK_m02.pre", "MUSKRAT_m03.pre"]
    assert "ROUTE V: the univariate models go through the gate as on route U" in t
    assert "Route V (the engine's): this gate is the same as route U's" in g
    assert "specifications with no ARMA" not in g          # that is the first route V
    n0 = [x for x in s.guion.entries if x.tool == "load_pre"][-1]
    assert n0.args["route"] == "V" and "(route V)" in n0.evidence


def test_estimate_is_the_engines_route_v(v):
    e = _fn(M.estimate)("rv", 2, 0)
    s = M._sess.get("rv")
    L = s.fits[s.current]
    assert L.route == "v"
    R = Ladder(JA, 2, 0, route="v")
    R.fit()
    assert L.result.logL == pytest.approx(R.result.logL, abs=1e-6)
    assert L.result.logL == pytest.approx(-568.8555, abs=1e-3)
    assert "ROUTE V — the full VARMA(2,0) through the gate" in e
    assert "replaced by a free AR(2)/MA(0)" in e
    assert "against the same model without cross terms" in e
    # the engine's warnings: an order below a univariate's is said, not banned
    assert "⚠ MINK's univariate model has a regular AR(4): this model, with p = 2" in e
    assert "⚠ MUSKRAT's univariate model has a regular MA(1)" in e
    # the own coefficients are the vector's
    assert "phi_MINK[B^1]" in L.result.names and "phi_MUSKRAT[B^2]" in L.result.names


def test_the_diagonal_model_is_the_same_on_both_routes(v):
    """p = q = 0: no vector part; the engine's route V needs p or q, and the
    model is the univariates' with a free covariance."""
    e = _fn(M.estimate)("rv", 0, 0)
    assert "ROUTE V" not in e
    s = M._sess.get("rv")
    U = Ladder(JA, 0, 0)
    U.fit()
    assert s.fits[s.current].result.logL == pytest.approx(U.result.logL, abs=1e-6)


def test_an_own_lag_can_be_held_at_zero_on_route_v_and_not_on_u(v):
    e = _fn(M.estimate)("rv", 2, 0, zeros="phi_MINK[B^2]")
    s = M._sess.get("rv")
    L = s.fits[s.current]
    assert "phi_MINK[B^2]" not in L.result.names and "phi_MINK[B^1]" in L.result.names
    assert "ROUTE V" in e
    _fn(M.load_pre)("ru", json.dumps(JA))
    _fn(M.run_gate)("ru")
    assert "on route U the diagonal is art's" in _fn(M.estimate)("ru", 2, 0, zeros="phi_MINK[B^2]")


def test_the_yardstick_is_the_sessions_univariates(v):
    _fn(M.estimate)("rv", 2, 0)
    t = _fn(M.evaluate)("rv", 2, 0, 50, 4)
    assert "RMSE" in t
    assert "ROUTE V: the yardstick is" not in t            # the first route V's text
    assert "there is nothing to give" in _fn(M.evaluate)("rv", 2, 0, 50, 4, yardstick=json.dumps(JA))


def test_the_caveats_are_route_us_plus_one_line(v):
    s = M._sess.get("rv")
    c = status.caveats(s)
    assert any(x.startswith("Route V (the vector first, through the gate)") for x in c)
    assert not any("built on specifications" in x for x in c)


def test_the_echelon_form_on_the_engines_route_v(v):
    e = _fn(M.estimate)("rv", indices="1, 1")
    s = M._sess.get("rv")
    L = s.fits[s.current]
    assert L.route == "v" and s.current[6] == (1, 1)
    assert "ROUTE V — the ECHELON FORM with Kronecker indices (MINK 1, MUSKRAT 1)" in e


def test_route_u_is_the_default_and_a_bad_route_is_refused():
    assert 'route: "U"' in _fn(M.load_pre)("rx", json.dumps(JA), route="W")
    _fn(M.load_pre)("rd", json.dumps(JA))
    s = M._sess.get("rd")
    assert s.route == "U" and not M._engine_v(s)
    _fn(M.run_gate)("rd")
    e = _fn(M.estimate)("rd", 2, 0)
    assert s.fits[s.current].route == "u" and "ROUTE V" not in e
