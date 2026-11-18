"""The envelope of a node's output — one shape for every tool that asks.

art's BUG-0094 (envuelve_iteracion): an iteration whose output changes shape
from tool to tool is chaotic, and it lets the analyst off: if a section may be
missing, nobody can be asked why they decided without reading it. sima's tools
that stop at a decision already wrote the same four sections and the same stop
mark, but each by hand (fifteen copies of the mark); the VARMA core — the
cross identification, the estimation, the yardstick — did not write them at
all, and its menus carried no call (docs/MANUAL-jenkins-alavi.md §2.4 asks for
them in every tool). This module is the one place that writes them:

    ## 1 · TABLE                  what was computed
    ## 2 · WHAT IT SHOWS          how to read it
    ## 3 · CONCLUSIONS            the READINGS the tool draws from its facts
    ## 4 · DECISION — alternatives   each option with the exact call
    ⏸ Your decision.

The conclusions are readings, never a recommendation (DESIGN.md §2): which
alternative to take is the analyst's, and in the autonomous lane the LLM's,
argued in record_decision.
"""
from __future__ import annotations

#: The stop mark. In the guided lane the assistant stops here and waits.
STOP = "⏸ **Your decision.** (guided lane: I do not go on until you say)"

TABLE = "## 1 · TABLE"
SHOWS = "## 2 · WHAT IT SHOWS"
CONCLUSIONS = "## 3 · CONCLUSIONS"
DECISION = "## 4 · DECISION — alternatives"

_LETTERS = "ABCDEFGHIJ"


def option_lines(options) -> list:
    """`[(what, call), ...]` -> the lettered lines, each with its call:

        **A)** what
           `call`
    """
    return [f"**{_LETTERS[t]})** {what}\n   `{call}`" for t, (what, call) in enumerate(options)]


def envelope(title: str, table, shows, conclusions, options, after=(),
             stop: bool = True) -> str:
    """The four sections and the stop mark, as one text.

    `table`, `shows`, `conclusions`: lists of lines (or one string). `options`:
    `[(what, call), ...]`; with none, the section says so instead of being
    empty. `after`: lines between the options and the mark (a caveat that
    belongs to the decision). `stop=False` leaves the mark out, for a tool
    that reports a procedure rather than a decision.
    """
    def _l(x):
        return [x] if isinstance(x, str) else list(x or [])

    out = [title, "", TABLE, ""] + _l(table)
    out += ["", SHOWS, ""] + _l(shows)
    out += ["", CONCLUSIONS, ""] + _l(conclusions)
    out += ["", DECISION, ""]
    out += option_lines(options) if options else [
        "No alternative to choose between here: the step is a procedure."]
    if after:
        out += [""] + _l(after)
    if stop:
        out += ["", STOP]
    return "\n".join(out)
