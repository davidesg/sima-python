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
def test_level_responses_and_the_permanent_effect(ja):
    from drvarma.irf import oirf
    L = M._current(S.get(ja))
    r = L.result
    diffs = responses.differences(L)
    O = oirf(r.phi, r.theta, r.sigma, 8)
    Ol, lo, hi, info = responses.responses(L, 8, None, levels=True)
    exp = np.stack([responses.undo(O[:, i, :], *diffs[i]) for i in range(O.shape[1])], axis=1)
    assert np.allclose(Ol, exp) and lo is None and info["levels"]
    # the level converges to the permanent effect where d = 1 (D = 0)
    Olong, *_ = responses.responses(L, 400, None, levels=True)
    pe = info["permanent"]
    for i, (d, D, _s) in enumerate(diffs):
        if d == 1 and D == 0:
            assert np.allclose(Olong[-1, i], pe[i], atol=1e-6)
        elif d == 0 and D == 0:
            assert np.allclose(pe[i], 0.0)
    b = L.irf_fevd_bands(8, ndraws=60)
    Ol, lo, hi, info = responses.responses(L, 8, b, levels=True, ndraws=60)
    assert np.all(lo <= Ol + 1e-9) and np.all(Ol <= hi + 1e-9)
    j = 1
    Os, lo, hi, info2 = responses.responses(L, 8, b, levels=True, scale=(j, 25.0), ndraws=60)
    c = 25.0 / Ol[0, j, j]
    assert Os[0, j, j] == pytest.approx(25.0)
    assert np.allclose(Os[:, :, 0], Ol[:, :, 0])                    # other shocks: 1 s.d.
    assert np.allclose(info2["permanent"][:, j], info["permanent"][:, j] * c, equal_nan=True)
    t = _fn(M.impulse_response)(ja, horizon=6, ndraws=60, levels=True, scale="MINK=1")
    assert "IMPULSE RESPONSE OF THE LEVEL" in t and "STEP response" in t
    assert "PERMANENT EFFECT" in t and "  inf" in t
    assert "SCALED: the shock to MINK" in t and "Units:" in t
    t = _fn(M.impulse_response)(ja, horizon=4, bands=False)
    assert "IMPULSE RESPONSE OF THE DIFFERENCES" in t and "dies out" in t
    assert "not one of the series" in _fn(M.impulse_response)(ja, scale="XX=1")


def test_undo_each_difference():
    x = np.array([1.0, 0.5, 0.25, 0.0, 0.0])
    assert np.allclose(responses.undo(x, 0, 0, 12), x)
    assert np.allclose(responses.undo(x, 1, 0, 12), np.cumsum(x))
    assert np.allclose(responses.undo(x, 2, 0, 12), np.cumsum(np.cumsum(x)))
    assert np.allclose(responses.undo(x, 0, 1, 2), [1.0, 0.5, 1.25, 0.5, 1.25])


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


def test_the_permanent_effect_keeps_box_and_jenkins_signs():
    """Phi(B) = I - phi_1 B - ..., Theta(B) = I - theta_1 B - ... (drvarma and its
    siblings): Psi(1) P must be the long sum of drvarma's own oirf, with an MA."""
    from drvarma.irf import oirf
    phi = np.array([[[0.5, 0.1], [0.2, 0.3]], [[-0.1, 0.0], [0.05, 0.1]]])
    theta = np.array([[[0.4, -0.2], [0.1, -0.3]]])
    sigma = np.array([[1.0, 0.3], [0.3, 2.0]])
    long = oirf(phi, theta, sigma, 600).sum(axis=0)
    pe = responses.permanent(phi, theta, sigma, [(1, 0, 12), (1, 0, 12)])
    assert np.allclose(pe, long, atol=1e-8)
    # the other sign would not do
    assert not np.allclose(responses.permanent(phi, -theta, sigma, [(1, 0, 12)] * 2), long)
