"""The packages: what the analyst sees at the two points that matter most.

art packs each node's information into one answer, and closes its autonomous
lane with a delivery: the final model, the hardest nodes, the decisions that
went against its own reading. sima, one rung up, had neither: the gate showed
a table of likelihoods and went on, and the hand-over listed the adopted model
in one line. Two packages fill that gap (the autonomous trial run of
25/26-nov-2026):

* **The univariate base** (N0 + N1, `run_gate`): each series' model as the
  file carries it, where it comes from (art's guion beside the file: its
  version, its lane, why art adopted it, its diagnosis), the gate, and what
  the system is about to be built on (the order, the purpose, the route). It
  is the CHECKPOINT before the system: it stops in both lanes, unless the
  analyst declared `checkpoint=False` at the load, and then the hand-over
  says so.
* **The hand-over** (N7, `hand_over`, and the top of the HTML guion): the
  models first -- the univariates and the system adopted --, the yardstick
  that decided, what the model says (the responses and the decomposition as
  they were read), the decisions with their reasons, the caveats, what was
  set aside, the figures and the record.

It informs; it does not decide.
"""
from __future__ import annotations

import hashlib
import json
import os

#: The checkpoint mark. Unlike the guided pause (envelope.STOP), the lane
#: filter does not replace it: the autonomous lane stops here too.
CHECKPOINT = ("⏸ **Checkpoint: the univariate base.** (both lanes: the system is not "
              "built until the analyst has seen these models and says go on)")

#: Box-Jenkins notation, the suite's for everything (fue, drtran, drvarma)
BJ_NOTE = ("Box-Jenkins notation: φ(B) = 1 − φ₁B − …, θ(B) = 1 − θ₁B − …; "
           "ω the intervention's weights, in the transformed series' units.")

_SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
_SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


# --------------------------------------------------------------------------- #
#  One series' model                                                           #
# --------------------------------------------------------------------------- #

def _v(xs):
    return "(" + ", ".join(f"{float(v):.4g}" for v in xs) + ")"


def _date(x, at0):
    """fue's `at` is 0-based."""
    y, p = x.date_of(int(at0) + 1)
    return f"{p:02d}/{y}" if x.freq > 1 else f"{y}"


def model_line(x):
    """The model of LadderSeries `x`, as its file carries it, in one line:
    the transformation, the differences, the ARMA factors, the mean and the
    deterministic terms (interventions dated)."""
    from fue.forecast import _reconstruct_params
    m = x.model
    om, de, ar, ars, ma, mas, arf, maf, mu = _reconstruct_params(m, list(x.x_file))
    lam = float(m.boxlam)
    y = "ln y" if lam == 0 else "y" if lam == 1 else f"y^({lam:g})"
    d, D, s = int(m.d or 0), int(m.D or 0), int(x.freq)
    diff = ("∇" + (str(d).translate(_SUP) if d > 1 else "") if d else "") + \
           (f"∇{str(s).translate(_SUB)}" + (str(D).translate(_SUP) if D > 1 else "") if D else "")
    parts = []
    for c in ar:
        parts.append(f"AR({len(c)}) φ={_v(c)}")
    for c in ars:
        parts.append(f"SAR{str(s).translate(_SUB)}({len(c)}) Φ={_v(c)}")
    for c in ma:
        parts.append(f"MA({len(c)}) θ={_v(c)}")
    for c in mas:
        parts.append(f"SMA{str(s).translate(_SUB)}({len(c)}) Θ={_v(c)}")
    if arf or maf:
        parts.append(f"{len(arf) + len(maf)} fixed-frequency factor(s)")
    if not parts:
        parts.append("no ARMA (white noise)")
    parts.append(f"μ={float(mu):.4g}" if m.estimate_mu else "μ=0")
    det, harm = [], 0
    for itv, w, dl in zip(m.interventions, om, de):
        t = itv.type
        if t in ("cos", "sin"):
            harm += 1
        elif t == "alter":
            det.append("(−1)ᵗ")
        else:
            det.append(f"{t} {_date(x, itv.at)} ω={_v(w)}" + (f" δ={_v(dl)}" if dl else ""))
    if harm:
        det.insert(0, f"{(harm + 1) // 2} harmonic(s)")
    return (f"{diff}{' ' if diff else ''}{y}: " + "; ".join(parts)
            + ("; " + "; ".join(det) if det else ""))


