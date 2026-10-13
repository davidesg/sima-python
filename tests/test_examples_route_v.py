"""The worked examples from raw data, on route V: examples/lutkepohl_poskitt
(the echelon form) and examples/tiao_box (Tiao and Box). load_example loads
the table and hands over to characterize; the papers' numbers come out."""
import os
import subprocess
import sys

import pytest

from sima import mcp_server as M

EXAMPLES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "examples")
pytest.importorskip("art", reason="the raw entry uses art's engine")


def _fn(tool):
    return getattr(tool, "fn", tool)


def _coef(s, name):
    r = s.fits[s.current].result
    return dict(zip(r.names, r.x))[name]


def test_lutkepohl_poskitt_in_real_time(tmp_path):
    """Their Table 1: SC and HQ choose (0, 0, 0), (1, 1, 1) second. Their
    Table 2: the restricted VAR(1), five coefficients."""
    t = _fn(M.load_example)("lutkepohl_poskitt", session="lp", dest=str(tmp_path))
    assert "sima://example/lutkepohl_poskitt" in t and 'Next: characterize("lp")' in t
    assert "RAW DATA — flour_prices.csv: 3 series, 100 observations, monthly" in t
    assert (tmp_path / "TUTORIAL.md").exists()
    c = _fn(M.characterize)("lp")
    assert "Buffalo              0   1" in c and "KansasCity           0   1" in c
    _fn(M.write_specs)("lp")
    assert "GATE: PASSED" in _fn(M.run_gate)("lp")
    i = _fn(M.identify_echelon)("lp", max_index=6)
    assert "Chosen by SC: Buffalo 0, Minneapolis 0, KansasCity 0" in i
    assert "HQ would choose (0, 0, 0)" in i
    assert "(1, 1, 1)    18     4.9739     5.5644" in i
    s = M._sess.get("lp")
    run = __import__("importlib").util.spec_from_file_location(
        "lp_run", os.path.join(EXAMPLES, "lutkepohl_poskitt", "run.py"))
    mod = __import__("importlib").util.module_from_spec(run)
    run.loader.exec_module(mod)
    _fn(M.estimate)("lp", 1, 0, zeros=mod.VAR_ZEROS)
    r = s.fits[s.current].result
    assert r.npar == 10 and r.logL == pytest.approx(-669.13, abs=0.01)
    assert _coef(s, "phi_Buffalo[B^1]") == pytest.approx(-0.88, abs=0.015)
    assert _coef(s, "AR1[Buffalo<-Minneapolis]") == pytest.approx(1.02, abs=0.015)
    assert _coef(s, "AR1[Minneapolis<-Buffalo]") == pytest.approx(-0.44, abs=0.015)
    assert _coef(s, "phi_Minneapolis[B^1]") == pytest.approx(0.62, abs=0.015)
    assert _coef(s, "AR1[KansasCity<-Minneapolis]") == pytest.approx(0.25, abs=0.015)


def test_tiao_box_in_real_time(tmp_path):
    """Their Table 12's M(l), the structure of the VAR(6), and their
    restricted AR(6): the input's AR(3) and the delay of three periods."""
    t = _fn(M.load_example)("tiao_box", session="tb", dest=str(tmp_path))
    assert 'Next: characterize("tb")' in t and "2 series, 296 observations" in t
    _fn(M.characterize)("tb", set="InputGasRate: lam=1, d=0; CO2: lam=1, d=0")
    _fn(M.write_specs)("tb")
    assert "GATE: PASSED" in _fn(M.run_gate)("tb")
    i = _fn(M.identify_matrices)("tb", nlags=11)
    assert "1649.7" in i and "665.1" in i and "M(l) is significant up to l = 6" in i
    run = __import__("importlib").util.spec_from_file_location(
        "tb_run", os.path.join(EXAMPLES, "tiao_box", "run.py"))
    mod = __import__("importlib").util.module_from_spec(run)
    run.loader.exec_module(mod)
    _fn(M.estimate)("tb", 6, 0, zeros=mod.TB_ZEROS)
    s = M._sess.get("tb")
    r = s.fits[s.current].result
    assert r.npar == 15 and r.logL == pytest.approx(-2647.48, abs=0.01)
    for k, v in ((1, 1.97), (2, -1.37), (3, 0.34)):
        assert _coef(s, f"phi_InputGasRate[B^{k}]") == pytest.approx(v, abs=0.02)
    assert _coef(s, "AR3[CO2<-InputGasRate]") == pytest.approx(-0.53, abs=0.01)
    st = _fn(M.structure)("tb")
    assert "CO2 -> InputGasRate                already absent" in st


@pytest.mark.parametrize("name, upto, line", [
    ("lutkepohl_poskitt", 5, " 5. N2 the echelon index search"),
    ("tiao_box", 7, " 7. N4t its structure: is there feedback?")])
def test_the_walkthrough_scripts_run(name, upto, line):
    r = subprocess.run([sys.executable, os.path.join(EXAMPLES, name, "run.py"),
                        "--upto", str(upto)],
                       capture_output=True, text=True, env=dict(os.environ), timeout=900)
    assert r.returncode == 0, r.stderr[-2000:]
    assert line in r.stdout
