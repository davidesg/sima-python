"""Cointegrated systems: sima's side of drvec (docs/STUDY-vec.md, docs/PLAN-vec.md).

The engine is drvec (Mauricio's VARMA-VEC by exact maximum likelihood, the
Python port of drvec C 0.13); it ships numbers and never argues. This module is
the assistant's: the checks before the rank (C0), the jobs that run the
bootstraps (C1, C6, C7), the reports around drvec's results, and the readings
sima computes itself (the half-lives and Gonzalo and Ng's decomposition, C5).
Only drvec's public API is used: ``fit``, ``rank_test``, ``read_pre``,
``to_levels_varma``, ``c_engine`` and the ``FitResult`` accessors.

Conventions, as drvec's: the VEC's matrices are in drvec's FILE ORDER, the
nabla Y2 block first and the Y1 block (the last r series, on which beta is
normalised) last; alpha is in Johansen's sign (negative is error-correcting).
"""
from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass, field

import numpy as np

from . import jobs

CASES = ("1", "2", "3", "pre")
CASE_TEXT = {"1": "case 1: E[nabla Y2] = 0, E[W] = 0 (no constant)",
             "2": "case 2: E[nabla Y2] = 0, E[W] free (a restricted constant)",
             "3": "case 3: E[nabla Y2] free, E[W] free (drifts)",
             "pre": "case pre: each drift free or held as its file's mean says (case 3's mask)"}
B_DEFAULT = 499
B_EXPLORE = 199          # below it a bootstrap is an exploration
# n / (M p) below it: the rank's verdict is conditional on p, and C1 offers the
# sweep over p (shakedown of 0.2.0, Martín Manjón and Treadway: 1985-1995,
# n / (M p) = 10.8, and 2016-2020 / 2022-2026, about 4-8, flip between p = 2 and
# p = 3; 1985-2008, 23.8, does not). A convention, not a test.
SMALL_N_PER_LAG = 15


# --------------------------------------------------------------------------- #
#  the specification (C0)                                                      #
# --------------------------------------------------------------------------- #

def case_arg(case):
    c = str(case).strip().lower()
    if c not in CASES:
        raise ValueError(f"case must be one of 1, 2, 3, pre (got {case!r}); the trend "
                         "(case 4) is for a single fit, in sweep")
    return c if c == "pre" else int(c)


def names_list(text):
    if not text:
        return []
    if isinstance(text, (list, tuple)):
        return [str(t).strip() for t in text if str(t).strip()]
    return [t.strip() for t in re.split(r"[,;]", str(text)) if t.strip()]


def drvec_order(names, normalise_on):
    """drvec's file order for a normalisation: the other series in the
    session's order, then the r series beta is normalised on (the Y1 block)."""
    rest = [n for n in names if n not in normalise_on]
    return rest + list(normalise_on)


def nodrift_index(order, nodrift):
    return [order.index(n) + 1 for n in nodrift] if nodrift else None


def p_rule(series):
    """p = the AR order of the univariate models in nabla, plus 1 (a d = 0
    series: its AR order in levels). -> (p, per series)."""
    per = {}
    for x in series:
        ar = int(x.orders()[0])
        per[x.name] = ar + 1 if int(x.model.d or 0) >= 1 else max(1, ar)
    return max(per.values()) if per else 1, per


def checks(s, mixed=False):
    """STUDY-vec §2.4: each check a refusal with its reason, or a warning.
    -> (refusals, warnings, facts)."""
    refuse, warn = [], []
    d = {x.name: int(x.model.d or 0) for x in s.series}
    D = {x.name: int(x.model.D or 0) for x in s.series}
    for nm in d:
        if d[nm] >= 2:
            refuse.append(f"{nm} has d = {d[nm]}: drvec models I(1) systems only. Take "
                          "the series back to art and reconsider its d there.")
        if D[nm] > 0:
            refuse.append(f"{nm} has a seasonal difference (D = {D[nm]}): drvec refuses it. "
                          "Its seasonality must be DETERMINISTIC in its file: back to art "
                          'with the objective "multivariante".')
    i1 = [nm for nm in d if d[nm] == 1]
    i0 = [nm for nm in d if d[nm] == 0]
    if len(i1) < 2 and not (mixed and i1 and i0):
        refuse.append(f"{len(i1)} series with d = 1: the cointegration question needs "
                      "two or more (or the mixed case, mixed=True, with one I(1) and "
                      "one I(0) series).")
    if i0 and not mixed:
        refuse.append(f"{', '.join(i0)} {'has' if len(i0) == 1 else 'have'} d = 0: the "
                      "MIXED case. It is an option, never the default: ask for it with "
                      "mixed=True (the I(0) series go in the Y1 block, and r >= "
                      f"{len(i0)}).")
    try:
        import drvec
        data = drvec.read_pre(list(s.files))
    except Exception as e:                                   # noqa: BLE001
        refuse.append(f"drvec does not take these files: {e}")
        data = None
    if s.gate:
        moved = [r["series"] for r in s.gate.get("rows", [])
                 if r.get("move", 0) > 1e-3 and not r.get("trimmed")]
        if moved:
            warn.append(f"{', '.join(moved)} moved at the gate: SPECIFICATIONS, not "
                        "optima. drvec reads only their transformation, deterministic "
                        "terms and mean flag, so the rank does not depend on their ARMA; "
                        "but their univariate model is not validated, and it is the "
                        "yardstick (C8).")
    facts = {"d": d, "D": D, "i1": i1, "i0": i0}
    if data is not None:
        n_gate = min(len(x.levels()) for x in s.series)
        facts["nobs"] = int(data.nobs_raw)
        if int(data.nobs_raw) != n_gate:
            warn.append(f"drvec's window has {data.nobs_raw} observations and the gate's "
                        f"{n_gate}: drvec lines the files up on the intersection of their "
                        "dates, the ladder at their common end. The comparison with the "
                        "univariates (C8) uses the ladder's window.")
        else:
            facts["window"] = "the same as the gate's"
        facts["pre_mean_free"] = list(getattr(data, "pre_mean_free", []) or [])
    return refuse, warn, facts


# --------------------------------------------------------------------------- #
#  the rank test: the job and its report (C1)                                  #
# --------------------------------------------------------------------------- #

def rank_args(spec, B, multistart=0):
    return {"p": int(spec["p"]), "q": int(spec["q"]), "case": str(spec["case"]),
            "nodrift": nodrift_index(spec["order"], spec.get("nodrift")) or [],
            "B": int(B), "multistart": int(multistart), "names": list(spec["order"])}


