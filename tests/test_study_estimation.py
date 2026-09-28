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
    inside = type("F", (), {"theta": np.array([[[0.99999999, 0.0], [0.0, -0.3]]])})()
    assert evidence.wall_frequencies(inside, 4) == [0.0]      # one tolerance, both sides


def test_record_decision_keeps_reason_evidence_and_alternatives():
    _session("w3")
    out = _fn(M.record_decision)("w3", "N5", "stay with the univariates",
                                 reason="the VARMA gains in no cell",
                                 evidence="RMSE ratio 1.02-1.11",
                                 alternatives="VARMA(1,1) diag: on the MA wall",
                                 decided_by="LLM")
    assert out.startswith("Recorded")
    g = _fn(M.export_guion)("w3", save=False)
    for part in ("because the VARMA gains in no cell", "RMSE ratio 1.02-1.11",
                 "LLM", "on the MA wall"):
        assert part in g, part


def test_irf_and_fevd_come_with_bands():
    pair = [os.path.join(os.path.dirname(__file__), "data", n)
            for n in ("IPC_ES_m10.pre", "IPC_FR_msar.pre")]
    _fn(M.load_pre)("b1", json.dumps(pair))
    _fn(M.run_gate)("b1")
    _fn(M.estimate)("b1", 1, 0, False)
    irf = _fn(M.impulse_response)("b1", 4, ndraws=200)
    assert "95% Monte-Carlo bands" in irf and "[" in irf.split("shock to")[1]
    fv = _fn(M.variance_decomposition)("b1", 12, ndraws=200)
    assert "the row marked *" in fv and "12*" in fv
    plain = _fn(M.impulse_response)("b1", 4, bands=False)
    assert "Point estimates only" in plain


def test_reorder_compares_the_cholesky_orders_without_reestimating():
    pair = [os.path.join(os.path.dirname(__file__), "data", n)
            for n in ("IPC_ES_m10.pre", "IPC_FR_msar.pre")]
    _fn(M.load_pre)("r1", json.dumps(pair))
    _fn(M.run_gate)("r1")
    _fn(M.estimate)("r1", 1, 0, False)
    txt = _fn(M.reorder)("r1", json.dumps(["IPC_FR", "IPC_ES"]), 4)
    assert "CHOLESKY ORDER" in txt and "largest change" in txt
    same = _fn(M.reorder)("r1", json.dumps(["IPC_ES", "IPC_FR"]), 4)
    assert "largest change 0.00000" in same          # the files' own order
    assert "must name every series" in _fn(M.reorder)("r1", '["IPC_ES", "IPC_ES"]')
    _fn(M.estimate)("r1", 1, 0, True)
    assert "diagonal" in _fn(M.reorder)("r1", json.dumps(["IPC_FR", "IPC_ES"]))


def test_the_covariance_parameters_carry_no_t_ratio():
    """drvarma BUG-0008: the innovation covariance is concentrated out and
    parametrised free of scale; its numbers are reported, not tested."""
    _fn(M.load_pre)("cov", json.dumps(PAIR))
    _fn(M.run_gate)("cov")
    txt = _fn(M.estimate)("cov", 1, 0, False)          # full covariance
    block = txt.split("innovation covariance, parametrised")[1].split("exact log-likelihood")[0]
    rows = [l for l in block.splitlines()[1:] if l.strip()]
    assert rows and all(l.strip().startswith(("log(Q[", "Q[")) for l in rows)
    assert all("*" not in l and len(l.split()) == 2 for l in rows)
    table = txt.split("innovation covariance, parametrised")[0]
    assert "log(Q[" not in table and "Q[" not in table
