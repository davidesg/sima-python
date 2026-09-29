"""Restricted cross terms in sima: identify_cross proposes the pairs, estimate
and evaluate take them (drvarma Ladder(links=), the C's -links)."""
import glob
import json
import os

from sima import mcp_server as M

DATA = os.path.join(os.path.dirname(__file__), "data", "m6")
M6 = sorted(glob.glob(os.path.join(DATA, "*.pre")))
PAIR = [os.path.join(DATA, "M6_EI.pre"), os.path.join(DATA, "M6_EP.pre")]


def _fn(tool):
    return getattr(tool, "fn", tool)


def test_identify_cross_proposes_the_pairs_that_showed_something():
    _fn(M.load_pre)("L1", json.dumps(M6))
    _fn(M.run_gate)("L1")
    txt = _fn(M.identify_cross)("L1")
    assert '(d) the same orders on the pairs that showed something only:' in txt
    assert 'links = "EU<-EA, EP<-EC, EC<-EP, EP<-EI, EI<-P"' in txt
    assert "5 of 30 pairs" in txt


def test_estimate_with_links_carries_only_those_pairs():
    _fn(M.load_pre)("L2", json.dumps(PAIR))
    _fn(M.run_gate)("L2")
    txt = _fn(M.estimate)("L2", 1, 0, False, "EI leads EP", "EP<-EI")
    assert "cross links: EP<-EI (the other pairs carry no cross dynamics)" in txt
    assert "AR1[EP<-EI]" in txt and "AR1[EI<-EP]" not in txt
    assert "df = 2" in txt                         # one AR link + the covariance
    g = _fn(M.export_guion)("L2", save=False)
    assert "EP<-EI" in g


def test_evaluate_the_restricted_candidate():
    _fn(M.load_pre)("L3", json.dumps(PAIR))
    _fn(M.run_gate)("L3")
    txt = _fn(M.evaluate)("L3", 1, 0, 50, 4, False, "EP<-EI")
    assert "links EP<-EI" in txt


def test_bad_links_are_refused_in_words():
    _fn(M.load_pre)("L4", json.dumps(PAIR))
    _fn(M.run_gate)("L4")
    assert "does not name two different series" in _fn(M.estimate)("L4", 1, 0, False, "", "EP<-XX")


def test_estimate_with_the_preliminary_start():
    _fn(M.load_pre)("L5", json.dumps(PAIR))
    _fn(M.run_gate)("L5")
    txt = _fn(M.estimate)("L5", 1, 0, False, "", "", "preliminary")
    assert "cross terms started at preliminary" in txt
    assert "'start': 'preliminary'" in _fn(M.export_guion)("L5", save=False) or \
           "start=preliminary" in _fn(M.export_guion)("L5", save=False)


def test_estimate_in_the_residual_model_form():
    _fn(M.load_pre)("L6", json.dumps(PAIR))
    _fn(M.run_gate)("L6")
    txt = _fn(M.estimate)("L6", 0, 1, False, "", "", "zero", "residual")
    assert "residual-model form (Jenkins-Alavi 3.22)" in txt
    txt2 = _fn(M.estimate)("L6", 0, 1, False, "", "", "zero", "additive")
    assert "residual-model form" not in txt2
    assert len(M._sess.get("L6").fits) == 2                    # two candidates
