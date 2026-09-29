"""sima — the MCP assistant for simultaneous VARMA models, on drvarma's ladder.

The engine is drvarma (``drvarma.ladder``): it ships numbers and never argues.
This server is the assistant: the protocol the model walks, the evidence at
each node and the menu of decisions. See docs/DESIGN.md.
"""
from __future__ import annotations

import json
import os

# pydantic_settings warns about `lifespan` when FastMCP is BUILT, not imported.
# A stdio server that writes to stderr at start-up can be read as a failure, so
# the filter is scoped to that one message (as in drvarma's old server).
import warnings as _w
_w.filterwarnings("ignore", message=r".*lifespan.*incomplete definition.*")
_w.filterwarnings("ignore", module=r"pydantic_settings.*",
                  message=r".*incomplete definition.*")

from mcp.server.fastmcp import FastMCP

from . import evidence, session as _sess

_INSTRUCTIONS = """
You are sima — the assistant for SIMULTANEOUS multivariate models: VARMA by
exact maximum likelihood (engine: drvarma). You are the third rung of the ATSW
ladder: art (one series) → mtram (transfer networks) → sima (systems).

══════════════════════════════════════════════════════
LANGUAGE
══════════════════════════════════════════════════════
Always answer in the user's language (English if ambiguous). Tool output is in
English; translate it. Present equations and tables faithfully.

══════════════════════════════════════════════════════
WHERE YOU COME FROM: THE UNIVARIATE MODELS, NEVER RAW DATA
══════════════════════════════════════════════════════
Your input is one fue file per series: a .pre (an optimum, from art or fue) or
an .inp (a specification). Each carries the series' whole univariate model:
Box-Cox, deterministic terms, differencing, mean, ARMA factors. The VARMA keeps
each model on its DIAGONAL; what you add is the CROSS dynamics between series.

You arrive here in one of two ways:
  • from art, with several univariate models the analyst wants to model jointly;
  • from mtram, when its network identification found a CYCLE: two series that
    feed each other. A cycle is where mtram ends. Load the SAME .pre files here.
There is no raw-data entry. If the user has raw series, send them to art first:
the univariate model of each series is the seed of the system and the
yardstick it has to beat. A multivariate drvarma .inp (deprecated) is
converted with split_inp and each resulting file goes through art.

══════════════════════════════════════════════════════
FIRST QUESTION
══════════════════════════════════════════════════════
  "How do you want to proceed?
   1) GUIDED — you decide at every node; I show the evidence and the options.
   2) AUTONOMOUS — I take the decisions, each with its reason in writing, and
      hand you the path and the model."
Both lanes walk the SAME nodes. Only who sits in the analyst's chair changes.

══════════════════════════════════════════════════════
THE PROTOCOL
══════════════════════════════════════════════════════
N0  load_pre          the files, their models, the common window
N1  run_gate          the univariate base, certified. If it FAILS, stop: the
                      joint model does not reproduce the univariate ones, and
                      nothing on top of it can be trusted. If a file is a
                      SPECIFICATION (it moved), offer to go back to art.
N2  identify_cross    the residual CCFs of the diagonal system: the evidence of
                      what the univariate models do NOT carry. It proposes
                      cross orders and whether the innovations correlate.
N3  estimate          a candidate: cross orders p, q; full or diagonal
                      covariance; optionally `links`, the cross dynamics only
                      on the pairs identify_cross found (its option (d)).
N4  (in estimate)     LR against the univariates, residuals, convergence.
N4b study_estimation  when estimate says the fit STOPPED ON THE MA
                      INVERTIBILITY WALL: the estimation is ill-defined there.
                      Show the roots, the second path (Shea) and the restarts,
                      and give the menu. Never present a point on the wall as
                      an optimum.
N5  evaluate          THE YARDSTICK: fixed-parameter forecasts from every origin,
                      the candidate against the univariates, same window.
N6  forecast, impulse_response, variance_decomposition — with the chosen model.
    Their figures: plot_forecast, plot_impulse_response (an ACF-like panel per
    response and shock), plot_variance_decomposition (the same layout, 0-100 %),
    and plot_residual_ccf for what the model leaves.
Record every decision with its reason: export_guion shows the path.

══════════════════════════════════════════════════════
THE AUTONOMOUS LANE — YOU ARE THE ANALYST
══════════════════════════════════════════════════════
You decide every node yourself: there is no human to confirm. That does NOT
mean going fast. It means each decision is yours and has to be reasoned in
writing. The same nodes as the guided lane, in the same order, ONE AT A TIME:

  N0 load_pre         the files are given; note any series trimmed to the
                      common window (it changes the sample of the others).
  N1 run_gate         if it FAILS, stop and say why. If a file MOVED (it was a
                      specification, not an optimum), decide whether to go on
                      and write it down: its univariate model has not been
                      validated here.
  N2 identify_cross   read the CCFs of the diagonal system: which pairs, at
                      which lags, and whether the innovations correlate
                      (full or diagonal covariance). Choose the candidates to
                      estimate FROM THIS EVIDENCE, not from a grid. When only
                      some pairs showed anything, the restricted candidate
                      (`links`) is one of them, and the full one tests it.
  N3/N4 estimate      one candidate at a time. A tie (LR p near 0.05, or two
                      candidates that read the same) is resolved by ESTIMATING
                      BOTH and comparing, not by choosing on paper.
  N4b study_estimation if a fit stops on the MA wall. Decide from its menu and
                      write why; never report a point on the wall as an optimum.
  N5 evaluate         every surviving candidate against the univariates, same
                      window. The rule: a VARMA is kept only if it forecasts
                      better OUT OF SAMPLE. In-sample significance is necessary,
                      not sufficient. If none wins, the univariate models are
                      the result: a finding, stated plainly.
  N6 forecast, impulse_response, variance_decomposition — with the chosen
                      model; state the Cholesky order as an assumption, and
                      with correlated innovations compare it with reorder.

NEVER DECIDE NODES IN BATCH. Choosing the candidates and the covariance before
the CCF exists, or the model before evaluate, flattens the loop into one pass
forward: the decision is taken before the evidence that could correct it.

DOCUMENTATION — mandatory. After EVERY node:
    record_decision(name, node="N…", decision=…, reason=<WHY>,
                    evidence=<the numbers>, alternatives=<what you set aside
                    and why>, decided_by="LLM")
A branch you abandon is recorded too: what a failed candidate contributes is
the reason it failed.

WHAT YOU HAND OVER at the end: the guion (export_guion); the chosen model, or
the univariate models if no VARMA beat them; the yardstick numbers (N5) that
decided it; and the caveats that stay open (a fit on the MA wall, a moved
file, the Cholesky order).

══════════════════════════════════════════════════════
RULES THAT ARE NOT NEGOTIATED
══════════════════════════════════════════════════════
1. THE UNIVARIATE MODEL IS THE YARDSTICK. A VARMA that does not forecast better
   than the univariate models out of sample (N5) has no reason to exist,
   however significant its cross terms are in sample. Say so plainly when it
   happens: it is a finding, not a failure.
2. The gate is not optional and not decorative. A failed gate stops the
   analysis. Do not estimate on top of it.
3. You are shown EVIDENCE and a MENU of options with arguments for and against.
   The tools do not decide. In the guided lane the analyst decides; in the
   autonomous lane you decide and write why, citing the evidence.
4. The Cholesky ORDER of the impulse responses is the order of the files, and
   it is an identifying assumption. With a strong contemporaneous correlation,
   reorder and compare before calling a response a finding.
5. Never pre-transform or difference the data: each file's own model does it.
6. Do not prune a link or drop a series to make a number look better. That is
   the analyst's judgement, stated as such.
7. Present the tables as the tools return them. Do not rebuild them.
"""

