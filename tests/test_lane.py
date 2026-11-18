"""P2 — the lane in the session (sima.lane, sima.session.declare_lane).

The lane is the session's, declared ONCE at the load; the answers follow it.
Guided: the decision ends with the pause. Autonomous: no pause; in its place
the record_decision call for that node, filled with the node and the evidence
of the step just recorded, the decision and the reason left to write. Not
declared: guided, and the answer says so. In art the lane was per call, and
that is what produced BUG-0181 (the pause in the autonomous lane).
"""
import warnings

import pytest

import sima.mcp_server as M
from sima import envelope as E
from sima import lane as L
from sima import session as S

_fn = lambda f: getattr(f, "fn", f)                      # noqa: E731


@pytest.fixture(scope="module")
def ja_dir(tmp_path_factory):
    return str(tmp_path_factory.mktemp("ja"))


def _cross(session, lane, d):
    warnings.simplefilter("ignore")
    _fn(M.load_example)("jenkins_alavi", session=session, dest=d, lane=lane)
    _fn(M.run_gate)(session)
    return _fn(M.identify_cross)(session)


def test_guided_declared_stops_and_says_nothing_more(ja_dir):
    out = _cross("lane_g", "guided", ja_dir)
    assert E.STOP in out
    assert L.UNDECLARED not in out and "Autonomous lane" not in out


def test_undeclared_is_guided_and_says_so(ja_dir):
    out = _cross("lane_u", "", ja_dir)
    assert E.STOP in out
    # said where the decision is, above the pause; the envelope's title stays first
    assert L.UNDECLARED + "\n" + E.STOP in out
    assert not out.startswith(L.UNDECLARED)


def test_autonomous_has_no_pause_and_the_call_filled_in(ja_dir):
    out = _cross("lane_a", "autonomous", ja_dir)
    assert E.STOP not in out and "⏸" not in out
    assert "▶ **Autonomous lane.**" in out
    call = next(ln for ln in out.splitlines() if "record_decision(" in ln
                and 'decided_by="LLM"' in ln)
    # the node and the evidence are the step just recorded: identify_cross is N2
    assert 'name="lane_a"' in call and 'node="N2"' in call
    last = S.get("lane_a").guion.entries[-1]
    assert last.tool == "identify_cross"
    assert L._first_line(last.evidence) in call
    # the decision and the reason are the analyst's (the model's): left blank
    assert 'decision="<your decision>"' in call and 'reason="<why>"' in call
    # the options stay: the autonomous analyst reads the same evidence
    assert E.DECISION in out


def test_the_lane_is_kept_on_a_reload_and_recorded_at_n0(ja_dir):
    _cross("lane_k", "autonomous", ja_dir)
    files = S.get("lane_k").files
    import json
    _fn(M.load_pre)("lane_k", json.dumps(files))            # no lane: keeps it
    assert S.get("lane_k").lane == "autonomous"
    n0 = [e for e in S.get("lane_k").guion.entries if e.node == "N0"]
    assert n0 and n0[-1].args.get("lane") == "autonomous"


def test_an_unknown_lane_is_refused(ja_dir):
    out = _fn(M.load_pre)("lane_x", '["a.pre", "b.pre"]', lane="automatic")
    assert "guided" in out and "autonomous" in out
    assert "lane_x" not in S._LANES


def test_autonomous_figures_go_by_their_path():
    class T:                                   # mcp.types' TextContent, ImageContent
        def __init__(self, type, text=None, data=None):
            self.type, self.text, self.data = type, text, data
    out = [T("text", text="evidence\n\n" + E.STOP + "\nPNG: /x/f.png"), T("image", data="AAAA")]
    res = L.apply(out, "autonomous", True, "s", "N4", "residuals")
    assert [c.type for c in res] == ["text"]
    assert "PNG: /x/f.png" in res[0].text and E.STOP not in res[0].text
    # and with no pause (a figure tool that does not decide) nothing changes
    plain = [T("text", text="PNG: /x/f.png"), T("image", data="AAAA")]
    assert L.apply(plain, "autonomous", True, "s", "N6", "") is plain
