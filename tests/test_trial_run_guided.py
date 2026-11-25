"""The guided trial run of 25-nov-2026 (the US monetary VAR, 1990-2007, FF):
what it found in sima, each fixed and held here.

(a) the UNITS line named a remedy the files already had; (b, l) figures and
guion went into the first series' folder; (c) no figure reached the desktop's
viewer; (d) a pair's P discounted the univariate operators; (f) simplify printed
the coefficients in the engine's units; (g) no cumulated, scaled responses;
(h) one IRF scale per row flattened the cross responses; (j) after adopt, the
structure menu offered only evaluate; (k) hand_over said "None recorded"; (l) a
failed call stayed in the guion.
"""
import os
import tempfile
import warnings

import numpy as np
import pytest

import sima.mcp_server as M
from sima import evidence, figures, responses, scale, session as S, status, viewer
from sima.guion import Guion

_fn = lambda f: getattr(f, "fn", f)                      # noqa: E731


@pytest.fixture(scope="module")
def ja():
    warnings.simplefilter("ignore")
    _fn(M.load_example)("jenkins_alavi", session="trial", dest=tempfile.mkdtemp(),
                        lane="guided")
    _fn(M.run_gate)("trial")
    _fn(M.estimate)("trial", 1, 0)
    return "trial"


# (a) ------------------------------------------------------------------------
def test_units_names_what_differs():
    only_lam = scale.units_note({"IPI": (0.0, 100.0), "FF": (1.0, 100.0)})
    assert "do not share one lambda" in only_lam
    assert "A common factor" not in only_lam and "nothing to change in the files" in only_lam
    only_fac = scale.units_note({"A": (0.0, 100.0), "B": (0.0, 1.0)})
    assert "one rescaling factor (" in only_fac and "A common factor" in only_fac


# (b, l) ----------------------------------------------------------------------
def test_the_session_has_its_own_folder_beside_the_files(tmp_path):
    a, b = tmp_path / "art" / "IPI" / "IPI.pre", tmp_path / "art" / "FF" / "FF.pre"
    g = Guion("mon", files=[str(a), str(b)])
    assert g.folder() == str(tmp_path / "art" / "sima_mon")
    assert g.path() == str(tmp_path / "art" / "sima_mon" / "mon.sima.json")
    assert g.figures_dir() == str(tmp_path / "art" / "sima_mon" / "figs")
    g.save()
    assert os.path.exists(g.path())


# (c) -------------------------------------------------------------------------
def test_the_viewer_keys():
    assert not viewer.should_open(False, "posix", {}, False)              # a script
    assert viewer.should_open(False, "posix", {"SIMA_VIEWER": "1"}, False)
    assert not viewer.should_open(False, "posix", {}, True)                # pytest
    assert not viewer.should_open(False, "posix", {"SIMA_NO_VIEWER": "1"}, False)
    assert not viewer.should_open(True, "nt", {}, False)                   # Windows host
    assert viewer.should_open(True, "nt", {"SIMA_VIEWER": "1"}, False)
    assert viewer.should_open(True, "posix", {}, False)


# (d) -------------------------------------------------------------------------
def test_a_pairs_p_discounts_the_system_orders(ja):
    L = M._current(S.get(ja))
    assert figures.residual_npq(L) == L.p + L.q == 1


# (g) -------------------------------------------------------------------------
def test_cumulated_and_scaled_responses(ja):
    from drvarma.irf import oirf
    L = M._current(S.get(ja))
    r = L.result
    O = oirf(r.phi, r.theta, r.sigma, 8)
    Oc, lo, hi, info = responses.responses(L, 8, None, cumulative=True)
    assert np.allclose(Oc, np.cumsum(O, axis=0)) and lo is None and info["cumulative"]
    b = L.irf_fevd_bands(8, ndraws=60)
    Oc, lo, hi, info = responses.responses(L, 8, b, cumulative=True, ndraws=60)
    assert np.all(lo <= Oc + 1e-9) and np.all(Oc <= hi + 1e-9)
    j = 1
    Os, lo, hi, info = responses.responses(L, 8, b, scale=(j, 25.0), ndraws=60)
    assert Os[0, j, j] == pytest.approx(25.0)
    assert np.allclose(Os[:, :, 0], O[:, :, 0])                     # other shocks: 1 s.d.
    assert np.all(lo[:, :, j] <= hi[:, :, j])
    t = _fn(M.impulse_response)(ja, horizon=6, ndraws=60, cumulative=True, scale="MINK=1")
    assert "CUMULATED responses" in t and "SCALED: the shock to MINK" in t and "Units:" in t
    assert "not one of the series" in _fn(M.impulse_response)(ja, scale="XX=1")


# (h) -------------------------------------------------------------------------
def test_each_irf_panel_fits_its_own_values():
    assert figures._panel_limit(np.array([0.0, 0.061]))[0] == (-0.08, 0.08)
    assert figures._panel_limit(np.array([0.61]))[0] == (-0.8, 0.8)
    assert figures._panel_limit(np.array([0.0]), None, None)[0] == (-1.0, 1.0)


# (j) -------------------------------------------------------------------------
def test_structure_menu_after_adoption_offers_the_hand_over():
    pair = {"label": "B -> A", "lr": 9.0, "df": 1, "p": 0.003}
    f = {"desc": "p = 1", "alpha": 0.05, "pairs": [pair], "orders": [], "pre": [],
         "adopted": True}
    assert 'hand_over(name="x")' in evidence.structure_report(f, "x")
    f["adopted"] = False
    t = evidence.structure_report(f, "x")
    assert "evaluate(...)" in t and "hand_over" not in t


# (k) -------------------------------------------------------------------------
def test_hand_over_lists_what_was_read_off_a_fit_not_adopted(ja):
    _fn(M.impulse_response)(ja, horizon=4, bands=False)
    _fn(M.record_decision)(ja, "N4", "diagnosis accepted", reason="r",
                           caveat="MINK keeps a residual correlation at lag 10")
    _fn(M.adopt)(ja, model="univariates", why="no gain where it matters")
    h = _fn(M.hand_over)(ja)
    assert "None recorded" not in h
    assert "were read off p = 1, q = 0, full covariance, which is NOT the adopted model" in h
    assert "rest on the Cholesky order MUSKRAT → MINK" in h
    assert "MINK keeps a residual correlation at lag 10" in h


# (l) -------------------------------------------------------------------------
def test_a_failed_call_leaves_no_step(ja, monkeypatch):
    s = S.get(ja)
    n = len(s.guion.entries)

    def boom(*a, **k):
        raise RuntimeError("no figure")
    monkeypatch.setattr(figures, "residual_ccf_figure", boom)
    with pytest.raises(RuntimeError):
        _fn(M.check_residuals)(ja)         # through the lane wrapper
    assert len(s.guion.entries) == n
