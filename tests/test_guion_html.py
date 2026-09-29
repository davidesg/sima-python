"""The HTML guion: art's look, the path node by node, the decisions and the
figures, which are saved next to the data so the page travels with them."""
import json
import os
import shutil

from sima import mcp_server as M

DATA = os.path.join(os.path.dirname(__file__), "data", "m6")


def _fn(tool):
    return getattr(tool, "fn", tool)


def test_export_guion_writes_a_page_with_steps_decisions_and_figures(tmp_path):
    pair = []
    for f in ("M6_EI.pre", "M6_EP.pre"):
        shutil.copy(os.path.join(DATA, f), tmp_path)
        pair.append(str(tmp_path / f))
    _fn(M.load_pre)("gh", json.dumps(pair))
    _fn(M.run_gate)("gh")
    _fn(M.identify_cross)("gh")
    _fn(M.estimate)("gh", 1, 0, False, "EI leads EP", "EP<-EI")
    _fn(M.record_decision)("gh", "N3", "keep the restricted candidate",
                           reason="one link carries the lead", evidence="LR p 0.02",
                           alternatives="p = 1 on both pairs", decided_by="analyst")
    _fn(M.plot_impulse_response)("gh", horizon=8, ndraws=60)
    txt = _fn(M.export_guion)("gh")
    html = tmp_path / "M6_EI.sima.html"
    assert f"HTML: {html}" in txt and html.exists()
    page = html.read_text(encoding="utf-8")
    for part in ("<h2>The path</h2>", "N1 — the diagonal gate", "N3 — estimation of a candidate",
                 "keep the restricted candidate -- because one link carries the lead",
                 "decided by: analyst", "Set aside:</b> p = 1 on both pairs",
                 "<img src='figs/sima_gh_irf.png'"):
        assert part in page, part
    assert (tmp_path / "figs" / "sima_gh_irf.png").exists()
    assert (tmp_path / "M6_EI.sima.json").exists()
