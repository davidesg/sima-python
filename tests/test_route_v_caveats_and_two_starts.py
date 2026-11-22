"""The hand-over's caveats on route V, and two starts for a VARMA with MA.

Route V's files are specifications by design: the hand-over says what the
route leaves open (no validated base until N5, the yardstick's origin), not
that "its univariate model was not validated" -- there is none. characterize's
outliers, modelled nowhere, are listed. And a VARMA with q > 0 is estimated
from two starts, the higher kept, the report saying whether they agree
(several maxima: Jenkins and Alavi's VARMA(2,1))."""
import os
import shutil
import types
import warnings

import pytest

import sima.mcp_server as M
from sima import session as S
from sima import status as ST

_fn = lambda f: getattr(f, "fn", f)                      # noqa: E731
GAS = os.path.join(os.path.dirname(__file__), "data", "gas_furnace.csv")


@pytest.fixture(scope="module")
def gas_v(tmp_path_factory):
    warnings.simplefilter("ignore")
    d = tmp_path_factory.mktemp("gasv")
    shutil.copy(GAS, d)
    _fn(M.load_data)("cv_gas", str(d / "gas_furnace.csv"), freq=1, start="1000")
    _fn(M.characterize)("cv_gas", set="InputGasRate: d=0; CO2: lam=1, d=0")
    _fn(M.write_specs)("cv_gas")
    _fn(M.run_gate)("cv_gas")
    _fn(M.estimate)("cv_gas", 1, 0)
    return "cv_gas"


def test_route_v_hand_over_names_the_route_and_the_yardstick(gas_v):
    cv = ST.caveats(S.get(gas_v))
    text = "\n".join(cv)
    assert "Route V (the vector first, Tiao and Box)" in text
    assert "built by sima's route U builder" in text and "evaluate(yardstick=" in text
    assert "its univariate model was not validated in art" not in text


def test_characterize_outliers_are_carried_to_the_caveats(gas_v, monkeypatch):
    r = S.get_raw("cv_gas")
    monkeypatch.setattr(r, "chars", [dict(c, outliers=[("1012", 4.2)]) if i == 0 else c
                                     for i, c in enumerate(r.chars)])
    text = "\n".join(ST.caveats(S.get(gas_v)))
    assert f"{r.names[0]}: characterize flagged 1 outlier(s) (1012)" in text
    assert "they stay in the system's dynamics" in text


class _Fake:
    def __init__(self, logL, start):
        self.result = types.SimpleNamespace(logL=logL, nit=40, termcode=1)
        self.start_used = start
        self.start = start

    def fit(self):
        return self


def _session_with(monkeypatch, fits):
    monkeypatch.setattr(M, "_model_ladder",
                        lambda s, key, start=None, **k: fits[start or "zero"])
    return types.SimpleNamespace(fits={}, route="U")


def test_two_starts_two_maxima_keeps_the_higher_and_says_so(monkeypatch):
    monkeypatch.setattr(M, "_best_start", lambda: "ols")
    s = _session_with(monkeypatch, {"ols": _Fake(-545.0, "ols"),
                                    "zero": _Fake(-547.9, "zero")})
    L, note = M._fit_paths(s, M._key(2, 1), "")
    assert L.result.logL == -545.0 and "TWO STARTS, TWO MAXIMA" in note


def test_two_starts_that_agree_say_so(monkeypatch):
    monkeypatch.setattr(M, "_best_start", lambda: "ols")
    s = _session_with(monkeypatch, {"ols": _Fake(-551.38, "ols"),
                                    "zero": _Fake(-551.38, "zero")})
    _L, note = M._fit_paths(s, M._key(1, 1), "")
    assert "two starts" in note and "reach the same optimum" in note


def test_no_second_start_without_ma_or_when_asked(monkeypatch):
    monkeypatch.setattr(M, "_best_start", lambda: "ols")
    asked = []
    monkeypatch.setattr(M, "_model_ladder",
                        lambda s, key, start=None, **k: asked.append(start) or _Fake(-1.0, start or "zero"))
    s = types.SimpleNamespace(fits={}, route="U")
    M._fit_paths(s, M._key(2, 0), "")                       # no MA: one start
    M._fit_paths(s, M._key(1, 1), "zero")                   # a start asked: that one
    assert asked == ["ols", "zero"]
