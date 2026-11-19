"""lag_order: the order of the VAR by LR on fitted models (VAR(0) .. VAR(pmax)),
Tiao and Box's M(l) beside it, AIC and BIC; the fits cached for estimate.
Jenkins and Alavi's muskrat and mink: VAR(1), as their paper."""
import tempfile
import warnings

import pytest

import sima.mcp_server as M
from sima import envelope as E
from sima import session as S

_fn = lambda f: getattr(f, "fn", f)                      # noqa: E731


@pytest.fixture(scope="module")
def ja():
    warnings.simplefilter("ignore")
    _fn(M.load_example)("jenkins_alavi", session="lo", dest=tempfile.mkdtemp(), lane="guided")
    _fn(M.run_gate)("lo")
    return "lo", _fn(M.lag_order)("lo", pmax=3)


def test_the_table_and_the_reading(ja):
    name, t = ja
    assert t.startswith("# N3 · The order of the VAR, by LR — VAR(0) to VAR(3)")
    for p in range(4):
        assert f"\n  {p:2d} " in t
    assert "By LR, the last significant step is VAR(1)" in t
    assert "M(l)" in t and "Wald" not in t.split("## 4")[0].split("## 1")[1]
    assert f'estimate(name="{name}", p=1, q=0)' in t and E.STOP in t


def test_the_fits_are_cached_and_estimate_reuses_them(ja):
    name, _ = ja
    s = S.get(name)
    assert all(M._key(p, 0) in s.fits for p in range(4))
    out = _fn(M.estimate)(name, 1, 0)
    assert "reused" in out


def test_the_guion_records_it(ja):
    name, _ = ja
    e = [e for e in S.get(name).guion.entries if e.tool == "lag_order"][-1]
    assert e.node == "N3" and "LR order 1" in e.evidence
