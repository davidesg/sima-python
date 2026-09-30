"""What the assistant SAYS in the delicate cases (a different discipline from
the numbers: ASSISTANT_LAYER_PROPOSAL.md §5.3)."""
import json

import numpy as np

from sima import evidence
from sima import mcp_server as M


def test_a_failed_gate_stops_the_analysis(trio_json, monkeypatch):
    from drvarma.ladder import GateError, Ladder

    def broken(self):
        raise GateError("the diagonal gate failed (difference 1.0)")
    monkeypatch.setattr(Ladder, "run_gate", broken)
    M.load_pre("f", trio_json)
    txt = M.run_gate("f")
    assert "GATE FAILED" in txt and "Stop here" in txt
    assert "gate first" in M.estimate("f", 1, 0)          # nothing on top of it


def test_no_evidence_offers_staying_univariate():
    r = np.random.default_rng(0).standard_normal((200, 2))
    txt, facts = evidence.cross_identification(r, ["A", "B"], 3, 12)
    assert not facts["any"]
    assert "stay with the univariates" in txt and "the system IS the diagonal" in txt


def test_the_evidence_offers_a_menu_not_a_verdict(trio_json):
    M.load_pre("m", trio_json)
    M.run_gate("m")
    txt = M.identify_cross("m")
    assert "(a)" in txt and "(b)" in txt and "for:" in txt and "against:" in txt
    assert "recommend" not in txt.lower()


def test_the_cholesky_order_is_said_to_be_an_assumption(trio_json):
    M.load_pre("c", trio_json)
    M.run_gate("c")
    M.estimate("c", 1, 0)
    txt = M.impulse_response("c", 2)
    assert "identifying ASSUMPTION" in txt and "IPC_ES -> IPC_FR -> IPC_DE" in txt


def test_a_yardstick_loss_is_named_a_finding():
    cand = {("A", 1): {"n": 40, "RMSE": 1.2, "MAPE": 1.1, "MAE": 1.0}}
    diag = {("A", 1): {"n": 40, "RMSE": 1.0, "MAPE": 1.0, "MAE": 0.9}}
    txt, facts = evidence.evaluation_text(cand, diag, "VARMA", [1], ["A"])
    assert facts == {"wins": 0, "cells": 1}
    assert "a finding, not a model to keep" in " ".join(txt.split())


def test_split_says_the_files_are_specifications(tmp_path):
    from conftest import DATA
    import os
    txt = M.split_inp(os.path.join(DATA, "IPC3.inp"), str(tmp_path))
    assert "specifications" in txt and "art" in txt
    assert len(list(tmp_path.glob("*.inp"))) == 3


def test_specifications_are_named_with_both_readings():
    gate = {"rows": [{"series": "A", "logL": 1.0, "sigma2": 1.0, "move": 0.1, "trimmed": 0},
                     {"series": "B", "logL": 1.0, "sigma2": 1.0, "move": 0.0, "trimmed": 0}],
            "sum": 2.0, "joint": 2.0, "difference": 0.0, "passed": True}
    txt = evidence.gate_text(gate)
    assert "SPECIFICATIONS" in txt and "ANOTHER sample" in txt and "go back to art" in txt


def test_evaluation_columns_hold_large_levels():
    """RMSEs of series in hundreds of thousands (muskrat skins) do not run
    into each other: the row splits into its columns."""
    from sima.evidence import evaluation_text
    cand = {("MUSKRAT", 1): {"n": 21, "RMSE": 249170.166, "MAPE": 29.3},
            ("MINK", 1): {"n": 21, "RMSE": 11452.2, "MAPE": 22.1}}
    diag = {("MUSKRAT", 1): {"n": 21, "RMSE": 227388.149, "MAPE": 26.1},
            ("MINK", 1): {"n": 21, "RMSE": 11074.6, "MAPE": 25.1}}
    txt, _f = evaluation_text(cand, diag, "x", [1], ["MUSKRAT", "MINK"])
    row = [l for l in txt.splitlines() if l.strip().startswith("MUSKRAT")][0].split()
    assert row[3:6] == ["249170", "227388", "1.096"]
