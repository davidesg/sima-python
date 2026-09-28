"""The server: what is registered and what the model is told."""
import asyncio

from sima import mcp_server as M

EXPECTED = {"load_pre", "run_gate", "identify_cross", "estimate", "evaluate",
            "forecast", "impulse_response", "variance_decomposition",
            "record_decision", "export_guion", "split_inp", "study_estimation", "reorder"}


def _tools():
    return {t.name: t for t in asyncio.run(M.mcp.list_tools())}


def test_every_tool_is_registered():
    assert EXPECTED <= set(_tools())


def test_the_docstrings_are_the_product():
    # what the model reads: none of them a one-liner (sima's old server
    # averaged 412 characters; art 963)
    for name, t in _tools().items():
        assert len(t.description or "") >= 150, name


def test_the_instructions_carry_the_protocol_and_its_rules():
    ins = M._INSTRUCTIONS
    for node in ("N0", "N1", "N2", "N3", "N4", "N4b", "N5", "N6"):
        assert node in ins
    assert "YARDSTICK" in ins                  # the univariate model
    assert "CYCLE" in ins and "mtram" in ins   # the hand-over
    assert "NEVER RAW DATA" in ins             # no entry below the rung
    assert "Cholesky" in ins
    assert "GUIDED" in ins and "AUTONOMOUS" in ins
    # the autonomous lane is written, as art's (BUG-0180 there: without it the
    # autonomous lane collapsed into one call)
    assert "THE AUTONOMOUS LANE" in ins
    assert "NEVER DECIDE NODES IN BATCH" in ins
    assert 'decided_by="LLM"' in ins
    assert "WHAT YOU HAND OVER" in ins
