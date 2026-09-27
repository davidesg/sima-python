"""The protocol, N0..N6, on the CPI trio, with the engine's numbers."""
import json
import re

import pytest

from sima import mcp_server as M
from sima import session


def test_n0_needs_two_series():
    assert "at least two" in M.load_pre("one", json.dumps(["x.pre"]))


def test_n0_refuses_what_fue_does_not_read(tmp_path):
    bad = tmp_path / "bad.pre"
    bad.write_text("not a model\n")
    other = tmp_path / "other.pre"
    other.write_text("nor this\n")
    assert "Cannot open the session" in M.load_pre("bad", json.dumps([str(bad), str(other)]))


def test_the_path_n0_to_n6(trio_json, tmp_path):
    out = M.load_pre("t", trio_json)
    assert "IPC_ES" in out and "run_gate" in out
    g = M.run_gate("t")
    assert "GATE: PASSED" in g and "fixed point" in g
    c = M.identify_cross("t")
    assert "Contemporaneous correlation" in c and "p = 1" in c
    e = M.estimate("t", 1, 0, reason="short leads at lag 1")
    # the C's VAR(1) on the same files: LR 205.9820, df 9 (tests/escalera)
    m = re.search(r"LR = ([0-9.]+), df = (\d+)", e)
    assert m and float(m.group(1)) == pytest.approx(205.982, abs=1e-2) and m.group(2) == "9"
    f = M.forecast("t", 3)
    assert f.count("origin 12/2019") == 3
    assert "Cholesky" in M.impulse_response("t", 4)
    assert "IPC_DE" in M.variance_decomposition("t", 6)
    s = session.get("t")
    assert [e.node for e in s.guion.entries] == ["N0", "N1", "N2", "N3", "N6", "N6", "N6"]
    path = s.guion.save(str(tmp_path / "g.json"))
    from sima.guion import load
    assert len(load(path).entries) == 7


def test_n5_the_yardstick(ext_json):
    M.load_pre("y", ext_json)
    M.run_gate("y")
    txt = M.evaluate("y", 1, 0, 216, 24)
    assert "THE YARDSTICK" in txt
    assert "lower RMSE in 8 of 12" in txt
    # the diagonal system is fue's forecasts: IPC_ES h=1 RMSE 0.8648 (the C)
    assert re.search(r"IPC_ES\s+1\s+47\s+[0-9.]+\s+0\.8648", txt)


def test_estimate_before_the_gate_is_refused(trio_json):
    M.load_pre("g", trio_json)
    assert "gate first" in M.estimate("g", 1, 0)


def test_arriving_from_an_mtram_cycle():
    """m6: the case whose network identification in mtram is CYCLIC
    (EP -> EC -> EA -> EP). mtram hands over the same six .pre files; sima
    loads them and certifies the univariate base."""
    from conftest import DATA
    import os
    paths = [os.path.join(DATA, "m6", f"M6_{n}.pre") for n in ("EP", "EI", "EU", "EC", "EA", "P")]
    assert "EA" in M.load_pre("m6", json.dumps(paths))
    g = M.run_gate("m6")
    assert "GATE: PASSED" in g
    assert "trimmed sample" in g            # different operators, one window
