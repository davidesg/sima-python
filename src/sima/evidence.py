"""The assistant layer: from the engine's numbers to evidence and a menu.

The rule that decides what lives here (ASSISTANT_LAYER_PROPOSAL.md, art-python):
**everything the model reads belongs to the assistant; the engine ships numbers
and never argues.** And the one thing not to copy from art: no hard-wired
recommendation. Every function here returns the EVIDENCE and, where there is a
decision, the MENU of options with the argument for and against each. The
verdict is the analyst's (or, in the autonomous lane, the model's, in writing).
"""
from __future__ import annotations

import math
import os

import numpy as np

# --------------------------------------------------------------------------- #
#  N0 — the series                                                             #
# --------------------------------------------------------------------------- #

def series_table(series):
    out = ["The univariate models (one fue file per series):",
           f"  {'#':<3}{'series':<14}{'obs':>6}  {'window':<17}{'lambda':>7}  "
           f"{'d':>2}{'D':>3}  {'det':>4}  {'AR/MA (expanded)':<18} mean"]
    for i, s in enumerate(series, 1):
        y0, p0 = s.ts.start
        y1, p1 = s.date_of(s.nobs_full)
        p, q = s.orders()
        out.append(f"  {i:<3}{s.name:<14}{s.nobs_full:>6}  {p0:>2}/{y0}-{p1:>2}/{y1}"
                   f"{s.model.boxlam:>7g}  {s.model.d:>2}{s.model.D:>3}  "
                   f"{len(s.model.interventions):>4}  AR {p:<3} MA {q:<8}"
                   f"{'estimated' if s.has_mu else 'fixed'}")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
#  N1 — the gate                                                               #
# --------------------------------------------------------------------------- #

def gate_text(gate, pre_move=1e-3):
    out = ["THE DIAGONAL GATE",
           "Each series fitted alone, on the common window; then the diagonal",
           "system EVALUATED at those optima. The identity is exact.",
           f"  {'series':<14}{'logL':>14}{'sigma2':>14}{'max|move|':>12}"]
    specs, trimmed = [], []
    for r in gate["rows"]:
        flag = ""
        if r["move"] > pre_move:
            if r["trimmed"]:
                flag = "  <- trimmed sample"; trimmed.append(r["series"])
            else:
                flag = "  <- not an optimum"; specs.append(r["series"])
        out.append(f"  {r['series']:<14}{r['logL']:>14.6f}{r['sigma2']:>14.6g}"
                   f"{r['move']:>12.3g}{flag}")
    out += [f"  {'SUM':<14}{gate['sum']:>14.6f}",
            f"  {'joint':<14}{gate['joint']:>14.6f}",
            f"  {'difference':<14}{gate['difference']:>14.3g}",
            f"  GATE: {'PASSED' if gate['passed'] else 'FAILED'}", ""]
    if specs:
        out += [f"These files moved when re-estimated ({', '.join(specs)}). Two readings:",
                "they are SPECIFICATIONS (an .inp, or a touched .pre), or they are",
                "optima on ANOTHER sample (the data were extended since the model",
                "was built). Either way the yardstick here is not the file as it is.",
                "Options:",
                "  (a) go back to art, finish those models there, and bring the .pre;",
                "      for: the yardstick is then the analyst's model, certified;",
                "  (b) continue with the re-estimated univariates;",
                "      for: nothing changes in the method; against: nobody has",
                "      validated those models (residuals, interventions, orders)."]
    if trimmed:
        out += [f"The common window trimmed {', '.join(trimmed)}: re-estimated on a",
                "shorter sample, moving is legitimate. If the lost observations",
                "matter, rebuild the files in art over one window."]
    if not specs and not trimmed:
        out.append("Every file is a fixed point: the base is the analysts' models.")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
#  N2 — cross identification                                                   #
# --------------------------------------------------------------------------- #

def cross_identification(res, names, nlags, freq):
    """CCFs of the residuals of the DIAGONAL system, pair by pair.

    Those residuals are each series' univariate innovations: prewhitened by
    construction, so a significant cross-correlation is the evidence of a
    dynamic the univariate models do not carry. Returns (text, facts).
    """
    from drvarma.diagnostics import ccf, qccf
    res = np.asarray(res, float)
    n, m = res.shape
    band = 2.0 / math.sqrt(n)
    lags_found, contemp, directed = [], [], []
    out = ["CROSS IDENTIFICATION — residual CCFs of the diagonal system",
           f"n = {n}, band 2/sqrt(n) = {band:.3f}. At lag k > 0 in the pair (A, B),",
           "B leads A by k periods; at k < 0, A leads B; k = 0 is contemporaneous.",
           f"With {2 * nlags + 1} lags per pair about {0.05 * (2 * nlags + 1):.1f} crossings are",
           "expected by chance alone: one isolated bar is weak evidence.", ""]
    for i in range(m):
        for j in range(i + 1, m):
            rho = ccf(res[:, i], res[:, j], nlags)
            Q, df, pv = qccf(res[:, i], res[:, j], nlags)
            sig = [k - nlags for k in range(2 * nlags + 1) if abs(rho[k]) > band]
            r0 = rho[nlags]
            A, B = names[i], names[j]
            out.append(f"  ({A}, {B}): r0 = {r0:+.3f}"
                       f"{'  (significant)' if abs(r0) > band else ''};"
                       f"  Hosking Q({nlags}) = {Q:.2f}, p = {pv:.4f}")
            leads = [k for k in sig if k != 0]
            if leads:
                txt = ", ".join(f"{k:+d} ({B + ' leads' if k > 0 else A + ' leads'},"
                                f" {rho[k + nlags]:+.3f})" for k in leads)
                out.append(f"      significant lags: {txt}")
                lags_found += [abs(k) for k in leads]
                for k in leads:
                    if abs(k) <= 3:                       # SHORT, below
                        link = f"{A}<-{B}" if k > 0 else f"{B}<-{A}"
                        if link not in directed:
                            directed.append(link)
            if abs(r0) > band:
                contemp.append((A, B, r0))
    SHORT = 3
    short = sorted({k for k in lags_found if k <= SHORT})
    longer = sorted({k for k in lags_found if k > SHORT})
    maxlag = max(short) if short else 0
    seasonal = [k for k in longer if freq > 1 and k % freq == 0]
    out += ["", "What this says, and the decisions it opens:"]
    if not lags_found and not contemp:
        out += ["  No cross-correlation beyond the band. The univariate models already",
                "  carry what the data show: the system IS the diagonal one.",
                "  (a) stay with the univariates (p = q = 0, -diagcov) — for: the",
                "      evidence; against: a weak link can hide under the band, and",
                "      only the out-of-sample yardstick (N5) can show it helps."]
    else:
        if contemp:
            out += ["  Contemporaneous correlation: "
                    + ", ".join(f"{a}-{b} {r:+.2f}" for a, b, r in contemp) + ".",
                    "  (a) a full innovation covariance (not -diagcov) — for: it is the",
                    "      measured fact; it costs m(m-1)/2 parameters and no dynamics;",
                    "      against: it does not help a forecast by itself (the future",
                    "      innovation of the other series is not known)."]
        if short:
            out += [f"  Short lead-lag correlation at lags {short} (up to {SHORT}).",
                    f"  (b) cross orders p = {maxlag}, q = 0 — for: the leads seen;",
                    f"      against: {m * (m - 1)} parameters per lag, on every pair,",
                    "      whether or not that pair showed anything;",
                    "  (c) p = 1, q = 1 — for: a decaying cross pattern is cheaper as MA",
                    "      than as several AR lags; against: harder to identify."]
            if directed and len(directed) < m * (m - 1):
                out += [f"  (d) the same orders on the pairs that showed something only:",
                        f"      links = \"{', '.join(directed)}\" — for: "
                        f"{len(directed)} of {m * (m - 1)} pairs, so",
                        "      fewer parameters, each one argued by a bar; against: a pair",
                        "      whose link sits under the band is excluded by construction.",
                        "      Estimating (b) as well tells them apart: the LR of the full",
                        "      model against this one is the test of the pairs left out."]
        if longer:
            out += [f"  Isolated correlations at longer lags {longer}: with this many lags",
                    "  some are chance, and a VAR does not reach them without many lags.",
                    "  They are better read as something the UNIVARIATE models miss."]
            if seasonal:
                out.append(f"  Some are seasonal ({seasonal}): a cross effect at the seasonal"
                           " lag usually means a seasonal pattern one of the univariate"
                           " models did not capture — look at art before building a VARMA"
                           " on it.")
        out += ["  In every case the decision is tested at N5: a VARMA that does not",
                "  beat the univariates out of sample has no reason to exist."]
    facts = {"maxlag": maxlag, "longer": longer, "contemporaneous": len(contemp) > 0,
             "links": directed,
             "any": bool(lags_found or contemp), "band": band}
    return "\n".join(out), facts


