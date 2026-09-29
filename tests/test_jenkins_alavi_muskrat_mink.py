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
