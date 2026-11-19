"""BUG-0019: the start is a path, not part of the model. The same start reuses
the fit and says so; another start optimises again and keeps the higher logL;
a fit below a model it nests, or one that stalled, is retried once from the
preliminary start. The real case (drvarma's stall on the monetary VAR) is
bugs/BUG-0019-repro; here the paths are checked on Jenkins and Alavi and the
guard on simulated fits."""
import tempfile
import types
import warnings

import pytest

import sima.mcp_server as M
from sima import session as S

_fn = lambda f: getattr(f, "fn", f)                      # noqa: E731


@pytest.fixture(scope="module")
def ja():
    warnings.simplefilter("ignore")
    _fn(M.load_example)("jenkins_alavi", session="b19", dest=tempfile.mkdtemp())
    _fn(M.run_gate)("b19")
    return "b19"


def test_the_same_start_reuses_and_says_so(ja):
    _fn(M.estimate)(ja, 1, 0)
    out = _fn(M.estimate)(ja, 1, 0)
    assert "PATH: this fit was already estimated" in out and "reused" in out


def test_another_start_optimises_again_and_reports_both(ja):
    out = _fn(M.estimate)(ja, 1, 0, start="preliminary")
    # Jenkins and Alavi's preliminary start is not admissible here: drvarma
    # falls back to zero and says why; the report carries it
    # the earlier start: zero, or the default (ols, with a drvarma that has
    # it) fallen back to zero -- the report names it either way
    assert 'PATH: start "' in out and 'the earlier start "zero' in out
    assert "reached logL" in out


def test_nesting():
    k1, k2 = M._key(1, 0), M._key(2, 0)
    assert M._nests(k1, k2) and not M._nests(k2, k1)
    assert M._nests(M._key(1, 0, diagcov=True), k2)
    assert not M._nests(M._key(1, 0), M._key(2, 0, diagcov=True))
    assert not M._nests(k1, M._key(2, 0, indices=(2, 1)))


class _Fake:
    def __init__(self, logL, nit, termcode, start):
        self.result = types.SimpleNamespace(logL=logL, nit=nit, termcode=termcode)
        self.start_used = start

    def fit(self):
        return self


def test_a_fit_below_its_nested_model_is_retried_from_the_preliminary_start(ja, monkeypatch):
    monkeypatch.setattr(M, "_best_start", lambda: "preliminary")   # drvarma 0.3.4
    s = S.get(ja)
    s.fits[M._key(1, 0)] = _Fake(-100.0, 50, 1, "zero")
    paths = {None: _Fake(-150.0, 2, 3, "zero"), "preliminary": _Fake(-98.0, 140, 2,
                                                                       "preliminary")}
    monkeypatch.setattr(M, "_model_ladder", lambda s, key, start=None, **k: paths[start])
    L, note = M._fit_paths(s, M._key(2, 0), "")
    assert L.result.logL == -98.0 and L.start_used == "preliminary"
    assert "THE FIRST PATH FAILED" in note and "lies BELOW" in note and "kept" in note
    assert "NOT AN OPTIMUM" not in note


def test_still_below_says_it_is_not_an_optimum(ja, monkeypatch):
    monkeypatch.setattr(M, "_best_start", lambda: "preliminary")
    s = S.get(ja)
    s.fits[M._key(1, 0)] = _Fake(-100.0, 50, 1, "zero")
    s.fits.pop(M._key(3, 0), None)
    paths = {None: _Fake(-150.0, 2, 3, "zero"), "preliminary": _Fake(-140.0, 20, 2,
                                                                       "preliminary")}
    monkeypatch.setattr(M, "_model_ladder", lambda s, key, start=None, **k: paths[start])
    L, note = M._fit_paths(s, M._key(3, 0), "")
    assert "NOT AN OPTIMUM" in note and "study_estimation" in note


def test_with_ols_it_is_the_default_and_the_retry(ja, monkeypatch):
    """A drvarma with start="ols" (> 0.3.4): sima starts there, and the guard
    retries from there; the echelon form keeps its own start."""
    monkeypatch.setattr(M, "_best_start", lambda: "ols")
    asked = []

    def ladder(s, key, start=None, **k):
        asked.append(start)
        return {"ols": _Fake(-98.0, 140, 1, "ols"), "zero": _Fake(-150.0, 2, 3, "zero"),
                "echelon": _Fake(-97.0, 40, 1, "echelon")}[start or "zero"]
    monkeypatch.setattr(M, "_model_ladder", ladder)
    s = S.get(ja)
    s.fits.pop(M._key(4, 0), None)
    L, note = M._fit_paths(s, M._key(4, 0), "")
    assert asked == ["ols"] and L.start_used == "ols" and not note
    # asked for zero explicitly, it stalls: the retry is from ols
    s.fits.pop(M._key(4, 0), None)
    asked.clear()
    L, note = M._fit_paths(s, M._key(4, 0), "zero")
    assert asked == ["zero", "ols"] and "Retried from the ols start" in note
    # the echelon form: no ols default
    asked.clear()
    M._fit_paths(s, M._key(0, 0, indices=(1, 1)), "")
    assert asked == [None]
