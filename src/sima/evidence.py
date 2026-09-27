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
    lags_found, contemp = [], []
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


def estimation_text(L, nlags):
    from drvarma.diagnostics import hosking_q
    r = L.result
    names = [s.name for s in L.series]
    out = [f"ESTIMATED: cross orders p = {L.p}, q = {L.q}, "
           f"{'diagonal' if L.diagcov else 'full'} innovation covariance",
           f"optimiser: {_TERM.get(r.termcode, r.termcode)} ({r.nit} iterations)",
           f"  {'parameter':<34}{'estimate':>12}{'s.e.':>12}{'t':>9}"]
    for n, v, se in zip(r.names, r.x, r.std_errors):
        t = v / se if se > 0 else float("nan")
        mark = "  *" if se > 0 and abs(t) > 1.96 else ""
        out.append(f"  {n:<34}{v:>12.6f}{se:>12.6f}{t:>9.2f}{mark}")
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


def irf_text(phi, theta, sigma, names, horizon):
    from drvarma.irf import oirf
    O = oirf(phi, theta, sigma, horizon)
    out = ["IMPULSE RESPONSES (orthogonalised, Cholesky in the ORDER OF THE FILES:",
           f"{' -> '.join(names)}). That order is an identifying ASSUMPTION: the first",
           "series is not moved within the period by the others' innovations. With a",
           "strong contemporaneous correlation the answer depends on it; reorder the",
           "files and compare before reading a response as a finding.",
           "Responses on the stationary (transformed, differenced) scale."]
    for j, sj in enumerate(names):
        out += ["", f"shock to {sj}:", "  h  " + "".join(f"{s:>12}" for s in names)]
        for h in range(horizon + 1):
            out.append(f"  {h:<3}" + "".join(f"{O[h, i, j]:>12.5f}" for i in range(len(names))))
    return "\n".join(out)


def fevd_text(phi, theta, sigma, names, horizon):
    from drvarma.irf import fevd
    F = fevd(phi, theta, sigma, horizon)
    out = ["FORECAST-ERROR VARIANCE DECOMPOSITION (%, same Cholesky order as the IRF)"]
    for i, si in enumerate(names):
        out += ["", f"{si}:", "  h  " + "".join(f"{s:>10}" for s in names)]
        for h in sorted({1, max(1, horizon // 4), max(1, horizon // 2), horizon}):
            out.append(f"  {h:<3}" + "".join(f"{F[h - 1, i, j]:>10.1f}" for j in range(len(names))))
    return "\n".join(out)