# --------------------------------------------------------------------------- #
#  N3/N4 — estimation                                                          #
# --------------------------------------------------------------------------- #

_TERM = {0: "not run (no free parameters, or the starting point failed)",
         1: "converged: the scaled gradient is below its tolerance",
         2: "stopped on the step size: suspect ill-conditioning, distrust the SEs",
         3: "stopped: the last step found no lower point",
         4: "stopped: iteration limit", 5: "stopped: five maximal steps"}


# --------------------------------------------------------------------------- #
#  N2 — Jenkins and Alavi (1981): the two identifications, as matrices          #
# --------------------------------------------------------------------------- #

_SHORT_MV = 4          # the lags read for a cut-off; longer ones are listed apart


def _block(sym):
    """One lag's m x m symbol matrix on one line: rows separated by ' | '."""
    return " | ".join(" ".join(row) for row in sym)


def _cutoff(sym, off_diagonal=False):
    """The cut-off: the end of the initial run of lags 1, 2, ... that have a
    significant element (0 if lag 1 has none); and the other significant lags,
    isolated, listed apart. A single element beyond two standard errors is
    expected by chance about once in twenty, so an isolated lag does not move
    the cut-off; it is shown for the analyst to judge."""
    K, m, _ = sym.shape
    mask = np.ones((m, m), bool)
    if off_diagonal:
        np.fill_diagonal(mask, False)
    sig = [k + 1 for k in range(K) if np.any((sym[k] != ".") & mask)]
    cut = 0
    while cut + 1 in sig and cut + 1 <= _SHORT_MV:
        cut += 1
    return cut, [k for k in sig if k > cut]


def _side(vals, band):
    """One side of a two-sided panel (lags 1..K): the bars beyond the band,
    the cut-off (end of the initial run, as `_cutoff`) and the isolated ones."""
    sig = [(k + 1, float(v)) for k, (v, b) in enumerate(zip(vals, band)) if abs(v) > b]
    lags = [k for k, _v in sig]
    cut = 0
    while cut + 1 in lags and cut + 1 <= _SHORT_MV:
        cut += 1
    return sig, cut, [k for k in lags if k > cut]


def ja_pair_facts(x, names, pairs, K, Kp, method):
    """The facts behind `plot_identification`, pair by pair, in the figure's
    layout: for "A - B" (A leads at k > 0), in the ccf (R_k) and the pccf
    (S_k), each side's bars beyond the band, its cut-off and its isolated
    lags; r(0); for method 2 Haugh's S* in total and by side. Facts only:
    which order to entertain is identify_matrices' menu and the analyst's."""
    from drvarma import identification_mv as im
    x = np.asarray(x, float)
    n, m = x.shape
    R, seR = im.corr_matrices(x, K, prewhitened=(method == 2))
    S, seS = im.partial_corr_matrices(x, Kp)
    r0 = np.corrcoef(x.T)
    out = []
    for i, j in pairs:
        a, b = names[j], names[i]                  # "a - b": a leads at k > 0
        out.append(f"{a} - {b}")
        z0 = 2.0 / np.sqrt(n)
        out.append(f"  ccf:  r(0) = {r0[i, j]:+.2f}"
                   + (" (outside)" if abs(r0[i, j]) > z0 else " (inside)"))
        for lab, pan in (("ccf", (R, seR, K)), ("pccf", (S, np.full(S.shape, seS), Kp))):
            M, se, KK = pan
            for side, who, vals, bnd in (
                    ("k > 0", a, M[:, i, j], 2 * se[:, i, j]),
                    ("k < 0", b, M[:, j, i], 2 * se[:, j, i])):
                sig, cut, iso = _side(vals, bnd)
                bars = ", ".join(f"{'+' if side == 'k > 0' else '-'}{k} {v:+.2f}"
                                 for k, v in sig) or "none"
                tail = f"cut-off after {cut}" + (f"; isolated: {', '.join(map(str, iso))}"
                                                 if iso else "")
                head = "  pccf:" if (lab == "pccf" and side == "k > 0") else "       "
                out.append(f"{head} {side} ({who} leads): {bars}  —  {tail}")
        if method == 2:
            h = im.haugh(x[:, i], x[:, j], K)
            out.append(f"  S*({h['all'][1]}) = {h['all'][0]:.1f}, p = {h['all'][2]:.3f};  "
                       f"k > 0 {h['k>0'][0]:.1f}, p = {h['k>0'][2]:.3f};  "
                       f"k < 0 {h['k<0'][0]:.1f}, p = {h['k<0'][2]:.3f}")
    out.append(f"With {K} lags a side, about {0.05 * K:.1f} bars per side cross the band "
               "by chance: an isolated one is weak evidence.")
    return out


def ja_pair_table(x, names, pairs, K, Kp, method):
    """The TABLE of plot_identification, as art's blocks: per pair, lag by
    lag, the ccf (R_k) and the pccf (S_k) with * beyond the band (and the
    band itself when it follows the lag, method 1), and the statistic."""
    from drvarma import identification_mv as im
    x = np.asarray(x, float)
    n, m = x.shape
    R, seR = im.corr_matrices(x, K, prewhitened=(method == 2))
    S, seS = im.partial_corr_matrices(x, Kp)
    r0 = np.corrcoef(x.T)
    zp = 2.0 * seS
    out = []
    for i, j in pairs:
        a, b = names[j], names[i]
        rho = im.two_sided(R, i, j, r0[i, j])
        band = 2.0 * im.two_sided(seR, i, j, 1.0 / np.sqrt(n))
        part = np.full(2 * K + 1, np.nan)
        part[K - Kp:K + Kp + 1] = im.two_sided(S, i, j, np.nan)
        head = f"{a} - {b}   (n = {n}; k > 0: {a} leads)"
        if method == 2:
            out += [head, f"band \u00b1{zp:.3f}", "", "     k      ccf     pccf"]
        else:
            out += [head, f"ccf band lag by lag (Bartlett); pccf band \u00b1{zp:.3f}", "",
                    "     k      ccf    band     pccf"]
        for t, k in enumerate(range(-K, K + 1)):
            c = f"{rho[t]:+7.2f}{'*' if abs(rho[t]) > band[t] else ' '}"
            pc = ("      \u00b7 " if np.isnan(part[t]) else
                  f"{part[t]:+7.2f}{'*' if abs(part[t]) > zp else ' '}")
            mid = "" if method == 2 else f"  {band[t]:5.2f}"
            out.append(f"  {k:+4d}  {c}{mid}  {pc}".replace("  +0 ", "   0 "))
        if method == 2:
            S_, df_, p_ = im.haugh(x[:, i], x[:, j], K)["all"]
            out += ["", f"S* ( {df_} ) = {S_:.1f}   p = {p_:.3f}"]
        out += ["* beyond the band", ""]
    return "\n".join(out).rstrip()


