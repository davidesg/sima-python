"""The worked example of the manual (examples/jenkins_alavi) runs: its files
load, pass the gate, and give the manual's identification and Table VIII."""
import json
import os
import subprocess
import sys

from sima import mcp_server as M

EX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                  "examples", "jenkins_alavi")
FILES = [os.path.join(EX, "art", "MUSKRAT_m03.pre"), os.path.join(EX, "art", "MINK_m02.pre")]


def _fn(tool):
    return getattr(tool, "fn", tool)


def test_the_example_files_and_the_manuals_numbers(tmp_path):
    _fn(M.load_pre)("ex", json.dumps(FILES))
    assert "GATE: PASSED" in _fn(M.run_gate)("ex")
    t = _fn(M.plot_identification)("ex", method=2, path=str(tmp_path / "i.png"))[0].text
    assert "+1    -0.36*    -0.39*" in t and "S* ( 21 ) = 45.7" in t
    _fn(M.estimate)("ex", 2, 0, False, links="MUSKRAT<-MINK, MINK<-MUSKRAT",
                    start="preliminary")
    u = _fn(M.forecast_uncertainty)("ex", horizon=3, estwin=48)
    assert "1      25.698    18.171*      26.175    22.016*" in u


def test_the_walkthrough_script_runs(tmp_path):
    """The script, end to end, up to the checking (the evaluations are slow)."""
    env = dict(os.environ)
    r = subprocess.run([sys.executable, os.path.join(EX, "run.py"), "--upto", "8"],
                       capture_output=True, text=True, env=env, timeout=900)
    assert r.returncode == 0, r.stderr[-2000:]
    assert " 8. N4 checking of A" in r.stdout


def test_load_example_in_real_time(tmp_path):
    """load_example copies the files to a working folder, loads the univariate
    models and hands over to the usual protocol, pointing at the tutorial;
    files already there are kept."""
    t = _fn(M.load_example)("jenkins_alavi", session="tut", dest=str(tmp_path))
    assert "sima://example/jenkins_alavi" in t and 'Next: run_gate("tut")' in t
    assert (tmp_path / "art" / "MUSKRAT_m03.pre").exists()
    assert (tmp_path / "TUTORIAL.md").exists()
    assert "GATE: PASSED" in _fn(M.run_gate)("tut")
    (tmp_path / "art" / "MINK_m02.out").write_text("mine")
    t2 = _fn(M.load_example)("jenkins_alavi", session="tut2", dest=str(tmp_path))
    assert "already there, kept" in t2
    assert (tmp_path / "art" / "MINK_m02.out").read_text() == "mine"
    assert "No example" in _fn(M.load_example)("nope", dest=str(tmp_path / "x"))
