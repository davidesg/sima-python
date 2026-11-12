"""BUG-0008: an own MA(1) that stops at the fold of the cast (theta = -1).

fue's cast reads a regular MA(1) with |theta| > 1 as 1/theta, so the
likelihood is symmetric about |theta| = 1 and its gradient vanishes there: the
optimiser stops and says "converged". With free cross MA terms the joint MA
need not be on the wall (ma_boundary 0), so sima reads the fold itself.
The case: the flour prices, route V, the echelon form (1, 1, 1).
"""
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


def test_the_fold_is_read_from_the_own_ma1_only():
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


def test_estimate_does_not_call_the_fold_a_convergence(tmp_path):
    _fn(M.load_example)("lutkepohl_poskitt", session="fold", dest=str(tmp_path))
    _fn(M.characterize)("fold")
    _fn(M.write_specs)("fold", overwrite=True)
    _fn(M.run_gate)("fold")
    t = _fn(M.estimate)("fold", indices="1, 1, 1")
    s = M._sess.get("fold")
    r = s.fits[s.current].result
    # The engine's own stop is the platform's: termcode 1 with ma_boundary 0 on
    # glibc, termcode 3 with the joint MA on the wall (ma_boundary 2) on macOS.
    # The flat likelihood at the fold leaves it to the last bits. What sima
    # must do is the same on every platform: read the fold and not call it
    # a convergence.
    assert [n for n, _ in evidence.folded_own_ma(s.fits[s.current].series, r)] == \
        ["theta_Minneapolis[B^1]", "theta_KansasCity[B^1]"]
    assert "STOPPED AT THE FOLD OF AN OWN MA(1)" in t
    assert "converged" not in t
    assert "Next: evaluate" not in t and "(study_estimation)" in t
    for nm in ("theta_Minneapolis", "theta_KansasCity"):
        row = next(ln for ln in t.splitlines() if ln.strip().startswith(nm + "[B^1]"))
        assert row.rstrip().endswith("<- fold") and "*" not in row
    # an own MA(1) inside keeps its inference
    row = next(ln for ln in t.splitlines() if ln.strip().startswith("phi_Buffalo[B^1]"))
    assert row.rstrip().endswith("*")
