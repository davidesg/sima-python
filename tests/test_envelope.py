"""P1 — the envelope of the VARMA core (sima.envelope).

Every node tool of the core ends with the same four sections, in order, and the
stop mark; every option carries a call, and the call names a tool that exists
(or says it is outside sima). The rule of art's BUG-0094, and of sima's own
manual (MANUAL-jenkins-alavi.md §2.4), which the core did not keep: estimate
said «Next: evaluate» and skipped the residuals (N4); evaluate's menu had no
call and did not stop.
"""
import re
import warnings

import pytest

import sima.mcp_server as M
from sima import envelope as E

_fn = lambda f: getattr(f, "fn", f)                      # noqa: E731


@pytest.fixture(scope="module")
def ja(tmp_path_factory):
    warnings.simplefilter("ignore")
    d = tmp_path_factory.mktemp("ja")
    _fn(M.load_example)("jenkins_alavi", session="env", dest=str(d))
    _fn(M.run_gate)("env")
    out = {"identify_cross": _fn(M.identify_cross)("env"),
           "identify_matrices": _fn(M.identify_matrices)("env"),
           "identify_echelon": _fn(M.identify_echelon)("env"),
           "estimate": _fn(M.estimate)("env", 1, 0)}
    out["study_estimation"] = _fn(M.study_estimation)("env")
    out["evaluate"] = _fn(M.evaluate)("env", 1, 0, estwin=40)
    return out


TOOLS = ["identify_cross", "identify_matrices", "identify_echelon", "estimate",
         "study_estimation", "evaluate"]


@pytest.mark.parametrize("tool", TOOLS)
def test_the_four_sections_in_order_and_the_stop(ja, tool):
    t = ja[tool]
    pos = [t.find(h) for h in (E.TABLE, E.SHOWS, E.CONCLUSIONS, E.DECISION)]
    assert all(p >= 0 for p in pos) and pos == sorted(pos), tool
    assert t.rstrip().endswith(E.STOP), tool


@pytest.mark.parametrize("tool", TOOLS)
def test_every_option_carries_a_call_to_a_tool_that_exists(ja, tool):
    t = ja[tool]
    opciones = re.findall(r"\*\*[A-J]\)\*\* .*\n   `([^`]+)`", t)
    assert opciones, f"{tool}: no option with a call"
    for call in opciones:
        if call.startswith("art"):
            continue                                     # outside sima, said so
        nombre = call.split("(")[0]
        assert callable(getattr(M, nombre, None)), f"{tool}: «{call}» names no tool"
        assert 'name="env"' in call, f"{tool}: «{call}» is not on the session"


def test_estimate_leads_to_the_residuals_before_the_yardstick(ja):
    """The residuals of the estimated model — each series' diagnosis and the CCF
    of every pair — come before N5, not after (it used to say «Next: evaluate»)."""
    t = ja["estimate"]
    assert "Next: evaluate" not in t
    assert t.index("check_residuals(") < t.index("evaluate(")


def test_the_conclusions_are_readings_not_a_recommendation(ja):
    for tool in TOOLS:
        concl = ja[tool].split(E.CONCLUSIONS)[1].split(E.DECISION)[0].lower()
        assert "recommend" not in concl and "you should" not in concl, tool