def art_record(path):
    """What art's guion beside the file says about it, or None.

    art writes guion.json in each series' folder; the entry whose model is this
    file (same stem) carries its version, status, lane, why it was adopted,
    its diagnosis and the hash of the .pre it wrote. A file whose hash no
    longer matches was edited after art estimated it: it is an .inp again."""
    folder = os.path.dirname(os.path.abspath(os.path.expanduser(path)))
    g = os.path.join(folder, "guion.json")
    try:
        with open(g, encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        return None
    stem = os.path.splitext(os.path.basename(path))[0]
    hits = [e for e in d.get("entries", [])
            if isinstance(e, dict) and os.path.splitext(
                os.path.basename(str(e.get("inp_path") or e.get("out_path") or "")))[0] == stem]
    if not hits:
        return None
    e = next((h for h in reversed(hits) if h.get("status") == "adopted"), hits[-1])
    try:
        with open(path, "rb") as fh:
            sha = hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        sha = None
    return {"guion": g, "lane": d.get("carril") or "", "version": e.get("version"),
            "status": e.get("status") or "", "why": e.get("why_adopted") or "",
            "stats": e.get("stats") or {},
            "unchanged": (sha == e.get("pre_sha")) if e.get("pre_sha") and sha else None}


def _diag(st):
    if not st:
        return ""
    bits = []
    if st.get("sigma_a") is not None:
        bits.append(f"σₐ={float(st['sigma_a']):.4g}")
    if "q_pass" in st:
        qp = st.get("q_pvalues") or []
        bits.append("Q passes" if st["q_pass"] else
                    "Q FAILS" + (f" (min p={min(qp):.3f})" if qp else ""))
    if "jb_pass" in st:
        bits.append("JB passes" if st["jb_pass"] else
                    f"JB FAILS (p={float(st.get('jb_pvalue') or 0):.3f})")
    if st.get("n_extreme"):
        bits.append(f"{st['n_extreme']} residual(s) |z|>3")
    return ", ".join(bits)


def provenance(x):
    """(line, caveat or None): where series `x`'s model comes from."""
    from .raw import PROVENANCE
    path = getattr(x, "path", "") or ""
    try:
        with open(path) as fh:
            head = fh.read()
    except OSError:
        head = ""
    if PROVENANCE in head:
        return ("built by sima's raw entry (build_univariate), NOT reviewed in art",
                "built by sima, not reviewed in art")
    a = art_record(path)
    if a is None:
        if path.lower().endswith(".inp"):
            return ("a specification (.inp), re-estimated at the load; no art guion beside it",
                    "an .inp: its model was not validated")
        return ("a fue file with no art guion beside it: its history is not on record", None)
    lane = {"autonomo": "autonomous", "guiado": "guided"}.get(a["lane"], a["lane"] or "?")
    g = os.path.basename(os.path.dirname(a["guion"])) + "/guion.json"   # the same on every OS
    line = (f"art, {lane} lane: version {a['version']} of {g}, "
            f"{a['status'] or 'no status'}")
    if a["unchanged"] is False:
        line += "; the file was EDITED after art wrote it"
    diag = _diag(a["stats"])
    if diag:
        line += f". art's diagnosis: {diag}"
    cav = None
    st = a["stats"]
    if a["status"] != "adopted":
        cav = f"not the version art adopted ({a['status'] or 'no status'})"
    elif st and (st.get("q_pass") is False or st.get("jb_pass") is False):
        cav = "art delivered it with a diagnosis caveat: " + _diag(st)
    if a["unchanged"] is False:
        cav = "edited after art wrote it"
    return line, cav


def models_block(series, why=True, width=320):
    """The univariate models, one block per series: the model, where it comes
    from, and (with `why`) why art adopted it."""
    out = []
    for i, x in enumerate(series, 1):
        out.append(f"{i}. **{x.name}** — `{os.path.basename(x.path)}`")
        try:
            out.append(f"   {model_line(x)}")
        except Exception as e:                               # noqa: BLE001
            out.append(f"   (the model could not be written out: {e})")
        line, _c = provenance(x)
        out.append(f"   from: {line}")
        a = art_record(x.path) if why else None
        if a and a["why"]:
            w = " ".join(str(a["why"]).split())
            out.append("   why art kept it: " + (w if len(w) <= width else w[:width - 1] + "…"))
    out.append(BJ_NOTE)
    return out


# --------------------------------------------------------------------------- #
#  The univariate base (N0 + N1)                                               #
# --------------------------------------------------------------------------- #

def base_envelope(s, name, gate_text, next_opts, checkpoint=True, notes=()):
    """run_gate's answer when the gate passes: the univariate base, as one
    package, ending in the checkpoint (or, without it, in the lane's pause)."""
    from . import envelope as E
    names = [x.name for x in s.series]
    table = ["### The univariate models", ""] + models_block(s.series)
    table += ["", "### The gate", "", "```", gate_text.rstrip(), "```"]
    table += ["", "### What the system is built on", "",
              "- the order (Cholesky, normalisation): " + " → ".join(names),
              f"- the purpose: {s.purpose or 'not declared'}",
              f"- the route: {s.route}" + (" (the univariate models on the diagonal; the "
                                           "system adds the cross dynamics)" if s.route == "U"
                                           else " (the vector first, through the same gate)"),
              f"- the lane: {s.lane}" + ("" if s.lane_declared else " (not declared)")]
    shows = ["Each model is the yardstick of its series (rule 1) and, on route U, the "
             "diagonal the system starts from: what is wrong here is inherited by "
             "everything after.",
             "The gate certifies the CAST (the joint likelihood reproduces the sum of the "
             "univariate ones), not the models: their adequacy is art's diagnosis, "
             "quoted with each one."]
    shows += list(notes)
    concl = []
    cav = [(x.name, provenance(x)[1]) for x in s.series]
    cav = [(n, c) for n, c in cav if c]
    concl.append("The gate passed: the system can be estimated on these files.")
    if cav:
        concl += [f"{n}: {c}." for n, c in cav]
    else:
        concl.append("Every model comes with a clean record: nothing to take back to art "
                     "before the system.")
    opts = list(next_opts)
    back = ", ".join(n for n, _c in cav) or "a series"
    opts.append((f"go back to art for {back} first, and load the new files",
                 f'load_pre(name="{name}", paths_json="[...]")'))
    opts.append(("load the same files in another order (it is part of the model)",
                 f'load_pre(name="{name}", paths_json="[...]")'))
    txt = E.envelope(f"# N1 · The univariate base — {name}", table, shows, concl, opts)
    if checkpoint:
        txt = txt.replace(E.STOP, CHECKPOINT)
    return txt


# --------------------------------------------------------------------------- #
#  Digests of the use (N6), kept in the guion for the hand-over                #
# --------------------------------------------------------------------------- #

def irf_digest(names, O, lo, hi, info, horizon):
    """The responses as the hand-over shows them: the shock that was scaled
    (or every shock), each response at h = 1, the middle and the last horizon,
    and the permanent effect on the levels; a value whose band covers zero
    marked (n.s.)."""
    m = len(names)
    hs = sorted({1, max(1, horizon // 2), horizon})
    fac = info.get("factor")
    shocks = [fac[0]] if fac else range(m)
    perm = info.get("permanent")
    plo, phi_ = info.get("perm_lo"), info.get("perm_hi")

    def cell(v, a, b):
        if a is None:
            return f"{v:.4g}"
        ns = "" if (a > 0 or b < 0) else " n.s."
        return f"{v:.4g} [{a:.3g}, {b:.3g}]{ns}"

    head = "| response | " + " | ".join(f"h = {h}" for h in hs) + \
           (" | permanent |" if perm is not None else " |")
    sep = "|---" * (len(hs) + 1 + (perm is not None)) + "|"
    out = []
    for j in shocks:
        lab = (f"shock to {names[j]}"
               + (f", scaled to {fac[1]:g} on its own impact" if fac else ", one s.d."))
        out += [f"*{'levels' if info.get('levels') else 'differences'} — {lab}*", "",
                head, sep]
        for i in range(m):
            row = [cell(O[h, i, j], None if lo is None else lo[h, i, j],
                        None if hi is None else hi[h, i, j]) for h in hs]
            if perm is not None:
                row.append(cell(perm[i, j], None if plo is None else plo[i, j],
                                None if phi_ is None else phi_[i, j]))
            out.append(f"| {names[i]} | " + " | ".join(row) + " |")
        out.append("")
    return "\n".join(out).rstrip()


def fevd_digest(names, F, horizon):
    """The decomposition at the last horizon: the share of each shock (%)."""
    m = len(names)
    out = [f"*share of each shock in the forecast-error variance at h = {horizon} (%)*", "",
           "| series | " + " | ".join(names) + " |", "|---" * (m + 1) + "|"]
    for i in range(m):
        out.append(f"| {names[i]} | " + " | ".join(f"{F[horizon - 1, i, j]:.1f}"
                                                 for j in range(m)) + " |")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
#  The hand-over's sections                                                    #
# --------------------------------------------------------------------------- #

def system_block(s, key, desc):
    """The adopted VARMA: its description, its likelihood, and the cross
    coefficients with their t (the own ones are the univariate models')."""
    L = s.fits.get(key)
    if L is None:
        return [desc(key)]
    r = L.result
    out = [f"{desc(key)}; logL = {float(r.logL):.3f}" if hasattr(r, "logL")
           else desc(key)]
    rows = []
    for n, v, se in zip(r.names, r.x, r.std_errors):
        if "<-" not in str(n):
            continue
        t = v / se if se > 0 else float("nan")
        rows.append(f"| {n} | {v:.4g} | {t:.2f}{' *' if abs(t) > 1.96 else ''} |")
    if rows:
        out += ["", "| cross coefficient | estimate | t |", "|---|---|---|"] + rows
        out.append("(* |t| > 1.96. In the engine's units; the own coefficients are each "
                   "series' model, re-estimated jointly.)")
    return out


def use_block(s, desc):
    """What the model says: the digests the N6 tools left in the guion."""
    a = getattr(s, "adopted", None)
    out = []
    for e in s.guion.entries:
        dg = (e.args or {}).get("digest")
        if not dg or e.node not in ("N6", "C6"):
            continue
        on = (e.args or {}).get("model", "")
        off = ""
        if a and a[0] == "VARMA" and desc and on and on != desc(a[1]):
            off = " — NOT the adopted model"
        elif a and a[0] == "UNIV":
            off = " — a system the analysis did NOT adopt (rule 1): in-sample reading"
        opts = ", ".join(f"{k}={v}" for k, v in (e.args or {}).items()
                         if k in ("horizon", "levels", "scale"))
        out += [f"**Step {e.n}, {e.tool}** ({opts}) on {on or 'the current model'}{off}", "",
                dg, ""]
    return out


def decisions_block(s, width=260):
    out = []
    for e in s.guion.entries:
        if e.tool == "record_decision":
            a = e.args or {}
            why = " ".join(str(a.get("reason") or "").split())
            why = why if len(why) <= width else why[:width - 1] + "…"
            out.append(f"- **{e.node}** (step {e.n}, {a.get('decided_by') or '?'}): "
                       f"{e.decision or a.get('decision', '')}" + (f" — {why}" if why else ""))
        elif e.tool in ("adopt", "abandon"):
            out.append(f"- **{e.node}** (step {e.n}, {e.tool}): {e.evidence}")
    return out


def figures_block(s):
    try:
        d = s.guion.figures_dir()
        figs = sorted(f for f in os.listdir(d) if f.lower().endswith(".png"))
    except OSError:
        return []
    return [f"`{os.path.join(d, f)}`" for f in figs]
