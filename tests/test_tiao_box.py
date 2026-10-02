"""The Wisconsin line in sima (docs/STUDY-tiao-box.md): Tiao and Box's
stepwise autoregression under method 1 (A) and Box and Tiao's canonical
analysis of the levels (E1)."""
import json
import os

import numpy as np

from sima import evidence
from sima import mcp_server as M

EX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                  "examples", "jenkins_alavi")
FILES = [os.path.join(EX, "art", "MUSKRAT_m03.pre"), os.path.join(EX, "art", "MINK_m02.pre")]


def _fn(tool):
    return getattr(tool, "fn", tool)


def test_identify_matrices_carries_the_stepwise_table():
    _fn(M.load_pre)("tb", json.dumps(FILES))
    _fn(M.run_gate)("tb")
    t = _fn(M.identify_matrices)("tb")
    assert "Tiao and Box's (1981) stepwise autoregression" in t
    assert "reading, Tiao and Box: the last significant M(l) is at l = 1" in t


def test_canonical_analysis_on_the_example():
    """Muskrat and mink: one differenced series, so the joint-differencing
    question does not arise; the report is art's, and the guion keeps it."""
    _fn(M.load_pre)("tbc", json.dumps(FILES))
    assert "Run the gate first" in _fn(M.canonical_analysis)("tbc")
    _fn(M.run_gate)("tbc")
    t = _fn(M.canonical_analysis)("tbc")
    for h in ("## 1 · TABLE", "## 2 · WHAT IT SHOWS", "## 3 · CONCLUSIONS",
              "## 4 · DECISION", "⏸"):
        assert h in t
    assert "the question of joint differencing does not arise" in t
    assert "sima does not change any d" in t
    e = M._sess.get("tbc").guion.entries[-1]
    assert e.node == "N1b" and e.tool == "canonical_analysis"


def _cointegrated(n=300, seed=3):
    """Box and Tiao's (4.9) with three series: one random walk drives all."""
    rng = np.random.default_rng(seed)
    z = np.cumsum(rng.standard_normal(n))
    return np.column_stack([z + 0.3 * rng.standard_normal(n),
                            0.8 * z + 0.4 * rng.standard_normal(n),
                            -0.5 * z + 0.5 * rng.standard_normal(n)])


def test_the_question_of_joint_differencing_is_asked():
    """Three I(1) series, one common trend: one component near 1, two nearly
    white — so 2 stationary combinations, and the menu names drvec."""
    t, f = evidence.canonical_report(_cointegrated(), ["A", "B", "C"], [1, 1, 1], 1,
                                     call="x")
    assert f["near_one"] == 1 and f["near_zero"] == 2 and f["question"]
    assert "there may be 2 stationary combination(s) of the levels" in t
    assert "drvec" in t and "Johansen" in t


def test_independent_random_walks_raise_no_question():
    rng = np.random.default_rng(5)
    x = np.cumsum(rng.standard_normal((300, 2)), axis=0)
    _t, f = evidence.canonical_report(x, ["A", "B"], [1, 1], 1)
    assert f["near_one"] == 2 and not f["question"]


# ── the worked example: flour prices (Tiao and Tsay 1989) ────────────────────

def test_the_flour_example_in_real_time(tmp_path):
    """load_example("flour_prices") loads the three univariate models; the
    gate proposes the canonical analysis, which finds two components near 1 for
    three differenced series (Tiao and Tsay's contrast, root .87), and the
    stepwise M(l) on the differences asks for a VAR(1)."""
    t = _fn(M.load_example)("flour_prices", session="fl", dest=str(tmp_path))
    assert "sima://example/flour_prices" in t
    g = _fn(M.run_gate)("fl")
    assert "GATE: PASSED" in g and "Next: canonical_analysis" in g
    c = _fn(M.canonical_analysis)("fl")
    assert "1  0.758    0.870" in c and "3  0.943    0.971" in c
    assert "there may be 1 stationary combination(s) of the levels" in c
    i = _fn(M.identify_matrices)("fl")
    assert "reading, Tiao and Box: the last significant M(l) is at l = 1" in i


def test_the_flour_example_is_listed():
    from sima import resources
    assert "flour_prices" in resources.examples_index()
    assert "contrast between markets" in resources.example_tutorial("flour_prices")
