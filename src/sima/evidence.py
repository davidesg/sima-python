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
                                           q_partial_corr_matrices, symbols)
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
    if p1 and q2:
        out.append("  Their warning (3.26): after prewhitening a cross AR structure reads "
                   "as an MA of higher order, and leads to a mis-specified AR and to "
                   "over-parameterisation. With both readings present, estimate (a) and "
                   "(b), compare them, and let N5 decide.")
    facts = {"method2_q": q2, "links": links, "method1_links": links1,
             "method1_q": q1, "method1_p": p1,
             "method1_pq": pq, "method1_whole": {"q": q1w, "p": p1w, "pq": pqw},
             "diagonal_left": diag_left}
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
    facts = {"n_beyond": len(beyond), "beyond": beyond, "large": len(big)}
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

def evaluation_text(cand, diag, label, horizons, series):
    """cand/diag: {(series, h): {n, MAE, RMSE, MAPE}}; series: names in order."""
    out = [f"THE YARDSTICK — {label} against the univariates (diagonal system),",
           "same window, parameters estimated once and held fixed, every origin.",
           f"  {'series':<12}{'h':>4}{'n':>5}{'RMSE var':>11}{'RMSE uni':>11}"
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
            out.append(f"  {s:<12}{h:>4}{c['n']:>5}{c['RMSE']:>11.4f}{u['RMSE']:>11.4f}"
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