def stepwise_lines(sw, names, indent="  "):
    """Tiao and Box's Table 3/8/12 layout, one line per l: the indicator
    symbols of the partial autoregression matrix (t-ratios beyond +-2), M(l)
    with its p-value, and the diagonal of the residual covariance matrix."""
    from drvarma.identification_mv import symbols
    sym = symbols(sw["T"], 1.0)
    out = [f"{indent}  l  partial    M(l)      p     diag Sigma ({', '.join(names)})"]
    for l in range(len(sw["M"])):
        out.append(f"{indent}{l + 1:3d}  {_block(sym[l]):9s}{sw['M'][l]:8.1f}  "
                   f"{sw['pvalue'][l]:6.3f}{'*' if sw['pvalue'][l] < 0.05 else ' '}  "
                   + " ".join(f"{v:>9.4g}" for v in sw["sigma"][l]))
    out.append(f"{indent}(* M(l) significant at 5 %. The symbols are their 'crude "
               "signal-to-noise' guide, not tests.)")
    return out


def ja_identification(w, res, names, K, qmax, freq):
    """Jenkins and Alavi's two identifications [§3.3-3.4], from the ladder.

    Method 2 (prewhitened): the correlation matrices of the residuals of the
    diagonal system — the univariate models' residuals —, standard error
    1/sqrt(n). Method 1 (not prewhitened): R_k with Bartlett's standard errors,
    S_k (multivariate Yule-Walker) and S_k(q) of the stationary series w_t of
    the same files. Returns (text, facts): the evidence and the menu, which
    the analyst reads; nothing is chosen here."""
    from drvarma.identification_mv import (corr_matrices, determinants,
                                           partial_corr_matrices,
                                           q_partial_corr_matrices, stepwise_ar,
                                           stepwise_order, symbols)
    w = np.asarray(w, float)
    res = np.asarray(res, float)
    n, m = w.shape
    R2, se2 = corr_matrices(res, K, prewhitened=True)
    S2 = symbols(R2, se2)
    R1, se1 = corr_matrices(w, K)
    Ssym1 = symbols(R1, se1)
    S, sse = partial_corr_matrices(w, K)
    Psym = symbols(S, sse)
    Sq = {q: q_partial_corr_matrices(w, K, q) for q in range(1, qmax + 1)}
    Qsym = {q: symbols(v[0], v[1]) for q, v in Sq.items()}

    out = ["JENKINS AND ALAVI (1981) — the two identifications, from the ladder",
           f"series (rows i, columns j): {', '.join(names)}.  Element (i, j) at lag k: "
           "series j, k periods back, on series i.",
           "+ / - beyond two standard errors, . inside.", ""]

    # method 2
    q2, long2 = _cutoff(S2, off_diagonal=True)
    links = []
    for k in range(min(K, _SHORT_MV)):
        for i in range(m):
            for j in range(m):
                if i != j and S2[k, i, j] != "." and f"{names[i]}<-{names[j]}" not in links:
                    links.append(f"{names[i]}<-{names[j]}")
    diag_left = sorted({k + 1 for k in range(min(K, _SHORT_MV))
                        for i in range(m) if S2[k, i, i] != "."})
    r0 = np.corrcoef(res.T)
    out += [f"METHOD 2, prewhitened — the residuals of the univariate models "
            f"(n = {res.shape[0]}, s.e. 1/sqrt(n) = {1 / np.sqrt(res.shape[0]):.3f})",
            "  R_k(a):"]
    out += [f"    k={k + 1:2d}  {_block(S2[k])}" for k in range(K)]
    out.append(f"  lag 0: correlations " + ", ".join(
        f"{names[i]}-{names[j]} {r0[i, j]:+.2f}" for i in range(m) for j in range(i + 1, m)))
    out.append(f"  reading: the off-diagonal elements cut off after lag {q2}"
               + (f"; isolated beyond the band at {long2}" if long2 else "")
               + (f".  Links: {', '.join(links)}." if links else "."))
    if diag_left:
        out.append(f"  ! diagonal elements beyond the band at lags {diag_left}: a "
                   "univariate model leaves autocorrelation — the residual model "
                   "would be absorbing it; look at art first.")

    # method 1
    # The whole matrices are Jenkins and Alavi's reading (they identify the
    # whole model); the ladder already has its diagonal, fixed by the
    # univariate models, and adds the CROSS terms, which the off-diagonal
    # elements read. Both are given; the menu uses the cross reading.
    q1w, long1 = _cutoff(Ssym1)
    p1w, longp = _cutoff(Psym)
    q1, _ = _cutoff(Ssym1, off_diagonal=True)
    p1, _ = _cutoff(Psym, off_diagonal=True)
    pqw = {q: _cutoff(v)[0] for q, v in Qsym.items()}
    pq = {q: _cutoff(v, off_diagonal=True)[0] for q, v in Qsym.items()}
    out += ["", f"METHOD 1, not prewhitened — the stationary series w_t of the same "
            f"files (s.e.: R_k Bartlett's; S_k and S_k(q) 1/sqrt(n) = {sse:.3f})"]
    out += ["  R_k(w):"] + [f"    k={k + 1:2d}  {_block(Ssym1[k])}" for k in range(K)]
    out += ["  S_k (multivariate Yule-Walker):"] + [f"    k={k + 1:2d}  {_block(Psym[k])}" for k in range(K)]
    for q in range(1, qmax + 1):
        out += [f"  S_k({q}):"] + [f"    k={k + 1:2d}  {_block(Qsym[q][k])}" for k in range(K)]
    Ls = max(1, min(K, n // (3 * m)))
    sw = stepwise_ar(w, Ls)
    tb_p, tb_gaps = stepwise_order(sw)
    out += [f"  Tiao and Box's (1981) stepwise autoregression (least squares, common "
            f"sample n = {sw['n_eff']}; M(l) chi-squared with {sw['df']} d.f.):"]
    out += stepwise_lines(sw, names, indent="    ")
    if m >= 3:
        out += ["  determinants (the same cut-offs, for many series):",
                "    |R_k| " + " ".join(f"{v:+.3f}" for v in determinants(R1)),
                "    |S_k| " + " ".join(f"{v:+.3f}" for v in determinants(S))]
    out.append(f"  reading, whole matrices (theirs: the whole model): R_k cuts off after "
               f"{q1w}, S_k after {p1w}"
               + "".join(f", S_k({q}) after {v}" for q, v in pqw.items())
               + (f"; isolated beyond the band at {sorted(set(long1 + longp))}" if (long1 or longp) else "")
               + ".")
    out.append(f"  reading, off-diagonal (the cross terms the ladder adds; its diagonal is "
               f"the univariate models'): R_k after {q1}, S_k after {p1}"
               + "".join(f", S_k({q}) after {v}" for q, v in pq.items()) + ".")
    out.append("  S_k(q) is unstable in samples of this size (they warn of large values at "
               "higher k, §4.1): read its cut-off as a hint.")
    out.append(f"  reading, Tiao and Box: the last significant M(l) is at l = {tb_p}"
               + (f" (not significant on the way: {tb_gaps})" if tb_gaps else "")
               + f"; S_k's whole-matrix cut-off is {p1w}. "
               + ("They agree." if tb_p == p1w else
                  "They differ: M(l) is the test, S_k the pattern; on an MA the "
                  "partials persist (their Table 4), so a long p here can be an MA."))
    seas = [k for k in sorted(set(long1 + longp + long2)) if freq > 1 and k % freq == 0]
    if seas:
        out.append(f"  seasonal lags {seas}: a cross effect there usually means a seasonal "
                   "pattern a univariate model misses (Jenkins and Alavi's 'leakage', "
                   "§4.2) — look at art before modelling it.")

    # the menu
    out += ["", "What this says, and the decisions it opens (Jenkins and Alavi: use both; "
            "if they agree, estimate with more confidence; if not, choose by what each "
            "explains of the system and by parsimony):"]
    if q2 == 0 and q1 == 0 and p1 == 0:
        out.append("  Neither method shows cross structure: the univariate models carry "
                   "it; the system is the diagonal one (N5 is still the test).")
    if q2:
        out.append(f"  (a) from method 2: an MA({q2}) residual model, the univariate "
                   f"models on the diagonal — estimate(p=0, q={q2}"
                   + (f', links="{", ".join(links)}"' if links else "")
                   + ', cross="residual"). That is Jenkins and Alavi\'s form (3.22): '
                   "the cross MA multiplied by each series' univariate MA; the "
                   "additive form (the default) is the same when the univariate "
                   "models have no MA factors, and a different candidate when they "
                   "have.")
    links1 = []
    for k in range(p1):
        for i in range(m):
            for j in range(m):
                if i != j and Psym[k, i, j] != "." and f"{names[i]}<-{names[j]}" not in links1:
                    links1.append(f"{names[i]}<-{names[j]}")
    if p1:
        out.append(f"  (b) from method 1: a cross AR of order {p1} (S_k) — "
                   f"estimate(p={p1}, q=0"
                   + (f', links="{", ".join(links1)}"' if links1 else "") + ").")
    for q, p in pq.items():
        if p and (p < p1 or not p1):
            out.append(f"  (c) from method 1: an ARMA({p},{q}) (S_k({q}) cuts off after "
                       f"{p}) — estimate(p={p}, q={q}).")
    if tb_p and tb_p != p1:
        out.append(f"  (d) Tiao and Box's order: M(l) asks for a VAR({tb_p}) on w_t. In the "
                   f"ladder that is the cross order — estimate(p={tb_p}, q=0) — with the "
                   "univariate models kept on the diagonal (theirs would refit the "
                   "diagonal too).")
    if p1 and q2:
        out.append("  Their warning (3.26): after prewhitening a cross AR structure reads "
                   "as an MA of higher order, and leads to a mis-specified AR and to "
                   "over-parameterisation. With both readings present, estimate (a) and "
                   "(b), compare them, and let N5 decide.")
    facts = {"method2_q": q2, "links": links, "method1_links": links1,
             "method1_q": q1, "method1_p": p1,
             "method1_pq": pq, "method1_whole": {"q": q1w, "p": p1w, "pq": pqw},
             "diagonal_left": diag_left, "tb_p": tb_p, "tb_gaps": tb_gaps,
             "tb_M": [float(v) for v in sw["M"]]}
    return "\n".join(out), facts


def ja_checking(res, sigma, names, K, freq, date_of):
    """Jenkins and Alavi's checking of a fitted model [§5.2].

    (1) the large residuals, on the UNCORRELATED transformed residuals
    a*_t = Q' a_t (Q the eigenvectors of Sigma, limits +-2 sqrt(lambda)),
    since the a_it correlate at lag 0 and cannot be judged one by one; with
    the original residual that moves most in each large a*; (2) the residual
    correlation matrices R_k(a); (3) the portmanteau matrix
    Q_ij = n SUM_k r_ij(k)^2 — which, they warn, deserves less attention than
    the individual matrices, "the only ones that give clues how the model can
    be changed for the better". `date_of(t)` dates residual t (0-based)."""
    from scipy.stats import chi2
    from drvarma.identification_mv import corr_matrices, symbols
    a = np.asarray(res, float)
    n, m = a.shape
    Sig = np.asarray(sigma, float)
    lam, Q = np.linalg.eigh(Sig)
    order = np.argsort(lam)[::-1]
    lam, Q = lam[order], Q[:, order]
    astar = (a - a.mean(0)) @ Q
    out = ["CHECKING, as Jenkins and Alavi (1981, §5.2)", "",
           "(1) Large residuals, on the uncorrelated transformed residuals a* = Q'a "
           "(Q: eigenvectors of Sigma; limits +-2 sqrt(lambda)):"]
    big = []
    for c in range(m):
        z = astar[:, c] / np.sqrt(lam[c])
        load = ", ".join(f"{names[i]} {Q[i, c]:+.2f}" for i in np.argsort(-np.abs(Q[:, c])))
        idx = [t for t in np.argsort(-np.abs(z)) if abs(z[t]) > 2.0][:6]
        out.append(f"  a*_{c + 1} (lambda {lam[c]:.4g}; loads {load}): "
                   + (", ".join(f"{'%d.%02d' % date_of(t) if freq > 1 else date_of(t)[0]} "
                                f"({z[t]:+.1f})" for t in sorted(idx)) if idx else "none beyond 2"))
        big += [(abs(z[t]), t) for t in idx]
    if big:
        worst = max(big)[1]
        out.append("  the largest: " + ("%d.%02d" % date_of(worst) if freq > 1 else str(date_of(worst)[0]))
                   + " — " + ", ".join(f"{names[i]} {a[worst, i] / np.sqrt(Sig[i, i]):+.1f} s.d."
                                       for i in range(m))
                   + ". A known cause is treated by intervention (in art, on the "
                     "series' own model) before reading anything else: large "
                     "residuals distort the structure, the estimates, the "
                     "correlations and the forecasts.")
    R, se = corr_matrices(a, K, prewhitened=True)
    sym = symbols(R, se)
    out += ["", f"(2) Residual correlation matrices R_k(a) (s.e. 1/sqrt(n) = {1 / np.sqrt(n):.3f}):"]
    out += [f"    k={k + 1:2d}  {_block(sym[k])}" for k in range(K)]
    beyond = [(k + 1, i, j) for k in range(K) for i in range(m) for j in range(m)
              if sym[k, i, j] != "."]
    out.append("  beyond the band: " + (", ".join(f"({names[i]}, {names[j]}) at {k}"
                                                  for k, i, j in beyond) if beyond else "none")
               + f"  (about {0.05 * K * m * m:.1f} expected by chance)")
    Qij = n * (R ** 2).sum(0)
    p = chi2.sf(Qij, K)
    out += ["", f"(3) Portmanteau matrix Q_ij = n SUM r_ij(k)^2, k <= {K} "
                "(a summary; the individual matrices above are what give clues):"]
    for i in range(m):
        out.append(f"  {names[i]:<12}" + "".join(f"{Qij[i, j]:9.1f}{'*' if p[i, j] < 0.05 else ' '}"
                                                  for j in range(m)))
    out.append("  * p < 0.05 against chi-square(K), no parameters discounted.")
    lab = (lambda t: "%d.%02d" % date_of(t) if freq > 1 else str(date_of(t)[0]))
    facts = {"n_beyond": len(beyond), "beyond": beyond, "large": len(big),
             "expected": 0.05 * K * m * m,
             "large_dates": sorted({lab(t) for _z, t in big}),
             "worst": lab(max(big)[1]) if big else None,
             "worst_z": float(max(big)[0]) if big else 0.0,
             "significant_Q": [(names[i], names[j]) for i in range(m) for j in range(m)
                               if p[i, j] < 0.05]}
    return "\n".join(out), facts


def uncertainty_text(fc_model, fc_diag, series, leads):
    """Jenkins and Alavi's Table VIII: the standard deviation of the forecast
    errors at each lead time, V(l) of the model against the univariate models'
    (the diagonal system), per cent of the level when the series is in logs
    (100 x the log metric) [§6.3]. In sample: V(l) takes the parameters as
    known; the out-of-sample yardstick is `evaluate` — "a large number of
    forecast origins would be needed", as they say."""
    out = ["FORECAST UNCERTAINTY — the standard deviation of the forecast errors "
           "by lead time, V(l) (Jenkins and Alavi's Table VIII)",
           "per cent for series in logs (100 x the log metric); otherwise in the "
           "units of the transformed series. Univariate = the diagonal system.", ""]
    head = "  lead " + "".join(f"{s.name[:10]:>12}{'':>11}" for s in series)
    sub = "       " + "".join(f"{'univariate':>11} {'model':>9}  " for _ in series)
    out += [head, sub]
    for l in leads:
        row = f"  {l:4d} "
        for c, s in enumerate(series):
            sc = (100.0 if s.model.boxlam == 0.0 else 1.0) / s.model.refactor
            u, v = sc * fc_diag[c]["sd"][l - 1], sc * fc_model[c]["sd"][l - 1]
            row += f"{u:11.3f} {v:9.3f}{'*' if v < u else ' '} "
        out.append(row)
    out += ["  * the model's forecast errors are smaller at that lead.",
            "  These take the parameters as known and the model as right; whether "
            "the gain is real is what `evaluate` measures, out of sample."]
    return "\n".join(out)


def _is_covariance(name):
    """The ladder's names for the innovation covariance parameters:
    `log(Q[b]/Q[a])` and `Q[b,a]` (drvarma.ladder)."""
    return name.startswith("log(Q[") or name.startswith("Q[")


def estimation_text(L, nlags):
    from drvarma.diagnostics import hosking_q
    r = L.result
    names = [s.name for s in L.series]
    links = getattr(L, "links", None)
    out = [f"ESTIMATED: cross orders p = {L.p}, q = {L.q}, "
           f"{'diagonal' if L.diagcov else 'full'} innovation covariance"
           + ("; cross MA in the residual-model form (Jenkins-Alavi 3.22)"
              if getattr(L, "cross", "additive") == "residual" else ""),
           *([f"cross links: " + ", ".join(
               f"{names[i]}<-{names[j]}" for i in range(len(names))
               for j in range(len(names)) if i != j and links[i, j])
              + " (the other pairs carry no cross dynamics)"] if links is not None else []),
           f"optimiser: {_TERM.get(r.termcode, r.termcode)} ({r.nit} iterations"
           + (f"; cross terms started at {L.start_used}" if getattr(L, "start_used", None)
              and L.start_used != "zero" else "") + ")"
           + (f"\n  STOPPED AT THE MA INVERTIBILITY BOUNDARY: "
              f"{r.ma_boundary} of {r.ma_nroots} MA inverse roots within 5e-5 of the unit circle"
              if getattr(r, "ma_boundary", 0) else ""),
           f"  {'parameter':<34}{'estimate':>12}{'s.e.':>12}{'t':>9}"]
    cov = []
    for n, v, se in zip(r.names, r.x, r.std_errors):
        if _is_covariance(n):
            cov.append((n, v))
            continue
        t = v / se if se > 0 else float("nan")
        mark = "  *" if se > 0 and abs(t) > 1.96 else ""
        out.append(f"  {n:<34}{v:>12.6f}{se:>12.6f}{t:>9.2f}{mark}")
    if cov:
        # drvarma BUG-0008: the covariance of the innovations is concentrated
        # out of the likelihood and parametrised free of scale (log ratios and
        # a Cholesky-type factor), so a t-ratio on these numbers tests nothing
        # anyone asked. They are reported, not tested; the correlations below
        # are what to read.
        out += ["", "  innovation covariance, parametrised (no inference: read the "
                    "correlations below)"]
        out += [f"  {n:<34}{v:>12.6f}" for n, v in cov]
    out += ["", f"exact log-likelihood {r.logL:.6f}  ({r.npar} parameters)"]
    if not (L.p == 0 and L.q == 0 and L.diagcov):
        lr, df, pv = L.lr_test()
        out += [f"against the diagonal system (the univariates): LR = {lr:.3f}, "
                f"df = {df}, p = {pv:.4f}",
                "  In sample. Significance here is necessary, not sufficient: the",
                "  cross terms have to pay for themselves out of sample (N5)."]
    sig = r.sigma
    d = np.sqrt(np.diag(sig))
    out += ["", "innovation correlations:"]
    for a in range(len(names)):
        out.append(f"  {names[a]:<14}" + "".join(f"{sig[a, b] / (d[a] * d[b]):>9.3f}"
                                               for b in range(len(names))))
    if r.residuals is not None and r.residuals.shape[0] > nlags + 1:
        Q, df, pv = hosking_q(r.residuals, nlags)
        out += ["", f"residuals: Hosking Q({nlags}) = {Q:.2f}, df = {df}, p = {pv:.4f}"
                f"  ({'white noise not rejected' if pv > 0.05 else 'NOT white noise'})"]
    return "\n".join(out)


# --------------------------------------------------------------------------- #
#  N5 — the yardstick                                                          #
# --------------------------------------------------------------------------- #

def _rmse(v):
    """An RMSE in the units of the series' level, which run from fractions to
    hundreds of thousands (muskrat skins): decimals by magnitude, so that the
    column never overflows into its neighbour."""
    a = abs(v)
    if not np.isfinite(v):
        return "nan"
    return f"{v:.0f}" if a >= 1e4 else f"{v:.1f}" if a >= 100 else \
        f"{v:.3f}" if a >= 1 else f"{v:.4g}"


def evaluation_text(cand, diag, label, horizons, series):
    """cand/diag: {(series, h): {n, MAE, RMSE, MAPE}}; series: names in order."""
    out = [f"THE YARDSTICK — {label} against the univariates (diagonal system),",
           "same window, parameters estimated once and held fixed, every origin.",
           f"  {'series':<12}{'h':>4}{'n':>5}{'RMSE var':>12}{'RMSE uni':>12}"
           f"{'ratio':>8}{'MAPE var':>10}{'MAPE uni':>10}"]
    wins = total = 0
    for s in series:
        for h in horizons:
            if (s, h) not in diag or (s, h) not in cand:
                continue
            c, u = cand[(s, h)], diag[(s, h)]
            ratio = c["RMSE"] / u["RMSE"] if u["RMSE"] else float("nan")
            total += 1
            wins += ratio < 1.0
            out.append(f"  {s:<12}{h:>4}{c['n']:>5}{_rmse(c['RMSE']):>12}{_rmse(u['RMSE']):>12}"
                       f"{ratio:>8.3f}{c['MAPE']:>10.3f}{u['MAPE']:>10.3f}")
    out += ["", f"The VARMA has the lower RMSE in {wins} of {total} (series, horizon) cells.",
            "Reading it: a ratio below 1 is a gain over the univariate model; the",
            "evidence is the pattern across series and horizons, not one cell. The",
            "number of origins is small at long horizons. Decisions:",
            "  (a) keep the VARMA — for the cells where it gains, if they are the",
            "      ones the analysis is about;",
            "  (b) stay with the univariates — if it does not gain where it matters:",
            "      a significant in-sample effect that does not forecast better is a",
            "      finding, not a model to keep;",
            "  (c) try another candidate (N2/N3)."]
    return "\n".join(out), {"wins": wins, "cells": total}


# --------------------------------------------------------------------------- #
#  N6 — use                                                                    #
# --------------------------------------------------------------------------- #

def forecast_text(fcs):
    out = ["FORECASTS — every series in its level, with its own model",
           "(95% band on the transformed scale, mapped back)"]
    for fc in fcs:
        y, p = fc["origin"]
        out += ["", f"{fc['series']} (origin {p}/{y}):",
                f"  {'date':<8}{'level':>11}{'low95':>11}{'high95':>11}"]
        for (yy, pp), v, lo, hi in zip(fc["dates"], fc["level"], fc["low95"], fc["high95"]):
            out.append(f"  {pp:>2}/{yy:<5}{v:>11.4f}{lo:>11.4f}{hi:>11.4f}")
    return "\n".join(out)


def _band_note(bands, why=None):
    if bands is None:
        return [f"No bands: {why}." if why else "Point estimates only (bands=False)."]
    a = bands["alpha"]
    return [f"{100 * (1 - a):.0f}% Monte-Carlo bands [lo, hi]: {bands['ndraws_used']} draws "
            f"from N(estimate, covariance), {bands['ndraws_rejected']} rejected as "
            "non-stationary / non-invertible (a large share says the fit sits near a boundary)."]


def irf_text(phi, theta, sigma, names, horizon, bands=None, why=None):
    from drvarma.irf import oirf
    O = oirf(phi, theta, sigma, horizon)
    out = ["IMPULSE RESPONSES (orthogonalised, Cholesky in the ORDER OF THE FILES:",
           f"{' -> '.join(names)}). That order is an identifying ASSUMPTION: the first",
           "series is not moved within the period by the others' innovations. With a",
           "strong contemporaneous correlation the answer depends on it; reorder the",
           "files and compare before reading a response as a finding.",
           "Responses on the stationary (transformed, differenced) scale."] + _band_note(bands, why)
    w = 30 if bands is not None else 12
    for j, sj in enumerate(names):
        out += ["", f"shock to {sj}:", "  h  " + "".join(f"{s:>{w}}" for s in names)]
        for h in range(horizon + 1):
            if bands is None:
                cells = [f"{O[h, i, j]:>12.5f}" for i in range(len(names))]
            else:
                lo, hi = bands["oirf_lo"][h, :, j], bands["oirf_hi"][h, :, j]
                cells = [f"{f'{O[h, i, j]:.5f} [{lo[i]:.5f}, {hi[i]:.5f}]':>{w}}"
                         for i in range(len(names))]
            out.append(f"  {h:<3}" + "".join(cells))
    return "\n".join(out)


def fevd_text(phi, theta, sigma, names, horizon, bands=None, why=None):
    from drvarma.irf import fevd
    F = fevd(phi, theta, sigma, horizon)
    out = ["FORECAST-ERROR VARIANCE DECOMPOSITION (%, same Cholesky order as the IRF)"]
    out += _band_note(bands, why)
    if bands is not None:
        out += [f"The bands are for the last horizon (h = {horizon}), the row marked *."]
    for i, si in enumerate(names):
        out += ["", f"{si}:", "  h  " + "".join(f"{s:>10}" for s in names)]
        for h in sorted({1, max(1, horizon // 4), max(1, horizon // 2), horizon}):
            out.append(f"  {h:<3}" + "".join(f"{F[h - 1, i, j]:>10.1f}" for j in range(len(names))))
        if bands is not None:
            lo, hi = bands["fevd_lo"][i], bands["fevd_hi"][i]
            out.append(f"  {str(horizon) + '*':<3}" + "".join(
                f"{f'[{lo[j]:.1f}, {hi[j]:.1f}]':>14}" for j in range(len(names))))
    return "\n".join(out)


# --------------------------------------------------------------------------- #
#  Studying an ill-defined estimation (the MA wall)                            #
# --------------------------------------------------------------------------- #

# The MA invertibility wall, one tolerance for both sides, as the engines
# (atsw-gui lib/lik/lik.h MA_WALL_TOL; drvarma.ladder.MA_WALL_TOL).
MA_WALL_TOL = 5e-5


def inverse_roots(poly):
    """Inverse roots of Phi(B) = I - sum_k poly[k] B^k: the companion eigenvalues.

    Same computation as the engine's chekma for the MA side (the wall is
    modulus >= 1 - MA_WALL_TOL; the engine refuses beyond 1 + MA_WALL_TOL).
    """
    poly = np.asarray(poly, float)
    if poly.ndim != 3 or poly.shape[0] == 0 or not np.any(poly):
        return np.zeros(0, complex)
    k, m, _ = poly.shape
    A = np.zeros((m * k, m * k))
    for j in range(k):
        A[:m, j * m:(j + 1) * m] = poly[j]
    for j in range(k - 1):
        A[(j + 1) * m:(j + 2) * m, j * m:(j + 1) * m] = np.eye(m)
    return np.linalg.eigvals(A)


def _root_row(z, freq):
    ang = abs(np.angle(z))
    period = (2 * math.pi / ang) if ang > 1e-9 else float("inf")
    per = "real (frequency 0)" if period == float("inf") else (
          "Nyquist (real, negative)" if abs(ang - math.pi) < 1e-6 else f"{period:6.2f} obs")
    return f"{z.real:+9.4f} {z.imag:+9.4f}i   modulus {abs(z):8.5f}   period {per}"


def roots_text(fit, freq, near=0.10):
    """The AR and MA inverse roots of the joint model, and the pairs that nearly
    cancel. Evidence, not a verdict: a near-common pair makes the likelihood a
    ridge along the cancellation; whether to remove it is the analyst's call."""
    ar = inverse_roots(fit.phi)
    ma = inverse_roots(fit.theta)
    out = [f"INVERSE ROOTS of the joint model (period in observations; freq {freq})",
           "  AR:"]
    out += [f"    {_root_row(z, freq)}" for z in sorted(ar, key=lambda z: -abs(z))] or ["    (none)"]
    out += ["  MA:"]
    out += [f"    {_root_row(z, freq)}" + ("   <- ON THE WALL" if abs(z) >= 1.0 - MA_WALL_TOL else "")
            for z in sorted(ma, key=lambda z: -abs(z))] or ["    (none)"]
    pairs = []
    for zm in ma:
        if ar.size:
            j = int(np.argmin(np.abs(ar - zm)))
            d = abs(ar[j] - zm)
            if d < near:
                pairs.append((d, ar[j], zm))
    out += ["", f"NEAR-COMMON AR/MA ROOTS (distance < {near}):"]
    if pairs:
        for d, za, zm in sorted(pairs, key=lambda t: t[0]):
            out.append(f"  AR {za.real:+.4f}{za.imag:+.4f}i  ~  MA {zm.real:+.4f}{zm.imag:+.4f}i"
                       f"   distance {d:.4f}   modulus AR {abs(za):.4f} / MA {abs(zm):.4f}")
    else:
        out.append("  none")
    return "\n".join(out)


def wall_frequencies(fit, freq, tol=1e-6):
    """The frequencies (in cycles per observation) of the MA roots on the wall."""
    ma = inverse_roots(fit.theta)
    return sorted({round(abs(np.angle(z)) / (2 * math.pi), 6) for z in ma if abs(z) >= 1.0 - MA_WALL_TOL})


# --------------------------------------------------------------------------- #
#  Box and Tiao (1977): the canonical analysis of the levels                  #
# --------------------------------------------------------------------------- #

NEAR_ONE = 0.90        # sqrt(lam) from here: a near non-stationary component
NEAR_ZERO = 0.15       # lam up to here: nearly white (their hog components at .02, .14)
# The threshold is on sqrt(lam), the scale of a root: for an AR(1) component
# lam = phi^2 (Box and Tiao's x5: lam .8868, phi .94; Tiao and Tsay's flour
# contrast: phi .88, lam .76 here). 0.90 is the convention art uses for an MA
# root that nearly cancels a difference; on lam it would ask for a root of .95.


def _combination(row, names):
    return ", ".join(f"{nm} {v:+.2f}" for nm, v in zip(names, row) if abs(v) >= 0.005)


def canonical_report(x, names, d, freq, p=0, near=NEAR_ONE, call="", raw=False):
    """Box and Tiao's (1977) canonical analysis of the transformed LEVELS x
    (n x m: Box-Cox and seasonal differences, no regular ones), under a
    VAR(p) by least squares (p = 0: the last significant M(l) of Tiao and
    Box's stepwise table, at least 1). Returns (report, facts): art's four
    sections; the reading, not a test, and no d is changed here."""
    from drvarma.identification_mv import canonical, stepwise_ar, stepwise_order
    x = np.asarray(x, float)
    n, m = x.shape
    L = max(1, min(2 * freq if freq > 1 else 6, n // (3 * m)))
    sw = stepwise_ar(x, L)
    p_tb, gaps = stepwise_order(sw)
    p_used = int(p) or max(1, p_tb)
    c = canonical(x, p_used)
    lam = c["lam"]
    W = c["weights"]
    diffd = [nm for nm, dd in zip(names, d) if dd >= 1]
    root = np.sqrt(lam)
    unit = [j for j in range(m) if root[j] >= near]
    white = [j for j in range(m) if lam[j] <= NEAR_ZERO]
    lines = [f"# Canonical analysis — Box and Tiao (1977)",
             f"*(the transformed levels: each series' Box-Cox"
             + (" and seasonal differences" if freq > 1 else "")
             + f", no regular differences; n = {c['n_eff']}, VAR({p_used}) by least squares)*",
             "", "## 1 · TABLE", "",
             "_[Claude: show the block below AS IT IS; do not build your own table]_", "", "```",
             "Tiao and Box's stepwise autoregression on the levels:"]
    lines += stepwise_lines(sw, names)
    lines += ["", f"components, least to most predictable (VAR({p_used})); "
              "weights scaled to the largest = 1:",
              "   j    lam  sqrt(lam)  1-lam   combination"]
    for j in range(m):
        tag = (" near 1" if j in unit else " white?" if j in white else "")
        lines.append(f"  {j + 1:2d}  {lam[j]:.3f}    {root[j]:.3f}   {1 - lam[j]:.3f}   "
                     f"{_combination(W[j], names)}{tag}")
    if "shares" in c:
        sh = c["shares"]
        lines += ["", "variance components (their Table 4.3): share of each component's "
                  "variance from each component's past, and from its own shock",
                  "        " + " ".join(f"   y{i + 1}(t-1)" for i in range(m)) + "     shock"]
        for j in range(m):
            lines.append(f"  y{j + 1}  " + " ".join(f"{v:10.3f}" for v in sh[j]))
    lines += ["```", "", "## 2 · WHAT IT SHOWS", "",
              "lam is the share of a component's variance its own past predicts "
              "(2.2); sqrt(lam) is on the scale of a root (for an AR(1) component "
              "lam = phi^2). Near 0: a nearly white combination, a relation among the series "
              "that stays stable over time (2.9). Near 1: a nearly non-stationary one, "
              "the series' common growth (§3.2: for a VAR(1), if and only if roots of "
              "the AR approach the unit circle).", ""]
    lines.append(f"- Order: the last significant M(l) on the levels is at l = {p_tb}"
                 + (f" (gaps {gaps})" if gaps else "")
                 + (f"; VAR({p_used}) used." if p_used == max(1, p_tb)
                    else f"; VAR({p_used}) asked for."))
    lines.append(f"- {len(unit)} component(s) with sqrt(lam) >= {near} (lam >= {near * near:.2f})"
                 + (": " + "; ".join(f"y{j + 1} = {_combination(W[j], names)}" for j in unit)
                    if unit else "") + ".")
    lines.append(f"- {len(white)} nearly white (lam <= {NEAR_ZERO})"
                 + (": " + "; ".join(f"y{j + 1} = {_combination(W[j], names)}" for j in white)
                    if white else "") + ".")
    lines.append(f"- Regular differences in the univariate models: "
                 + (", ".join(f"{nm} d={dd}" for nm, dd in zip(names, d))) + ".")
    lines += ["", "## 3 · CONCLUSIONS", ""]
    question = len(diffd) >= 2 and len(unit) < len(diffd)
    if len(diffd) < 2:
        lines.append("Fewer than two series are differenced: the question of joint "
                     "differencing does not arise. The nearly white components, if any, "
                     "are static relations worth naming.")
    elif question:
        lines.append(f"{len(diffd)} series are differenced, but only {len(unit)} "
                     f"component(s) of their levels look non-stationary: there may be "
                     f"{len(diffd) - len(unit)} stationary combination(s) of the levels. "
                     "Then differencing every series is more than the system needs "
                     "(Box and Tiao 1977, §4.4: the differenced model carries a "
                     "non-invertible MA and leaves the autoregressive form), which is "
                     "cointegration — drvec's ground, where Johansen's test decides.")
    else:
        lines.append(f"As many near non-stationary components ({len(unit)}) as "
                     f"differenced series ({len(diffd)}): the levels show no stationary "
                     "combination, and the univariates' differences are consistent with "
                     "the joint reading.")
    lines.append("A reading, not a test: lam near 1 also comes from a nearly singular "
                 "innovation covariance (§5.1), near 0 from identities in the data "
                 f"(§5.2); the threshold {near} on sqrt(lam) is a convention. Interventions are not "
                 "removed from the levels.")
    lines += ["", "## 4 · DECISION — alternatives", ""]
    if raw:
        opts = [("keep the characterization's differences: route U (the univariate "
                 "models first)", f'build_univariate(name="{call}")'),
                ("keep them: route V (the vector first; under construction)", "route V")]
    else:
        opts = [("go on with the univariates' differences (the ladder, Jenkins and Alavi's "
                 "assumption)", f'identify_matrices(name="{call}")' if call else "identify_matrices")]
    if question:
        opts.insert(1, ("take the series to drvec: Johansen's reduced-rank test, a model "
                        "in levels with the error correction", "drvec (outside sima)"))
        opts.insert(2, ("change a series' d with this reading in hand",
                        f'characterize(name="{call}", set="SERIES: d=0")') if raw else
                    ("back to art: reconsider a series' d with this reading in hand",
                     "art (outside sima)"))
    if p_used != max(1, p_tb) or p_tb != 1:
        opts.append(("the same reading at another VAR order",
                     f'canonical_analysis(name="{call}", p=1)'))
    for t, (what, cl) in enumerate(opts):
        lines.append(f"**{'ABCDEF'[t]})** {what}\n   `{cl}`")
    lines += ["", "sima does not change any d on its own: " + (
        "it is the analyst's, in characterize." if raw else "it belongs to the `.pre`."), "",
              "⏸ **Your decision.** (guided lane: I do not go on until you say)"]
    facts = {"lam": [float(v) for v in lam], "p": p_used, "p_tb": p_tb,
             "near_one": len(unit), "near_zero": len(white), "differenced": len(diffd),
             "question": bool(question)}
    return "\n".join(lines), facts


# --------------------------------------------------------------------------- #
#  The raw-data entry: the table and the characterization                     #
# --------------------------------------------------------------------------- #

def raw_table_text(names, data, freq, start, nonpos, path):
    from .raw import window
    n, m = data.shape
    fq = {1: "annual", 4: "quarterly", 12: "monthly"}.get(freq, f"{freq} per year")
    out = [f"RAW DATA — {os.path.basename(path)}: {m} series, {n} observations, {fq}, "
           f"{window(start, freq, n)}", "",
           "  #  series              min          max     first      last"]
    for j, nm in enumerate(names):
        y = data[:, j]
        out.append(f"  {j + 1}  {nm:<14}{y.min():>11.4g}  {y.max():>11.4g}  "
                   f"{y[0]:>8.4g}  {y[-1]:>8.4g}")
    if nonpos:
        out += ["", f"Non-positive values in {', '.join(nonpos)}: logs are impossible "
                "there (lambda = 1)."]
    return "\n".join(out)


def characterize_report(chars, freq, call, changes=()):
    """art's four sections for the characterization of raw series."""
    from .raw import _fmt_p
    m = len(chars)
    lines = ["# Characterization — each series' transformation (art's engine)",
             "*(lambda -> d -> seasonality -> preliminary outliers, in art's order; "
             "each series keeps its own)*", "", "## 1 · TABLE", "",
             "_[Claude: show the block below AS IT IS; do not build your own table]_", "", "```",
             "  series            lambda   d   seasonal          treatment     outliers (|z|>3.5)"]
    for c in chars:
        if c["seasonal"] is None:
            seas = "annual"
        else:
            det, F, p = c["seasonal"]
            seas = f"{'yes' if det else 'no'} F {F:.2f} p {p:.3f}"
        treat = ("harmonics" if c["harmonics"] else f"D = {c['D']}" if c["D"] else "—")
        outl = (", ".join(f"{dt} ({z:+.1f})" for dt, z in c["outliers"][:3])
                + (" ..." if len(c["outliers"]) > 3 else "")) if c["outliers"] else "none"
        mark = " *" if c.get("changed") else ""
        lines.append(f"  {c['name']:<16}{c['lam']:>6.0f}  {c['d']:>2}   {seas:<17} "
                     f"{treat:<13} {outl}{mark}")
    lines += ["", "  unit roots (ADF p / KPSS p by d; ADF rejects a unit root, KPSS "
              "rejects stationarity):"]
    for c in chars:
        lines.append(f"  {c['name']:<16}" + "   ".join(
            f"d={d}: {_fmt_p(a)} / {_fmt_p(k)} {v}" for d, a, k, v in c["unit_root"]))
    if any(c.get("changed") for c in chars):
        lines.append("  * changed by the analyst")
    lines += ["```", "", "## 2 · WHAT IT SHOWS", ""]
    for c in chars:
        bits = []
        if c["corr_raw"] is None:
            bits.append(f"lambda = 1 ({c['lam_why']})")
        else:
            bits.append(f"lambda = {c['lam']:.0f}: the mean-sd correlation is "
                        f"{c['corr_raw']:+.2f} in levels and {c['corr_log']:+.2f} in logs"
                        + (" — opposite signs: the statistic does not close it, the "
                           "domain does (a price or a quantity goes to logs)"
                           if c["lam_ambiguous"] else ""))
        dt = c["d_tests"]
        bits.append(f"d = {c['d']}" + (f" (the tests reach stationarity at d = {dt}; "
                                        "art's policy takes one step at a time)"
                                        if dt != c["d"] else ""))
        if c["seasonal"] is not None:
            det, F, p = c["seasonal"]
            bits.append(f"seasonality {'detected' if det else 'not detected'} "
                        f"(HAC F {F:.2f}, p {p:.3f})")
        if c["outliers"]:
            bits.append(f"{len(c['outliers'])} observation(s) beyond 3.5 s.d. on the "
                        "stationary series, before any model")
        lines.append(f"- **{c['name']}**: " + "; ".join(bits) + ".")
    if changes:
        lines.append("- Changed by the analyst: " + "; ".join(changes) + ".")
    nd = [c["name"] for c in chars if c["d"] >= 1]
    lines += ["", "## 3 · CONCLUSIONS", ""]
    lams = {c["lam"] for c in chars}
    ds = {c["d"] for c in chars}
    lines.append("Each series keeps its own transformation"
                 + ("" if len(lams) == 1 and len(ds) == 1 else
                    " — and they differ here, which is why there is no joint consensus "
                    "(the old sima gave every series the largest d)") + ".")
    if len(nd) >= 2:
        lines.append(f"{len(nd)} series are differenced ({', '.join(nd)}). Whether the "
                     "system needs every difference is worth asking NOW, before anything "
                     "is built on them: Box and Tiao's canonical analysis of the levels.")
    if any(c["outliers"] for c in chars):
        lines.append("The outliers are reported, not treated: an intervention belongs to "
                     "the series' own model (art).")
    lines.append("This is a starting point, as in art: the formal test of d is "
                 "Shin-Fuller on an estimated model"
                 + (", and the seasonal treatment (harmonics or D) is the analyst's choice."
                    if freq > 1 else "."))
    lines += ["", "## 4 · DECISION — alternatives", ""]
    opts = [("route U: build the univariate models first, then the system (Jenkins "
             "and Alavi; the ladder)", f'build_univariate(name="{call}")'),
            ("route V: the vector first, the univariates only as the yardstick (Tiao and "
             "Box) — under construction (docs/STUDY-raw-entry.md)", "route V"),
            ("change a series' lambda, d, D or harmonics",
             f'characterize(name="{call}", set="SERIES: lam=0, d=1; ...")')]
    if len(nd) >= 2:
        opts.insert(1, ("read the levels first: Box and Tiao's canonical analysis",
                        f'canonical_analysis(name="{call}")'))
    opts.append(("take a series to art, to build its model there with every node",
                 "art (outside sima)"))
    for t, (what, cl) in enumerate(opts):
        lines.append(f"**{'ABCDEF'[t]})** {what}\n   `{cl}`")
    lines += ["", "⏸ **Your decision.** (guided lane: I do not go on until you say)"]
    return "\n".join(lines)


def build_report(built, freq, call):
    """Route U's report: the univariate models sima built, art's four sections."""
    lines = ["# Route U — the univariate models, built by sima (art's engine, light)",
             "*(art's first-ranked orders on each series' characterization, fitted with "
             "fue; not reviewed in art)*", "", "## 1 · TABLE", "",
             "_[Claude: show the block below AS IT IS; do not build your own table]_", "", "```"]
    weak = []
    for b in built:
        lines.append(f"{b['name']}: {b['label']}   sigma {b['sigma']:.2f}   {b['mean']}")
        lines.append(f"  parameters: " + (", ".join(f"{v:.4g}" for v in b["params"])
                                          if b["params"] else "none (a random walk)"))
        if b["lb"]:
            lines.append("  Ljung-Box: " + "   ".join(
                f"Q({int(k)}) = {q:.1f} p {pv:.3f}{'*' if pv < 0.05 else ''}"
                for k, q, pv in b["lb"]))
            if any(pv < 0.05 for _k, _q, pv in b["lb"]):
                weak.append(b["name"])
        dt, z = b["max_z"]
        lines.append(f"  largest residual: {dt} ({z:+.1f} s.d.)")
        if len(b["tied"]) > 1:
            lines.append(f"  tie: {', '.join(b['tied'])}")
        lines.append(f"  file: {b['pre']}")
        lines.append("")
    lines[-1:] = ["```", "", "## 2 · WHAT IT SHOWS", ""]
    for b in built:
        bits = [f"{b['label'].split()[-1]} on its characterization"]
        if len(b["tied"]) > 1:
            bits.append(f"a genuine tie with {len(b['tied']) - 1} other(s): the first was "
                        "taken; art's domain card would decide it")
        if b["name"] in weak:
            bits.append("the residuals are NOT white at the 5 % level")
        if abs(b["max_z"][1]) >= 3.5:
            bits.append(f"a large residual at {b['max_z'][0]}")
        lines.append(f"- **{b['name']}**: " + "; ".join(bits) + ".")
    lines += ["", "## 3 · CONCLUSIONS", "",
              "These are art's AUTONOMOUS models in miniature: the orders art ranks first, "
              "the mean or drift, a residual check. Not done here: over-parameterisation, "
              "Easter and calendar effects, the formal tests (Shin-Fuller), MEG, "
              "interventions. Every .pre says so in its header, and the guion records it."]
    if weak:
        lines.append(f"Residual autocorrelation in {', '.join(weak)}: that model is not "
                     "a good seed yet — the system would absorb what it misses (Jenkins "
                     "and Alavi's diagonal residuals in method 2 will show it).")
    if any(len(b["tied"]) > 1 for b in built):
        lines.append("Where there is a tie, another order is as defensible; it changes the "
                     "seed, not the method.")
    lines += ["", "## 4 · DECISION — alternatives", ""]
    opts = [("go on: certify these models as the system's base",
             f'run_gate(name="{call}")')]
    if weak or any(len(b["tied"]) > 1 for b in built):
        who = weak or [b["name"] for b in built if len(b["tied"]) > 1]
        opts.append((f"take {', '.join(who)} to art's guided lane first, and come back "
                     "with the reviewed .pre (load_pre)", "art (outside sima)"))
    opts.append(("change a transformation and rebuild",
                 f'characterize(name="{call}", set="...") then build_univariate(name="{call}", '
                 "overwrite=True)"))
    for t, (what, cl) in enumerate(opts):
        lines.append(f"**{'ABCDEF'[t]})** {what}\n   `{cl}`")
    lines += ["", "⏸ **Your decision.** (guided lane: I do not go on until you say)"]
    return "\n".join(lines)
