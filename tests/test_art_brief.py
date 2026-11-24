"""N0a — art_brief: the brief for building each series' univariate model in
art (decided 22-nov-2026: route V's univariate models with art, one series
after another, with two biases: objetivo="multivariante", and a pure AR
unless the MA is very clear, as an instruction to the agent)."""
import json
import os
import shutil

import pytest

import sima.mcp_server as M

pytest.importorskip("art", reason="the raw entry uses art's engine")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, "examples", "lutkepohl_poskitt", "data", "flour_prices.csv")
ART = os.path.join(ROOT, "tests", "data", "flour_art")


def _fn(tool):
    return getattr(tool, "fn", tool)


@pytest.fixture(scope="module")
def brief(tmp_path_factory):
    d = tmp_path_factory.mktemp("brief")
    csv = shutil.copy(CSV, d)
    _fn(M.load_data)("ab", csv, lane="autonomous")
    assert "Characterize the series first" in _fn(M.art_brief)("ab")
    _fn(M.characterize)("ab")
    return d, csv, _fn(M.art_brief)("ab")


def test_the_brief_says_the_cost_and_one_after_another(brief):
    _d, _csv, t = brief
    assert t.startswith("ART'S AUTONOMOUS LANE, ONE SERIES AFTER ANOTHER (3 series, "
                        "never in parallel)")
    assert "for 3 series about 6-12 minutes and 315,000-432,000 tokens" in t


def test_the_common_rules_are_given_once(brief):
    t = brief[2]
    for rule in ("protocolo_autonomo()", 'modo="autonomo"', 'objetivo="multivariante"',
                 "prefer a pure AR over an ARMA or MA unless the MA is very clear",
                 "In a tie, estimate both", "after two reformulations"):
        assert t.count(rule) == 1, rule


def test_each_series_has_its_load_and_its_characterization(brief):
    d, csv, t = brief
    for nm in ("Buffalo", "Minneapolis", "KansasCity"):
        folder = os.path.join(str(d), "flour_prices_art", nm)
        assert f"SERIES {nm} (" in t and f"folder {folder}" in t
        assert (f'load_data(source_path="{csv}", output_inp="{folder}/{nm}.inp", '
                f'column="{nm}", freq=12, start_year=1972, start_period=8)') in t
    assert t.count("lambda 0, d 1, no seasonality detected") == 3
    assert ('load_pre(name="ab", paths_json=<the 3 .pre files, in this order: Buffalo, '
            'Minneapolis, KansasCity>, route="V")') in t


def test_it_is_in_the_guion_and_load_pre_goes_on_with_it(brief):
    from sima import session as S
    r = S.get_raw("ab")
    e = [x for x in r.guion.entries if x.tool == "art_brief"][-1]
    assert e.node == "N0a" and e.args["lane"] == "autonomous"
    files = [os.path.join(ART, f) for f in
             ("Buffalo_rw.pre", "Minneapolis_ar1.pre", "KansasCity_ar1.pre")]
    _fn(M.load_pre)("ab", json.dumps(files), route="V")
    tools = [x.tool for x in S.get("ab").guion.entries]
    assert tools.index("art_brief") < tools.index("load_pre")
    assert "characterize" in tools


def test_the_guided_lane_gets_the_guided_brief(tmp_path):
    csv = shutil.copy(CSV, tmp_path)
    _fn(M.load_data)("abg", csv)
    _fn(M.characterize)("abg")
    t = _fn(M.art_brief)("abg")
    assert t.startswith("ART'S GUIDED LANE") and "the analyst decides each node" in t
    assert "(A proposal to the analyst.)" in t and 'modo="autonomo"' not in t
