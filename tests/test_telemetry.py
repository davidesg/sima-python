"""The local, opt-in telemetry (sima.telemetry): off unless SIMA_TELEMETRY
names a folder; then one JSON line per call and the answer in a file. It never
changes what a tool does, and an exception is recorded and still raised."""
import json
import os
import tempfile
import warnings

import pytest

import sima.mcp_server as M
from sima import telemetry as T

_fn = lambda f: getattr(f, "fn", f)                      # noqa: E731


@pytest.fixture
def tdir(tmp_path, monkeypatch):
    monkeypatch.setenv(T.ENV, str(tmp_path / "tel"))
    monkeypatch.setitem(T._state, "path", None)
    monkeypatch.setitem(T._state, "seq", 0)
    return tmp_path / "tel"


def _lines(d):
    (f,) = [p for p in os.listdir(d) if p.endswith(".jsonl")]
    with open(os.path.join(d, f)) as fh:
        return [json.loads(x) for x in fh]


def test_off_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv(T.ENV, raising=False)
    monkeypatch.setitem(T._state, "path", None)
    warnings.simplefilter("ignore")
    _fn(M.load_example)("jenkins_alavi", session="t_off", dest=str(tmp_path / "ex"))
    assert T._state["path"] is None


def test_each_call_is_recorded_with_its_answer(tdir, tmp_path):
    warnings.simplefilter("ignore")
    _fn(M.load_example)("jenkins_alavi", session="t_on", dest=str(tmp_path / "ex"),
                        lane="autonomous")
    _fn(M.run_gate)("t_on")
    _fn(M.identify_cross)("t_on")
    _fn(M.estimate)("t_on", 1, 0)
    recs = _lines(tdir)
    assert recs[0]["type"] == "start" and "drvarma" in recs[0]["versions"]
    calls = [r for r in recs if r["type"] == "call"]
    tools = [r["tool"] for r in calls]
    assert tools[-3:] == ["run_gate", "identify_cross", "estimate"]
    ic = calls[-2]
    assert ic["lane"] == "autonomous" and ic["ends"] == "autonomous"
    assert ic["guion"][-1]["node"] == "N2" and ic["guion"][-1]["status"] == "pending"
    est = calls[-1]
    assert {"n": ic["guion"][-1]["n"], "chosen": "A"} in est["closed"]
    assert est["dur_s"] >= 0 and est["ok"]
    with open(tdir / est["answer_file"]) as fh:
        assert "N3" in fh.read()


def test_an_error_is_recorded_and_still_raised(tdir):
    with pytest.raises(KeyError):
        _fn(M.estimate)("no_such_session", 1, 0)
    err = [r for r in _lines(tdir) if r["type"] == "call"][-1]
    assert not err["ok"] and err["error"]["type"] == "KeyError"
    assert "Traceback" in err["error"]["traceback"]