def job_rank_test(job, folder):
    import drvec
    from .provenance import of_drvec
    a = job["args"]
    files = job["files"]
    M = len(files)
    prog = jobs.Progress(folder, a["B"], range(M - 1))
    eng = job["engine"][0]
    rt = drvec.rank_test(files, a["p"], a["q"], case=case_arg(a["case"]),
                         nodrift=a["nodrift"] or None, bootstrap=a["B"], progress=prog,
                         multistart=a["multistart"], seed=job.get("seed"),
                         workers=job["workers"], engine=eng,
                         folder=os.path.join(folder, "c") if eng == "c" else None)
    prog.write(force=True)
    jobs.write_text(os.path.join(folder, "rank.out"), rt.out_text("rank"))
    jobs.write_text(os.path.join(folder, "rank.boot"), rt.boot_text(drvec.__version__))
    comps = []
    for b in rt.bootstraps:
        cv = rt.critical_values(b.h0)
        comps.append({"h0": b.h0, "lr": b.lr, "B": len(b.reps),
                      "ok": b.nok,
                      "simfail": sum(r.status == "simfail" for r in b.reps),
                      "fitfail": sum(r.status == "fitfail" for r in b.reps),
                      "cv": list(b.cv) if b.cv else None, "pvalue": b.pvalue,
                      "asym_cv": list(cv) if cv else None,
                      "asym_verdict": rt.verdict(b.h0)})
    ranks = [{"r": r, "logL": rt.ll[r], "npar": rt.npar[r],
              "ma_boundary": bool(rt.boundary[r])} for r in range(M)]
    return {"tool": "rank_test", "names": list(rt.names), "M": M, "nobs": rt.nobs,
            "p": a["p"], "q": a["q"], "case": a["case"], "nodrift": a["nodrift"],
            "B": a["B"], "multistart": a["multistart"], "drift_how": rt.drift_how,
            "ranks": ranks, "comparisons": comps,
            "provenance": of_drvec(rt.provenance), "files": ["rank.out", "rank.boot"]}


def mc_error(p, n):
    return math.sqrt(max(p * (1.0 - p), 0.0) / max(n, 1))


def propose_rank(res):
    """r-hat read from the bootstrap's critical values at 5 %, sequentially;
    -> (r_hat or None, text, tie). r_hat = M - 1 with "at least" when every
    comparison rejects. Below B_EXPLORE no tie is flagged: the result is
    already an exploration, and at small B almost every p-value is within two
    Monte Carlo errors of 5 % (decided 2026-10-18)."""
    M = res["M"]
    flag_ties = res["B"] >= B_EXPLORE
    by = {c["h0"]: c for c in res["comparisons"]}
    tie = []
    for h in range(M - 1):
        c = by.get(h)
        if c is None:
            return None, (f"the comparison r = {h} -> {h + 1} did not run (a fit failed): "
                          "no rank can be read beyond it"), tie
        if c["cv"] is None:
            return None, (f"r = {h} -> {h + 1}: fewer than 10 replications ok, no critical "
                          "value"), tie
        if flag_ties and c["pvalue"] is not None and abs(c["pvalue"] - 0.05) <= 2 * mc_error(c["pvalue"], c["ok"]):
            tie.append(h)
        if c["lr"] <= c["cv"][1]:
            return h, f"r = {h}: the first comparison not rejected at 5 % (LR {c['lr']:.2f} " \
                      f"<= {c['cv'][1]:.2f})", tie
    return M - 1, (f"every comparison rejects at 5 %: AT LEAST M - 1 = {M - 1} (drvec "
                   "fits r <= M - 1; full rank is not tested here)"), tie


def small_sample(res):
    """n / (M p) when it is below SMALL_N_PER_LAG (the rank is then read at the
    neighbouring orders too), else 0."""
    v = res["nobs"] / max(1, res["M"] * int(res["p"]))
    return v if v < SMALL_N_PER_LAG else 0.0


def sweep_orders(p):
    return [x for x in (int(p) - 1, int(p), int(p) + 1) if x >= 1]


def rank_cell_text(res):
    """A sweep's rank cell: r-hat and each comparison's LR and bootstrap p."""
    r_hat, _why, _t = propose_rank(res)
    return (f"r-hat {r_hat} (B = {res['B']}); "
            + "; ".join(f"r={c['h0']}: LR {c['lr']:.2f}, 95% {c['cv'][1]:.2f}, p {c['pvalue']:.3f}"
                        for c in res["comparisons"] if c["cv"]))