mcp = FastMCP("sima — simultaneous VARMA on the ATSW ladder (drvarma)",
              instructions=_INSTRUCTIONS)


def _ladder(files, p, q, diagcov, estwin=None, links=None):
    from drvarma.ladder import Ladder
    return Ladder(list(files), p, q, diagcov=diagcov, estwin=estwin,
                  links=links or None)


def _links(links):
    """The canonical text of `links`: "" for every pair (no restriction)."""
    if not links or not links.strip():
        return ""
    return ", ".join(t.strip() for t in links.split(",") if t.strip())


def _bands(s, horizon, want, ndraws):
    """(bands, None) or (None, why): the ladder's Monte-Carlo IRF/FEVD bands."""
    if not want:
        return None, None
    try:
        return _current(s).irf_fevd_bands(horizon, ndraws=int(ndraws)), None
    except Exception as e:                                   # noqa: BLE001
        return None, str(e)


def _names(s):
    return [x.name for x in s.series]


def _diagonal(s):
    """The diagonal system (p = q = 0, diagonal Q), fitted once per session."""
    if s.diagonal is None:
        L = _ladder(s.files, 0, 0, True)
        L.fit()
        s.diagonal = L
        s.gate = L.gate
    return s.diagonal


# --------------------------------------------------------------------------- #
#  N0                                                                          #
# --------------------------------------------------------------------------- #

