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
                      covariance.
N4  (in estimate)     LR against the univariates, residuals, convergence.
N5  evaluate          THE YARDSTICK: fixed-parameter forecasts from every origin,
                      the candidate against the univariates, same window.
N6  forecast, impulse_response, variance_decomposition — with the chosen model.
Record every decision with its reason: export_guion shows the path.

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


def _ladder(files, p, q, diagcov, estwin=None):
    from drvarma.ladder import Ladder
    return Ladder(list(files), p, q, diagcov=diagcov, estwin=estwin)


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
             reason: str = "") -> str:
    """N3/N4 — Estimate a candidate: cross orders p, q; full or diagonal covariance.

    Each series keeps its univariate model on the diagonal (its ARMA factors are
    re-estimated jointly, its deterministic terms stay as in its file). Reports
    the parameters, the LR test against the univariates (in sample: necessary,
    not sufficient), the innovation correlations, the residual portmanteau and
    how the optimiser stopped. `reason` is recorded in the guion: say why this
    candidate.
    """
    s = _sess.get(name)
    if s.gate is None:
        return "Run the gate first (run_gate)."
    key = (int(p), int(q), bool(diagcov))
    try:
        L = _ladder(s.files, *key)
        L.fit()
    except Exception as e:
        s.guion.add("N3", "estimate", {"p": p, "q": q, "diagcov": diagcov},
                    f"failed: {e}", reason)
        return f"Estimation failed: {e}"
    s.fits[key] = L
    s.current = key
    freq = s.series[0].freq
    txt = evidence.estimation_text(L, max(8, 2 * freq))
    lr = "" if (p == 0 and q == 0 and diagcov) else " LR %.2f df %d p %.4f" % L.lr_test()
    s.guion.add("N3", "estimate", {"p": p, "q": q, "diagcov": diagcov},
                f"logL {L.result.logL:.4f}, {L.result.npar} parameters;{lr}", reason)
    return txt + "\n\nNext: evaluate — the candidate against the univariates."


# --------------------------------------------------------------------------- #
#  N5                                                                          #
# --------------------------------------------------------------------------- #

@mcp.tool()
def evaluate(name: str, p: int, q: int, estwin: int, horizon: int = 12,
             diagcov: bool = False) -> str:
    """N5 — The yardstick: does the candidate forecast better than the univariates?

    Estimates the candidate AND the diagonal system (the univariate models) on
    the first `estwin` observations, holds the parameters fixed, and forecasts
    from every origin to the end of the data, `horizon` steps ahead. Compares
    RMSE and MAPE series by series and horizon by horizon. A VARMA that does not
    gain here has no reason to exist, whatever its in-sample significance.

    `estwin` counts observations of the FIRST series; leave enough data after it
    (at least a few dozen origins) or the comparison says little.
    """
    s = _sess.get(name)
    if s.gate is None:
        return "Run the gate first (run_gate)."
    H = int(horizon)
    try:
        Lc = _ladder(s.files, p, q, diagcov, estwin=estwin)
        Lc.fit()
        _rows, cand = Lc.recursive(H)
        Ld = _ladder(s.files, 0, 0, True, estwin=estwin)
        Ld.fit()
        _rows, diag = Ld.recursive(H)
    except Exception as e:
        return f"The evaluation failed: {e}"
    freq = s.series[0].freq
    hs = sorted({1, max(1, freq // 2), freq, 2 * freq} & set(range(1, H + 1))) or [1, H]
    label = f"VARMA p={p} q={q} ({'diagonal' if diagcov else 'full'} cov)"
    txt, facts = evidence.evaluation_text(cand, diag, label, hs, _names(s))
    s.evaluations[(p, q, diagcov, estwin, H)] = (cand, diag)
    s.guion.add("N5", "evaluate", {"p": p, "q": q, "diagcov": diagcov,
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
def impulse_response(name: str, horizon: int = 12) -> str:
    """N6 — Orthogonalised impulse responses of the last estimated model.

    Cholesky in the ORDER OF THE FILES: an identifying assumption, stated in the
    output. With a strong contemporaneous correlation, reload the files in
    another order and compare before reading a response as a finding.
    """
    s = _sess.get(name)
    try:
        r = _current(s).result
    except Exception as e:
        return f"{e}"
    s.guion.add("N6", "impulse_response", {"horizon": horizon}, "Cholesky, files order")
    return evidence.irf_text(r.phi, r.theta, r.sigma, _names(s), int(horizon))


@mcp.tool()
def variance_decomposition(name: str, horizon: int = 12) -> str:
    """N6 — Forecast-error variance decomposition of the last estimated model.

    For each series and horizon, the share of its forecast-error variance that
    comes from each series' innovation: how much of what is not predictable in
    one series is really the other's surprise. Same Cholesky order as
    impulse_response, and the same caveat: with correlated innovations the
    shares of the first series in the order are inflated by construction.
    """
    s = _sess.get(name)
    try:
        r = _current(s).result
    except Exception as e:
        return f"{e}"
    s.guion.add("N6", "variance_decomposition", {"horizon": horizon}, "Cholesky, files order")
    return evidence.fevd_text(r.phi, r.theta, r.sigma, _names(s), int(horizon))


# --------------------------------------------------------------------------- #
#  The record, and the way out of the old format                               #
# --------------------------------------------------------------------------- #

@mcp.tool()
def record_decision(name: str, node: str, decision: str) -> str:
    """Record a decision and its reason in the guion.

    Every node that opens a decision (which files, which candidate, keep the
    VARMA or stay with the univariates, which Cholesky order) should leave one:
    the decision, and the evidence it rests on. Example: node "N5", decision
    "stay with the univariates: the VARMA gains in no cell at h >= 6". In the
    autonomous lane this is where your reasoning is written down.
    """
    s = _sess.get(name)
    e = s.guion.add(node, "record_decision", {}, "", decision)
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
