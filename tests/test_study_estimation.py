"""Studying an ill-defined estimation: a fit that stops on the MA wall.

drvarma reports the stop as a fact (Fit.ma_boundary); sima studies it and hands
over a menu, never a verdict. The case: m6's EI and EP, VARMA(1,1) with a
diagonal covariance, whose fit stops with an MA root at modulus 1.00005 at
frequency 0 (the signature of over-differencing).
"""
import json
import os

import numpy as np

from sima import evidence, mcp_server as M

DATA = os.path.join(os.path.dirname(__file__), "data", "m6")
PAIR = [os.path.join(DATA, "M6_EI.pre"), os.path.join(DATA, "M6_EP.pre")]


def _fn(tool):
    return getattr(tool, "fn", tool)


def _session(name="wall"):
    _fn(M.load_pre)(name, json.dumps(PAIR))
    _fn(M.run_gate)(name)
    return _fn(M.estimate)(name, 1, 1, True)


def test_estimate_states_the_wall_and_points_to_the_study():
    txt = _session("w1")
    assert "STOPPED AT THE MA INVERTIBILITY BOUNDARY" in txt
    assert "study_estimation" in txt


def test_the_study_gives_evidence_and_a_menu_not_a_verdict():
    _session("w2")
    txt = _fn(M.study_estimation)("w2")
    for part in ("INVERSE ROOTS", "ON THE WALL", "NEAR-COMMON",
                 "SECOND PATH (Shea", "RESTARTS", "MENU (the analyst decides)"):
        assert part in txt, part
    assert "over-differencing" in txt          # the frequency-0 wall root
    low = txt.lower()
    for verdict in ("you should", "the correct model", "we recommend"):
        assert verdict not in low


def test_roots_and_near_common_pairs():
    phi = np.array([[[0.9, 0.0], [0.0, 0.2]]])
    theta = np.array([[[0.88, 0.0], [0.0, 0.5]]])
    fit = type("F", (), {"phi": phi, "theta": theta})()
    txt = evidence.roots_text(fit, 12)
    assert "NEAR-COMMON" in txt and "distance 0.0200" in txt
    assert "none" not in txt.split("NEAR-COMMON")[1]


def test_wall_frequencies():
    fit = type("F", (), {"theta": np.array([[[1.00003, 0.0], [0.0, -0.3]]])})()
    assert evidence.wall_frequencies(fit, 4) == [0.0]
