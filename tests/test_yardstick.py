"""Route V's yardstick (BUG-0004): N5 names the univariate models it measures
against, and takes the analyst's.

On the flour prices the light builder takes, inside art's tie, an MA(1) for
Minneapolis; the analyst's model in art is an AR(1). Against the light one
Lutkepohl and Poskitt's restricted VAR(1) gains at h = 1 (RMSE 7.035 vs 7.478,
0.941); against the AR(1), on the same window, it does not (7.046)."""
import json
import os
import shutil

import pytest

from sima import mcp_server as M

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, "examples", "lutkepohl_poskitt", "data", "flour_prices.csv")
ART = os.path.join(ROOT, "tests", "data", "flour_art")
FILES = [os.path.join(ART, f) for f in
         ("Buffalo_rw.pre", "Minneapolis_ar1.pre", "KansasCity_ar1.pre")]
Z = ("phi_KansasCity[B^1], AR1[Buffalo<-KansasCity], "
     "AR1[Minneapolis<-KansasCity], AR1[KansasCity<-Buffalo]")
pytest.importorskip("art", reason="the raw entry uses art's engine")


def _fn(tool):
    return getattr(tool, "fn", tool)


def _row(out, name):
    return next(ln.split() for ln in out.splitlines() if ln.split()[:2] == [name, "1"])


@pytest.fixture(scope="module")
def flour(tmp_path_factory):
    d = tmp_path_factory.mktemp("yard")
    _fn(M.load_data)("yard", shutil.copy(CSV, d))
    _fn(M.characterize)("yard", set="Buffalo: lam=0, d=1; Minneapolis: lam=0, d=1; "
                                    "KansasCity: lam=0, d=1")
    _fn(M.write_specs)("yard")
    assert "GATE: PASSED" in _fn(M.run_gate)("yard")
    return "yard"


def test_the_light_yardstick_is_named_with_its_tie(flour):
    out = _fn(M.evaluate)(flour, 1, 0, estwin=72, horizon=6, zeros=Z)
    assert "Minneapolis    ARIMA(0,1,1)  — MA(1), the first of art's tie:" in out
    assert "evaluate(yardstick=...)" in out
    assert _row(out, "Minneapolis")[3:5] == ["7.035", "7.478"]


def test_the_analysts_yardstick(flour):
    out = _fn(M.evaluate)(flour, 1, 0, estwin=72, horizon=6, zeros=Z,
                          yardstick=json.dumps(FILES))
    assert "the yardstick is the analyst's univariate models" in out
    assert "Minneapolis    ARIMA(1,1,0)" in out and "Buffalo        ARIMA(0,1,0)" in out
    assert _row(out, "Minneapolis")[3:5] == ["7.035", "7.046"]
    # it stays for the session
    again = _fn(M.evaluate)(flour, 1, 0, estwin=72, horizon=6, zeros=Z)
    assert "the analyst's univariate models" in again


def test_a_yardstick_that_does_not_fit_is_refused(flour):
    out = _fn(M.evaluate)(flour, 1, 0, estwin=72, horizon=6, yardstick=json.dumps(FILES[:2]))
    assert out.startswith("The yardstick was not taken: the yardstick takes one file per series")
