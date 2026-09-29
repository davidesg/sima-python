"""Jenkins and Alavi's checking (§5.2): check_residuals."""
import json
import os

import numpy as np

from sima import evidence, mcp_server as M

DATA = os.path.join(os.path.dirname(__file__), "data", "m6")
PAIR = [os.path.join(DATA, "M6_EI.pre"), os.path.join(DATA, "M6_EP.pre")]


def _fn(tool):
    return getattr(tool, "fn", tool)


def test_a_planted_joint_shock_is_found_on_the_transformed_residuals():
    """Two residual series correlated at lag 0 (rho 0.8): a shock of OPPOSITE
    sign, 1.8 s.d. in each, is extreme in neither alone, but is (about 5.7) in
    the transformed residual of the difference — Jenkins and Alavi's butter
    price and purchases at 1971(2)."""
    rng = np.random.default_rng(4)
    Sig = np.array([[1.0, 0.8], [0.8, 1.0]])
    a = rng.standard_normal((200, 2)) @ np.linalg.cholesky(Sig).T
    a[60] = [1.8, -1.8]
    txt, facts = evidence.ja_checking(a, Sig, ["A", "B"], 6, 1, lambda t: (1900 + t, 1))
    line = txt.split("a*_2")[1].split("\n")[0]
    assert "1960 (" in line
    assert "the largest: 1960" in txt
    assert facts["large"] >= 1


def test_the_tool():
    _fn(M.load_pre)("ck", json.dumps(PAIR))
    _fn(M.run_gate)("ck")
    assert "estimate" in _fn(M.check_residuals)("ck")          # no model yet
    _fn(M.estimate)("ck", 1, 0, False)
    txt = _fn(M.check_residuals)("ck")
    for part in ("(1) Large residuals", "(2) Residual correlation matrices", "(3) Portmanteau matrix"):
        assert part in txt
    assert "check_residuals" in _fn(M.export_guion)("ck", save=False)


def test_forecast_uncertainty_table():
    _fn(M.load_pre)("fu", json.dumps(PAIR))
    _fn(M.run_gate)("fu")
    assert "Cannot compute" in _fn(M.forecast_uncertainty)("fu")      # no model yet
    _fn(M.estimate)("fu", 1, 0, False)
    txt = _fn(M.forecast_uncertainty)("fu", 6)
    assert "Table VIII" in txt and "univariate" in txt
    rows = [l for l in txt.splitlines() if l.strip()[:1].isdigit()]
    assert [int(r.split()[0]) for r in rows] == [1, 2, 3, 6]
