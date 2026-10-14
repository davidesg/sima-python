"""The echelon form on route U: its own part is sima's (BUG-0003).

With indices, each row's free AR(n_i)/MA(n_i) replaces the univariate
model's regular ARMA, so `zeros` and `simplify` reach the own coefficients
as on route V. On the flour prices with art's models (a random walk and two
AR(1)), the echelon form (1, 1, 1) without its MA part is the VAR(1): the
same likelihood as route V's (the tutorial's -667.677245)."""
import json
import os

import pytest

from sima import mcp_server as M

DATA = os.path.join(os.path.dirname(__file__), "data", "flour_art")
NAMES = ("Buffalo", "Minneapolis", "KansasCity")
NO_MA = ", ".join([f"theta_{a}[B^1]" for a in NAMES]
                  + [f"MA1[{a}<-{b}]" for a in NAMES for b in NAMES if a != b])


def _fn(tool):
    return getattr(tool, "fn", tool)


@pytest.fixture(scope="module")
def flour():
    files = [os.path.join(DATA, f) for f in
             ("Buffalo_rw.pre", "Minneapolis_ar1.pre", "KansasCity_ar1.pre")]
    _fn(M.load_pre)("flu", json.dumps(files))
    assert "GATE: PASSED" in _fn(M.run_gate)("flu")
    return "flu"


def test_zeros_reach_the_own_part_of_the_echelon_form(flour):
    t = _fn(M.estimate)(flour, indices="1, 1, 1", zeros=NO_MA)
    assert "is a coefficient of a univariate model" not in t
    assert "theta_" not in t and "MA1[" not in t
    assert "phi_KansasCity[B^1]" in t
    assert "exact log-likelihood -667.6772" in t


def test_simplify_proposes_the_own_coefficients(flour):
    _fn(M.estimate)(flour, indices="1, 1, 1", zeros=NO_MA)
    s = _fn(M.simplify)(flour)
    assert "phi_KansasCity[B^1]" in s.split("to zero")[1].split("full")[0]


def test_without_indices_the_diagonal_is_still_arts(flour):
    t = _fn(M.estimate)(flour, 1, 0, zeros="phi_Minneapolis[B^1]")
    assert "is a coefficient of a univariate model" in t


def test_the_lr_is_against_the_model_without_cross_terms(flour):
    # BUG-0002: at (0, 0, 0) the LR has 3 df, the innovation covariances; the
    # univariates' AR(1) is not in it, so it is not against the univariates
    t = _fn(M.estimate)(flour, indices="0, 0, 0")
    lr = [ln for ln in t.splitlines() if "LR = " in ln]
    assert lr and "df = 3" in lr[0]
    assert all("(the univariates)" not in ln for ln in lr)
    assert "against the same model without cross terms" in lr[0]


def test_load_pre_does_not_count_the_placeholder(flour):
    # BUG-0001: the random walk carries fue's AR(1) fixed at 0.0
    t = _fn(M.load_pre)("flu_tbl", json.dumps(
        [os.path.join(DATA, "Buffalo_rw.pre"), os.path.join(DATA, "Minneapolis_ar1.pre")]))
    rows = {ln.split()[1]: ln for ln in t.splitlines() if ln.strip()[:1].isdigit()}
    assert "AR 0" in rows["Buffalo"] and "AR 1" in rows["Minneapolis"]