def rank_report(res, call, folder=None, prov_line=""):
    M, B = res["M"], res["B"]
    names = res["names"]
    case = res["case"]
    L = [f"# The cointegration rank — sequential LR test on the exact likelihood, "
         f"parametric bootstrap (C1)",
         f"*(drvec; p = {res['p']}, q = {res['q']}, {CASE_TEXT.get(str(case), case)}; "
         f"M = {M}: {', '.join(names)}; n = {res['nobs']}; B = {B})*", "",
         "## 1 · TABLE", "",
         "_[Claude: show the block below AS IT IS; do not build your own table]_", "", "```",
         "  r        logL   npar"]
    for r in res["ranks"]:
        L.append(f"  {r['r']}  {r['logL']:12.4f}   {r['npar']:4d}"
                 + ("   MA on the boundary" if r.get("ma_boundary") else ""))
    L += ["", "  H0       LR      bootstrap: 90%      95%      99%   p-value  MC err"
          "   ok / B   asymptotic 5% (orientation)"]
    for c in res["comparisons"]:
        h = c["h0"]
        cv = c["cv"] or [float("nan")] * 3
        pv = c["pvalue"] if c["pvalue"] is not None else float("nan")
        asym = (f"{c['asym_cv'][1]:8.2f}  {c['asym_verdict']}" if c["asym_cv"] else
                "   none (case 3/pre: bootstrap only)")
        L.append(f"  r={h}  {c['lr']:8.2f}      {cv[0]:8.2f} {cv[1]:8.2f} {cv[2]:8.2f}"
                 f"   {pv:6.3f}  {mc_error(pv, c['ok']) if c['ok'] else float('nan'):6.3f}"
                 f"   {c['ok']:3d}/{c['B']:<4d} {asym}")
    L += ["```", "", "## 2 · WHAT IT SHOWS", ""]
    L.append("Each comparison tests H0: rank r against r + 1 with the EXACT likelihood "
             "ratio (a lambda-max-type test, not Johansen's trace), calibrated by "
             f"simulating {B} samples from the fitted rank-r model and refitting each at r "
             "and r + 1 by the same route as the data. Negative LR* are kept (the exact LR "
             "sits about log T below Johansen's conditional one).")
    for c in res["comparisons"]:
        if c["cv"]:
            verdict = ("REJECTED at 5 %" if c["lr"] > c["cv"][1] else "not rejected at 5 %")
            L.append(f"- r = {c['h0']} -> {c['h0'] + 1}: LR {c['lr']:.2f} against the "
                     f"bootstrap's 95 % value {c['cv'][1]:.2f}: {verdict}; p {c['pvalue']:.3f} "
                     f"(floor 1/(B+1) = {1 / (c['ok'] + 1):.3f}).")
        if c["ok"] < 0.9 * c["B"]:
            L.append(f"  WARNING: only {c['ok']} of {c['B']} replications ok "
                     f"({c['simfail']} simulation and {c['fitfail']} fit failures): the "
                     "percentiles rest on fewer samples than asked.")
    if res["comparisons"] and res["comparisons"][0]["asym_cv"] is None:
        L.append("- No asymptotic table for this case: the bootstrap is the only "
                 "calibration.")
    elif res["comparisons"]:
        L.append("- The asymptotic column is ORIENTATION ONLY: at these sample sizes the "
                 "sequential test over-rejects with it. It is never the verdict.")
    if B < B_EXPLORE:
        L.append(f"- B = {B} is below {B_EXPLORE}: an EXPLORATION, not a verdict. Rerun "
                 f"with B >= {B_DEFAULT} before deciding.")
    r_hat, why, tie = propose_rank(res)
    L += ["", "## 3 · CONCLUSIONS", ""]
    L.append(f"Proposed r-hat, read from the bootstrap's critical values: "
             f"{'none' if r_hat is None else (('at least ' if why.startswith('every') else '') + str(r_hat))}"
             f" — {why}. The tool PROPOSES; the rank is the analyst's decision (the "
             "autonomous lane: yours, with its reason written down).")
    if tie:
        L.append(f"A TIE at r = {', '.join(map(str, tie))}: the p-value is within two Monte "
                 "Carlo errors of 5 %. Estimate BOTH ranks and compare (their "
                 "restrictions, responses and yardstick), not on paper; a Monte Carlo "
                 "check with another seed is the other tool.")
    L.append("Every claim from here is conditional on r, on p, q and the case, and on the "
             "files' transformations and deterministic terms.")
    small = small_sample(res)
    if small:
        L.append(f"SMALL SAMPLE FOR THIS ORDER: n / (M p) = {small:.1f} (below "
                 f"{SMALL_N_PER_LAG}). Here the bootstrap's verdict can flip with p, and the "
                 "LR need not be monotone in it (beta and alpha at a given r hardly move; "
                 "the rank's evidence does). The verdict is conditional on p = "
                 f"{res['p']}: read the rank at the neighbouring orders before deciding "
                 "(the autonomous lane runs the sweep first).")
    L += ["", "## 4 · DECISION — alternatives", ""]
    opts = []
    if r_hat == 0:
        opts.append(("r = 0: no stationary combination — the univariates' differences are "
                     "right jointly. Back to N2: the VARMA in differences on drvarma's "
                     "ladder, in this session", f'identify_cross(name="{call}")'))
        opts.append(("adopt r = 1 on THEORY against the bootstrap (written in the guion as "
                     "such)" + (" — the tie at r = 0 asks for it: estimate both and compare"
                                if 0 in tie else ""),
                     f'estimate_vec(name="{call}", r=1, theory="...")'))
    elif r_hat is not None and 0 < r_hat < M - 1:
        opts.append((f"adopt r = {r_hat}: the VEC (C2), normalised on the last {r_hat} "
                     "series unless you say on which", f'estimate_vec(name="{call}", r={r_hat})'))
    elif r_hat == M - 1:
        opts.append((f"AT LEAST M - 1 = {M - 1}: adopt r = {M - 1}, one common trend",
                     f'estimate_vec(name="{call}", r={M - 1})'))
        opts.append(("M - 1 against M is a unit-root question: is there a common trend at "
                     "all? The canonical analysis (a component near 1?), art's unit-root "
                     "table per series; if the levels look stationary, the VARMA in levels "
                     "(route V with d = 0) or the series back to art",
                     f'canonical_analysis(name="{call}")'))
    else:
        opts.append(("no rank can be read: rerun with a larger B, or another p or case",
                     f'rank_test(name="{call}", B={max(B, B_DEFAULT)})'))
    for h in tie:
        if h + 1 < M and not (r_hat == 0 and h == 0):    # (B) already offers r = 1
            opts.append((f"the tie: estimate r = {h + 1} as well and compare",
                         f'estimate_vec(name="{call}", r={h + 1}, theory="tie: ...")'))
    if small:
        opts.insert(0, (f"the rank at p = {', '.join(map(str, sweep_orders(res['p'])))} "
                        "(the sweep over p, one cached rank job per order) before deciding",
                        f'sweep(name="{call}", p="{",".join(map(str, sweep_orders(res["p"])))}", '
                        f'B={B})'))
    opts.append(("the bootstrap distribution against the observed LR (the figure)",
                 f'plot_rank_bootstrap(name="{call}")'))
    if tie:
        opts.append(("a Monte Carlo check of the edge-of-5 % verdict: the same bootstrap "
                     "with another seed (always on the Python engine)",
                     f'rank_test(name="{call}", B={B}, seed=12345)'))
    for t, (what, cl) in enumerate(opts):
        L.append(f"**{'ABCDEFGH'[t]})** {what}\n   `{cl}`")
    L += ["", "⏸ **Your decision.** (guided lane: I do not go on until you say)"]
    if folder:
        L += ["", f"The engine's files: {os.path.join(folder, 'rank.out')} and "
              f"{os.path.join(folder, 'rank.boot')}."]
    if prov_line:
        L += ["", prov_line]
    return "\n".join(L), r_hat


# --------------------------------------------------------------------------- #
#  the adopted VEC (C2)                                                        #
# --------------------------------------------------------------------------- #

@dataclass
class VecFit:
    key: tuple
    fit: object                    # drvec.FitResult
    files: list                    # in drvec's order
    order: list                    # the names, in drvec's order
    p: int
    q: int
    r: int
    case: str
    nodrift: list
    restriction: dict = field(default_factory=dict)
    multistart: int = 0
    rank_job: str = ""
    theory: str = ""

    @property
    def M(self):
        return len(self.order)

    def y1(self):
        return self.order[self.M - self.r:]

    def y2(self):
        return self.order[:self.M - self.r]

    def call_kw(self):
        """drvec.fit's keywords for this fit (and its bootstraps)."""
        kw = dict(case=case_arg(self.case), nodrift=nodrift_index(self.order, self.nodrift),
                  multistart=self.multistart)
        kw.update(restriction_kw(self.restriction, self.order, self.r))
        return kw


def vec_key(order, p, q, r, case, nodrift, restriction=None, multistart=0):
    rk = tuple(sorted((k, str(v)) for k, v in (restriction or {}).items()))
    return (tuple(order), int(p), int(q), int(r), str(case), tuple(nodrift or ()), rk,
            int(multistart))


def restriction_kw(restr, order, r):
    """sima's restriction (names) -> drvec.fit's keywords (1-based indices)."""
    kw = {}
    if not restr:
        return kw
    if restr.get("weakex"):
        kw["weakex"] = order.index(restr["weakex"]) + 1
    if restr.get("alpha") is not None:
        kw["alpha"] = [list(map(float, row)) for row in restr["alpha"]]
    if restr.get("fixb2") is not None:
        kw["fixb2"] = float(restr["fixb2"])
    if restr.get("fixb2row"):
        kw["fixb2row"] = {order.index(nm) + 1: float(v) for nm, v in restr["fixb2row"].items()}
    if restr.get("xsys"):
        kw["xsys"] = [order.index(nm) + 1 for nm in restr["xsys"]]
    if restr.get("xpre"):
        kw["xpre"] = list(restr["xpre"])
        kw["xlink"] = restr["xlink"]
    return kw


