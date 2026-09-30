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
    ("plot_forecast", {"horizon": 6, "series": "all"}, "fc.png"),
    ("plot_forecast", {"horizon": 6, "series": "EP"}, "fc_ep.png")])
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


def test_forecast_one_figure_per_series_by_default(session, tmp_path):
    out = _fn(M.plot_forecast)(session, horizon=6, path=str(tmp_path))
    assert [getattr(c, "type", None) for c in out] == ["text", "image"] * 2
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "sima_fig_forecast_EI.png", "sima_fig_forecast_EP.png"]


def test_forecast_unknown_series():
    _fn(M.load_pre)("figx", json.dumps(PAIR))
    _fn(M.run_gate)("figx")
    _fn(M.estimate)("figx", 0, 0, True)
    out = _fn(M.plot_forecast)("figx", series="XX")
    assert "No series named 'XX'" in str(out[0])


def test_identification_pairs_with_three_series(tmp_path, trio_json):
    """Three series: all three pairs by default, `pairs` draws only those asked,
    and an unknown pair is refused with the names."""
    from sima import figures
    _fn(M.load_pre)("fig3", trio_json)
    _fn(M.run_gate)("fig3")
    out = _fn(M.plot_identification)("fig3", method=2, pairs="IPC_ES-IPC_FR",
                                     path=str(tmp_path / "one.png"))
    _check(out, tmp_path, "one.png")
    assert "Unknown pair" in str(_fn(M.plot_identification)("fig3", pairs="IPC_ES-XX")[0])
    s = M._sess.get("fig3")
    L = M._diagonal(s)
    fig = figures.identification_figure(L.result.residuals, M._names(s), 12, 2, 12)
    assert sum(a.get_visible() for a in fig.axes) == 6                      # 3 pairs x (R_k over S_k), 2 per row: 8, 2 hidden
    assert fig.axes[0].get_xlabel().startswith("S* ( 25 ) = ")    # between the panels
    assert fig.axes[2].get_xlabel() == ""                         # nothing under S_k
    assert "given the other series" in out[0].text                # said in the text


def test_portmanteau_lags_leave_degrees_of_freedom():
    """The legacy lags move up to leave at least 2 beyond the parameters: in
    annual data a long model (muskrat's AR(6)MA(1): 7) would leave none with
    GraphMaker's 7 lags, and 2 with fug's 9. Never beyond n - 2."""
    from sima.figures import MIN_DF_LAGS, q_lags
    assert MIN_DF_LAGS == 2
    assert q_lags(7, 7, 61) == 9 and q_lags(7, 8, 61) == 10
    assert q_lags(9, 7, 61) == 9 and q_lags(24, 3, 200) == 24
    assert q_lags(7, 20, 15) == 13
