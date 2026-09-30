"""Jenkins and Alavi (1981) on their own data: muskrat and mink.

What they publish, and sima reproduces from the ladder: the prewhitened
correlation at lag 0 (0.42 +- 0.13; here 0.38 on 1850-1911), the lag-1 cross
correlations with the predator-prey signs (more muskrat -> more mink next
year; more mink -> fewer muskrat), an MA(1) residual model from method 2, a
cross AR of order 2 from method 1 (their (5.9)), and fitted cross terms with
the signs of their Lotka-Volterra reading (5.10).
"""
import json
import os

import numpy as np
import pytest

from sima import mcp_server as M

D = os.path.join(os.path.dirname(__file__), "data", "muskrat_mink")
F = [os.path.join(D, "muskrat.pre"), os.path.join(D, "mink.pre")]


def _fn(tool):
    return getattr(tool, "fn", tool)


@pytest.fixture(scope="module")
def session():
    _fn(M.load_pre)("mm", json.dumps(F))
    _fn(M.run_gate)("mm")
    return "mm"


def test_their_identification(session):
    from sima import evidence
    s = M._sess.get(session)
    L = M._diagonal(s)
    _mu, _p, _t, _q, W, _i = L.cast(L.result.x)
    res = L.result.residuals
    txt, facts = evidence.ja_identification(W, res, ["muskrat", "mink"], 6, 2, 1)
    assert 0.3 < np.corrcoef(res.T)[0, 1] < 0.5                       # theirs 0.42
    assert facts["method2_q"] == 1
    assert sorted(facts["links"]) == ["mink<-muskrat", "muskrat<-mink"]
    assert "k= 1  . - | + ." in txt                                    # the predator-prey signs
    assert facts["method1_p"] == 2                                     # their (5.9): AR(2)


def test_the_fitted_cross_terms_tell_their_story(session):
    from drvarma.ladder import Ladder
    r = Ladder(F, 2, 0).fit()
    x = dict(zip(r.names, r.x))
    assert x["AR1[muskrat<-mink]"] < 0 < x["AR1[mink<-muskrat]"]        # predation / food
    ma = Ladder(F, 0, 1, cross="residual").fit()
    y = dict(zip(ma.names, ma.x))
    assert y["MA1[muskrat<-mink]"] > 0 > y["MA1[mink<-muskrat]"]        # I - Theta B convention
    assert r.ma_boundary == 0 and ma.ma_boundary == 0


@pytest.mark.parametrize("method", [1, 2])
def test_their_identification_figure(session, tmp_path, method):
    """plot_identification: R_k | S_k by pair, as an image, recorded at N2."""
    p = tmp_path / f"ident{method}.png"
    out = _fn(M.plot_identification)(session, method=method, path=str(p))
    assert [getattr(c, "type", None) for c in out] == ["text", "image"]
    assert p.exists() and p.stat().st_size > 5000
    last = M._sess.get(session).guion.entries[-1]
    assert (last.node, last.tool) == ("N2", "plot_identification")


def test_the_figures_facts_in_the_text(session, tmp_path):
    """plot_identification's text carries what the terse figure does not: per
    side, the bars beyond the band, the cut-off and the isolated lags —
    method 2: the predator-prey pair at lag 1 on both sides, cut-off after 1."""
    out = _fn(M.plot_identification)(session, method=2, path=str(tmp_path / "f.png"))
    t = out[0].text
    assert "r(0) = +0.38 (outside)" in t
    assert "k > 0 (mink leads): +1 -0.36  —  cut-off after 1" in t
    assert "k < 0 (muskrat leads): -1 +0.35, -5 +0.27  —  cut-off after 1; isolated: 5" in t
    assert "S*(21) = 45.7" in t
    t1 = _fn(M.plot_identification)(session, method=1, path=str(tmp_path / "g.png"))[0].text
    assert "pccf: k > 0 (mink leads): +1 -0.64, +2 +0.32" in t1 and "cut-off after 2" in t1


def test_the_report_is_arts(session, tmp_path):
    """As art: 1 · TABLE (a block to show as it is), 2 · WHAT IT SHOWS,
    3 · CONCLUSIONS, 4 · DECISION with the calls, the pause; then the figure."""
    out = _fn(M.plot_identification)(session, method=2, path=str(tmp_path / "r.png"))
    t = out[0].text
    heads = ["## 1 · TABLE", "## 2 · WHAT IT SHOWS", "## 3 · CONCLUSIONS",
             "## 4 · DECISION"]
    assert [t.index(h) for h in heads] == sorted(t.index(h) for h in heads)
    assert "AS IT IS" in t and "⏸" in t
    assert "   0    +0.38*" in t and "  +1    -0.36*    -0.39*" in t
    assert 'estimate(name="mm", p=0, q=1' in t and 'estimate(name="mm", p=2, q=0' in t
    assert out[1].type == "image"


def test_their_table_viii_on_48_observations(session):
    """§6.3: the models refitted on 48 observations (their 1848-1895, here
    1850-1897). The univariate V(l) is theirs to within half a point (their
    25.6 38.6 40.8 and 25.9 31.8 32.9), and the cross AR lowers it."""
    _fn(M.estimate)(session, 2, 0, False, links="muskrat<-mink, mink<-muskrat",
                    start="preliminary")
    t = _fn(M.forecast_uncertainty)(session, horizon=3, estwin=48)
    assert "Refitted on the first 48 observations (to 1897" in t
    row = [l.split() for l in t.splitlines() if l.strip().startswith("1 ")][0]
    uni_m, mod_m, uni_k, mod_k = (float(v.rstrip("*")) for v in row[1:5])
    assert abs(uni_m - 25.6) < 0.6 and abs(uni_k - 25.9) < 0.6
    assert mod_m < uni_m and mod_k < uni_k
