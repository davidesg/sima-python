"""An own MA factor that ends outside the unit circle read alone (drvarma's
own_ma_outside, the C's and the port's, 23-nov-2026): sima says it and does
not call it a convergence. Muskrat and mink, VARMA(2,1), route U, from zero:
the optimiser stops (no lower point, termcode 3) with theta_MUSKRAT = 1.5483."""
import json
import os

import pytest

import sima.mcp_server as M
from sima import evidence

pytest.importorskip("drvarma")
from drvarma.ladder import Fit                       # noqa: E402

pytestmark = pytest.mark.skipif("own_ma_outside" not in Fit.__dataclass_fields__,
                                reason="needs a drvarma with own_ma_outside")

HERE = os.path.dirname(os.path.abspath(__file__))
JA = [os.path.join(HERE, "..", "examples", "jenkins_alavi", "art", f)
      for f in ("MUSKRAT_m03.pre", "MINK_m02.pre")]


def _fn(tool):
    return getattr(tool, "fn", tool)


def test_the_text_says_it():
    own = [("MUSKRAT", "regular MA", 1, "theta = 1.548284", 1.548284)]
    t = evidence.own_ma_outside_text(own)
    assert t.startswith("OWN MA FACTOR OUTSIDE THE UNIT CIRCLE, READ ALONE: MUSKRAT")
    assert "fue never estimates" in t and "Not a convergence" in t
    assert evidence.own_ma_outside_text([]) == ""


def test_estimate_does_not_call_it_a_convergence():
    _fn(M.load_pre)("own", json.dumps(JA))
    _fn(M.run_gate)("own")
    t = _fn(M.estimate)("own", 2, 1, start="zero")
    s = M._sess.get("own")
    r = s.fits[s.current].result
    if not r.own_ma_outside:
        pytest.skip("this platform's optimiser does not end there from zero")
    assert "OWN MA FACTOR OUTSIDE THE UNIT CIRCLE, READ ALONE: MUSKRAT" in t
    if r.termcode in (1, 2):           # the gradient's stop: not called a convergence
        assert "stopped with an own MA factor outside the unit circle" in t
    head = t.split("OWN MA FACTOR")[0].lower().split("optimiser:")[-1]
    assert "converged" not in head
    assert "not a model to read" in t
