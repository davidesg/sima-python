"""Local, opt-in telemetry of a sima session: what each tool call did.

OFF unless the environment variable ``SIMA_TELEMETRY`` names a folder. Then
every tool call leaves one JSON line in ``<folder>/sima-<start>-<pid>.jsonl``
and its whole answer (the text the model reads) in
``<folder>/answers/<seq>-<tool>.md``. Nothing leaves the machine.

It is for trial runs (a "rodaje") and for teaching: the conversation records
what was said, and this records what the server did -- the time each call
took, the lane and how the answer ended (the pause, the autonomous call, or
neither), the guion steps the call added, the decisions it opened and closed,
the adoption, and any exception with its traceback (the call still raises: the
record never changes what the tool does).

The first line of each file is the environment: the versions of sima and of
its engines, Python, the platform, the working folder.
"""
from __future__ import annotations

import json
import os
import platform
import sys
import time
import traceback
from datetime import datetime

ENV = "SIMA_TELEMETRY"
_state = {"path": None, "seq": 0}


def folder():
    d = os.environ.get(ENV, "").strip()
    return os.path.expanduser(d) if d else None


def _versions():
    out = {}
    for mod in ("sima", "drvarma", "drvec", "fue", "pyfug", "art", "numpy"):
        try:
            m = __import__(mod)
            out[mod] = getattr(m, "__version__", "?")
        except Exception:                                    # noqa: BLE001
            out[mod] = None
    try:
        from importlib.metadata import version
        out["sima-tseries"] = version("sima-tseries")
    except Exception:                                        # noqa: BLE001
        pass
    return out


def _open(d):
    if _state["path"] is None:
        os.makedirs(os.path.join(d, "answers"), exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        _state["path"] = os.path.join(d, f"sima-{stamp}-{os.getpid()}.jsonl")
        _write({"type": "start", "when": datetime.now().isoformat(timespec="seconds"),
                "versions": _versions(), "python": sys.version.split()[0],
                "platform": platform.platform(), "cwd": os.getcwd(), "pid": os.getpid()})
    return _state["path"]


def _write(rec):
    with open(_state["path"], "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


def _safe(v, width=400):
    s = v if isinstance(v, (int, float, bool)) or v is None else str(v)
    return s if not isinstance(s, str) or len(s) <= width else s[:width] + "…"


def ends(text, stop, auto_mark):
    if stop in text:
        return "pause"
    if auto_mark in text:
        return "autonomous"
    return "none"


def record(tool, bound, session, t0, out=None, error=None, guion_new=(), closed=(),
           pending=0, lane=None, declared=None, adopted=None, texts=(), images=0,
           ending=None):
    """One call. Never raises: telemetry must not cost a tool its answer."""
    d = folder()
    if not d:
        return
    try:
        _open(d)
        _state["seq"] += 1
        seq = _state["seq"]
        text = "\n\n".join(texts)
        ans = None
        if text:
            ans = os.path.join(d, "answers", f"{seq:04d}-{tool}.md")
            with open(ans, "w", encoding="utf-8") as fh:
                fh.write(f"<!-- {tool} · session {session} · {datetime.now().isoformat(timespec='seconds')} -->\n\n")
                fh.write(text)
        rec = {"type": "call", "seq": seq,
               "when": datetime.fromtimestamp(t0).isoformat(timespec="seconds"),
               "dur_s": round(time.time() - t0, 3), "tool": tool, "session": session,
               "args": {k: _safe(v) for k, v in (bound or {}).items()},
               "ok": error is None, "lane": lane, "lane_declared": declared,
               "answer_chars": len(text), "images": images, "ends": ending,
               "guion": [{"n": e.n, "node": e.node, "tool": e.tool, "status": e.status}
                         for e in guion_new],
               "closed": [{"n": n, "chosen": c} for n, c in closed],
               "open_decisions": pending, "adopted": adopted,
               "answer_file": os.path.relpath(ans, d) if ans else None}
        if error is not None:
            rec["error"] = {"type": type(error).__name__, "message": str(error),
                            "traceback": "".join(traceback.format_exception(
                                type(error), error, error.__traceback__))[-4000:]}
        _write(rec)
    except Exception:                                        # noqa: BLE001
        pass