def fit_vec(files, order, p, q, r, case, nodrift, restriction=None, multistart=0,
            fdhess=True, **extra):
    import drvec
    kw = dict(case=case_arg(case), nodrift=nodrift_index(order, nodrift),
              multistart=int(multistart), fdhess=fdhess)
    kw.update(restriction_kw(restriction, order, r))
    kw.update(extra)
    return drvec.fit(list(files), int(p), int(q), int(r), **kw)


_BANNER = re.compile(r"^={20,}\s*$")


def out_block(text, title):
    """One section of drvec's .out, verbatim: from its banner to the next."""
    lines = text.splitlines()
    for i in range(1, len(lines) - 1):
        if lines[i].strip() == title and _BANNER.match(lines[i - 1]) and _BANNER.match(lines[i + 1]):
            j = i + 2
            while j < len(lines) - 1 and not (_BANNER.match(lines[j])
                                              and j + 1 < len(lines) and lines[j + 1].strip()
                                              and j + 2 < len(lines) and _BANNER.match(lines[j + 2])):
                j += 1
            return "\n".join(lines[i - 1:j]).rstrip()
    return ""


def search_lines(text):
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("Search:"):
            out = [ln]
            for x in lines[i + 1:i + 30]:
                if not x.strip():
                    break
                out.append(x)
            return "\n".join(out)
    return ""


def canonical_beside_beta(canon, order, vf):
    """STUDY-vec §3.12: the canonical weights of the least predictable
    components beside beta-hat, normalised the same way (on the Y1 series)."""
    if not canon or "weights" not in canon:
        return ""
    names = canon["names"]
    W = np.asarray(canon["weights"], float)
    lam = canon["lam"]
    beta = np.asarray(vf.fit.beta, float)              # (M, r), drvec's order
    out = ["Beside beta-hat: the canonical analysis' least predictable components "
           "(Box and Tiao), normalised on the same series:"]
    y1 = vf.y1()
    for c in range(vf.r):
        if c >= W.shape[0]:
            break
        w = np.array([W[c][names.index(nm)] for nm in vf.order])
        piv = w[vf.order.index(y1[c])]
        b = beta[:, c]
        if abs(piv) < 1e-12:
            out.append(f"  component {c + 1} has no weight on {y1[c]}: not comparable")
            continue
        out.append(f"  relation {c + 1}  " + "  ".join(
            f"{nm} {b[k]:+.3f}" for k, nm in enumerate(vf.order)))
        out.append(f"  component {c + 1} (lam {lam[c]:.3f})  " + "  ".join(
            f"{nm} {w[k] / piv:+.3f}" for k, nm in enumerate(vf.order)))
    out.append("  They can disagree: a reading is not the test. A disagreement is "
               "reported, not resolved by sima.")
    return "\n".join(out)


def ridge_text(f):
    """E1's lesson: a search that stopped on a flat ridge is not a maximum."""
    if f.termcode in (1, 2):
        return ""
    return (f"THE OPTIMISER STOPPED ON CRITERION {f.termcode}, not on the gradient: this "
            "point is NOT A DEMONSTRATED MAXIMUM (a flat ridge, as Lutkepohl's E1 "
            "2 1 1 -case 2). Do not present it as an optimum. Options: more starts "
            "(estimate_vec with multistart=5), a lower q, or declare it as such in the "
            "guion.")


def alpha_reading(vf):
    f = vf.fit
    A = np.asarray(f.alpha, float)
    out = ["alpha, read from the matrix (Johansen's sign: negative is error-correcting "
           "on the variable the relation is normalised on; on the others the correction "
           "has the sign of -beta):"]
    se = {p.label: p.se for p in f.params if p.kind == "alpha"}
    for c in range(vf.r):
        for i, nm in enumerate(vf.order):
            lab = f"D.{nm} <- ec{c + 1}"
            s = se.get(lab, float("nan"))
            t = A[i, c] / s if s and np.isfinite(s) and s > 0 else float("nan")
            out.append(f"  {lab:<28} {A[i, c]:+.4f}  (t {t:+.2f})"
                       + ("  adjusts" if np.isfinite(t) and abs(t) >= 2 else ""))
    out.append("  A |t| < 2 is a candidate for weak exogeneity: test it by LR "
               "(test_restriction), never by this t or the .out's Wald.")
    return "\n".join(out)


def estimate_report(vf, call, rank_note, canon_text="", prov_line="", purpose=None):
    f = vf.fit
    text = f.out_text("vec")
    L = [f"# The VEC — rank r = {vf.r}, VARMA({vf.p},{vf.q}) short run, "
         f"{CASE_TEXT.get(str(vf.case), vf.case)} (C2)",
         f"*(drvec, exact ML; n = {f.nobs}; logL {f.loglik:.4f}, {f.npar} parameters; "
         f"standard errors from the finite-difference Hessian)*", "",
         "THE ROLES (they are part of the model): beta is normalised on "
         f"{', '.join(vf.y1())} (the Y1 block, the last {vf.r} of drvec's order); the "
         f"nabla Y2 block is {', '.join(vf.y2()) or '(empty)'}. drvec's order "
         f"({', '.join(vf.order)}) is ALSO the Cholesky order of the level responses. "
         "Another normalisation is another fit (estimate_vec with normalise_on), not "
         "a reorder.", "",
         f"THE RANK it rests on: {rank_note}", ""]
    if purpose:
        L += [f"THE PURPOSE recorded at N1c: {purpose}.", ""]
    rid = ridge_text(f)
    if rid:
        L += [rid, ""]
    L += ["## 1 · TABLE", "",
          "_[Claude: show the blocks below AS THEY ARE: they are drvec's .out]_", "", "```"]
    sl = search_lines(text)
    if sl:
        L += [sl, ""]
    for title in ("Estimated Parameters and Standard Deviations",
                  "Vector Error Correction Model", "Cointegration Diagnostics",
                  "MULTIVARIATE RESIDUAL DIAGNOSTICS"):
        b = out_block(text, title)
        if b:
            L += [b, ""]
    L += ["```", "", "## 2 · WHAT IT SHOWS", "", alpha_reading(vf), ""]
    d = f.diagnostics()
    if d is not None:
        L.append(f"Residuals: Hosking's Q({d.hosking_df}) = {d.hosking_Q:.2f}, p "
                 f"{d.hosking_p:.4f} at {d.hosking_lags} lags; multivariate JB({d.jb_df}) = "
                 f"{d.jb:.2f}, p {d.jb_p:.4f}.")
    sh = re.findall(r"relation (\d+): the Y1 block carries\s+([\d.]+)%", text)
    for rel, pct in sh:
        if float(pct) < 5.0:
            L.append(f"Relation {rel}: the Y1 block carries only {pct} % of the weight — a "
                     "DUBIOUS normalisation: the relation hardly involves the series it is "
                     "solved for. Normalise on another series.")
    if f.ma_on_boundary:
        L.append("An MA root is on the unit circle: the .out prints no s.e. for Theta; "
                 "lower q.")
    if canon_text:
        L += ["", canon_text]
    L += ["", "The .out's Wald statistics (Joint Hypothesis Tests) are NOT CITABLE: they "
          "depend on the normalisation, and under H0: alpha = 0 beta is not identified. "
          "Every restriction is tested by LR (test_restriction).", "",
          "## 3 · CONCLUSIONS", "",
          f"A VEC with {vf.r} stationary relation(s) among {vf.M} series, conditional on "
          "r, p, q, the case and the files' transformations. In sample until the "
          "yardstick (C8).", "", "## 4 · DECISION — alternatives", ""]
    opts = [("who corrects: weak exogeneity, series by series (LR)",
             f'test_restriction(name="{call}", weakex="{vf.order[0]}")'),
            ("the long run read: theta, the half-lives, Gonzalo and Ng's permanent and "
             "transitory shocks", f'long_run(name="{call}")'),
            ("the level responses and their bands (a job)",
             f'impulse_response(name="{call}")  /  irf_bands(name="{call}")'),
            ("the yardstick against the univariates (C8)",
             f'evaluate(name="{call}", estwin=...)'),
            ("robustness: p, the case, the subsample (a sweep of jobs)",
             f'sweep(name="{call}", p="{max(1, vf.p - 1)},{vf.p},{vf.p + 1}")')]
    if rid:
        opts.insert(0, ("more starts on the ridge", f'estimate_vec(name="{call}", r={vf.r}, '
                                                  "multistart=5)"))
    for t, (what, cl) in enumerate(opts):
        L.append(f"**{'ABCDEFGH'[t]})** {what}\n   `{cl}`")
    L += ["", "⏸ **Your decision.** (guided lane: I do not go on until you say)"]
    if prov_line:
        L += ["", prov_line]
    return "\n".join(L)


