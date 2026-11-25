"""P3 and P7: where an analysis stands, and what it hands over.

`where` reads the session and its guion and says where the analysis stands:
the path walked, the decisions still open with their options, what was
adopted, and the protocol's next node. It INFORMS; it does not decide and it
does not chain calls (art's BUG-0180): the open decision's options are the
analyst's, as they were when the tool that opened it answered.

`hand_over` gathers what the protocol asks for at the end (the result, the
yardstick that decided it, the caveats that stay open, the guion), in both
lanes. docs/DECISION_NODES.md is the map behind both.
"""
from __future__ import annotations

import os

from .guion import NODES, STATUS_MARK


def _names(s):
    return [x.name for x in s.series]


def _gate_failed(s):
    n1 = [e for e in s.guion.entries if e.node == "N1"]
    return bool(n1) and not str(n1[-1].evidence).startswith("passed")


def _desc_adopted(s, desc, vec_desc):
    a = s.adopted
    if not a:
        return None
    if a[0] == "UNIV":
        return "the univariate models (the diagonal system)"
    return desc(a[1]) if a[0] == "VARMA" else vec_desc(s.vec_fits[a[1]])


def next_step(s, name):
    """The protocol's next node, as information: (what, call)."""
    q = f'name="{name}"'
    if _gate_failed(s):
        return ("STOP — the gate failed (rule 2): report it; nothing is estimated on it", "")
    if s.gate is None:
        return ("N1 — certify the univariate base", f"run_gate({q})")
    if s.guion.pending():
        e = s.guion.pending()[-1]
        return (f"decide the open decision of {e.node} (step {e.n}, {e.tool}): its "
                "options are listed above", "")
    if getattr(s, "adopted", None):
        return ("N6 — use the adopted model, or close the analysis",
                f"hand_over({q})")
    nodes = {e.node for e in s.guion.entries}
    i1 = sum(int(x.model.d or 0) == 1 for x in s.series)
    if not s.fits and not s.vec_fits:
        if i1 >= 2 and "N1b" not in nodes and s.route == "U":
            return ("N1b — the canonical analysis of the levels, then the cointegration "
                    "question", f"canonical_analysis({q})")
        if s.route == "V":
            return ("N2 — the identification, route V: the matrices", f"identify_matrices({q})")
        return ("N2 — the identification, in its order: the residual CCFs first",
                f"identify_cross({q})")
    if s.current_kind() == "VEC":
        if "C8" not in nodes:
            return ("C8 — the yardstick for the VEC", f"evaluate({q})")
    elif "N5" not in nodes:
        if "N4" not in nodes:
            return ("N4 — the residuals of the candidate", f"check_residuals({q})")
        return ("N5 — the yardstick against the univariates", f"evaluate({q})")
    return ("N5 — adopt a model, or the univariates, with its reason",
            f'adopt({q}, model="...", why="...")')


def where(s, name, desc, vec_desc):
    names = _names(s)
    head = [f"# Where the analysis stands — {name}", "",
            f"Lane: {s.lane}" + ("" if s.lane_declared else " (not declared: the default)")
            + f" · route {s.route} · purpose: {s.purpose or 'not recorded'}"
            + f" · order: {' → '.join(names)}", ""]
    path = [f"[{e.n}] {e.node} {e.tool}"
            + (f" — {STATUS_MARK.get(e.status, e.status)}" if e.status else "")
            + (f" ({e.chosen})" if e.status == "closed" and e.chosen else "")
            for e in s.guion.entries]
    L = head + ["## The path", ""] + (path[-15:] if path else ["(nothing yet)"])
    if len(path) > 15:
        L.insert(len(head) + 2, f"(the last 15 of {len(path)} steps; export_guion has them all)")
    L += ["", "## Open decisions", ""]
    open_ = s.guion.pending()
    if not open_:
        L.append("None.")
    for e in open_:
        L.append(f"- {e.node} — {NODES.get(e.node, '')} (step {e.n}, {e.tool}):")
        L += [f"   **{'ABCDEFGHIJ'[i]})** `{c}`" for i, c in enumerate(e.proposal)]
    ad = _desc_adopted(s, desc, vec_desc)
    L += ["", "## Adopted", "", ad or "Nothing yet."]
    if s.abandoned:
        L.append("Set aside: " + "; ".join(
            (desc(k) if kd == "VARMA" else vec_desc(s.vec_fits[k])) + f" ({why})"
            for kd, k, why in s.abandoned))
    what, call = next_step(s, name)
    L += ["", "## Next, by the protocol", "", what + (f"\n   `{call}`" if call else ""), "",
          "This informs; it does not decide. The map: sima://doc/DECISION_NODES."]
    return "\n".join(L)


