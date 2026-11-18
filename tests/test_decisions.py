"""P4 -- the decisions as data: pending, closed, adopted, set aside.

A tool that ends in a decision leaves it pending with its options; the call
that takes one closes it and notes which; adopt and abandon mark what the
analysis keeps and what it set aside; the final-stage tools warn when they
act on a model that is not the adopted one. The guion loads keys it does not
know (a newer sima's), as art's does.
"""
import json
import tempfile
import warnings

import pytest

import sima.mcp_server as M
from sima import decisions as D
from sima import guion as G
from sima import session as S

_fn = lambda f: getattr(f, "fn", f)                      # noqa: E731


@pytest.fixture(scope="module")
def ja():
    warnings.simplefilter("ignore")
    _fn(M.load_example)("jenkins_alavi", session="dec", dest=tempfile.mkdtemp(),
                        lane="guided")
    _fn(M.run_gate)("dec")
    return "dec"


def _last(name, tool):
    return [e for e in S.get(name).guion.entries if e.tool == tool][-1]


def test_a_decision_is_left_pending_with_its_options(ja):
    _fn(M.identify_cross)(ja)
    e = _last(ja, "identify_cross")
    assert e.status == "pending" and e.proposal
    assert e.proposal[0].startswith('estimate(name="dec"')
    assert e in S.get(ja).guion.pending()


def test_the_call_that_takes_an_option_closes_it_and_says_which(ja):
    e = _last(ja, "identify_cross")
    letter = "ABCDEF"[[c.split("(")[0] for c in e.proposal].index("estimate")]
    _fn(M.estimate)(ja, 1, 0)                 # option A: p = 1, q = 0
    assert e.status == "closed" and e.chosen == letter
    assert e.closed_by == _last(ja, "estimate").n


def test_record_decision_on_the_node_closes_it(ja):
    est = _last(ja, "estimate")
    assert est.status == "pending"
    out = _fn(M.record_decision)(ja, node="N3", decision="go on", reason="LR p 0.01")
    assert est.status == "closed" and est.chosen == "recorded"
    assert "not one of sima's nodes" not in out


def test_an_unknown_node_is_recorded_and_said(ja):
    out = _fn(M.record_decision)(ja, node="N9", decision="x", reason="y")
    assert "not one of sima's nodes" in out


def test_adopt_and_the_warning_of_the_final_tools(ja):
    assert "Say why" in _fn(M.adopt)(ja, model="current")
    out = _fn(M.adopt)(ja, model="p = 1, q = 0", why="gains at h 1-3")
    assert out.startswith("Adopted")
    s = S.get(ja)
    assert s.adopted[0] == "VARMA" and s.adopted[1] == s.current
    assert _last(ja, "adopt").status == "adopted"
    assert not str(_fn(M.forecast)(ja, 6)).startswith("⚠")        # the adopted one
    _fn(M.estimate)(ja, 0, 0)                                       # another, current now
    f = _fn(M.forecast)(ja, 6)
    assert f.startswith("⚠ This acts on the CURRENT model")
    _fn(M.adopt)(ja, model="univariates", why="no gain where it matters")
    assert _fn(M.forecast)(ja, 6).startswith("⚠ The analysis ADOPTED THE UNIVARIATES")


def test_an_ambiguous_or_unknown_model_is_refused_with_the_list(ja):
    out = _fn(M.adopt)(ja, model="covariance", why="x")
    assert out.startswith("Cannot adopt") and "several models match" in out
    assert "p = 0, q = 0" in out and "p = 1, q = 0" in out
    assert "no fitted model" in _fn(M.adopt)(ja, model="p = 7", why="x")


def test_abandon_marks_a_dead_end(ja):
    out = _fn(M.abandon)(ja, model="p = 0, q = 0", why="no cross dynamics: the diagonal")
    assert out.startswith("Set aside")
    assert _last(ja, "abandon").status == "dead-end"
    assert "not set aside" in _fn(M.abandon)(ja, model="univariates", why="x")


def test_the_guion_shows_the_status_and_the_open_decisions(ja):
    txt = S.get(ja).guion.render()
    assert "status: ADOPTED" in txt and "status: set aside" in txt
    assert "status: decided -- option" in txt
    html = G.render_html(S.get(ja).guion)
    assert "ADOPTED" in html and "set aside" in html


def test_a_newer_guion_still_loads(tmp_path):
    p = tmp_path / "g.sima.json"
    p.write_text(json.dumps({"name": "x", "files": [], "entries": [
        {"n": 1, "node": "N0", "tool": "load_pre", "args": {}, "evidence": "",
         "status": "pending", "a_field_from_the_future": 1}]}))
    g = G.load(str(p))
    assert g.entries[0].status == "pending"


def test_matching_ignores_placeholders():
    assert D._matches('adopt(name="a", model="current", why="...")',
                      {"name": "a", "model": "current", "why": "it gains"})
    assert not D._matches('estimate(name="a", p=1, q=0)', {"name": "a", "p": 2, "q": 0})
    # an option that is not a single call (an expression, prose) never matches,
    # and never breaks the tool that answers (the VEC's options have some)
    assert not D._matches("rank_test(name='a') + job_result", {"name": "a"})
    assert not D._matches("art (outside sima)", {})