# --------------------------------------------------------------------------- #
#  restrictions (C3) and inputs (C4)                                           #
# --------------------------------------------------------------------------- #

def lr_from(ll_free, ll_restr, df):
    from scipy.stats import chi2
    lr = 2.0 * (ll_free - ll_restr)
    return lr, (float(chi2.sf(max(lr, 0.0), df)) if df > 0 else float("nan"))


def restriction_report(base, rf, restr, call, label, prov_line=""):
    """The LR of a restriction against the free model: drvec's (its free fit is
    the C's: one est() for -alpha/-weakex, no ladder for -fixb2row) and, when it
    is higher, the best free fit sima knows: the adopted VEC (STUDY-vec Q7)."""
    f = base.fit
    rl = rf.restriction_lr
    best = f.loglik
    L = [f"# Restriction — {label} (C3)",
         f"*(on the VEC r = {base.r}, VARMA({base.p},{base.q}), "
         f"{CASE_TEXT.get(str(base.case), base.case)}; drvec's order {', '.join(base.order)})*",
         "", "## 1 · TABLE", "", "```"]
    if rl is not None:
        df = rl.df
        L.append(f"drvec's LR ({rl.kind}): free logL {rl.ll_free:.4f}, restricted "
                 f"{rl.ll_restricted:.4f}; LR = {rl.lr:.4f}, df {df}, p {rl.pvalue:.4f}")
        ll_free_drvec = rl.ll_free
        ll_r = rl.ll_restricted
    else:
        df = restr.get("_df", 0)
        ll_free_drvec = None
        ll_r = rf.loglik
        L.append(f"drvec prints no LR for this restriction (-fixb2 alone): restricted "
                 f"logL {ll_r:.4f}, df {df} (the entries of B2 held)")
    lr_b, p_b = lr_from(best, ll_r, df)
    L.append(f"against the ADOPTED VEC (the best free fit sima knows): free logL "
             f"{best:.4f}; LR = {lr_b:.4f}, df {df}, p {p_b:.4f}")
    L += ["```", "", "## 2 · WHAT IT SHOWS", ""]
    used = "the adopted VEC's"
    if ll_free_drvec is not None and best > ll_free_drvec + 1e-6:
        L.append(f"drvec's free model for this LR is weaker than the adopted VEC "
                 f"({ll_free_drvec:.4f} < {best:.4f}): the C fits it from a cold start "
                 "(one est() for alpha and weakex; no ladder for fixb2row), so its LR is "
                 "understated. The LR read is the one against the adopted VEC; both are "
                 "shown.")
    elif ll_free_drvec is not None and ll_free_drvec > best + 1e-6:
        used = "drvec's"
        lr_b, p_b = rl.lr, rl.pvalue
        L.append(f"drvec's free fit is HIGHER than the adopted VEC ({ll_free_drvec:.4f} > "
                 f"{best:.4f}): the adopted VEC is not the maximum. The LR read is drvec's; "
                 "re-estimate with multistart.")
    else:
        L.append("drvec's free model and the adopted VEC agree: one LR.")
    verdict = ("REJECTED at 5 %" if p_b < 0.05 else "not rejected at 5 %")
    L.append(f"The restriction ({label}) is {verdict}: LR {lr_b:.2f}, chi2({df}), p {p_b:.4f}"
             f" ({used} free fit). An asymptotic chi2 test given r: beta is superconsistent, "
             "alpha and the short run standard. No bootstrap of this LR exists in drvec.")
    if restr.get("weakex"):
        L.append(f"Weak exogeneity of {restr['weakex']}: "
                 + ("it does NOT adjust to the equilibrium (it is not the one that corrects)."
                    if p_b >= 0.05 else "it adjusts: it takes part in the correction."))
        L.append("If every series but one is weakly exogenous and the short run has no "
                 "feedback, the system is a CONDITIONAL model, a transfer network on I(1) "
                 "inputs: offer mtram (never go there yourself).")
    L += ["", "The Wald statistics of the .out are NOT CITABLE (they depend on the "
          "normalisation).", "", "## 4 · DECISION — alternatives", "",
          f"**A)** keep the restriction: the restricted VEC becomes the current model\n"
          f"   `test_restriction(name=\"{call}\", {restr.get('_call', '')}, adopt=True)`",
          "**B)** keep the free VEC and record the test as evidence\n"
          f"   `record_decision(name=\"{call}\", node=\"C3\", ...)`",
          "", "⏸ **Your decision.** (guided lane: I do not go on until you say)"]
    if prov_line:
        L += ["", prov_line]
    return "\n".join(L), {"lr": lr_b, "df": df, "p": p_b, "ll_free": best, "ll_restricted": ll_r,
                          "ll_free_drvec": ll_free_drvec}