def _yardstick_lines(s):
    a = s.adopted
    if not a or a[0] == "UNIV":
        ev = [e for e in s.guion.entries if e.tool == "evaluate"]
        return [f"step {e.n}: {e.evidence}" for e in ev]
    if a[0] == "VEC":
        return [f"step {e.n}: {e.evidence}" for e in s.guion.entries
                if e.tool == "evaluate" and e.node == "C8"]
    p, q, dc, lk = a[1][:4]
    return [f"step {e.n}: {e.evidence}" for e in s.guion.entries
            if e.tool == "evaluate" and e.node == "N5" and e.args.get("p") == p
            and e.args.get("q") == q and bool(e.args.get("diagcov")) == bool(dc)
            and (e.args.get("links") or "") == (lk or "")]


def _raw_of(s):
    """The raw session the system came from (load_data), or None."""
    from . import session as _sess
    nm = (getattr(s, "v", None) or {}).get("raw") or s.name
    try:
        return _sess.get_raw(nm) if _sess.has_raw(nm) else None
    except Exception:                                        # noqa: BLE001
        return None


def _outliers(s):
    """characterize's outliers, per series: reported there, modelled nowhere."""
    r = _raw_of(s)
    out = []
    for nm, c in zip(getattr(r, "names", []) or [], getattr(r, "chars", None) or []):
        o = (c or {}).get("outliers") or []
        if o:
            dates = ", ".join(str(d) for d, _z in o[:6]) + (" …" if len(o) > 6 else "")
            out.append((nm, len(o), dates))
    return out


def caveats(s, desc=None):
    from .raw import PROVENANCE
    out = []
    if getattr(s, "route", "U") == "V":
        out.append("Route V (the vector first, through the gate): each series' regular "
                   "ARMA was replaced by a free AR(p)/MA(q) estimated with the cross "
                   "terms; the univariate models gave the mean, the deterministic terms "
                   "and the yardstick.")
    for x in s.series:
        path = getattr(x, "path", "") or ""
        try:
            with open(path) as fh:
                txt = fh.read()
        except OSError:
            txt = ""
        if PROVENANCE in txt:
            out.append(f"{x.name}: its model was built by sima's raw entry, not reviewed in art.")
        elif path.lower().endswith(".inp"):
            out.append(f"{x.name}: a specification (.inp), re-estimated at the load; its "
                       "univariate model was not validated in art.")
    for nm, k, dates in _outliers(s):
        out.append(f"{nm}: characterize flagged {k} outlier(s) ({dates}), modelled nowhere"
                   + ": the models built from the raw data carry no interventions"
                   + (", and on route V the outliers stay in the system's dynamics."
                      if getattr(s, "route", "U") == "V" else ".")
                   + " art's guided lane is where they are decided.")
    a = s.adopted
    if a and a[0] == "VARMA" and a[1] in s.fits:
        r = s.fits[a[1]].result
        if getattr(r, "ma_boundary", 0):
            out.append("The adopted fit sits on the MA invertibility wall: ill-defined "
                       "there, not an optimum (N4b).")
        if not a[1][2]:
            done = any(e.tool == "reorder" for e in s.guion.entries)
            out.append("The Cholesky order " + " → ".join(_names(s)) + " is an identifying "
                       "assumption of the responses and the decomposition (full covariance: "
                       "the innovations correlate)" + ("; another order was compared (reorder)."
                                                      if done else "; no other order was compared."))
    if a and a[0] == "VEC" and a[1] in s.vec_fits:
        vf = s.vec_fits[a[1]]
        if vf.theory:
            out.append(f"The rank r = {vf.r} was adopted on THEORY ({vf.theory}), not by the "
                       "bootstrap.")
        out.append("In a VEC the order of the series is the normalisation (β on the last "
                   f"r) and the Cholesky order: {' → '.join(vf.order)}.")
    out += _final_on_other(s, desc)
    for e in s.guion.entries:
        c = (e.args or {}).get("caveat") if e.tool == "record_decision" else None
        if c:
            out.append(f"{c} (step {e.n}, {e.node}).")
    for e in s.guion.pending():
        out.append(f"An open decision: {e.node} (step {e.n}, {e.tool}).")
    return out


