"""P4 -- the decisions as data: pending, closed, adopted, set aside.

A tool that ends in a decision (its answer carries the guided pause) leaves
its guion entry PENDING, with the calls of its options. The next call that
takes one of them closes it and notes which (the letter when the call is the
option's own, "<tool>, other arguments" when it is the same tool with others);
record_decision on the same node closes it too. So the guided lane is
recorded without asking the analyst for anything more (art's BUG-0207).

`adopt` marks the model the analysis keeps; `abandon`, a candidate set aside.
The final-stage tools act on the CURRENT model, which is the last one
estimated: when an adoption exists and the current model is not it, they say
so. They warn; they do not refuse.

Nothing here decides (art's BUG-0180): it records what was decided.
"""
from __future__ import annotations

import ast
import re

_OPTION = re.compile(r"\*\*([A-Z])\)\*\*[^\n]*\n\s+`([^`\n]+)`")

#: the tools that USE the current model (N6, C6): they warn when it is not the adopted one
FINAL = {"forecast", "impulse_response", "variance_decomposition", "plot_forecast",
         "plot_impulse_response", "plot_variance_decomposition", "irf_bands"}


def options(text):
    """The options of a decision, [(letter, call)], in order."""
    return _OPTION.findall(text or "")


def _tool(call):
    return call.split("(", 1)[0].strip()


def _matches(call, bound):
    """Is `call` (an option's) the call made with arguments `bound`? Every
    argument the option names must have the value the call had."""
    try:
        node = ast.parse(call, mode="eval").body
        if not isinstance(node, ast.Call):           # prose, or an expression: no match
            return False
        kws = {k.arg: ast.literal_eval(k.value) for k in node.keywords}
    except (SyntaxError, ValueError, TypeError):
        return False
    # a placeholder ("...", "<why>") is the analyst's to fill: it does not count
    return all(str(bound.get(k)) == str(v) for k, v in kws.items()
               if not (isinstance(v, str) and (v.strip(". ") == "" or v.startswith("<"))))


def open_pending(entry, text):
    """Leave `entry` pending with the options of the decision in `text`."""
    opts = options(text)
    if not opts:
        return
    entry.status = "pending"
    entry.proposal = [c for _, c in opts]


def close(guion, new, tool, bound):
    """Close the pending decisions that the step `new` (made by `tool` with
    arguments `bound`) takes."""
    for e in guion.pending():
        if e is new or e.n >= new.n:
            continue
        chosen = None
        if tool == "record_decision" and bound.get("node") == e.node:
            chosen = "recorded"
        else:
            letters = "ABCDEFGHIJ"
            same = [i for i, c in enumerate(e.proposal) if _tool(c) == tool]
            for i in same:
                if _matches(e.proposal[i], bound):
                    chosen = letters[i]
                    break
            else:
                if same:
                    chosen = f"{tool}, other arguments"
        if chosen:
            e.status, e.chosen, e.closed_by = "closed", chosen, new.n


def model_of(s):
    """(kind, key) of the session's current model."""
    if s.current_kind() == "VEC":
        return ("VEC", s.vec_current)
    return ("VARMA", s.current)


def adoption_note(s, tool):
    """The warning of a final-stage tool acting on a model that is not the
    adopted one; "" when there is nothing to say."""
    a = getattr(s, "adopted", None)
    if tool not in FINAL or not a:
        return ""
    if a[0] == "UNIV":
        return ("⚠ The analysis ADOPTED THE UNIVARIATES (N5); this acts on the last "
                "system estimated, for comparison only.")
    if model_of(s) != a:
        return ("⚠ This acts on the CURRENT model, the last one estimated, which is not "
                "the ADOPTED one. adopt() it, or estimate the adopted one again (it is "
                "cached), before reading this as the analysis' result.")
    return ""