def parse_links(text):
    """'OUT <- IN b r s; ...' -> the lines of a drvec -xlink network file."""
    out = []
    for tok in re.split(r"[;\n]", text or ""):
        t = tok.strip()
        if not t:
            continue
        m = re.fullmatch(r"(\S+)\s*<-\s*(\S+)\s+(\d+)\s+(\d+)\s+(\d+)", t)
        if not m:
            raise ValueError(f"a link is 'OUTPUT <- INPUT b r s' (r <= 2), got: {t!r}")
        out.append(f"{m.group(1)} <- {m.group(2)} {m.group(3)} {m.group(4)} {m.group(5)}")
    if not out:
        raise ValueError("give the links: 'OUTPUT <- INPUT b r s', one per input and output")
    return out


# --------------------------------------------------------------------------- #
#  the long run, read (C5)                                                     #
# --------------------------------------------------------------------------- #

def psi_levels(f, K):
    """The levels' MA weights Psi_k, k = 0..K, from drvec's level IRF
    (orthogonalised by Sigma's Cholesky in drvec's order): Psi_k = G_k C^-1."""
    G = np.asarray(f.level_irf(K), float)               # (K+1, M, M)
    C = np.linalg.cholesky(np.asarray(f.Sigma, float))
    Ci = np.linalg.inv(C)
    return np.array([g @ Ci for g in G])


def half_life(series):
    """The first k at which |series| falls to half its peak and stays below,
    counted from the peak. -> (k_peak, k_half or None)."""
    v = np.abs(np.asarray(series, float))
    kp = int(np.argmax(v))
    peak = v[kp]
    if peak <= 0:
        return kp, None
    for k in range(kp, len(v)):
        if np.all(v[k:] <= 0.5 * peak):
            return kp, k
    return kp, None


def long_run(vf, K=None, freq=1):
    """theta, both half-lives and Gonzalo and Ng's decomposition (STUDY-vec
    §3.8, Q6): readings computed by sima from drvec's matrices."""
    f = vf.fit
    M, r = vf.M, vf.r
    s = M - r
    K = int(K or max(60, 8 * max(freq, 1)))
    A = np.asarray(f.alpha, float)                     # (M, r)
    Bt = np.asarray(f.beta, float)                     # (M, r): [B2 ; I]
    B2 = np.asarray(f.beta2, float)                    # (s, r)
    Sig = np.asarray(f.Sigma, float)
    out = {"theta": (-B2).tolist(), "K": K}
    # the textbook half-life, per relation, on the variable it is solved for
    tb = []
    for c in range(r):
        a = A[s + c, c]
        # Johansen's sign: only a NEGATIVE alpha corrects on the variable the
        # relation is solved for; otherwise there is no textbook half-life
        hl = (math.log(0.5) / math.log(1.0 + a)) if -1 < a < 0 else None
        tb.append({"relation": c + 1, "on": vf.order[s + c], "alpha": a, "half_life": hl})
    out["textbook"] = tb
    # the relation's own rate absent short-run dynamics: eig(I + beta'alpha)
    ev = np.linalg.eigvals(np.eye(r) + Bt.T @ A)
    out["beta_alpha"] = [complex(e) for e in ev]
    # the model's: beta'Y's response, the norm over the shocks (order-invariant)
    Psi = psi_levels(f, K)                            # (K+1, M, M)
    C = np.linalg.cholesky(Sig)
    ms = []
    for c in range(r):
        z = np.array([Bt[:, c] @ Psi[k] @ C for k in range(K + 1)])   # (K+1, M)
        nrm = np.sqrt((z ** 2).sum(axis=1))
        kp, kh = half_life(nrm)
        ms.append({"relation": c + 1, "peak_at": kp, "half_life": kh,
                   "norm": nrm.tolist()})
    out["model"] = ms
    # Gonzalo and Ng (2001): permanent and transitory shocks
    from scipy.linalg import null_space
    aperp = null_space(A.T)                            # (M, s)
    bperp = null_space(Bt.T)
    G = np.vstack([aperp.T, Bt.T])                    # (M, M)
    Om = G @ Sig @ G.T
    Lc = np.linalg.cholesky(Om)
    H = np.linalg.inv(G) @ Lc                         # the structural impact
    R = np.array([Psi[k] @ H for k in range(K + 1)])  # (K+1, M, M): permanent first
    # the long run itself: drvec's gain (the limit, to convergence), not Psi_K
    Pinf = np.asarray(f.long_run().gain, float) @ np.linalg.inv(C)
    Rinf = Pinf @ H
    trans_lr = float(np.max(np.abs(Rinf[:, s:]))) if r else 0.0
    perm_lr = Rinf[:, :s]
    cum = np.cumsum(R ** 2, axis=0)                   # (K+1, M, M)
    tot = cum.sum(axis=2)
    share = cum[:, :, :s].sum(axis=2) / np.where(tot > 0, tot, 1.0)
    ab = aperp.T @ bperp
    try:
        A1 = bperp @ np.linalg.inv(ab)                # Y = A1 alpha_perp'Y + A2 beta'Y
        A2 = A @ np.linalg.inv(Bt.T @ A)
    except np.linalg.LinAlgError:
        A1 = A2 = None
    out["gn"] = {"alpha_perp": aperp.tolist(), "trans_long_run_max": trans_lr,
                 "perm_long_run": perm_lr.tolist(), "share_permanent": share.tolist(),
                 "A1": None if A1 is None else A1.tolist(),
                 "A2": None if A2 is None else A2.tolist()}
    return out


