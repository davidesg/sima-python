"""The two packages (sima.package), after the autonomous trial run of
25/26-nov-2026: sima was unbalanced against art's lanes in how it packs the
information. The univariate base comes as one package at the gate and stops
in BOTH lanes (the checkpoint); the hand-over shows the models first, then the
yardstick, what the model says, the decisions, the caveats and the record,
and the HTML guion opens with it.
"""
import hashlib
import json
import os
import shutil
import tempfile
import warnings

import pytest

import sima.mcp_server as M
from sima import envelope as E
from sima import package as P
from sima import session as S
from sima import status
from sima.guion import NODES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "examples", "jenkins_alavi", "art")
_fn = lambda f: getattr(f, "fn", f)                      # noqa: E731


def _files(tmp):
    """The example's two .pre in their own folders, each with an art guion
    beside it (as art writes it): MUSKRAT adopted and clean, MINK delivered
    with a failed Q."""
    out = []
    for stem, ver, q in (("MUSKRAT_m03", 7, True), ("MINK_m02", 4, False)):
        d = os.path.join(tmp, stem.split("_")[0])
        os.makedirs(d)
        pre = os.path.join(d, stem + ".pre")
        shutil.copy(os.path.join(ART, stem + ".pre"), pre)
        sha = hashlib.sha256(open(pre, "rb").read()).hexdigest()
        g = {"series": stem, "carril": "autonomo", "entries": [
            {"version": ver - 1, "inp_path": pre[:-4] + "_x.inp", "status": "dead-end"},
            {"version": ver, "inp_path": pre[:-4] + ".inp", "out_path": pre[:-4] + ".out",
             "status": "adopted", "why_adopted": f"why {stem}", "pre_sha": sha,
             "stats": {"sigma_a": 0.3, "q_pass": q, "q_pvalues": [0.2 if q else 0.01],
                       "jb_pass": True, "n_extreme": 0}}]}
        json.dump(g, open(os.path.join(d, "guion.json"), "w"))
        out.append(pre)
    return out


def _load(name, lane, checkpoint=None):
    warnings.simplefilter("ignore")
    tmp = tempfile.mkdtemp()
    files = _files(tmp)
    _fn(M.load_pre)(name, json.dumps(files), lane=lane, checkpoint=checkpoint)
    return files


# --------------------------------------------------------------------------- #
#  A · the univariate base                                                     #
# --------------------------------------------------------------------------- #

def test_the_gate_packs_the_models_and_stops_in_the_autonomous_lane():
    _load("pk_auto", "autonomous")
    t = _fn(M.run_gate)("pk_auto")
    assert "# N1 · The univariate base" in t
    for part in ("### The univariate models", "### The gate", "### What the system is built on",
                 "MUSKRAT", "MINK", "AR(", "Box-Jenkins notation", "GATE: PASSED",
                 "the order (Cholesky, normalisation): MUSKRAT → MINK"):
        assert part in t, part
    assert "version 7 of MUSKRAT/guion.json, adopted" in t
    assert "why art kept it: why MUSKRAT_m03" in t
    assert "MINK: art delivered it with a diagnosis caveat" in t
    # the checkpoint stays: the lane filter does not replace it
    assert t.rstrip().endswith(P.CHECKPOINT)
    assert "Autonomous lane." not in t and E.STOP not in t
    s = S.get("pk_auto")
    assert [e.node for e in s.guion.pending()] == ["N1"]
    # going on closes it with the option taken
    _fn(M.identify_cross)("pk_auto")
    assert not s.guion.pending() or s.guion.pending()[0].node != "N1"


def test_checkpoint_false_skips_it_and_the_hand_over_says_so():
    _load("pk_skip", "autonomous", checkpoint=False)
    t = _fn(M.run_gate)("pk_skip")
    assert P.CHECKPOINT not in t and "Autonomous lane." in t
    h = _fn(M.hand_over)("pk_skip")
    assert "checkpoint at the univariate base was skipped" in h


def test_the_guided_lane_stops_at_the_checkpoint_too():
    _load("pk_guided", "guided")
    assert P.CHECKPOINT in _fn(M.run_gate)("pk_guided")


def test_a_file_edited_after_art_is_said():
    files = _load("pk_edit", "guided")
    with open(files[0], "a") as fh:
        fh.write("\n")
    line, cav = P.provenance(S.get("pk_edit").series[0])
    assert "EDITED after art wrote it" in line and cav == "edited after art wrote it"


def test_no_art_guion_no_invented_history():
    warnings.simplefilter("ignore")
    _fn(M.load_example)("jenkins_alavi", session="pk_plain", dest=tempfile.mkdtemp())
    line, cav = P.provenance(S.get("pk_plain").series[0])
    assert "no art guion beside it" in line and cav is None


def test_n0a_is_a_node():
    assert "N0a" in NODES


# --------------------------------------------------------------------------- #
#  C · the hand-over                                                           #
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def closed():
    _load("pk_close", "autonomous")
    _fn(M.run_gate)("pk_close")
    _fn(M.estimate)("pk_close", 1, 0)
    _fn(M.record_decision)("pk_close", "N3", "VAR(1)", reason="the CCFs at lag 1",
                           decided_by="LLM")
    _fn(M.adopt)("pk_close", "current", why="for the test")
    _fn(M.impulse_response)("pk_close", horizon=8, bands=False, levels=True,
                            scale="MINK=1")
    _fn(M.variance_decomposition)("pk_close", horizon=8, bands=False)
    return "pk_close"


def test_the_hand_over_shows_the_models_first(closed):
    h = _fn(M.hand_over)(closed)
    order = ["## 1 · The models", "### The univariate models", "### The system adopted",
             "## 2 · The yardstick", "## 3 · What the model says",
             "## 4 · The decisions", "## 5 · The caveats", "The record"]
    pos = [h.index(x) for x in order]
    assert pos == sorted(pos)
    assert "| cross coefficient | estimate | t |" in h
    assert "shock to MINK, scaled to 1" in h and "| permanent |" in h
    assert "share of each shock in the forecast-error variance at h = 8" in h
    assert "**N3** (step" in h and "the CCFs at lag 1" in h
    assert "MINK: art delivered it with a diagnosis caveat" in h


def test_the_html_guion_opens_with_the_hand_over(closed):
    out = _fn(M.export_guion)(closed)
    html = open(out.split("HTML: ")[1].strip(), encoding="utf-8").read()
    assert html.index("The hand-over") < html.index("The path")
    assert "<table><tr><th>response</th>" in html
    assert "digest=" not in html


def test_art_models_are_not_said_to_carry_unmodelled_outliers(monkeypatch):
    """(s) characterize's outliers are the raw entry's: a model from art
    decided them there, and the hand-over said otherwise."""
    _load("pk_out", "guided")
    s = S.get("pk_out")
    monkeypatch.setattr(status, "_outliers", lambda s: [("MINK", 2, "1900")])
    assert not any("modelled nowhere" in c for c in status.caveats(s))