#: the tools whose result is the model's USE: what the analyst reads off a fit
_USE = {"impulse_response": "responses", "plot_impulse_response": "responses",
        "variance_decomposition": "decomposition", "plot_variance_decomposition": "decomposition",
        "forecast": "forecasts", "plot_forecast": "forecasts"}


def _final_on_other(s, desc=None):
    """The responses, decompositions and forecasts read off a fit that is NOT
    the adopted model — in the trial run of 25-nov-2026 the univariates were
    adopted (rule 1) and the VAR's IRF and FEVD were read as an in-sample
    finding, and the hand-over said "None recorded". They are reported with
    the fit they came from, and the Cholesky order they rest on."""
    a = getattr(s, "adopted", None)
    if not a:
        return []
    adopted = None if a[0] == "UNIV" else a
    by_model = {}
    for e in s.guion.entries:
        what = _USE.get(e.tool)
        model = (e.args or {}).get("model")
        if not what or not model or e.kind == "VEC":
            continue
        key = next((k for k in s.fits if desc and desc(k) == model), None)
        if adopted is not None and adopted[0] == "VARMA" and key == adopted[1]:
            continue
        by_model.setdefault(model, []).append((e.n, what))
    out = []
    for model, items in by_model.items():
        whats = sorted({w for _n, w in items})
        steps = ", ".join(str(n) for n, _w in items)
        out.append(f"The {' and '.join(whats)} (steps {steps}) were read off {model}, which is "
                   "NOT the adopted model"
                   + (" (the univariates were adopted: rule 1)" if adopted is None else "")
                   + ": an in-sample reading, not the analysis' result.")
        if "full covariance" in model and ("responses" in whats or "decomposition" in whats):
            out.append("Those responses and that decomposition rest on the Cholesky order "
                       + " → ".join(_names(s)) + ", an identifying assumption"
                       + ("; another order was compared (reorder)."
                          if any(e.tool == "reorder" for e in s.guion.entries)
                          else "; no other order was compared."))
    return out


def hand_over(s, name, desc, vec_desc):
    ad = _desc_adopted(s, desc, vec_desc)
    L = [f"# The hand-over — {name}", "", "## The result", ""]
    if not ad:
        L += ["NOTHING ADOPTED: the analysis is not closed. Adopt a model, or the "
              f'univariates, with its reason: adopt(name="{name}", model="...", why="...").']
    else:
        L.append(f"Adopted: **{ad}**.")
        why = [e for e in s.guion.entries if e.tool == "adopt"]
        if why:
            L.append(f"Why (step {why[-1].n}): {why[-1].evidence}")
        if s.adopted[0] == "UNIV":
            L.append("No system beat the univariate models where it matters: that is the "
                     "finding, stated plainly (rule 1).")
    ys = _yardstick_lines(s)
    L += ["", "## The yardstick that decided it", ""]
    L += ys or ["NOT EVALUATED: rule 1 needs the yardstick (evaluate) before a system is kept."]
    if ys and s.adopted and s.adopted[0] == "VARMA":
        import re
        m = re.search(r"lower RMSE in (\d+) of (\d+) cells", ys[-1])
        if m and 2 * int(m.group(1)) <= int(m.group(2)):
            L.append(f"⚠ RULE 1: the adopted VARMA has the lower RMSE in only {m.group(1)} of "
                     f"{m.group(2)} cells. Out of sample it does not beat the univariates in "
                     "most of them: keeping it needs the reason that the cells where it gains "
                     "are the ones the analysis is about — and that reason is in the adoption "
                     "above, or it is missing.")
    cv = caveats(s, desc)
    L += ["", "## The caveats that stay open", ""] + ([f"- {c}" for c in cv] or ["None recorded."])
    if s.abandoned:
        L += ["", "## Set aside", ""] + [
            "- " + (desc(k) if kd == "VARMA" else vec_desc(s.vec_fits[k])) + f": {why}"
            for kd, k, why in s.abandoned]
    L += ["", "## The record", "",
          f'The path, node by node: `export_guion(name="{name}")` (JSON and HTML, next to '
          "the files)."]
    return "\n".join(L), ad, len(cv)