def long_run_report(vf, lr, call, freq=1, prov_line=""):
    names = vf.order
    M, r = vf.M, vf.r
    s = M - r
    f = vf.fit
    L = [f"# The long run — read from the VEC r = {r} (C5)",
         "*(theta, the half-lives and Gonzalo and Ng's decomposition are computed by "
         "sima from drvec's matrices; drvec computes none of them)*", "",
         "## 1 · TABLE", "", "```", "theta, the long-run coefficients (beta normalised: "
         "Y1 = theta' Y2 + a stationary error):"]
    th = np.asarray(lr["theta"])
    for c in range(r):
        L.append(f"  {names[s + c]} = " + " ".join(
            f"{th[i, c]:+.4f}*{names[i]}" for i in range(s)) + "  + stationary")
    L += ["", "half-life, the TEXTBOOK one: ln 0.5 / ln(1 - |alpha|) on the variable the "
          "relation is solved for (orientation only: exact for one relation with no "
          "short-run dynamics):"]
    for t in lr["textbook"]:
        L.append(f"  relation {t['relation']} on {t['on']}: alpha {t['alpha']:+.4f}, "
                 + (f"half-life {t['half_life']:.1f} periods" if t["half_life"] else
                    f"undefined: {t['on']} does not correct (alpha >= 0, or <= -1); the "
                    "correction is done by the others (read beta'alpha below)"))
    L.append("  the relation's own rate without short-run dynamics, eig(I + beta'alpha): "
             + ", ".join(f"{abs(e):.4f}" for e in lr["beta_alpha"]))
    L += ["", "half-life, the MODEL's: the response of the equilibrium error beta'Y to the "
          "shocks, its norm over the shocks (it does not depend on the Cholesky order), "
          "from the peak:"]
    for m in lr["model"]:
        L.append(f"  relation {m['relation']}: peak at k = {m['peak_at']}, "
                 + (f"half of it by k = {m['half_life']} ({m['half_life'] - m['peak_at']} "
                    "periods after the peak)" if m["half_life"] is not None else
                    f"not halved within {lr['K']} periods"))
    gn = lr["gn"]
    L += ["", f"Gonzalo and Ng: {s} permanent shock(s) (alpha_perp'e, the common trends' "
          f"innovations) and {r} transitory (beta'e), orthogonalised with the permanent "
          "first.", "  alpha_perp (columns: the common trends' weights on the innovations):"]
    ap = np.asarray(gn["alpha_perp"])
    for i, nm in enumerate(names):
        L.append(f"    {nm:<14}" + " ".join(f"{v:+.4f}" for v in ap[i]))
    L.append(f"  the transitory shocks' long-run effect, max |.| = {gn['trans_long_run_max']:.2e}"
             " (zero by construction: the self-check)")
    sh = np.asarray(gn["share_permanent"])
    hs = sorted({1, max(1, freq), 2 * max(1, freq), lr["K"]} & set(range(1, lr["K"] + 1)))
    L.append("  share of each level's forecast-error variance due to the permanent "
             "shock(s), %:")
    L.append("    " + " " * 14 + "".join(f"{'h=' + str(h):>9}" for h in hs))
    for i, nm in enumerate(names):
        L.append(f"    {nm:<14}" + "".join(f"{100 * sh[h - 1, i]:>9.1f}" for h in hs))
    L += ["```", "", "## 2 · WHAT IT SHOWS", "",
          "theta is a point value, with its sign: the standard errors are beta's in the "
          "estimate_vec table (drvec's -fdhess). Bands for any response come only from the "
          "bootstrap (irf_bands).",
          "The two half-lives answer different questions: the textbook one is the speed "
          "of one coefficient; the model's is how long the system's own equilibrium error "
          "takes to halve after a shock, short run included. When they differ, the "
          "short run matters.",
          "A series whose variance is almost all permanent at every horizon is a "
          "driver of the common trend; one with a large transitory share at short "
          "horizons is the one that moves around the equilibrium.", "",
          "## 3 · CONCLUSIONS", "",
          "Descriptive readings of the adopted VEC, conditional on r and the restrictions; "
          "the claim 'who corrects' is the LR's (test_restriction), not these numbers'.",
          "", "⏸ **Your decision.** (guided lane: I do not go on until you say)"]
    if prov_line:
        L += ["", prov_line]
    return "\n".join(L)


# --------------------------------------------------------------------------- #
#  the bootstraps of a fit: IRF bands (C6) and a sweep's cells (C7)            #
# --------------------------------------------------------------------------- #

def fit_args(vf, **more):
    a = {"p": vf.p, "q": vf.q, "r": vf.r, "case": str(vf.case),
         "nodrift": list(vf.nodrift or []), "order": list(vf.order),
         "restriction": {k: v for k, v in (vf.restriction or {}).items()
                         if not k.startswith("_")},
         "multistart": vf.multistart}
    a.update(more)
    return a


def _arr(x):
    return np.asarray(x, float).tolist()


def job_irf_bands(job, folder):
    import drvec
    from .provenance import of_drvec
    a = job["args"]
    eng = job["engine"][0]
    tk = jobs.Ticks(folder, a["N"], "IRF bootstrap replications")
    f = fit_vec(job["files"], a["order"], a["p"], a["q"], a["r"], a["case"], a["nodrift"],
                a["restriction"], a["multistart"], fdhess=False, irfboot=int(a["N"]),
                workers=job["workers"], engine=eng, seed=job.get("seed"),
                folder=os.path.join(folder, "c") if eng == "c" else None,
                progress=tk)
    jobs.write_text(os.path.join(folder, "irf.out"), f.out_text("irf"))
    txt = f.irfboot_text("irf")
    if txt:
        jobs.write_text(os.path.join(folder, "irf.irfboot"), txt)
    b = f.irf_bands()
    if b is None:
        raise RuntimeError("drvec gave no bands: fewer than 20 good replications")
    return {"tool": "irf_bands", "N": int(a["N"]), "K": b.K, "nok": b.nok, "nfail": b.nfail,
            "names": list(a["order"]), "irf": _arr(b.irf),
            "irf_pct": {str(k): _arr(v) for k, v in b.irf_pct.items()},
            "fevd": _arr(b.fevd), "fevd_pct": {str(k): _arr(v) for k, v in b.fevd_pct.items()},
            "loglik": f.loglik, "provenance": of_drvec(f.provenance),
            "files": ["irf.out", "irf.irfboot"]}


def job_fit_cell(job, folder):
    """One cell of a sweep: a fit at the given p, case and window."""
    from .provenance import of_drvec
    a = job["args"]
    extra = {}
    case = a["case"]
    if case == "trend":
        extra["trend"] = True
        case = "3"
    if a.get("estwin"):
        extra["estwin"] = int(a["estwin"])
    f = fit_vec(job["files"], a["order"], a["p"], a["q"], a["r"], case, a["nodrift"],
                a["restriction"], a["multistart"], fdhess=False, **extra)
    jobs.write_text(os.path.join(folder, "cell.out"), f.out_text("cell"))
    d = f.diagnostics()
    return {"tool": "fit_cell", "p": a["p"], "case": a["case"], "estwin": a.get("estwin", 0),
            "loglik": f.loglik, "npar": f.npar, "nobs": f.nobs, "termcode": f.termcode,
            "alpha": _arr(f.alpha), "theta": _arr(-np.asarray(f.beta2, float)),
            "hosking_p": None if d is None else d.hosking_p,
            "provenance": of_drvec(f.provenance), "files": ["cell.out"]}


# --------------------------------------------------------------------------- #
#  the yardstick (C8): drvec's rolling-origin errors                           #
# --------------------------------------------------------------------------- #

def _summary(acc):
    out = {}
    for k, v in acc.items():
        e = np.array([x[0] for x in v])
        a = np.array([x[1] for x in v])
        out[k] = {"n": len(v), "MAE": float(np.mean(np.abs(e))),
                  "RMSE": float(math.sqrt(np.mean(e ** 2))),
                  "MAPE": float(np.mean(np.abs(e / np.where(a != 0, a, np.nan))) * 100)}
    return out


def recursive_rows(csv_text, nobs):
    """drvec's -estwin/-f CSV -> [(origin, series, h, error, actual)], the
    origin counted in periods BEFORE THE LAST OBSERVATION (drvec's origin is a
    row of nabla Y: observation origin + 1 of its window of `nobs`)."""
    out = []
    for line in csv_text.splitlines():
        if not line or line.startswith("#") or line.startswith("origin,"):
            continue
        o, h, nm, act, _fc, err = line.split(",")
        out.append((nobs - (int(o) + 1), nm, int(h), float(err), float(act)))
    return out


