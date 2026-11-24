"""BUG-0008: an own MA(1) that stops at the fold of the cast (theta = -1).

With a drvarma that casts each series with fue's flip (< 0.4.0), a regular
MA(1) with |theta| > 1 was read as 1/theta: the likelihood was symmetric
about |theta| = 1, its gradient vanished there and the optimiser stopped and
said "converged". sima read that fold itself.

drvarma 0.4.0 does not flip (its BUG-0030: the C's ladder never did, and the
port now follows it): there is no fold. The same fit -- the flour prices,
route V, the echelon form (1, 1, 1) -- ends on the joint MA's invertibility
wall, and sima says that. Where on the wall depends on the platform's
arithmetic; on Linux x86-64, where the C was run, it is the C's point. The reading of the fold stays
for the older engine, and stands down with this one.
"""
import platform
import sys
from types import SimpleNamespace as NS

import numpy as np
import pytest

from sima import evidence, mcp_server as M


def _fn(tool):
    return getattr(tool, "fn", tool)


def _series(name, ma=((0.0,),), ma_f=()):
    model = NS(ma=[list(f) for f in ma], ma_free=None, ma_f=list(ma_f))
    return NS(name=name, model=model)


def _result(values):
    return NS(names=list(values), x=np.array(list(values.values()), float))


def _flips():
    from drvarma.ladder import LadderSeries
    return hasattr(LadderSeries, "canonicalize")


def test_with_an_engine_that_does_not_flip_nothing_is_folded():
    if _flips():
        pytest.skip("this drvarma still flips (< 0.4.0)")
    ser = [_series("A")]
    assert evidence.folded_own_ma(ser, _result({"theta_A[B^1]": -1.0})) == []
    assert evidence.folded_own_ma(ser, _result({"theta_A[B^1]": -1.25})) == []


def test_the_fold_is_read_from_the_own_ma1_only(monkeypatch):
    from drvarma.ladder import LadderSeries
    if not _flips():                                     # the reading, as with the older engine
        monkeypatch.setattr(LadderSeries, "canonicalize", lambda self: False, raising=False)
    ser = [_series("A"), _series("B"), _series("C", ma=((0.0,), (0.0, 0.0))),
           _series("D", ma=(), ma_f=[NS(freq=0.25, free=True)])]
    r = _result({"theta_A[B^1]": -1.0, "theta_B[B^1]": 0.99999,
                 "theta1_C[B^1]": 0.3, "theta2_C[B^1]": -1.0, "theta2_C[B^2]": 0.1,
                 "thetaf_D[f=0.25]": -1.0, "MA1[A<-B]": -1.0})
    # an MA(2) factor does not fold, nor does a cross MA
    assert evidence.folded_own_ma(ser, r) == [("theta_A[B^1]", -1.0),
                                              ("theta_B[B^1]", 0.99999),
                                              ("thetaf_D[f=0.25]", -1.0)]
    inside = _result({"theta_A[B^1]": -0.999, "theta_B[B^1]": 0.5,
                      "thetaf_D[f=0.25]": 1.0})            # c2 = +1 is not the fold
    assert evidence.folded_own_ma(ser, inside) == []


pytest.importorskip("art", reason="the raw entry uses art's engine")


def test_estimate_does_not_call_the_wall_a_convergence(tmp_path):
    _fn(M.load_example)("lutkepohl_poskitt", session="fold", dest=str(tmp_path))
    _fn(M.characterize)("fold")
    _fn(M.build_univariate)("fold", overwrite=True, route="V")
    _fn(M.run_gate)("fold")
    t = _fn(M.estimate)("fold", indices="1, 1, 1")
    s = M._sess.get("fold")
    r = s.fits[s.current].result
    assert "converged" not in t
    if _flips():
        # the older engine: the fold on glibc, the wall on macOS (BUG-0008)
        folded = [n for n, _ in evidence.folded_own_ma(s.fits[s.current].series, r)]
        assert folded or r.ma_boundary > 0
        return
    # drvarma 0.4.0: no fold on any platform, and the fit is on the joint MA's
    # invertibility wall, said as such
    assert r.ma_boundary > 0 and "STOPPED AT THE MA INVERTIBILITY BOUNDARY" in t
    assert "STOPPED AT THE FOLD" not in t and "<- fold" not in t
    assert evidence.folded_own_ma(s.fits[s.current].series, r) == []
    # WHERE on the wall is the platform's. There is no interior maximum
    # there, so the point reached is the path's, and the path follows the
    # sixteenth digit of the compiler's and the C library's arithmetic:
    # measured on CI, -658.9552 on Linux, -659.2055 on Windows, -659.7980 on
    # macOS (sima 0.2.4, on the first route V's specifications). The C engine
    # was built and run on Linux x86-64, and there the port gives its number,
    # digit for digit. Since sima 0.2.5 route V goes through the gate, on the
    # univariate models sima's builder writes (with their means): drvarma
    # -route v -echelon 1,1,1 on those files gives -660.000819 after 206
    # iterations from zero, -665.062491 after 85 from the stage-II start.
    if not (sys.platform.startswith("linux") and platform.machine() in ("x86_64", "AMD64")):
        assert -662.0 < r.logL < -657.0
        return
    assert r.logL == pytest.approx(-660.000819, abs=1e-4) and r.nit == 206
    assert "TWO STARTS, TWO END POINTS" in t and "-665.06" in t
    # own MA coefficients beyond the unit circle are ordinary coordinates
    # here: what is judged is the system's MA operator, whole
    # (and drvarma >= 0.4.0 says so: own_ma_outside)
    at = dict(zip(r.names, r.x))
    assert at["theta_Buffalo[B^1]"] == pytest.approx(1.121785, abs=1e-4)
    assert at["theta_Minneapolis[B^1]"] == pytest.approx(-1.766582, abs=1e-4)
