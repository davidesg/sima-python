"""The figures: presentation of the same numbers, returned INSIDE the answer
(as art and mtram) and written as PNG."""
import json
import os

import numpy as np
import pytest

from sima import mcp_server as M

DATA = os.path.join(os.path.dirname(__file__), "data", "m6")
PAIR = [os.path.join(DATA, "M6_EI.pre"), os.path.join(DATA, "M6_EP.pre")]


def _fn(tool):
    return getattr(tool, "fn", tool)


@pytest.fixture(scope="module")
def session():
    _fn(M.load_pre)("fig", json.dumps(PAIR))
    _fn(M.run_gate)("fig")
    _fn(M.estimate)("fig", 1, 0, False)
    return "fig"


def _check(out, tmp_path, name):
    kinds = [getattr(c, "type", None) for c in out]
    assert kinds == ["text", "image"], out
    assert out[1].mimeType == "image/png"
    p = tmp_path / name
    assert p.exists() and p.stat().st_size > 5000


@pytest.mark.parametrize("tool,kw,fname", [
    ("plot_impulse_response", {"horizon": 12, "ndraws": 100}, "irf.png"),
    ("plot_variance_decomposition", {"horizon": 12, "ndraws": 100}, "fevd.png"),
    ("plot_residual_ccf", {}, "ccf.png"),
    ("plot_forecast", {"horizon": 6}, "fc.png")])
def test_each_figure_comes_back_as_an_image(session, tmp_path, tool, kw, fname):
    out = _fn(getattr(M, tool))(session, path=str(tmp_path / fname), **kw)
    _check(out, tmp_path, fname)


def test_no_model_no_figure():
    _fn(M.load_pre)("fig0", json.dumps(PAIR))
    out = _fn(M.plot_impulse_response)("fig0")
    assert len(out) == 1 and "estimate" in str(out[0])


def test_fevd_bands_at_every_horizon():
    """The engine's per-horizon FEVD band (fevd_lo_h/hi_h) holds the point."""
    from drvarma.irf import fevd
    from drvarma.ladder import Ladder
    L = Ladder(PAIR, 1, 0)
    r = L.fit()
    b = L.irf_fevd_bands(8, ndraws=200)
    F = fevd(r.phi, r.theta, r.sigma, 8)
    assert b["fevd_lo_h"].shape == F.shape
    np.testing.assert_allclose(b["fevd_lo_h"][-1], b["fevd_lo"])
    assert np.all((F >= b["fevd_lo_h"] - 1e-9) & (F <= b["fevd_hi_h"] + 1e-9))