def ladder_rows(rows, freq, last):
    """drvarma's Ladder.recursive rows -> the same form (origin before the end)."""
    ly, lp = last
    out = []
    for (y, p), nm, h, fc, act in rows:
        if act is None:
            continue
        back = (ly * freq + lp - 1) - (y * freq + p - 1)
        out.append((back, nm, int(h), float(act) - float(fc), float(act)))
    return out


def summary_on(rows, origins=None):
    """{(series, h): {n, MAE, RMSE, MAPE}} over the given origins (all: None)."""
    acc = {}
    for o, nm, h, e, a in rows:
        if origins is None or o in origins:
            acc.setdefault((nm, h), []).append((e, a))
    return _summary(acc)


def yardstick_rule(purpose, wins, cells):
    head = f"The VEC has the lower RMSE in {wins} of {cells} (series, horizon) cells."
    if purpose == "forecast":
        return (head + "\nTHE RULE, the purpose being FORECAST (recorded at N1c): the "
                "yardstick is a VETO. A VEC that does not forecast better than the "
                "univariates out of sample is not kept for forecasting, however "
                "significant its equilibrium is in sample. Read the pattern across "
                "series and horizons, not one cell.")
    if purpose == "long run":
        return (head + "\nTHE RULE, the purpose being the LONG RUN (recorded at N1c): the "
                "yardstick is a CAVEAT, NOT A VETO. The equilibrium and who corrects can "
                "stand without a forecasting gain (imposing cointegration often helps "
                "little at short horizons; Christoffersen and Diebold 1998). Report it "
                "beside the long-run claim, always.")
    return (head + "\nNo purpose was recorded at N1c: record it (prepare_vec's purpose) — "
            "the rule depends on it (forecast: a veto; long run: a caveat).")


# --------------------------------------------------------------------------- #
#  the final-stage tools on a VEC (C6, N6): responses, decomposition, forecast #
# --------------------------------------------------------------------------- #

def _bands_of(bands, kind, k, i, j, lo="5.0", hi="95.0"):
    if not bands:
        return None
    pct = bands[f"{kind}_pct"]
    if lo not in pct:                       # the keys as drvec writes them
        lo, hi = sorted(pct, key=float)[1], sorted(pct, key=float)[-2]
    return pct[lo][k][i][j], pct[hi][k][i][j]


def irf_report(vf, K, bands=None, why=""):
    f = vf.fit
    G = np.asarray(f.level_irf(K), float)
    names = vf.order
    M = vf.M
    Kb = bands["K"] if bands else -1
    L = ["IMPULSE RESPONSES OF THE LEVELS (drvec; a one-s.d. orthogonalised shock, "
         f"Cholesky in DRVEC'S ORDER: {' -> '.join(names)}).",
         "That order is the VEC's normalisation order as well: another order is another "
         "fit (estimate_vec with normalise_on), never a reorder. In a cointegrated system "
         f"the response does not die out: it converges to the permanent effect, of rank "
         f"M - r = {M - vf.r}.",
         ("Bands: the parametric bootstrap's 90 % (5 and 95 percentiles) from irf_bands: "
          f"{bands['nok']} replications refitted as the data were, to k = {Kb}."
          if bands else
          f"No bands{': ' + why if why else ''}. In a VEC they come ONLY from the bootstrap "
          "(irf_bands, a job): never from the covariance of the estimates.")]
    hs = sorted({0, 1, 2, 4, 8, K} & set(range(K + 1)))
    w = 30 if bands else 12
    for j, sj in enumerate(names):
        L += ["", f"shock to {sj}:", "  k  " + "".join(f"{s:>{w}}" for s in names)]
        for k in hs:
            cells = []
            for i in range(M):
                b = _bands_of(bands, "irf", k, i, j) if bands and k <= Kb else None
                cells.append(f"{f'{G[k, i, j]:.4f} [{b[0]:.4f}, {b[1]:.4f}]':>{w}}" if b else
                             f"{G[k, i, j]:>{w}.4f}")
            L.append(f"  {k:<3}" + "".join(cells))
    lr = f.long_run()
    L += ["", "the permanent effect (the long-run gain, drvec's): "
          + "; ".join(f"{names[i]} <- {names[j]} {lr.gain[i, j]:+.4f}"
                      for j in range(M) for i in range(M)),
          f"self-check max |beta' gain| = {lr.beta_gain:.2e} (zero by construction)"]
    return "\n".join(L)


def fevd_report(vf, K, bands=None, why=""):
    F = np.asarray(vf.fit.fevd(K), float)
    names = vf.order
    M = vf.M
    L = ["FORECAST-ERROR VARIANCE DECOMPOSITION OF THE LEVELS (%, drvec; the same "
         f"Cholesky order as the responses: {' -> '.join(names)}).",
         ("Bands (5 and 95 percentiles) from irf_bands, at the last horizon it reaches."
          if bands else f"No bands{': ' + why if why else ''} (only irf_bands gives them).")]
    hs = sorted({1, 2, 4, 8, K + 1} & set(range(1, K + 2)))
    for i, si in enumerate(names):
        L += ["", f"{si}:", "  h  " + "".join(f"{s:>12}" for s in names)]
        for h in hs:
            L.append(f"  {h:<3}" + "".join(f"{F[h - 1, i, j]:>12.1f}" for j in range(M)))
        if bands:
            kb = min(bands["K"], K)
            L.append(f"  {str(kb + 1) + '*':<3}" + "".join(
                f"{'[%.1f, %.1f]' % _bands_of(bands, 'fevd', kb, i, j):>12}" for j in range(M)))
    return "\n".join(L)


def forecast_vec(vf, H, conf=0.95):
    """The VEC forecast by drvarma's forecaster (PLAN-vec decision 5: one
    forecaster): drvec.to_levels_varma(fit).forecast(H)."""
    import drvec
    lv = drvec.to_levels_varma(vf.fit)
    fc = lv.forecast(int(H), conf)
    dates = vf.fit.forecasts(int(H)).dates
    return fc, dates


def forecast_report(vf, fc, dates, freq):
    L = ["FORECASTS — the VEC written in levels (drvec.to_levels_varma) and forecast by "
         "drvarma's forecaster (forecast_given): one forecaster for every system.",
         "Each series in its own units: its deterministic path added back and its Box-Cox "
         "inverted; the 95 % band on the transformed scale, mapped back (drvec's "
         "multiplier, 1.959964)."]
    for i, nm in enumerate(vf.order):
        L += ["", f"{nm}:", f"  {'date':<9}{'level':>12}{'low95':>12}{'high95':>12}"]
        for (y, sp), v, lo, hi in zip(dates, fc[i]["level"], fc[i]["low"], fc[i]["high"]):
            d = f"{y}" if freq == 1 else f"{sp}/{y}"
            L.append(f"  {d:<9}{v:>12.4f}{lo:>12.4f}{hi:>12.4f}")
    return "\n".join(L)
