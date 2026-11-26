"""P3 and P7 -- where an analysis stands, and what it hands over.

`where` informs and records nothing: the path, the open decisions with their
options, what was adopted, and the protocol's next node. `hand_over` gathers
the end: the result, the yardstick that decided it, the caveats, the guion;
and says so when an adopted VARMA does not win most cells (rule 1).
"""
import tempfile
import warnings

import pytest

import sima.mcp_server as M
from sima import session as S

_fn = lambda f: getattr(f, "fn", f)                      # noqa: E731


@pytest.fixture(scope="module")
def ja():
    warnings.simplefilter("ignore")
    _fn(M.load_example)("jenkins_alavi", session="wh", dest=tempfile.mkdtemp(),
                        lane="autonomous")
    return "wh"


def test_where_at_the_start_points_to_the_gate_and_records_nothing(ja):
    n = len(S.get(ja).guion.entries)
    w = _fn(M.where)(ja)
    assert "Lane: autonomous" in w and "order: MUSKRAT → MINK" in w
    assert 'run_gate(name="wh")' in w and "it does not decide" in w
    assert len(S.get(ja).guion.entries) == n
    assert "⏸" not in w and "Autonomous lane" not in w      # not a decision itself


def test_where_lists_the_open_decision_with_its_options(ja):
    _fn(M.run_gate)(ja)
    _fn(M.identify_cross)(ja)
    _fn(M.estimate)(ja, 1, 0)
    w = _fn(M.where)(ja)
    assert "N2 identify_cross — decided (A)" in w
    assert "N3 estimate — OPEN" in w
    assert '`art: suggest_intervention_form(...)`' in w      # the reformulation, first
    assert '`evaluate(name="wh", p=1, q=0, estwin=...)`' in w
    assert "decide the open decision of N3" in w


def test_hand_over_before_adopting_says_the_analysis_is_not_closed(ja):
    h = _fn(M.hand_over)(ja)
    assert "NOTHING ADOPTED" in h and 'export_guion(name="wh")' in h


def test_hand_over_gives_the_result_the_yardstick_and_the_caveats(ja):
    _fn(M.check_residuals)(ja)
    _fn(M.evaluate)(ja, 1, 0, estwin=40)
    _fn(M.adopt)(ja, model="current", why="the gain at h 1 on MINK is the question")
    h = _fn(M.hand_over)(ja)
    assert "Adopted: **p = 1, q = 0, full covariance**." in h
    assert "lower RMSE in" in h
    assert "The Cholesky order MUSKRAT → MINK is an identifying assumption" in h
    e = S.get(ja).guion.entries[-1]
    assert e.node == "N7" and e.tool == "hand_over"
    # rule 1, said: this VARMA does not win most cells
    assert "⚠ RULE 1" in h


def test_hand_over_with_the_univariates_states_the_finding(ja):
    _fn(M.adopt)(ja, model="univariates", why="no gain where it matters")
    h = _fn(M.hand_over)(ja)
    assert "the univariate models (the diagonal system)" in h
    assert "that is the finding" in h and "⚠ RULE 1" not in h


def test_the_decision_nodes_document_is_served():
    from sima import resources
    names = resources.docs_index()
    assert "DECISION_NODES" in names