@mcp.tool()
def load_pre(name: str, paths_json: str) -> str:
    """N0 — Start a session from the univariate models: one fue file per series.

    `paths_json` is a JSON list of paths to fue files — `.pre` (optima, from art
    or fue) or `.inp` (specifications) — in the order you want the system (it is
    also the Cholesky order of the impulse responses). This is how you arrive
    from mtram when it found a cycle: load the SAME `.pre` files it had.

    The files are read by fue's own parser and recognised by their content. The
    series must share their frequency and their LAST date (BUG-2): different
    start dates are aligned at the end; different ends are refused.
    """
    try:
        paths = json.loads(paths_json)
    except json.JSONDecodeError:
        paths = [p.strip() for p in paths_json.split(",") if p.strip()]
    paths = [os.path.expanduser(p) for p in paths]
    if len(paths) < 2:
        return "A system needs at least two series (two fue files)."
    try:
        s = _sess.open_session(name, paths)
    except Exception as e:                                # the engine says why
        return f"Cannot open the session: {e}"
    txt = evidence.series_table(s.series)
    s.guion.add("N0", "load_pre", {"files": len(paths)},
                f"{len(paths)} series: {', '.join(_names(s))}")
    return (txt + "\n\nNext: run_gate — the univariate base has to be certified "
            "before anything is built on it.")


# --------------------------------------------------------------------------- #
#  N1                                                                          #
# --------------------------------------------------------------------------- #

@mcp.tool()
def run_gate(name: str) -> str:
    """N1 — The diagonal gate: does the joint cast reproduce the univariate models?

    Each series is fitted alone on the common window; the diagonal system is
    then evaluated at those optima. The identity logL_joint = SUM logL_i is
    exact. If it fails, the analysis STOPS: nothing estimated on top of a joint
    model that does not reproduce its parts can be trusted.

    It also says whether each file is an OPTIMUM (it does not move when
    re-estimated) or a SPECIFICATION (it moves), which decides whether the
    yardstick is the analyst's certified model or not.
    """
    from drvarma.ladder import GateError
    s = _sess.get(name)
    try:
        _diagonal(s)
    except GateError as e:
        s.guion.add("N1", "run_gate", {}, f"FAILED: {e}")
        return (f"GATE FAILED: {e}\n\nStop here. Report it: it is a defect of the "
                f"engine or of the files, and the system cannot be estimated on it.")
    except Exception as e:
        s.guion.add("N1", "run_gate", {}, f"error: {e}")
        return f"The gate could not run: {e}"
    s.guion.add("N1", "run_gate", {},
                f"passed, difference {s.gate['difference']:.2e}")
    return evidence.gate_text(s.gate) + "\n\nNext: identify_cross."


# --------------------------------------------------------------------------- #
#  N2                                                                          #
# --------------------------------------------------------------------------- #

@mcp.tool()
def identify_cross(name: str, nlags: int = 0) -> str:
    """N2 — What the univariate models do NOT carry: residual cross-correlations.

    Reads the CCFs of the residuals of the diagonal system, pair by pair. Those
    residuals are each series' own innovations — prewhitened by construction —
    so a cross-correlation beyond the band is evidence of a dynamic between the
    series. Contemporaneous correlation points to a full innovation covariance;
    lead-lag correlation points to cross orders p (and q). Returns the evidence
    and the menu of candidates, each with its argument. It does not choose.

    `nlags` defaults to twice the frequency (24 for monthly data).
    """
    s = _sess.get(name)
    try:
        L = _diagonal(s)
    except Exception as e:
        return f"Run the gate first ({e})."
    freq = s.series[0].freq
    K = nlags or max(8, 2 * freq)
    txt, facts = evidence.cross_identification(L.result.residuals, _names(s), K, freq)
    s.guion.add("N2", "identify_cross", {"nlags": K},
                f"short leads up to {facts['maxlag']}, longer {facts['longer']}, contemporaneous "
                f"{'yes' if facts['contemporaneous'] else 'no'}")
    return txt


# --------------------------------------------------------------------------- #
#  N3 / N4                                                                     #
# --------------------------------------------------------------------------- #

