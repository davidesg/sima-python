"""The lane in the answer (docs/ESTUDIO P2): one filter on every tool's output.

The envelopes (sima.envelope) end a decision with the guided lane's pause,
``envelope.STOP``. Which lane is in force is the SESSION's, set once at the
load; the tools that build the envelopes (evidence, vec) do not know it, and
need not. This filter does, and it is the only place that reads it:

* guided, declared: the answer as it is;
* guided, not declared: the same, with one line above the pause saying so --
  a silent default cannot be discussed;
* autonomous: no pause. In its place, the call that documents the node,
  already filled with the node and the evidence of the step just recorded --
  the analyst in the chair (the model) only writes the decision and the
  reason. The figures go by their path (the PNG lines stay), not inside the
  answer: in the autonomous lane nobody is looking at them as they come.

It informs; it does not decide (BUG-0180 in art): the decision is left blank.
"""
from __future__ import annotations

import functools
import inspect

from . import envelope as _env

UNDECLARED = ("Lane: guided (not declared: the default). Say lane=\"guided\" or "
              "lane=\"autonomous\" when loading.")


def _first_line(text, width=160):
    line = next((ln.strip() for ln in str(text or "").splitlines() if ln.strip()), "")
    line = line.replace('"', "'")
    return line if len(line) <= width else line[:width - 1] + "…"


def record_call(name, node, evidence):
    return (f'record_decision(name="{name}", node="{node}", decision="<your decision>", '
            f'reason="<why>", evidence="{_first_line(evidence)}", '
            f'alternatives="<what you set aside, and why>", decided_by="LLM")')


def autonomous_block(name, node, evidence):
    return ("▶ **Autonomous lane.** No pause: decide this node yourself, and write "
            "it down before the next call:\n   `" + record_call(name, node, evidence) + "`")


def _session_name(fn, args, kw):
    try:
        b = inspect.signature(fn).bind_partial(*args, **kw)
    except TypeError:
        return None
    a = b.arguments
    if fn.__name__ == "load_example":
        return a.get("session") or a.get("name") or "jenkins_alavi"
    return a.get("name")


def _texts(out):
    """(is_list, [(index, text)]) for a str, a list of str or of TextContent."""
    if isinstance(out, str):
        return False, [(None, out)]
    if isinstance(out, list):
        return True, [(i, getattr(c, "text", c)) for i, c in enumerate(out)
                      if isinstance(c, str) or getattr(c, "type", None) == "text"]
    return False, []


def apply(out, lane, declared, name, node, evidence):
    """The answer `out` in the lane in force."""
    is_list, texts = _texts(out)
    if not any(_env.STOP in t for _, t in texts):
        return out
    if lane == "autonomous":
        block = autonomous_block(name, node or "N…", evidence)
        new = lambda t: t.replace(_env.STOP, block)           # noqa: E731
    elif not declared:
        # next to the pause, where the decision is; the title stays first
        new = lambda t: t.replace(_env.STOP, UNDECLARED + "\n" + _env.STOP)  # noqa: E731
    else:
        return out
    if not is_list:
        return new(out)
    res = []
    for c in out:
        if isinstance(c, str):
            res.append(new(c))
        elif getattr(c, "type", None) == "text":
            res.append(type(c)(type="text", text=new(c.text)))
        elif lane == "autonomous" and getattr(c, "type", None) == "image":
            continue                                          # by its path only
        else:
            res.append(c)
    return res


def _bound(fn, args, kw):
    try:
        b = inspect.signature(fn).bind(*args, **kw)
        b.apply_defaults()
        return dict(b.arguments)
    except TypeError:
        return dict(kw)


def _prepend(out, note):
    if isinstance(out, str):
        return note + "\n\n" + out
    if isinstance(out, list) and out:
        c = out[0]
        if isinstance(c, str):
            return [note + "\n\n" + c] + out[1:]
        if getattr(c, "type", None) == "text":
            return [type(c)(type="text", text=note + "\n\n" + c.text)] + out[1:]
    return out


def wrap(fn, sessions):
    """`fn`, with its answer passed through `apply` in its session's lane; and
    its decisions recorded as data (sima.decisions): a decision it ends in is
    left pending, the ones it takes are closed, and a final-stage tool warns
    when it acts on a model that is not the adopted one."""
    from . import decisions as _dec

    from . import telemetry as _tm
    import time as _time

    @functools.wraps(fn)
    def tool(*args, **kw):
        t0 = _time.time()
        name = _session_name(fn, args, kw)
        before = sessions._SESSIONS.get(name) if name else None
        n0 = len(before.guion.entries) if before is not None else 0
        open0 = {e.n for e in before.guion.pending()} if before is not None else set()
        try:
            out = fn(*args, **kw)
        except Exception as err:
            if _tm.folder():
                _tm.record(fn.__name__, _bound(fn, args, kw), name, t0, error=err)
            raise
        out = _finish(fn, args, kw, out, name, before, n0, sessions)
        if _tm.folder():
            try:
                s = sessions._SESSIONS.get(name) if name else None
                new = (s.guion.entries[n0:] if s is before else s.guion.entries) if s else []
                closed = [(e.n, e.chosen) for e in (s.guion.entries if s else [])
                          if e.n in open0 and e.status == "closed"]
                _, texts = _texts(out)
                tx = [t for _, t in texts]
                images = sum(1 for c in out if getattr(c, "type", None) == "image") \
                    if isinstance(out, list) else 0
                ad = getattr(s, "adopted", None) if s else None
                _tm.record(fn.__name__, _bound(fn, args, kw), name, t0, out=out,
                           guion_new=new, closed=closed,
                           pending=len(s.guion.pending()) if s else 0,
                           lane=sessions._LANES.get(name, "guided") if name else None,
                           declared=(name in sessions._LANES) if name else None,
                           adopted=(ad[0] if ad else None), texts=tx, images=images,
                           ending=_tm.ends("\n".join(tx), _env.STOP, "▶ **Autonomous lane.**"))
            except Exception:                                 # noqa: BLE001
                pass
        return out
    return tool


def _finish(fn, args, kw, out, name, before, n0, sessions):
    """The answer after the session's bookkeeping and its lane (see `wrap`)."""
    from . import decisions as _dec
    if not name:
        return out
    s = sessions._SESSIONS.get(name)
    node = evidence = None
    if s is not None:
        new = s.guion.entries[n0:] if s is before else s.guion.entries
        if new:
            node, evidence = new[-1].node, new[-1].evidence
        # the bookkeeping never costs the answer: a failure here is the
        # record's, and the tool's result goes out as it is
        try:
            if new:
                _dec.close(s.guion, new[0], fn.__name__, _bound(fn, args, kw))
                text = "\n".join(t for _, t in _texts(out)[1])
                if _env.STOP in text:
                    _dec.open_pending(new[-1], text)
            note = _dec.adoption_note(s, fn.__name__)
            if note:
                out = _prepend(out, note)
        except Exception:                                 # noqa: BLE001
            pass
    lane = sessions._LANES.get(name, "guided")
    return apply(out, lane, name in sessions._LANES, name, node, evidence)
