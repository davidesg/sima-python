"""The autonomous trial run of 25-nov-2026 (the US monetary VAR from raw data,
univariate models built in art with art_brief): what it found in sima.

(n) record_decision could not record the raw entry's nodes before load_pre;
(o) characterize and canonical_analysis offered the retired write_specs and not
art_brief; (p) the figures travelled as images and opened windows in the
autonomous lane; (q) art_brief did not say how interventions are specified;
(m) an argument a tool does not take was ignored in silence.
"""
import asyncio
import os
import tempfile
import warnings

import pytest

import sima.mcp_server as M
from sima import session as S

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLOUR = os.path.join(ROOT, "examples", "flour_prices", "data", "flour_prices.csv")
_fn = lambda f: getattr(f, "fn", f)                      # noqa: E731


# (n) ------------------------------------------------------------------------
def test_record_decision_in_the_raw_entry_goes_on_after_load_pre():
    _fn(M.load_data)("ta_raw", FLOUR, lane="autonomous")
    _fn(M.characterize)("ta_raw")
    t = _fn(M.record_decision)("ta_raw", "N0c", "keep the characterization",
                               reason="r", decided_by="LLM")
    assert t.startswith("Recorded as step")
    g = S.get_raw("ta_raw").guion
    assert [e.tool for e in g.entries][-1] == "record_decision"


# (o) ------------------------------------------------------------------------
def test_the_raw_menus_offer_art_brief_and_not_write_specs():
    _fn(M.load_data)("ta_menu", FLOUR)
    c = _fn(M.characterize)("ta_menu")
    k = _fn(M.canonical_analysis)("ta_menu")
    for t in (c, k):
        assert 'art_brief(name="ta_menu")' in t
        assert 'build_univariate(name="ta_menu", route="V")' in t
        assert "write_specs" not in t


# (q) ------------------------------------------------------------------------
def test_art_brief_says_how_interventions_are_specified():
    _fn(M.load_data)("ta_brief", FLOUR)
    _fn(M.characterize)("ta_brief")
    b = _fn(M.art_brief)("ta_brief", out_dir=tempfile.mkdtemp())
    assert "suggest_intervention_form" in b and "LEVELS" in b
    assert "a spike in the differences is a step" in b
    assert "only with your reason written" in b
    assert "<SERIES>_mNN" in b


# (p) ------------------------------------------------------------------------
@pytest.fixture(scope="module")
def auto():
    warnings.simplefilter("ignore")
    _fn(M.load_example)("jenkins_alavi", session="ta_auto", dest=tempfile.mkdtemp(),
                        lane="autonomous")
    _fn(M.run_gate)("ta_auto")
    _fn(M.estimate)("ta_auto", 1, 0)
    return "ta_auto"


def _images(out):
    return [c for c in out if getattr(c, "type", None) == "image"]


def test_no_figures_returned_in_the_autonomous_lane(auto, monkeypatch):
    monkeypatch.delenv("SIMA_FIGURES", raising=False)
    out = _fn(M.plot_impulse_response)(auto, horizon=4, bands=False)
    text = "\n".join(getattr(c, "text", c) for c in out if not _images([c]))
    assert not _images(out) and "not returned nor opened" in text
    png = [ln.split("PNG: ", 1)[1] for ln in text.splitlines() if ln.startswith("PNG: ")][0]
    assert os.path.exists(png)                                   # still written
    out = _fn(M.check_residuals)(auto)
    assert not _images(out)
    monkeypatch.setenv("SIMA_FIGURES", "1")
    assert _images(_fn(M.plot_impulse_response)(auto, horizon=4, bands=False))


def test_figures_returned_in_the_guided_lane(monkeypatch):
    monkeypatch.delenv("SIMA_FIGURES", raising=False)
    warnings.simplefilter("ignore")
    _fn(M.load_example)("jenkins_alavi", session="ta_guided", dest=tempfile.mkdtemp(),
                        lane="guided")
    _fn(M.run_gate)("ta_guided")
    _fn(M.estimate)("ta_guided", 1, 0)
    assert _images(_fn(M.plot_impulse_response)("ta_guided", horizon=4, bands=False))
    monkeypatch.setenv("SIMA_FIGURES", "0")
    assert not _images(_fn(M.plot_impulse_response)("ta_guided", horizon=4, bands=False))


# (m) ------------------------------------------------------------------------
def test_an_unknown_argument_is_refused_by_name():
    from mcp.server.fastmcp.exceptions import ToolError
    with pytest.raises(ToolError, match="levelz"):
        asyncio.run(M.mcp.call_tool("impulse_response", {"name": "x", "levelz": True}))
    with pytest.raises(ToolError, match="bogus"):
        asyncio.run(M.mcp.call_tool("rank_test", {"name": "x", "bogus": 1}))