@mcp.tool()
def estimate(name: str, p: int, q: int, diagcov: bool = False,
             reason: str = "", links: str = "") -> str:
    """N3/N4 — Estimate a candidate: cross orders p, q; full or diagonal covariance.

    Each series keeps its univariate model on the diagonal (its ARMA factors are
    re-estimated jointly, its deterministic terms stay as in its file). Reports
    the parameters, the LR test against the univariates (in sample: necessary,
    not sufficient), the innovation correlations, the residual portmanteau and
    how the optimiser stopped. `reason` is recorded in the guion: say why this
    candidate.

    `links` restricts the cross dynamics to the pairs the evidence points at:
    "A<-B, C<-A" (B enters the equation of A, AR and MA, every lag up to p and
    q; names as in identify_cross). Empty (default): every pair. identify_cross
    proposes it as option (d) when only some pairs showed anything.
    """
    s = _sess.get(name)
    if s.gate is None:
        return "Run the gate first (run_gate)."
    lk = _links(links)
    key = (int(p), int(q), bool(diagcov), lk)
    try:
        L = _ladder(s.files, int(p), int(q), bool(diagcov), links=lk)
        L.fit()
    except Exception as e:
        s.guion.add("N3", "estimate", {"p": p, "q": q, "diagcov": diagcov, "links": lk},
                    f"failed: {e}", reason)
        return f"Estimation failed: {e}"
    s.fits[key] = L
    s.current = key
    freq = s.series[0].freq
    txt = evidence.estimation_text(L, max(8, 2 * freq))
    lr = "" if (p == 0 and q == 0 and diagcov) else " LR %.2f df %d p %.4f" % L.lr_test()
    s.guion.add("N3", "estimate", {"p": p, "q": q, "diagcov": diagcov, "links": lk},
                f"logL {L.result.logL:.4f}, {L.result.npar} parameters;{lr}", reason)
    nxt = "Next: evaluate — the candidate against the univariates."
    if getattr(L.result, "ma_boundary", 0):
        nxt = ("The fit stopped on the MA invertibility wall: study it before "
               "reading its numbers (study_estimation).")
    return txt + "\n\n" + nxt


@mcp.tool()
def study_estimation(name: str, restarts: int = 6, retreat: float = 0.97) -> str:
    """N4b — Study the current fit when the estimation may be ill-defined.

    For a fit that stopped on the MA invertibility wall (estimate says so), or
    any fit whose optimum you doubt. Evidence, then a menu; no verdict:

    1. the AR and MA inverse roots of the joint model, and the pairs that nearly
       cancel (a near-common factor makes the likelihood a ridge);
    2. a SECOND PATH: the same model optimised with Shea's exact likelihood
       (AS 242) instead of elf (AS 311) -- same function, independent code,
       another path;
    3. RESTARTS: from the stopping point, step back towards the start
       (x = start + retreat * (stop - start)) and re-optimise; repeat while the
       likelihood rises. If it keeps rising, the ridge climbs along the wall and
       the reported point is not a maximum.
    """
    import copy
    from drvarma.ladder import Ladder
    s = _sess.get(name)
    if s.current is None or s.current not in s.fits:
        return "Estimate a model first (estimate)."
    p, q, diagcov, lk = s.current
    L = s.fits[s.current]
    r = L.result
    freq = s.series[0].freq
    out = [f"STUDY of the fit p = {p}, q = {q}, "
           f"{'diagonal' if diagcov else 'full'} covariance" + (f", links {lk}" if lk else ""),
           f"  as estimated: logL {r.logL:.6f}, {r.nit} iterations, "
           + (f"STOPPED ON THE MA WALL ({r.ma_boundary} of {r.ma_nroots} roots)"
              if getattr(r, "ma_boundary", 0) else "not on the MA wall"), "",
           evidence.roots_text(r, freq), ""]
    # 2. the second path
    try:
        Ls = Ladder(list(s.files), p, q, diagcov=diagcov, lik="shea", links=lk or None)
        rs = Ls.fit()
        out += ["SECOND PATH (Shea's likelihood, AS 242):",
                f"  logL {rs.logL:.6f}  ({rs.nit} iterations; "
                + (f"on the MA wall, {rs.ma_boundary} of {rs.ma_nroots} roots)"
                   if rs.ma_boundary else "not on the MA wall)")
                + f"   difference to the fit: {rs.logL - r.logL:+.6f}", ""]
    except Exception as e:                                # pragma: no cover
        out += [f"SECOND PATH failed: {e}", ""]
    # 3. restarts
    rows = []
    if L.x_start is not None and 0.0 < retreat < 1.0:
        Lr = copy.deepcopy(L)
        x, best = r.x.copy(), r.logL
        for k in range(1, int(restarts) + 1):
            xk = L.x_start + retreat * (x - L.x_start)
            try:
                rk = Lr.refit(xk)
            except Exception as e:                        # pragma: no cover
                rows.append(f"  round {k}: failed ({e})")
                break
            rows.append(f"  round {k}: logL {rk.logL:.6f}  ({rk.nit} it.)  "
                        + (f"on the wall ({rk.ma_boundary} of {rk.ma_nroots})"
                           if rk.ma_boundary else "inside"))
            if not rk.logL > best + 1e-6:
                break
            x, best = rk.x.copy(), rk.logL
        out += [f"RESTARTS (retreat {retreat} towards the start, re-optimise):"] + rows
        out += [f"  highest reached: logL {best:.6f}  ({best - r.logL:+.6f} over the fit)", ""]
    out += ["MENU (the analyst decides):",
            "  a) Remove the near-common factor, or lower p or q, and re-estimate:",
            "     a model whose likelihood has an interior maximum.",
            "  b) Keep the model knowing it sits on the invertibility boundary: its",
            "     values are one point of a ridge, and they depend on the path.",
            "  c) If the restarts or the second path climbed, the fit as estimated",
            "     is not the top of the ridge; report the highest point as such,",
            "     stating that it is on the wall."]
    wall = evidence.wall_frequencies(r, freq)
    seasonal = sorted({round(k / freq, 6) for k in range(1, freq // 2 + 1)}) if freq > 1 else []
    if 0.0 in wall:
        out += ["  d) An MA root ON THE WALL AT FREQUENCY 0 is the signature of",
                "     over-differencing: the series may be differenced once too often.",
                "     That is the univariate model's decision (art: its d), not this",
                "     rung's. For: it removes the wall at its cause. Against: the",
                "     univariate diagnosis chose that d for its own reasons."]
    if any(f in seasonal for f in wall if f > 0):
        out += ["  e) An MA root ON THE WALL AT A SEASONAL FREQUENCY suggests a seasonal",
                "     over-difference (or a deterministic seasonality treated as",
                "     stochastic): again the univariate model's decision (art)."]
    s.guion.add("N4b", "study_estimation", {"p": p, "q": q, "diagcov": diagcov},
                f"fit logL {r.logL:.4f}; boundary {getattr(r, 'ma_boundary', 0)}",
                "")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
#  N5                                                                          #
# --------------------------------------------------------------------------- #

@mcp.tool()
def evaluate(name: str, p: int, q: int, estwin: int, horizon: int = 12,
             diagcov: bool = False, links: str = "") -> str:
    """N5 — The yardstick: does the candidate forecast better than the univariates?

    Estimates the candidate AND the diagonal system (the univariate models) on
    the first `estwin` observations, holds the parameters fixed, and forecasts
    from every origin to the end of the data, `horizon` steps ahead. Compares
    RMSE and MAPE series by series and horizon by horizon. A VARMA that does not
    gain here has no reason to exist, whatever its in-sample significance.

    `estwin` counts observations of the FIRST series; leave enough data after it
    (at least a few dozen origins) or the comparison says little. `links`: as in
    estimate, the same restricted candidate.
    """
    s = _sess.get(name)
    if s.gate is None:
        return "Run the gate first (run_gate)."
    H = int(horizon)
    try:
        lk = _links(links)
        Lc = _ladder(s.files, p, q, diagcov, estwin=estwin, links=lk)
        Lc.fit()
        _rows, cand = Lc.recursive(H)
        Ld = _ladder(s.files, 0, 0, True, estwin=estwin)
        Ld.fit()
        _rows, diag = Ld.recursive(H)
    except Exception as e:
        return f"The evaluation failed: {e}"
    freq = s.series[0].freq
    hs = sorted({1, max(1, freq // 2), freq, 2 * freq} & set(range(1, H + 1))) or [1, H]
    label = (f"VARMA p={p} q={q} ({'diagonal' if diagcov else 'full'} cov)"
             + (f", links {lk}" if lk else ""))
    txt, facts = evidence.evaluation_text(cand, diag, label, hs, _names(s))
    s.evaluations[(p, q, diagcov, lk, estwin, H)] = (cand, diag)
    s.guion.add("N5", "evaluate", {"p": p, "q": q, "diagcov": diagcov, "links": lk,
                                   "estwin": estwin, "horizon": H},
                f"lower RMSE in {facts['wins']} of {facts['cells']} cells")
    return txt


# --------------------------------------------------------------------------- #
#  N6                                                                          #
# --------------------------------------------------------------------------- #

def _current(s):
    if s.current is None or s.current not in s.fits:
        raise KeyError("no model estimated yet: run estimate")
    return s.fits[s.current]


@mcp.tool()
def forecast(name: str, horizon: int = 12) -> str:
    """N6 — Forecast every series in its level with the last estimated model.

    Each series goes back to its level with its own univariate model:
    deterministic terms (known in the future), its differencing, its Box-Cox.
    The 95% band is built on the transformed scale and mapped back.
    """
    s = _sess.get(name)
    try:
        L = _current(s)
        fcs = L.forecast(int(horizon))
    except Exception as e:
        return f"Cannot forecast: {e}"
    s.guion.add("N6", "forecast", {"horizon": horizon, "model": str(s.current)},
                f"{horizon} steps")
    return evidence.forecast_text(fcs)


@mcp.tool()
def impulse_response(name: str, horizon: int = 12, bands: bool = True,
                     ndraws: int = 800) -> str:
    """N6 — Orthogonalised impulse responses of the last estimated model.

    Cholesky in the ORDER OF THE FILES: an identifying assumption, stated in the
    output. With a strong contemporaneous correlation, reload the files in
    another order and compare before reading a response as a finding.
    With `bands` (default): 95% Monte-Carlo bands from the covariance of the
    estimates, redrawing the whole model through the ladder's cast; a response
    whose band covers zero is not a finding.
    """
    s = _sess.get(name)
    try:
        r = _current(s).result
    except Exception as e:
        return f"{e}"
    b, why = _bands(s, int(horizon), bands, ndraws)
    s.guion.add("N6", "impulse_response", {"horizon": horizon, "bands": b is not None},
                "Cholesky, files order")
    return evidence.irf_text(r.phi, r.theta, r.sigma, _names(s), int(horizon), b, why)


@mcp.tool()
def reorder(name: str, order_json: str, horizon: int = 12) -> str:
    """N6 — The impulse responses under ANOTHER Cholesky order, against the files'.

    The reduced-form model (Phi, Theta, Sigma) does not depend on the order of
    the series; only the orthogonalisation does. So nothing is re-estimated:
    the model is permuted, the responses recomputed, and put back in the
    files' order to compare cell by cell. A response that changes sign or
    size with the order is an assumption, not a finding. With a diagonal
    covariance the order does not matter at all, and the tool says so.
    `order_json`: the series names in the new order, e.g. '["WTI", "IPC_ES"]'.
    """
    import numpy as np
    from drvarma.irf import oirf
    s = _sess.get(name)
    try:
        r = _current(s).result
    except Exception as e:
        return f"{e}"
    names = _names(s)
    try:
        order = json.loads(order_json)
        perm = [names.index(x) for x in order]
    except Exception:
        return f"order_json must be a JSON list of the series names: {names}"
    if sorted(perm) != list(range(len(names))):
        return f"order_json must name every series exactly once: {names}"
    sig = np.asarray(r.sigma, float)
    off = sig - np.diag(np.diag(sig))
    if not np.any(np.abs(off) > 1e-12 * np.max(np.abs(np.diag(sig)))):
        return ("The innovation covariance is diagonal: the Cholesky order does not "
                "change the responses. Nothing to compare.")
    H = int(horizon)
    P = np.eye(len(names))[perm]
    base = oirf(r.phi, r.theta, sig, H)
    ph = np.array([P @ a @ P.T for a in r.phi]) if len(r.phi) else r.phi
    th = np.array([P @ a @ P.T for a in r.theta]) if len(r.theta) else r.theta
    alt = oirf(ph, th, P @ sig @ P.T, H)
    alt = np.array([P.T @ alt[h] @ P for h in range(H + 1)])  # back to files order
    d = np.sqrt(np.diag(sig))
    corr = sig / np.outer(d, d)
    out = [f"CHOLESKY ORDER: files {' -> '.join(names)}  vs  {' -> '.join(order)}",
           "Same estimated model; only the orthogonalisation changes. Largest",
           "innovation correlation: " + ", ".join(
               f"{names[i]}-{names[j]} {corr[i, j]:+.3f}"
               for i in range(len(names)) for j in range(i) ), ""]
    for j, sj in enumerate(names):
        out += [f"shock to {sj}:  (files order | new order)",
                "  h  " + "".join(f"{x:>26}" for x in names)]
        for h in range(H + 1):
            out.append(f"  {h:<3}" + "".join(
                f"{f'{base[h, i, j]:+.5f} | {alt[h, i, j]:+.5f}':>26}"
                for i in range(len(names))))
        dmax = float(np.max(np.abs(base[:, :, j] - alt[:, :, j])))
        flips = int(np.sum(np.sign(base[1:, :, j]) * np.sign(alt[1:, :, j]) < 0))
        out += [f"  largest change {dmax:.5f}; sign changes {flips}", ""]
    s.guion.add("N6", "reorder", {"order": order, "horizon": H},
                "Cholesky order compared")
    return "\n".join(out)


@mcp.tool()
def variance_decomposition(name: str, horizon: int = 12, bands: bool = True,
                           ndraws: int = 800) -> str:
    """N6 — Forecast-error variance decomposition of the last estimated model.

    For each series and horizon, the share of its forecast-error variance that
    comes from each series' innovation: how much of what is not predictable in
    one series is really the other's surprise. Same Cholesky order as
    impulse_response, and the same caveat: with correlated innovations the
    shares of the first series in the order are inflated by construction.
    With `bands` (default): 95% Monte-Carlo bands at the last horizon.
    """
    s = _sess.get(name)
    try:
        r = _current(s).result
    except Exception as e:
        return f"{e}"
    b, why = _bands(s, int(horizon), bands, ndraws)
    s.guion.add("N6", "variance_decomposition", {"horizon": horizon, "bands": b is not None},
                "Cholesky, files order")
    return evidence.fevd_text(r.phi, r.theta, r.sigma, _names(s), int(horizon), b, why)


# --------------------------------------------------------------------------- #
#  The record, and the way out of the old format                               #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
#  Figures (presentation of the same numbers; sima.figures)                    #
# --------------------------------------------------------------------------- #

def _figure(s, fig, kind, path, note):
    """The figure INSIDE the answer (as art and mtram), and a PNG on disk."""
    import base64
    import tempfile
    from . import figures
    p = path or os.path.join(tempfile.gettempdir(), f"sima_{s.name}_{kind}.png")
    figures.save(fig, p)
    text = f"{note}\nPNG: {p}"
    try:
        from mcp.types import ImageContent, TextContent
        with open(p, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        return [TextContent(type="text", text=text),
                ImageContent(type="image", data=b64, mimeType="image/png")]
    except Exception:                                        # noqa: BLE001
        return [text]


@mcp.tool()
def plot_impulse_response(name: str, horizon: int = 24, bands: bool = True,
                          ndraws: int = 500, path: str = "") -> list:
    """FIGURE — The orthogonalised impulse responses of the last estimated model.

    Drawn as what an impulse response is, a function of the lag like an ACF:
    one panel per (response, shock), thick impulses at h = 0..H, the seasonal
    grid, and the 95 % Monte-Carlo band dashed (it follows h). Cholesky in the
    order of the files, as impulse_response. The numbers are impulse_response's.
    """
    from . import figures
    s = _sess.get(name)
    try:
        L = _current(s)
    except KeyError as e:
        return [str(e)]
    b, why = _bands(s, int(horizon), bands, ndraws)
    fig = figures.irf_figure(L, int(horizon), b, s.series[0].freq)
    note = "Orthogonalised impulse responses" + (f" (no band: {why})" if why else "")
    return _figure(s, fig, "irf", path, note)


@mcp.tool()
def plot_variance_decomposition(name: str, horizon: int = 24, bands: bool = True,
                                ndraws: int = 500, path: str = "") -> list:
    """FIGURE — The forecast-error variance decomposition, in the IRF's layout.

    Panel (i, j): the % of the h-step forecast-error variance of i due to the
    shock of j, h = 1..H, as impulses on a 0-100 axis with the 95 % band
    dashed. A row reads the same as in plot_impulse_response.
    """
    from . import figures
    s = _sess.get(name)
    try:
        L = _current(s)
    except KeyError as e:
        return [str(e)]
    b, why = _bands(s, int(horizon), bands, ndraws)
    fig = figures.fevd_figure(L, int(horizon), b, s.series[0].freq)
    note = "Variance decomposition" + (f" (no band: {why})" if why else "")
    return _figure(s, fig, "fevd", path, note)


@mcp.tool()
def plot_residual_ccf(name: str, nlags: int = 0, path: str = "") -> list:
    """FIGURE — The residual cross-correlations of the last estimated model,
    pair by pair: drvus' two-sided CCF (the suite's reference), with the
    Hosking Q. What is left beyond the band is what the model does not carry.
    `nlags` defaults to twice the frequency."""
    from . import figures
    s = _sess.get(name)
    try:
        L = _current(s)
    except KeyError as e:
        return [str(e)]
    freq = s.series[0].freq
    K = int(nlags) or max(8, 2 * freq)
    return _figure(s, figures.residual_ccf_figure(L, K, freq), "ccf", path,
                   f"Residual CCFs, {K} lags each side")


@mcp.tool()
def plot_forecast(name: str, horizon: int = 24, series: str = "", path: str = "") -> list:
    """FIGURE — The forecasts of the last estimated model in the format of FUF
    and art: on top the annual rate of change (%) of the last `horizon`
    observations and the `horizon` forecasts, +-1 sigma dashed (the LEVEL with
    +-2 sigma when the series is not in logs); below, ERR, the residuals of
    those observations with +-2 sigma. The numbers are forecast's.

    One figure PER SERIES, as FUF draws one page per series, so that the
    forecast report can go series by series: `series` empty (default) returns
    one figure for each; a series' name, only that one; "all", every series
    in a single grid. `path` (optional) is a directory, or with one series a
    file.
    """
    import tempfile
    from . import figures
    s = _sess.get(name)
    try:
        L = _current(s)
        fcs = L.forecast(int(horizon))
    except Exception as e:                                   # noqa: BLE001
        return [f"Cannot forecast: {e}"]
    names = _names(s)
    if series == "all":
        return _figure(s, figures.forecast_figure(L, fcs), "forecast", path,
                       f"Forecasts, {horizon} steps, every series")
    wanted = [series] if series else names
    if series and series not in names:
        return [f"No series named {series!r}; the session has {', '.join(names)}."]
    out = []
    for nm in wanted:
        if path and len(wanted) == 1 and not os.path.isdir(path):
            p = path
        else:
            p = os.path.join(path or tempfile.gettempdir(), f"sima_{s.name}_forecast_{nm}.png")
        out += _figure(s, figures.forecast_figure(L, fcs, only=nm), f"forecast_{nm}", p,
                       f"Forecasts of {nm}, {horizon} steps")
    return out


@mcp.tool()
def record_decision(name: str, node: str, decision: str, reason: str = "",
                    evidence: str = "", alternatives: str = "",
                    decided_by: str = "analyst") -> str:
    """Record a decision, WHY, on WHAT evidence, and what was set aside.

    Every node that opens a decision (which files, which candidate, keep the
    VARMA or stay with the univariates, what to do with a fit on the MA wall,
    which Cholesky order) should leave one. Example: node "N5", decision "stay
    with the univariates", reason "the VARMA gains in no cell at h >= 6",
    evidence "RMSE ratio 1.02-1.11 over 36 origins", alternatives "VARMA(1,0)
    full: better in sample (LR p 0.01), worse out of sample". In the
    AUTONOMOUS lane this is where your reasoning is written down, with
    decided_by="LLM"; a decision without its reason is not documented.
    """
    s = _sess.get(name)
    args = {"decided_by": decided_by}
    if alternatives:
        args["alternatives"] = alternatives
    e = s.guion.add(node, "record_decision", args, evidence,
                    decision + (f" -- because {reason}" if reason else ""))
    return f"Recorded as step {e.n}."


@mcp.tool()
def export_guion(name: str, save: bool = True) -> str:
    """The path of the analysis, node by node, with its evidence and decisions.

    This is what makes the analysis reviewable and repeatable: every tool call
    and every recorded decision, in order. Saved next to the first file as
    <first>.sima.json when `save`, so that the record travels with the data.
    """
    s = _sess.get(name)
    txt = s.guion.render()
    if save:
        try:
            txt += f"\n\nSaved to {s.guion.save()}"
        except OSError as e:
            txt += f"\n\n(not saved: {e})"
    return txt


@mcp.tool()
def split_inp(path: str, out_dir: str, mean: bool = True, harmonics: bool = False,
              ar: int = 0, ma: int = 0) -> str:
    """Convert a multivariate drvarma .inp (deprecated) into one fue .inp per series.

    Each file is a SPECIFICATION with the old file's transformation (and, if
    asked, an estimated mean, seasonal harmonics, a free regular AR/MA). Take
    each one through art to build its univariate model, then come back with the
    .pre files: the univariate models are the seed and the yardstick.
    """
    from drvarma.ladder import LadderError, split
    try:
        files = split(os.path.expanduser(path), mean=mean, harmonics=harmonics,
                      ar=ar, ma=ma, out_dir=os.path.expanduser(out_dir))
    except LadderError as e:
        return f"Cannot split: {e}"
    return ("Written:\n  " + "\n  ".join(files) +
            "\n\nThese are specifications. Build each series' model in art and "
            "come back with the .pre files.")


def main():
    mcp.run()


if __name__ == "__main__":
    main()
