"""sima — the MCP assistant for simultaneous VARMA models, on drvarma's ladder.

The engine is drvarma (``drvarma.ladder``): it ships numbers and never argues.
This server is the assistant: the protocol the model walks, the evidence at
each node and the menu of decisions. See docs/DESIGN.md.
"""
from __future__ import annotations

import json
import os
import re

# pydantic_settings warns about `lifespan` when FastMCP is BUILT, not imported.
# A stdio server that writes to stderr at start-up can be read as a failure, so
# the filter is scoped to that one message (as in drvarma's old server).
import warnings as _w
_w.filterwarnings("ignore", message=r".*lifespan.*incomplete definition.*")
_w.filterwarnings("ignore", module=r"pydantic_settings.*",
                  message=r".*incomplete definition.*")

from mcp.server.fastmcp import FastMCP

from . import evidence, session as _sess
from . import envelope as _env

_INSTRUCTIONS = """
You are sima — the assistant for SIMULTANEOUS multivariate models: VARMA by
exact maximum likelihood (engine: drvarma) and, when the series are
COINTEGRATED, the VARMA-VEC in levels (engine: drvec, the port of drvec C).
You are the third rung of the ATSW ladder: art (one series) → mtram (transfer
networks) → sima (systems). One session and one guion hold both: each fit
carries a KIND, VARMA or VEC, and the final-stage tools (forecast,
impulse_response, variance_decomposition, evaluate, the plots, reorder) act
on the current one.

══════════════════════════════════════════════════════
LANGUAGE
══════════════════════════════════════════════════════
Always answer in the user's language (English if ambiguous), FROM THE FIRST
ANSWER TO THE LAST. Every tool answers in English, and that is not the user's
choice: translate it — the narrative, the conclusions, the options — and keep
writing in the user's language however much English the tools send back. Do
not drift into English after a few tool calls: if the user wrote in Spanish,
the hundredth answer is in Spanish too. Tables, equations and the calls of the
options stay as the tools give them (a call is code); everything around them
is translated.

══════════════════════════════════════════════════════
WHERE YOU COME FROM: THE UNIVARIATE MODELS, OR RAW DATA
══════════════════════════════════════════════════════
Your input is one fue file per series: a .pre (an optimum, from art or fue) or
an .inp (a specification). Each carries the series' whole univariate model:
Box-Cox, deterministic terms, differencing, mean, ARMA factors. The VARMA keeps
each model on its DIAGONAL; what you add is the CROSS dynamics between series.

You arrive here in one of three ways:
  • from art, with several univariate models the analyst wants to model jointly;
  • from mtram, when its network identification found a CYCLE: two series that
    feed each other. A cycle is where mtram ends. Load the SAME .pre files here.
    With two or more of them I(1), the routing is yours, at N1c (below): the
    cointegration question comes before any VARMA in differences.
  • from RAW DATA, with no univariate models: load_data (the table) and
    characterize (each series' lambda, d and seasonality, with art's engine;
    each series keeps its own). Then a route (docs/STUDY-raw-entry.md):
    (U) build the univariate models first and climb the ladder (Jenkins and
    Alavi) with build_univariate, or (V) the vector first, the univariates
    only as the yardstick (Tiao and Box) with write_specs. Route
    U's models are art's autonomous lane in miniature: say it, and offer art
    for any series with a tie or a residual problem. With two or more differenced series, offer
    canonical_analysis on the levels right after characterize.
A multivariate drvarma .inp (deprecated) is converted with split_inp and each
resulting file goes through art.

══════════════════════════════════════════════════════
FIRST QUESTION
══════════════════════════════════════════════════════
  "How do you want to proceed?
   1) GUIDED — you decide at every node; I show the evidence and the options.
   2) AUTONOMOUS — I take the decisions, each with its reason in writing, and
      hand you the path and the model."
Both lanes walk the SAME nodes. Only who sits in the analyst's chair changes.

With the lane, in the same first exchange:
  • THE PURPOSE — "forecast" or "long run" (an equilibrium, who corrects).
    For a VEC it decides the yardstick's role (rule 9); pass it as purpose= at
    the load and N1c (prepare_vec) inherits it instead of asking again. If the
    analyst does not know yet, leave it: N1c asks. For a VARMA it decides
    nothing (rule 1 holds whatever the purpose): when the analysis is about
    impulse responses or a decomposition and no VEC is in sight, LEAVE IT
    EMPTY rather than forcing one of the two values.
  • THE ORDER of the series — the order of the files in load_pre IS the
    Cholesky order, a VEC's normalisation (beta on the last r) and the frame
    of the echelon form's A0. Ask for it before loading (most exogenous first,
    on theory); load_pre restates what it fixes.
  • With RAW DATA (no univariate models), the route: "(U) build them first
    and model the system on top of them (Jenkins and Alavi; the ladder), or
    (V) model the vector directly, the univariate models only as the yardstick
    (Tiao and Box). Either way every series keeps its own transformation."
    It is taken after characterize (build_univariate or write_specs).

Pass the lane ONCE, when loading: lane="guided" or lane="autonomous" in
load_pre, load_data or load_example. It is the session's from then on; do not
ask again. The answers follow it: in the guided lane each decision ends with
the pause (⏸ Your decision) and you stop there; in the autonomous lane the
pause is replaced by the record_decision call for that node, already filled
with the node and its evidence -- write the decision and the reason, call it,
and go on. Undeclared, the lane is guided, and every pause says so.

If the user is new to sima, or asks to see how it works, offer a WORKED
EXAMPLE first: `examples()` lists them, `load_example(<name>)` loads one (the
univariate models of a real analysis), and its tutorial, sima://example/<name>,
is your map: run it node by node in the guided lane, and after each report
add what the original analysis found. Jenkins and Alavi's muskrat and mink
(`jenkins_alavi`) is the one to start with.

══════════════════════════════════════════════════════
THE PROTOCOL
══════════════════════════════════════════════════════
N0r load_data         raw series (no univariate models): the table
N0c characterize      each series' lambda, d, seasonality, outliers (art's engine)
N0v write_specs       route V: each series' spec with only its transformation;
                      estimate(p, q) then fits the full VARMA, the diagonal
                      free; the yardstick is built for N5 only
N0u build_univariate  route U: each series' model with art's engine (light, not
                      reviewed in art), then the ladder session on those files
N0  load_pre          the files, their models, the common window
N1  run_gate          the univariate base, certified. If it FAILS, stop: the
                      joint model does not reproduce the univariate ones, and
                      nothing on top of it can be trusted. If a file is a
                      SPECIFICATION (it moved), offer to go back to art.
N1b canonical_analysis  when two or more series are differenced: Box and
                      Tiao's (1977) canonical analysis of the LEVELS. Fewer
                      near non-stationary components than differenced series
                      = stationary combinations: the joint model may not need
                      every difference (cointegration). A reading, not a
                      test; sima never changes a d.
N1c prepare_vec       THE COINTEGRATION QUESTION, offered whenever TWO OR MORE
                      series have d = 1, whatever the canonical count (the count
                      sets the emphasis, not whether it is asked). It is the
                      analyst's; in the autonomous lane yours, with the reason
                      written down. Feedback is NOT a precondition: it is
                      tested inside the VEC. First record the PURPOSE,
                      "forecast" or "long run" (it decides C8). Declined:
                      N2, the VARMA in differences. The MIXED case (I(0) and
                      I(1) series) is an option (mixed=True), never the default.
    C0 (same tool)    the checks (d >= 2, D > 0, drvec's refusals, a moved
                      file, the window), p (the AR rule or Tiao and Box's M(l)
                      on the levels, up to its first run of non-significant
                      lags: a lag significant alone after a silence is named
                      and offered, not taken), the deterministic case
                      (default "pre").
    C1 rank_test      THE RANK, by PARAMETRIC BOOTSTRAP (a JOB): the only way
                      to a rank. Outcomes:
                        r = 0       — the differences are right: back to N2
                                      (drvarma's VARMA in differences, this
                                      session);
                        0 < r < M   — the VEC: C2 onwards;
                        all reject  — "at least M - 1": the last step is a
                                      unit-root question (canonical analysis,
                                      art's table, a VARMA in levels or art);
                        a tie       — estimate both ranks and compare;
                        not I(1, r) — the model under H0 is not I(1, r) and
                                      drvec does not simulate from it: no
                                      rank is read; reread the integration
                                      orders, or another specification.
                      plot_rank_bootstrap draws LR* against the observed LR.
                      With n / (M p) small (C1 says so) the verdict can flip
                      with p: sweep(name, p="p-1,p,p+1", B=...) reads the rank
                      at the neighbouring orders (jobs); the autonomous lane
                      runs it before deciding, and argues p, not the rank.
    C2 estimate_vec   the adopted VEC: the ROLES (normalise_on), drvec's .out
                      blocks, alpha from the matrix, the canonical weights
                      beside beta; a fit on a ridge is declared, never an
                      optimum.
    C3 test_restriction  alpha and beta by LR (weak exogeneity: who corrects);
                      Gamma by LR too (gamma="X1,X2 <- Y": no feedback). With
                      weakex/alpha on the same inputs it is the CONDITIONAL
                      model's joint test; when it holds, offer mtram (output
                      and inputs named in the report), never go there yourself.
    C4 add_exogenous  inputs, dispatched by their order of integration.
    C5 long_run       theta, both half-lives, Gonzalo and Ng.
    C6 impulse_response / variance_decomposition on the VEC: the LEVELS; bands
                      only from irf_bands (a JOB, the bootstrap).
    C7 sweep          robustness: p, case, subsamples (one cached job a cell).
    C8 evaluate       the yardstick for the VEC (see rule 9).
    JOBS              rank_test, irf_bands and sweep run as detached jobs that
                      survive the conversation: job_status, job_result,
                      job_cancel, jobs. A job tool waits ~20 s, then returns the
                      job id. NOTHING PARTIAL IS EVER A RESULT.
N2  (in this order: identify_cross → identify_matrices → identify_echelon when
    an MA is in sight; route V starts at identify_matrices)
    identify_cross    the residual CCFs of the diagonal system: the evidence of
                      what the univariate models do NOT carry. It proposes
                      cross orders and whether the innovations correlate.
    identify_matrices Jenkins and Alavi's (1981) two identifications as
                      matrices: method 2 on the univariate residuals
                      (prewhitened: an MA residual model and its links), method
                      1 on the stationary series (S_k, S_k(q): the AR/ARMA
                      orders; and Tiao and Box's (1981) stepwise M(l), the
                      test beside S_k's pattern), and the comparison. Use
                      both, as they did.
    plot_identification  their figure, pair by pair: R_k over S_k, two-sided, in
                      GraphMaker's CCF panel, method=2 (prewhitened) or 1 (not).
    identify_echelon  the third form, Lutkepohl and Poskitt's (1996) echelon
                      VARMA. Its Kronecker indices from the data (a long VAR,
                      then least squares per candidate, SC). The order of the
                      series is part of the model. On route U the models'
                      seasonal factors multiply their whole rows.
N3  lag_order         the order of the VAR by LR: VAR(0) -> ... -> VAR(pmax) by
                      exact ML, each step against the one before (Tiao and
                      Box's sequential reading on the fitted models), their
                      least-squares M(l) beside it, AIC and BIC as
                      information. LR only, never Wald (a fit on a ridge gives
                      no Hessian to trust).
    estimate          a candidate: cross orders p, q; full or diagonal
                      covariance; optionally `links`, the cross dynamics only
                      on the pairs identify_cross found (its option (d)).
                      `indices` fits the echelon form instead (route U: with
                      the row factor's LR check).
N4  (in estimate)     LR against the univariates, residuals, convergence.
    check_residuals   Jenkins and Alavi's checking: large residuals on the
                      uncorrelated transformed residuals (with dates, the entry
                      to interventions), the residual correlation matrices,
                      the portmanteau matrix.
N4s simplify          Tiao and Box's simplification: coefficients |t| < 1 at
                      zero, refitted, tested by LR (and AIC, BIC); adopt with
                      the estimate call it gives (cached). Several rounds.
N4t structure         is the system simultaneous? Each pair's cross terms at
                      zero (LR), and every triangular ordering; one that
                      stands = a transfer network: offer mtram, never go.
                      Warn: a low-order fit can show a spurious feedback.
N4b study_estimation  when estimate says the fit STOPPED ON THE MA
                      INVERTIBILITY WALL: the estimation is ill-defined there.
                      Show the roots, the second path (Shea) and the restarts,
                      and give the menu. Never present a point on the wall as
                      an optimum.
N5  evaluate          THE YARDSTICK: fixed-parameter forecasts from every origin,
                      the candidate against the univariates, same window.
    forecast_uncertainty  Jenkins and Alavi's Table VIII: V(l) of the model
                      against the univariates, by lead (in sample; evaluate
                      is the test).
    adopt / abandon   the decision of N5 as data: adopt(model=..., why=...)
                      keeps a model (or "univariates"), abandon(...) sets a
                      candidate aside with its reason. The final-stage tools
                      warn when they act on a model that is not the adopted
                      one. A decision a tool ends in stays OPEN in the guion
                      until a call takes one of its options.
N6  forecast, impulse_response, variance_decomposition — with the chosen model.
    Their figures: plot_forecast, plot_impulse_response (an ACF-like panel per
    response and shock), plot_variance_decomposition (the same layout, 0-100 %),
    and plot_residual_ccf for what the model leaves.
Record every decision with its reason: export_guion shows the path.

══════════════════════════════════════════════════════
REPORTS: TABLE, INFORMATION, FIGURE — AS art DOES
══════════════════════════════════════════════════════
A tool that draws a figure returns art's report around it, and you present it
in its order: 1 · TABLE (the block, AS IT IS — never rebuild it), 2 · WHAT IT
SHOWS (read it to the analyst in their words: per pair and side, which bars
cross the band, who leads, the cut-off, the isolated ones, the statistic and
its p-value), 3 · CONCLUSIONS, 4 · DECISION — the alternatives with their
calls; then the figure, which comes inside the answer. The figure is terse,
as the originals it copies (GraphMaker, drvus, fue); the numbers are in the
table. Which alternative you would take, and why, is said AS A SUGGESTION,
with the argument against it too. Guided lane: stop at ⏸, the analyst
decides. Autonomous: decide and record_decision. Do not describe what the
report does not say.

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
  N1c prepare_vec     with two or more I(1) series: decide whether to test the
                      rank, and the PURPOSE ("forecast" or "long run"), and
                      record both. Then rank_test, and DO NOT DECIDE THE RANK
                      until job_result has the final table (poll job_status).
                      The rank is the bootstrap's; adopting another one is a
                      claim on theory, written as such (estimate_vec theory=).
  C2-C8               one node at a time, as below: the roles, each
                      restriction, each input, the long run, the yardstick —
                      each with its record_decision.
  N2 identify_cross   read the CCFs of the diagonal system: which pairs, at
                      which lags, and whether the innovations correlate
                      (full or diagonal covariance). Choose the candidates to
                      estimate FROM THIS EVIDENCE, not from a grid. When only
                      some pairs showed anything, the restricted candidate
                      (`links`) is one of them, and the full one tests it.
                      THE ORDER IN N2 is always the same: identify_cross (route
                      U; the quick reading, pair by pair) → identify_matrices
                      (Jenkins and Alavi's two methods, Tiao and Box's M(l);
                      route V starts here, it has no univariate residuals) →
                      identify_echelon when the orders point to an MA or a fit
                      reaches the MA wall.
  N3/N4 estimate      one candidate at a time. A tie (LR p near 0.05, or two
                      candidates that read the same) is resolved by ESTIMATING
                      BOTH and comparing, not by choosing on paper.
  N4b study_estimation if a fit stops on the MA wall. Decide from its menu and
                      write why; never report a point on the wall as an optimum.
  N5 evaluate         (then adopt or abandon, with why=)
                      every surviving candidate against the univariates, same
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

WHAT YOU HAND OVER at the end: hand_over(name) gathers it — the adopted model,
or the univariate models if no VARMA beat them; the yardstick numbers (N5) that
decided it; the caveats that stay open (a fit on the MA wall, a moved file,
the Cholesky order); then export_guion. At any point, where(name) says where
the analysis stands and what is open (sima://doc/DECISION_NODES).

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
8. NO COINTEGRATION CLAIM WITHOUT A FINISHED BOOTSTRAP. The rank is decided
   by rank_test's parametric bootstrap; the asymptotic table is orientation,
   never the verdict; read the critical values, not the p-value. No rank, no
   beta, no equilibrium is reported without a finished bootstrap behind it,
   unless the analyst adopts r on THEORY — then estimate_vec(theory=...) writes
   it in the guion as such, beside the bootstrap's numbers.
9. THE YARDSTICK FOR A VEC is always computed and reported (C8). It is a VETO
   when the purpose recorded at N1c is "forecast" (rule 1 as it stands); a
   CAVEAT, not a veto, beside a "long run" claim (an equilibrium, who
   corrects): imposing cointegration often helps little at short horizons.
10. LR, not Wald, for every restriction on a VEC: the .out's Wald depends on
   the normalisation and is not citable. drvec's free model in those LRs can
   be weaker than the adopted VEC: test_restriction uses the best free fit
   known and shows both.
11. In a VEC the order of the series IS the normalisation (beta on the last r)
   and the Cholesky order: another order is ANOTHER FIT (estimate_vec with
   normalise_on), never a reorder. The bands of a VEC's responses come only
   from the bootstrap (irf_bands).
12. drvec's refused options are never offered: -warma, -mawarma, -specs,
   -matest, -artest, the rank test's combinations, -m 2, -rankadm, the
   instruments and the writers. No .pre is written for the system.
13. A VEC is forecast by drvarma's forecaster (the VEC written in levels): one
   forecaster for every system.
14. Resources to ASK for when needed: sima://protocol (this text),
   sima://defects (sima's and the engine's defect registers; one report with
   sima://engine-defects/BUG-XXXX), sima://docs (the design documents and the
   user manuals: the map of the decisions, node by node, with the autonomous
   lane's declared defaults and the stops, sima://doc/DECISION_NODES; the
   architecture and principles (the ladder; route U against route V, the less
   structured one), sima://doc/ARCHITECTURE;
   sima://doc/MANUAL-jenkins-alavi, sima://doc/MANUAL-echelon
   and, for cointegrated systems, sima://doc/MANUAL-vec; the VEC's study and
   plan, sima://doc/STUDY-vec and sima://doc/PLAN-vec), sima://examples and
   sima://example/<name> (a worked example's tutorial).
"""

mcp = FastMCP("sima — simultaneous VARMA and VEC on the ATSW ladder (drvarma, drvec)",
              instructions=_INSTRUCTIONS)

# Every tool's answer goes through the lane of its session (sima.lane): the
# guided pause, or in the autonomous lane the record_decision call in its
# place. One filter here, so that the tools that build the envelopes need not
# know who is in the analyst's chair.
from . import lane as _lane                                   # noqa: E402

_mcp_tool = mcp.tool


def _tool(*a, **k):
    deco = _mcp_tool(*a, **k)
    return lambda fn: deco(_lane.wrap(fn, _sess))


mcp.tool = _tool


# --------------------------------------------------------------------------- #
#  Resources: what the model can ASK for (sima.resources)                      #
# --------------------------------------------------------------------------- #

@mcp.resource("sima://protocol")
def _r_protocol() -> str:
    """The whole protocol and its doctrine: the server's instructions, to
    reread them in the middle of an analysis."""
    return _INSTRUCTIONS


@mcp.resource("sima://defects")
def _r_defects() -> str:
    """The defect registers: sima's and the engine's (drvarma), with what is
    still open. Read before proposing a simplification that looks obvious."""
    from .resources import defects_index
    return defects_index()


@mcp.resource("sima://defects/{bug_id}")
def _r_defect(bug_id: str) -> str:
    """One report of sima's register, whole (`BUG-0001` or `0001`)."""
    from .resources import defect
    return defect("sima", bug_id)


@mcp.resource("sima://engine-defects/{bug_id}")
def _r_engine_defect(bug_id: str) -> str:
    """One report of the engine's register (drvarma), whole: the ladder, the
    estimation, the MA wall (`BUG-0010` or `0010`)."""
    from .resources import defect
    return defect("drvarma", bug_id)


@mcp.resource("sima://docs")
def _r_docs() -> str:
    """The index of sima's documents (design, tool reference)."""
    from .resources import docs_index
    return docs_index()


@mcp.resource("sima://examples")
def _r_examples() -> str:
    """The worked examples this installation carries: what each teaches and
    its plan. Run one node by node with load_example."""
    from .resources import examples_index
    return examples_index()


@mcp.resource("sima://example/{name}")
def _r_example(name: str) -> str:
    """One example's step-by-step tutorial: what to look at at each node and
    what the original analysis found, for the assistant leading it."""
    from .resources import example_tutorial
    return example_tutorial(name)


@mcp.resource("sima://doc/{name}")
def _r_doc(name: str) -> str:
    """One of sima's documents, whole, by name without the extension."""
    from .resources import doc
    return doc(name)


def _ladder(files, p, q, diagcov, estwin=None, links=None, start=None,
            cross="additive", zeros=None, lik="elf", echelon=None, own="spec",
            own_zeros=None):
    """start None: the Ladder's default (zero; the stage II estimates for
    the echelon form). own "free": the echelon rows' own part replaces each
    univariate model's regular ARMA (route U); `own_zeros` holds some of its
    lags at zero (BUG-0003)."""
    from drvarma.ladder import Ladder
    if echelon:
        p = q = 0                       # the indices give the orders
    return Ladder(list(files), p, q, diagcov=diagcov, estwin=estwin,
                  links=links or None, start=start, cross=cross,
                  zeros=list(zeros) if zeros else None, lik=lik,
                  echelon=tuple(echelon) if echelon else None,
                  own=own if echelon else "spec",
                  own_zeros=own_zeros if (echelon and own == "free") else None)


_OWN = re.compile(r"(phi|theta)_(.+)\[B\^(\d+)\]")


def _zeros(text):
    """The canonical zeros: a sorted tuple of coefficient names, cross
    (AR3[A<-B]) and, in route V, own (phi_A[B^3], theta_A[B^1])."""
    if not text:
        return ()
    toks = text if isinstance(text, (list, tuple)) else text.split(",")
    return tuple(sorted({t.strip() for t in toks if t.strip()}))


def _own_is_free(s, key):
    """Are a fit's own AR/MA coefficients sima's? On route V always; on
    route U only in the echelon form, whose free AR(n_i)/MA(n_i) replaces
    the univariate model's regular ARMA (BUG-0003). Otherwise they are the
    univariate model's, art's."""
    return s.route == "V" or bool(key[6])


def _split_zeros(s, zeros, echelon=False):
    """(cross names for the ladder, own lags {series: {"ar": set, "ma": set}})."""
    cross, own = [], {}
    names = _names(s)
    for z in zeros:
        m = _OWN.fullmatch(z)
        if not m:
            cross.append(z)
            continue
        if s.route != "V" and not echelon:
            raise ValueError(f"'{z}' is a coefficient of a univariate model: on route U "
                             "the diagonal is art's — simplify it there (in the "
                             "echelon form, with indices, the own part is sima's).")
        if m.group(2) not in names:
            raise ValueError(f"'{z}': no series {m.group(2)}")
        own.setdefault(m.group(2), {"ar": set(), "ma": set()})[
            "ar" if m.group(1) == "phi" else "ma"].add(int(m.group(3)))
    return cross, own


def _key(p, q, diagcov=False, links="", cross="additive", zeros=(), indices=()):
    """A fit key: (p, q, diagcov, links, cross, zeros, indices). `indices`
    is () for the VARMA(p, q), the Kronecker indices for the echelon form
    (then p = q = their maximum)."""
    ech = tuple(int(k) for k in indices)
    if ech:
        p = q = max(ech)
    return (int(p), int(q), bool(diagcov), links, cross, zeros, ech)


def _indices(text):
    """The Kronecker indices from "1, 2, 1", "(1,2,1)" or a list: a tuple."""
    if not text:
        return ()
    if isinstance(text, (list, tuple)):
        return tuple(int(k) for k in text)
    toks = re.findall(r"-?\d+", str(text))
    if not toks or re.sub(r"[\d\s,()\[\]-]", "", str(text)):
        raise ValueError(f"indices: '{text}' is not a list of integers, e.g. \"1, 2, 1\"")
    return tuple(int(k) for k in toks)


def _nests(small, big):
    """Does the fit key `small` nest in `big` (a restriction of it)? Only the
    plain cases the guard needs: same form, lower or equal orders, a diagonal
    covariance inside a full one, and no links or zeros the big one lacks."""
    ps, qs, ds, ls, cs, zs, es = small
    pb, qb, db, lb, cb, zb, eb = big
    if es or eb or small == big or cs != cb:
        return False
    if ps > pb or qs > qb or (db and not ds):
        return False
    if lb and ls != lb:
        return False
    return set(zb) <= set(zs)


def _start_of(L):
    """The start a fit used, as a word: drvarma's start_used can carry why
    ("zero (the preliminary start was not admissible ...)")."""
    return str(getattr(L, "start_used", "") or "").split(" ")[0].strip() or "zero"


def _stalled(L):
    r = L.result
    return int(r.termcode) == 3 and int(r.nit) <= 5


def _below_nested(s, key, L):
    """The fitted models this fit nests and lies BELOW (BUG-0019): a model
    cannot fit worse than one it contains, so this is not an optimum."""
    out = []
    for k, M in s.fits.items():
        if _nests(k, key) and M.result.logL > L.result.logL + 1e-3:
            out.append((k, M.result.logL))
    return out


def _best_start():
    """The start sima uses for a VARMA's cross terms: "ols" -- the original
    drvarma's init_varma in the ladder (drvarma > 0.3.4; the C's -start ols,
    homologated) -- when the installed drvarma has it, else "preliminary"
    (Jenkins and Alavi's; the same optimum on route U, measured 19-nov-2026)."""
    try:
        from drvarma.ladder import Ladder
        return "ols" if hasattr(Ladder, "_ols_start") else "preliminary"
    except Exception:                                        # noqa: BLE001
        return "preliminary"


def _fit_paths(s, key, start):
    """The fit of `key`, by the path asked, and what the report must say
    about the path (BUG-0019).

    The cache keeps the best optimum known for a specification; the start is a
    PATH, not part of the model. Asked again with the same start, the fit is
    reused, and the report says so. With another start it is optimised again
    and the higher logL is kept, the report giving both. And a fit that lies
    below a model it nests, or that stopped within a few iterations with
    termcode 3 (drvarma BUG-0027: from the zero start the GS1 VAR(2) of the US
    monetary VAR stops after 2 iterations, 50 points below its VAR(1)), is
    retried once from the preliminary start: an impossible point is not a
    decision for the analyst, it is a failed search."""
    want = (start or "").strip().lower() or None
    best = _best_start()
    if want is None and not key[6] and best == "ols":
        # the default when the engine has it: the ladder's start plus the
        # parameters of the relation (route U: the cross terms and Q's
        # covariances, on both routes: the own models are the univariate
        # ones -- the .pre's, or route V's diagonal fit -- the ladder's principle)
        want = "ols"
    notes = []
    if key in s.fits:
        L = s.fits[key]
        # the same start: the one ASKED for (L.start) or the one used -- an
        # ols start that fell back to zero was asked as ols, and is reused
        if want is None or want in (getattr(L, "start", None), _start_of(L)):
            notes.append(f"PATH: this fit was already estimated in this session (start "
                         f"\"{L.start_used}\", logL {L.result.logL:.4f}): reused, not "
                         "optimised again. Another start (start=\"preliminary\" or "
                         "\"zero\") optimises again.")
        else:
            L2 = _model_ladder(s, key, start=want)
            L2.fit()
            a, b = L.result.logL, L2.result.logL
            same = abs(a - b) < 1e-3
            notes.append(f"PATH: start \"{L2.start_used}\" reached logL {b:.4f} in "
                         f"{L2.result.nit} iterations; the earlier start \"{L.start_used}\""
                         f" had {a:.4f}." + (" The same optimum by two paths." if same else
                         f" Kept the higher ({max(a, b):.4f})."))
            if b > a + 1e-3:
                L = L2
    else:
        L = _model_ladder(s, key, start=want)
        L.fit()
    if not key[6]:                                          # not the echelon form
        low = _below_nested(s, key, L)
        if (low or _stalled(L)) and _start_of(L) != best:
            why = ("lies BELOW " + ", ".join(f"{_desc(k)} (logL {v:.4f})" for k, v in low)
                   + ", which it nests" if low else
                   f"stopped after {L.result.nit} iteration(s) with termcode 3")
            L2 = _model_ladder(s, key, start=best)
            L2.fit()
            a, b = L.result.logL, L2.result.logL
            notes.append(f"⚠ THE FIRST PATH FAILED: from the start \"{L.start_used}\" the "
                         f"fit {why} (logL {a:.4f}, {L.result.nit} iterations): not an "
                         f"optimum. Retried from the {best} start: logL {b:.4f} in "
                         f"{L2.result.nit} iterations" + ("; kept." if b > a + 1e-3 else
                         "; no better."))
            if b > a + 1e-3:
                L = L2
        low = _below_nested(s, key, L)
        if low:
            notes.append("⚠ NOT AN OPTIMUM: this fit still lies below "
                         + ", ".join(f"{_desc(k)} (logL {v:.4f})" for k, v in low)
                         + ", which it nests. Do not read its LR or its t: run "
                         "study_estimation (the second path, Shea's).")
    return L, "\n".join(notes)


def _model_ladder(s, key, estwin=None, start=None, lik="elf"):
    """The Ladder of a fit key (p, q, diagcov, links, cross, zeros, indices)
    on its files."""
    p, q, dc, lk, cr, zs, ech = key
    cross, own = _split_zeros(s, zs, echelon=bool(ech))
    files = _files_for(s, p, q, own, orders=ech or None)
    free = bool(ech) and s.route != "V"
    return _ladder(files, p, q, dc, estwin=estwin, links=lk, start=start, cross=cr,
                   zeros=cross, lik=lik, echelon=ech or None,
                   own="free" if free else "spec", own_zeros=own if free else None)


def _factor_check(s, L):
    """The row factor's LR test (drvarma Ladder.factor_test), once per fit:
    its text, recorded in the guion."""
    if getattr(L, "factor_check", None) is None:
        try:
            L.factor_check = L.factor_test()
        except Exception as e:                               # noqa: BLE001
            return f"THE ROW FACTOR'S CHECK could not run: {e}"
    t = L.factor_check
    if t["df"] <= 0:
        return ("THE ROW FACTOR'S CHECK: the factored rows have no cross terms to share "
                "it (index 0, or links and zeros removed them), so each factor is its "
                "univariate model's: nothing to test here (art checks it).")
    fr = t["free"].result
    head = (f"THE ROW FACTOR'S CHECK — the same rows with every position the factored "
            f"product reaches free: LR {t['lr']:.2f}, df {t['df']}, p {t['p']:.4f} "
            f"(logL {t['logL']:.2f} -> {t['logL_free']:.2f}).")
    if fr.termcode not in (1, 2):
        head += (f" The free rows' optimiser stopped with termcode {fr.termcode}: it "
                 "started at this fit, so the LR is a lower bound.")
    if t["p"] >= 0.05:
        read = ("The factor holds: these rows keep the univariate models' seasonal "
                "structure, the cross terms included.")
    else:
        read = ("The data reject the factor: the seasonality of these rows is not the "
                "univariate models', once the cross terms share it. Compare with the "
                "VARMA(p, q) of route U, where the seasonal factors stay on the diagonal "
                "and the cross terms are not filtered by them.")
    s.guion.add("N3", "factor_test", {}, f"LR {t['lr']:.2f} df {t['df']} p {t['p']:.4f}")
    return ("A seasonal factor on a whole row is an a priori simplification, which "
            "Lutkepohl and Poskitt accept only when it is checked.\n" + head + "\n" + read)


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


def _files_for(s, p, q, own=None, orders=None):
    """The files a candidate is estimated on. Route U: the session's (the
    univariate models on the diagonal). Route V: each series' specification
    with a free AR(p)/MA(q) of its own, written once per order — with cross
    orders p, q the ladder is the full VARMA(p, q), Tiao and Box's model.
    `orders`: one degree per series instead (the echelon form's indices:
    series i gets a free AR(n_i)/MA(n_i))."""
    if s.route != "V":
        return s.files
    from . import raw
    r = _sess.get_raw(s.v["raw"])
    own = own or {}
    deg = list(orders) if orders else [None] * len(r.names)
    paths = []
    for j, nm in enumerate(r.names):
        pj, qj = (p, q) if deg[j] is None else (deg[j], deg[j])
        path = raw.v_path(s.v["dir"], nm, pj, qj, own.get(nm))
        if not os.path.exists(path):
            raw.write_v(s.v["dir"], [nm], r.data[:, [j]], [r.chars[j]], r.freq, r.start,
                        pj, qj, own={nm: own[nm]} if nm in own else None)
        paths.append(path)
    return paths


def _yardstick_files(s):
    """Route V's yardstick: the analyst's univariate models if evaluate was
    given them (BUG-0004), else those of route U's builder, for N5 only (they
    never enter the system). Built once, next to the specs, with what the
    builder chose and among which (yardstick.json)."""
    if s.v.get("yardstick"):
        return s.v["yardstick"]
    from . import raw
    r = _sess.get_raw(s.v["raw"])
    pres = [os.path.join(s.v["dir"], f"{nm}_u.pre") for nm in r.names]
    if not all(os.path.exists(x) for x in pres):
        facts = raw.build_univariate(r.names, r.data, r.chars, r.freq, r.start, s.v["dir"])
        with open(os.path.join(s.v["dir"], "yardstick.json"), "w") as fh:
            json.dump({f["name"]: {"label": f["label"], "tied": f["tied"]} for f in facts},
                      fh, indent=1)
    return pres


def _paths(text):
    """A JSON list of paths, or the paths separated by commas (as load_pre)."""
    try:
        paths = json.loads(text)
    except json.JSONDecodeError:
        paths = [p.strip() for p in text.split(",") if p.strip()]
    return [str(p) for p in ([paths] if isinstance(paths, str) else paths)]


def _set_yardstick(s, files):
    """The analyst's univariates as route V's yardstick: one fue file per
    series, the same series and transformation as the specs. Kept in the
    session: evaluate, forecast_uncertainty and structure read them."""
    from drvarma.ladder import load
    paths = _paths(files)
    r = _sess.get_raw(s.v["raw"])
    if len(paths) != len(r.names):
        raise ValueError(f"the yardstick takes one file per series ({len(r.names)}: "
                         f"{', '.join(r.names)}); got {len(paths)}")
    by = {x.name: x for x in load(paths)}
    if set(by) != set(r.names):
        raise ValueError(f"the yardstick's series ({', '.join(sorted(by))}) are not the "
                         f"system's ({', '.join(r.names)})")
    for nm, c in zip(r.names, r.chars):
        m = by[nm].model
        if (float(m.boxlam), int(m.d), int(m.D or 0)) != \
                (float(c["lam"]), int(c["d"]), int(c.get("D", 0))):
            raise ValueError(
                f"{nm}: the yardstick's transformation (lam={m.boxlam:g}, d={m.d}, "
                f"D={m.D or 0}) is not the system's (lam={c['lam']:g}, d={c['d']}, "
                f"D={c.get('D', 0)}): the forecasts would not be of the same thing")
    s.v["yardstick"] = [by[nm].path for nm in r.names]


def _yardstick_text(s):
    """Which models the yardstick is, series by series (BUG-0004)."""
    from drvarma.ladder import load
    files = _yardstick_files(s)
    try:
        with open(os.path.join(s.v["dir"], "yardstick.json")) as fh:
            built = json.load(fh)
    except (OSError, ValueError):
        built = {}
    rows = []
    for x in load(files):
        p, q = x.orders()
        m = x.model
        row = f"  {x.name:<14} ARIMA({p},{m.d},{q})" + (f", D = {m.D}" if m.D else "")
        if not s.v.get("yardstick"):
            b = built.get(x.name, {})
            if len(b.get("tied", [])) > 1:
                # art's labels open with the differences, "(d,D)  MA(1)"
                lbl = lambda t: re.sub(r"^\(\d+,\d+\)\s+", "", t)
                row += (f"  — {lbl(b['label'])}, the first of art's tie: "
                        f"{', '.join(map(lbl, b['tied']))}")
        rows.append(row + f"  ({x.path})")
    if s.v.get("yardstick"):
        head = "ROUTE V: the yardstick is the analyst's univariate models, given to evaluate"
    else:
        head = ("ROUTE V: the yardstick is univariate models built by route U's builder "
                "(art's engine, light; not reviewed in art). Inside a tie the builder "
                "takes the first: the analyst's models may be others, and the ratios "
                "depend on it. Give yours with evaluate(yardstick=...)")
    return head + " — they never entered the system:\n" + "\n".join(rows)


# --------------------------------------------------------------------------- #
#  N0                                                                          #
# --------------------------------------------------------------------------- #

@mcp.tool()
def examples() -> str:
    """The worked examples that come with sima, to see how it works in real
    time: each is a real analysis, from the univariate models built in art,
    run node by node with the same tools and pauses as any other.
    load_example(<name>) starts one."""
    from .resources import examples_index
    return examples_index()


@mcp.tool()
def load_example(name: str = "jenkins_alavi", session: str = "", dest: str = "",
                 lane: str = "", purpose: str = "") -> str:
    """N0 for a worked example: copy its files to a working folder (`dest`,
    default ~/sima-examples/<name>; files already there are kept) and load
    them. An example from univariate models loads them as load_pre does, and
    goes on with run_gate. An example from RAW DATA (the vector first, as
    Tiao and Box or Lutkepohl and Poskitt) loads the table as load_data does,
    and goes on with characterize. From there the analysis is the usual one,
    node by node, the analyst deciding at every pause.

    Before going on, READ its tutorial, `sima://example/<name>`: at each step
    it says what to look at and what the original analysis found, which you
    add after each report ("In the paper: ..."). The tools do not change in a
    tutorial; the explanation of the method is the manual it names.

    `lane`: "guided" or "autonomous" -- who decides the nodes, set ONCE for the
    session (the first question). Undeclared, guided, and every decision says
    so; a later load of the same session keeps the lane it has.
    `purpose`: "forecast" or "long run" -- what the model is for, asked with
    the first question and recorded at N0. Optional here; N1c (prepare_vec)
    inherits it instead of asking again. It decides the role of the yardstick
    for a VEC (rule 9).
    """
    import json as _json
    import shutil
    from .resources import example_files
    ex = example_files(name)
    if ex is None:
        from .resources import examples_index
        return f"No example `{name}`.\n\n" + examples_index()
    src, m = ex
    dest = os.path.expanduser(dest or os.path.join("~", "sima-examples", name))
    kept = 0
    raw = m.get("raw")
    for rel in (list(m.get("files", [])) + ([raw["data"]] if raw else [])
                + list(m.get("also", [])) + [m["tutorial"]]):
        o, d = os.path.join(src, rel), os.path.join(dest, rel)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        if os.path.exists(d):
            kept += 1
        else:
            shutil.copy2(o, d)
    # the example's job cache (its bootstraps, already run): found by content
    # key, so the tutorial's long jobs return at once (PLAN-vec C6)
    cached = 0
    for rel in m.get("jobs", []):
        o, d = os.path.join(src, rel), os.path.join(dest, rel)
        if os.path.isdir(o) and not os.path.exists(os.path.join(d, "result.json")):
            shutil.copytree(o, d, dirs_exist_ok=True)
        cached += os.path.isdir(o)
    session = session or name
    try:
        _sess.declare_lane(session, lane)
        _sess.declare_purpose(session, purpose)
    except ValueError as e:
        return str(e)
    if raw:
        loaded = getattr(load_data, "fn", load_data)(
            session, os.path.join(dest, raw["data"]), int(raw.get("freq", 0)),
            str(raw.get("start", "")))
        what, nxt = "The data, loaded", f'characterize("{session}")'
        import importlib.util
        if importlib.util.find_spec("art") is None:
            from .raw import RAW_EXTRA
            nxt = ("install art first: this example starts from the data, and "
                   f"characterize uses art's engine. {RAW_EXTRA}, then {nxt}")
    else:
        files = [os.path.join(dest, r) for r in m["files"]]
        loaded = _fn_load_pre(session, _json.dumps(files))
        what, nxt = "The univariate models, loaded", f'run_gate("{session}")'
    out = [f"# Worked example — {m['title']}", "", m["summary"], "",
           f"Files in `{dest}`" + (f" ({kept} already there, kept as they were)" if kept else "")
           + f"; session `{session}`."
           + (f" The example's job cache ({cached} finished job(s): its bootstraps) came "
              "with it: on this platform's tier they return at once." if cached else ""), "",
           "## The plan", ""] + [f"- {p}" for p in m.get("plan", [])] + [
           "", "## For the assistant", "",
           f"Read the tutorial now: `sima://example/{name}`. Lead it in the guided "
           "lane, ONE node at a time: present each report as always, then add what "
           "the original analysis found at that step, and stop at the pause. The "
           f"method is explained in `sima://doc/{m['manual']}`.", "",
           f"## {what}", "", loaded, "",
           f"Next: {nxt} — as the tutorial says."]
    return "\n".join(out)


def _fn_load_pre(name, paths_json):
    return getattr(load_pre, "fn", load_pre)(name, paths_json)


@mcp.tool()
def load_data(name: str, path: str, freq: int = 0, start: str = "",
              lane: str = "", purpose: str = "") -> str:
    """N0r — RAW DATA: an analyst with series and no univariate models
    (docs/STUDY-raw-entry.md). An Excel (.xlsx/.xls) or CSV table, one column
    per series in ORIGINAL levels (never transformed or differenced), a header
    row with the names, and optionally a first column of dates (a year, or
    year-period: 1972-08, 1972Q3).

    `freq`: 1, 4 or 12 (0: inferred from the date column). `start`: the first
    date, "1972-08" or "1850" (empty: from the date column). The table must be
    complete on one common calendar: missing values are refused, with where.
    Next: characterize — each series' transformation with art's engine.

    `lane`: "guided" or "autonomous" -- who decides the nodes, set ONCE for the
    session (the first question). Undeclared, guided, and every decision says
    so; a later load of the same session keeps the lane it has.
    `purpose`: "forecast" or "long run" -- what the model is for, asked with
    the first question and recorded at N0. Optional here; N1c (prepare_vec)
    inherits it instead of asking again. It decides the role of the yardstick
    for a VEC (rule 9).
    """
    try:
        _lane_now = _sess.declare_lane(name, lane)
        _pur_now = _sess.declare_purpose(name, purpose)
    except ValueError as e:
        return str(e)
    from . import raw
    try:
        names, data, dates = raw.read_table(path)
        f = int(freq)
        if not f and dates and len(dates) > 1:
            d0, d1 = raw._parse_date(dates[0], 12), raw._parse_date(dates[1], 12)
            if d0 and d1:
                f = 1 if d1[0] - d0[0] == 1 and d0[1] == d1[1] == 1 else (
                    4 if "q" in str(dates[0]).lower() else 12)
        if f not in (1, 4, 12):
            return ("Say the frequency: freq = 1 (annual), 4 (quarterly) or 12 (monthly)"
                    + ("" if dates else "; the table has no date column") + ".")
        st = raw._parse_date(start, f) if start.strip() else raw.infer_start(dates, f)
        if st is None:
            return ('Say the first date: start = "1972-08" (monthly), "1972Q3" '
                    '(quarterly) or "1850" (annual); the table has no usable date column.')
        nonpos = raw.check_table(names, data)
    except raw.RawError as e:
        return f"Cannot load: {e}"
    s = _sess.open_raw(name, os.path.abspath(os.path.expanduser(path)), names, data, f, st)
    s.guion.add("N0r", "load_data", {"path": path, "freq": f, "start": list(st),
                                     "lane": _lane_now, "purpose": _pur_now},
                f"{len(names)} series, {data.shape[0]} observations")
    return (evidence.raw_table_text(names, data, f, st, nonpos, path)
            + "\n\nNo univariate models: this is the raw entry. Next: characterize — "
            f'each series\' transformation, with art\'s engine (characterize("{name}")).'
            + "\n" + _lane_line(name))


@mcp.tool()
def characterize(name: str, set: str = "") -> str:
    """N0c — Each raw series' transformation, with art's engine and in art's
    order: lambda (Box-Cox, 0 or 1), d (ADF + KPSS, art's policy: one step at a
    time), seasonality (HAC F-test; harmonics proposed when detected) and a
    preliminary outlier scan (reported, not treated). Each series keeps its
    OWN lambda and d — no joint consensus: forcing them alike was the old
    sima's first fault.

    `set` records the analyst's changes on top of the proposal:
    "MINK: lam=0, d=0; MUSKRAT: d=1, harmonics=no" (keys lam, d, D,
    harmonics). It is the starting point of both routes (U: the univariate
    models first; V: the vector first)."""
    from . import raw
    try:
        s = _sess.get_raw(name)
    except KeyError as e:
        return str(e)
    try:
        if s.chars is None or not set.strip():
            s.chars = raw.characterize(s.names, s.data, s.freq, s.start)
        changes = raw.apply_overrides(s.chars, set)
    except raw.RawError as e:
        return f"Cannot characterize: {e}"
    s.guion.add("N0c", "characterize", {"set": set},
                "; ".join(f"{c['name']} lam {c['lam']:.0f} d {c['d']}"
                          + (" harmonics" if c["harmonics"] else f" D {c['D']}" if c["D"] else "")
                          for c in s.chars),
                "analyst: " + "; ".join(changes) if changes else "")
    return evidence.characterize_report(s.chars, s.freq, name, changes)


@mcp.tool()
def build_univariate(name: str, out_dir: str = "", overwrite: bool = False) -> str:
    """N0u — ROUTE U from raw data (docs/STUDY-raw-entry.md): build each
    series' univariate model with art's engine, then climb the ladder as
    always (Jenkins and Alavi: the univariate models first).

    On each series' characterization (characterize): the orders art ranks
    first, the mean (d = D = 0) or a drift kept only if |t| >= 2, a fue fit,
    a residual check; `<SERIES>_u.inp/.pre/.out` written to `out_dir`
    (default: `<data>_sima/` next to the table). Every .pre carries the line
    "Built by sima's raw entry (route U), not reviewed in art". This is art's
    autonomous lane in miniature — no over-parameterisation, calendar
    effects, formal tests or interventions: the report offers art for any
    series with a tie or a residual problem.

    It then opens the ladder session of the same name with those files (the
    guion goes on): next, run_gate. Existing files are kept unless
    `overwrite`."""
    from . import raw
    try:
        r = _sess.get_raw(name)
    except KeyError as e:
        return str(e)
    if r.chars is None:
        return f'Characterize the series first (characterize("{name}")).'
    d = os.path.expanduser(out_dir) if out_dir else \
        os.path.splitext(r.path)[0] + "_sima"
    pres = [os.path.join(d, f"{nm}_u.pre") for nm in r.names]
    there = [p for p in pres if os.path.exists(p)]
    if there and not overwrite:
        return ("These files exist and are kept: " + ", ".join(there) + ". Load them "
                f"(load_pre), or rebuild with overwrite=True.")
    try:
        built = raw.build_univariate(r.names, r.data, r.chars, r.freq, r.start, d)
    except Exception as e:                                   # noqa: BLE001
        return f"Cannot build the univariate models: {e}"
    r.guion.add("N0u", "build_univariate", {"out_dir": d},
                "; ".join(f"{b['name']} {b['label'].split()[-1]}" for b in built)
                + " (route U, not reviewed in art)")
    try:
        s = _sess.open_session(name, [b["pre"] for b in built])
    except Exception as e:                                   # noqa: BLE001
        return f"Built, but the session could not open: {e}"
    entries = list(r.guion.entries)
    s.guion.entries = entries
    s.guion.add("N0", "load_pre", {"files": len(built)},
                f"{len(built)} series: {', '.join(_names(s))} (route U)")
    return (evidence.build_report(built, r.freq, name) + "\n\n"
            + evidence.series_table(s.series)
            + "\n\nThe session is open on these files: next, run_gate.")


@mcp.tool()
def write_specs(name: str, out_dir: str = "", overwrite: bool = False) -> str:
    """N0v — ROUTE V from raw data (docs/STUDY-raw-entry.md): the vector
    first, as Tiao and Box (1981). No univariate models: each series gets a
    fue .inp with ONLY its characterization — lambda, d, D or harmonics, the
    mean when d = D = 0 — in `out_dir` (default `<data>_sima/`), and the
    ladder session opens on them (the guion goes on).

    Then: run_gate (it certifies the cast; the diagonal here is white noise,
    or a random walk for d = 1, not a yardstick), canonical_analysis and
    identify_matrices' method 1 (R_k, S_k, Tiao and Box's M(l)) on the
    vector. estimate(p, q) in this route writes each series' spec with a FREE
    AR(p)/MA(q) of its own and fits the full VARMA(p, q): the diagonal is
    estimated with the cross terms. evaluate compares it with univariate
    models built by route U's builder, for the yardstick only. Route V writes
    no .pre for the system: its estimates are rows of the system, not
    univariate optima."""
    from . import raw
    try:
        r = _sess.get_raw(name)
    except KeyError as e:
        return str(e)
    if r.chars is None:
        return f'Characterize the series first (characterize("{name}")).'
    d = os.path.expanduser(out_dir) if out_dir else os.path.splitext(r.path)[0] + "_sima"
    base = [raw.v_path(d, nm) for nm in r.names]
    there = [x for x in base if os.path.exists(x)]
    if there and not overwrite:
        return ("These files exist and are kept: " + ", ".join(there) + ". Rebuild with "
                "overwrite=True.")
    if overwrite:                       # order files from an older characterization
        import glob
        for nm in r.names:
            for x in glob.glob(os.path.join(d, f"{nm}_v_p*q*.inp")):
                os.remove(x)
    files = raw.write_v(d, r.names, r.data, r.chars, r.freq, r.start, base=True)
    r.guion.add("N0v", "write_specs", {"out_dir": d},
                "route V: " + "; ".join(f"{c['name']} lam {c['lam']:.0f} d {c['d']}"
                                         for c in r.chars))
    try:
        s = _sess.open_session(name, files)
    except Exception as e:                                   # noqa: BLE001
        return f"Written, but the session could not open: {e}"
    s.route, s.v = "V", {"dir": d, "raw": name}
    s.guion.entries = list(r.guion.entries)
    s.guion.add("N0", "load_pre", {"files": len(files)},
                f"{len(files)} specifications (route V): {', '.join(_names(s))}")
    return ("ROUTE V — the vector first (Tiao and Box). Each series' specification "
            "carries only its transformation:\n  " + "\n  ".join(files) + "\n\n"
            + evidence.series_table(s.series)
            + "\n\nNo univariate models enter the system. Next: run_gate (it certifies "
            "the cast), then canonical_analysis and identify_matrices on the vector.")


@mcp.tool()
def load_pre(name: str, paths_json: str, lane: str = "", purpose: str = "") -> str:
    """N0 — Start a session from the univariate models: one fue file per series.

    `paths_json` is a JSON list of paths to fue files — `.pre` (optima, from art
    or fue) or `.inp` (specifications) — in the order you want the system (it is
    also the Cholesky order of the impulse responses). This is how you arrive
    from mtram when it found a cycle: load the SAME `.pre` files it had.

    The files are read by fue's own parser and recognised by their content. The
    series must share their frequency and their LAST date (BUG-2): different
    start dates are aligned at the end; different ends are refused.

    `lane`: "guided" or "autonomous" -- who decides the nodes, set ONCE for the
    session (the first question). Undeclared, guided, and every decision says
    so; a later load of the same session keeps the lane it has.
    `purpose`: "forecast" or "long run" -- what the model is for, asked with
    the first question and recorded at N0. Optional here; N1c (prepare_vec)
    inherits it instead of asking again. It decides the role of the yardstick
    for a VEC (rule 9).
    """
    try:
        _lane_now = _sess.declare_lane(name, lane)
        _pur_now = _sess.declare_purpose(name, purpose)
    except ValueError as e:
        return str(e)
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
    from . import scale as _sc
    _notas = _sc.load_notes(s.series)
    if _notas:
        txt += "\n\n" + "\n".join("! " + n for n in _notas)
    s.guion.add("N0", "load_pre", {"files": len(paths), "lane": _lane_now,
                                   "purpose": _pur_now, "order": _names(s)},
                f"{len(paths)} series: {', '.join(_names(s))}")
    nd = sum(int(x.model.d or 0) == 1 for x in s.series)
    coint = ("\n\nTwo or more series have d = 1: after the gate and the canonical "
             "analysis sima asks the COINTEGRATION QUESTION (N1c: the rank by drvec's "
             "parametric bootstrap) before any VARMA in differences — the same files "
             "mtram hands over with a cycle." if nd >= 2 else "")
    return (txt + coint + "\n\n" + _order_text(s) + "\n\nNext: run_gate — the univariate "
            "base has to be certified before anything is built on it.\n" + _lane_line(name)
            + ("\nPurpose: " + _pur_now + " (recorded at N0; N1c inherits it)." if _pur_now else ""))


def _order_text(s):
    """N0: the order of the series is part of the model (P5) -- said once, here,
    where it is fixed."""
    names = _names(s)
    return ("THE ORDER of the series is the order of the files: "
            + " → ".join(names) + ". It is part of the model, not a detail: it is "
            "the Cholesky order of the impulse responses and the variance "
            "decomposition (rule 4: reorder compares another), in a VEC the "
            "normalisation, beta on the LAST r series (rule 11: another order is "
            "another fit), and in the echelon form the structure of A0, which the "
            "Kronecker indices are read against. Put first what is most exogenous on theory. To change it, "
            "load the files again in another order, now: everything after "
            "depends on it.")


def _lane_line(name):
    """The lane in force, as the load states it."""
    if name not in _sess._LANES:
        return _lane.UNDECLARED
    return {"guided": "Lane: guided — you decide every node; I stop at each decision.",
            "autonomous": "Lane: autonomous — I decide every node and write down "
                          "why (record_decision, decided_by=\"LLM\")."}[_sess._LANES[name]]


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
    from .raw import PROVENANCE
    built = []
    for x in s.series:
        try:
            with open(x.path) as fh:
                if PROVENANCE in fh.read(2000):
                    built.append(x.name)
        except OSError:
            pass
    prov = ("\n\nBuilt by sima's raw entry (route U), not reviewed in art: "
            + ", ".join(built) + ". The gate certifies the cast, not the models."
            if built else "")
    nd = sum(int(x.model.d or 0) >= 1 for x in s.series)
    nxt = ("Next: canonical_analysis — "
           f"{nd} series are differenced, and Box and Tiao's reading of the levels "
           "says whether they need every difference jointly; then N1c, the "
           "cointegration question (prepare_vec: the rank by drvec's bootstrap), or "
           "identify_cross."
           if nd >= 2 else "Next: identify_cross.")
    if s.route == "V":
        prov = ("\n\nRoute V: the files are specifications with no ARMA. The gate "
                "certifies the cast; the diagonal it checks is white noise (a random "
                "walk where d = 1), not a model to beat — the yardstick comes at N5.")
        nxt = ("Next: canonical_analysis (the levels), then identify_matrices — "
               "method 1 and Tiao and Box's M(l) on the vector.")
    gt = evidence.gate_text(s.gate)
    if built or s.route == "V":
        gt = gt.replace("the base is the analysts' models", "the base is the models in the files")
    return gt + prov + "\n\n" + nxt


# --------------------------------------------------------------------------- #
#  N2                                                                          #
# --------------------------------------------------------------------------- #

@mcp.tool()
def canonical_analysis(name: str, p: int = 0, near: float = 0.90,
                       interventions: str = "remove") -> str:
    """N1b — Box and Tiao's (1977) canonical analysis of the transformed LEVELS
    (each series' Box-Cox and seasonal differences; NOT its regular ones):
    the combinations of the series ordered from least to most predictable.
    Nearly white ones are relations among the series that stay stable over
    time; nearly non-stationary ones (sqrt(lam) >= `near`, the scale of a
    root: for an AR(1) component lam = phi^2) their common growth.
    When two or more series are differenced and fewer components look
    non-stationary, the joint model may not need every difference — the
    question of cointegration, which N1c asks (prepare_vec) and C1 answers
    (rank_test, by parametric bootstrap on drvec); this reading is not a
    test, and sima never changes a d on its own. `p` is the VAR order (0: the
    last significant M(l) of Tiao and Box's stepwise table on the levels). Run
    it after the gate, before the identification, when two or more series are
    differenced; with raw data (load_data, characterize), right after
    characterize, on the characterization's levels.

    The levels are read WITHOUT each model's deterministic terms (BUG-0018):
    its deterministic seasonality always (a harmonic is predictable by
    construction), its interventions by default (`interventions="keep"`
    leaves them in), never mu nor a trend. The answer says what was removed
    and, when there are interventions, gives the reading with them inside
    too, so the difference shows without asking for it."""
    import numpy as np
    if _sess.has_raw(name) and name not in _sess.names():
        from . import raw
        r = _sess.get_raw(name)
        if r.chars is None:
            return f'Characterize the series first (characterize("{name}")).'
        X = raw.levels(r.data, r.chars, r.freq)
        d = [c["d"] for c in r.chars]
        txt, facts = evidence.canonical_report(X, r.names, d, r.freq, int(p), float(near),
                                               call=name, raw=True)
        r.guion.add("N1b", "canonical_analysis", {"p": facts["p"], "near": near},
                    f"raw levels; lam {', '.join(f'{v:.3f}' for v in facts['lam'])}; "
                    f"{facts['near_one']} near 1 of {facts['differenced']} differenced")
        return txt
    s = _sess.get(name)
    if s.gate is None:
        return "Run the gate first (run_gate)."
    from . import levels as _lv
    itv = (interventions or "remove").strip().lower()
    if itv not in ("remove", "keep"):
        return 'interventions must be "remove" or "keep".'

    def _matrix(mode):
        lev = [_lv.clean_levels(x, mode) for x in s.series]
        n = min(len(v) for v in lev)
        return np.column_stack([v[-n:] for v in lev])          # aligned at the end
    try:
        X = _matrix(itv)
    except ValueError as e:
        return f"Cannot remove the deterministic terms: {e}"
    d = [int(x.model.d or 0) for x in s.series]
    removed = [(nm, _lv.describe(x, itv)) for nm, x in zip(_names(s), s.series)]
    note = ("THE LEVELS READ (BUG-0018): each model's deterministic seasonality removed"
            + (", its interventions removed too" if itv == "remove" else
               ", its interventions KEPT (interventions=\"keep\")")
            + "; never mu nor a trend. "
            + "; ".join(f"{nm}: {r}" for nm, r in removed if r) + "."
            if any(r for _, r in removed) else
            "THE LEVELS READ: no deterministic terms in the models; the levels as they are.")
    txt, facts = evidence.canonical_report(X, _names(s), d, s.series[0].freq,
                                           int(p), float(near), call=name, route=s.route,
                                           removed_note=note)
    has_itv = any(t not in _lv.SEASONAL | _lv.KEPT_ALWAYS
                  for x in s.series for t, _ in _lv._groups(x))
    if has_itv:
        other = "keep" if itv == "remove" else "remove"
        try:
            _t, f2 = evidence.canonical_report(_matrix(other), _names(s), d,
                                               s.series[0].freq, int(p), float(near),
                                               call=name, route=s.route)
            cmp_ = ("With the interventions " + ("INSIDE" if other == "keep" else "REMOVED")
                    + f" (for comparison): sqrt(lam) "
                    + ", ".join(f"{np.sqrt(v):.3f}" for v in f2["lam"])
                    + f"; order by M(l) {f2.get('p_run', f2['p'])} (here "
                    + f"{facts.get('p_run', facts['p'])}). "
                    + 'canonical_analysis(name="' + name + '", interventions="' + other
                    + '") reads that one.')
            anchor = "## 4 · DECISION"
            txt = (txt.replace(anchor, cmp_ + "\n\n" + anchor, 1) if anchor in txt
                   else txt + "\n\n" + cmp_)
        except ValueError:
            pass
    facts["interventions"] = itv
    s.canonical = facts                 # for prepare_vec (p) and estimate_vec (beta)
    s.guion.add("N1b", "canonical_analysis", {"p": facts["p"], "near": near,
                                              "interventions": itv},
                f"lam {', '.join(f'{v:.3f}' for v in facts['lam'])}; "
                f"{facts['near_one']} near 1 of {facts['differenced']} differenced"
                + ("; stationary combinations possible (N1c)" if facts["question"] else ""))
    return txt


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
    txt, facts = evidence.cross_identification(L.result.residuals, _names(s), K, freq,
                                               [x.n_arma() for x in L.series], call=name)
    s.guion.add("N2", "identify_cross", {"nlags": K},
                f"short leads up to {facts['maxlag']}, longer {facts['longer']}, contemporaneous "
                f"{'yes' if facts['contemporaneous'] else 'no'}")
    return txt


@mcp.tool()
def identify_matrices(name: str, nlags: int = 0, qmax: int = 2) -> str:
    """N2 — Jenkins and Alavi's (1981) two identifications, as matrices.

    Method 2, prewhitened: the correlation matrices R_k of the residuals of the
    diagonal system (the univariate models' residuals), which suggest an MA
    residual model and its links. Method 1, not prewhitened: R_k, the partial
    correlation matrices S_k (multivariate Yule-Walker) and Alavi's
    q-conditioned S_k(q) of the stationary series of the same files, which
    suggest the AR (and ARMA) orders; determinants with three or more series.
    Then the comparison as a menu, with their warning when a cross AR shows:
    prewhitening can mis-specify it. `nlags` defaults to max(6, frequency);
    `qmax` the largest q-conditioning. Complements identify_cross (the
    pairwise CCFs).
    """
    s = _sess.get(name)
    try:
        L = _diagonal(s)
    except Exception as e:                                   # noqa: BLE001
        return f"Run the gate first ({e})."
    freq = s.series[0].freq
    K = int(nlags) or max(6, freq)
    _mu, _phi, _theta, _qq, W, _ifa = L.cast(L.result.x)
    txt, facts = evidence.ja_identification(W, L.result.residuals, _names(s), K,
                                            int(qmax), freq, route=s.route, call=name)
    s.guion.add("N2", "identify_matrices", {"nlags": K, "qmax": qmax},
                f"method 2: MA({facts['method2_q']}) residual model"
                + (f", links {', '.join(facts['links'])}" if facts["links"] else "")
                + f"; method 1: R_k cut {facts['method1_q']}, S_k cut {facts['method1_p']}")
    return txt


@mcp.tool()
def identify_echelon(name: str, max_index: int = 3, criterion: str = "SC") -> str:
    """N2 — the third form, the ECHELON VARMA of Lutkepohl and Poskitt (1996),
    and its Kronecker indices from the data.

    The indices n_i are the row degrees of the system's unique echelon form:
    series i gets its own AR(n_i)/MA(n_i), and their table says which cross
    terms are free, the contemporaneous ones included. Unlike the VARMA(p, q),
    the form is identified: no common factors, no MA driven to the wall by
    spare parameters. The univariate orders do NOT give the indices (every
    component's marginal is ARMA(N, N), N = the sum of the indices), so they
    are searched on the stationary vector: a long VAR (its residuals stand
    for the innovations), then least squares on each candidate's echelon form
    with one round of Hannan and Kavalieris' correction, and a criterion. SC
    (default) or HQ, which overfits. Every candidate with each index in
    0..`max_index` while there are at most 256, Hannan and Kavalieris' two
    steps beyond.

    The ORDER of the series is part of the echelon form (A_0 is lower
    triangular): the indices are those of the files' order. Measured on
    simulated systems (drvarma docs/STUDY-echelon-search.md): the true indices
    in 80-97 % of the replications, more with more data; weak cross dynamics
    are missed (the search underfits), which check_residuals then shows.

    On ROUTE U each univariate model's seasonal and fixed-frequency factors
    are its row's FACTOR (they multiply the whole row; drvarma's echelon
    stage 4) and the search runs on each row filtered by them; the
    univariate regular ARMA is replaced by the row's own AR(n_i)/MA(n_i).
    """
    from drvarma import echelon as E
    s = _sess.get(name)
    try:
        L = _diagonal(s)
    except Exception as e:                                   # noqa: BLE001
        return f"Run the gate first ({e})."
    if criterion not in E.CRITERIA:
        return f"criterion must be one of {', '.join(E.CRITERIA)}."
    _mu, _phi, _theta, _qq, W, _ifa = L.cast(L.result.x)
    factored = [nm for nm, x in zip(_names(s), L.series) if x.has_row_factor()]
    hist = []
    try:
        if factored:
            from drvarma.ladder import search_row_factors
            sr, hist = search_row_factors(s.files, n_max=int(max_index),
                                          criterion=criterion)
        else:
            sr = E.search(W, n_max=int(max_index), criterion=criterion)
    except Exception as e:                                   # noqa: BLE001
        return f"The search cannot run: {e}"
    names = _names(s)
    n = sr.indices
    ind = ", ".join(map(str, n))
    other = "HQ" if criterion == "SC" else "SC"
    alt = min(sr.fits, key=lambda k: sr.fits[k].criterion(other))
    # BUG-0005: every candidate is compared on one sample, which starts after
    # the long VAR's h lags plus max_index (and the row factors' degree), so
    # max_index moves the sample and can move the choice. Say on how many.
    T = next(iter(sr.fits.values())).T
    lost = W.shape[0] - T
    lines = ["# Echelon form — the Kronecker indices (Lutkepohl and Poskitt 1996)", "",
             "_[Claude: show the block below AS IT IS]_", "", "```", sr.text(names), "```", "",
             f"The table is computed on T = {T} of the {W.shape[0]} observations of the "
             f"stationary vector: every candidate on the same sample, which starts after "
             f"the long VAR's {sr.h} lag{'s' if sr.h != 1 else ''} plus max_index = "
             f"{int(max_index)}{' and the row factors' if lost > sr.h + int(max_index) else ''}. "
             "A different max_index changes that sample, and on a short series it can "
             "change the choice.", "",
             f"**Chosen by {criterion}: {', '.join(f'{a} {k}' for a, k in zip(names, n))}** "
             f"(McMillan degree {sum(n)}; {E.dim(n)} AR/MA coefficients).",
             f"{other} would choose ({', '.join(map(str, alt))}).", "",
             "The order of the series is part of the form: these are the indices in the "
             f"files' order ({', '.join(names)}).", ""]
    if s.route != "V":
        lines += ["ROUTE U: each row's own part is a free AR(n_i)/MA(n_i) in place of the "
                  "univariate model's regular ARMA (the univariate orders are not the "
                  "indices)."
                  + (f" The seasonal and fixed-frequency factors of {', '.join(factored)} "
                     "are their rows' FACTOR: they multiply the whole row, cross terms "
                     "included, and the search ran on each row filtered by them. "
                     "estimate checks the factor with an LR test." if factored else ""),
                  ""]
        if hist:
            lines += ["The search in passes: the univariate factors first, then those of "
                      "the exact-ML fit of each choice (a series' univariate model mixes "
                      "the other rows' factors):"]
            lines += [f"  pass {k + 1}: ({', '.join(map(str, nn))}), factors of the {src}"
                      for k, (nn, src) in enumerate(hist)]
            lines += [""]
    from . import envelope as E
    nq = f'name="{name}"'
    concl = [f"The search chooses the Kronecker indices ({ind}) by {criterion}."
             + (f" {other} chooses ({', '.join(map(str, alt))})." if alt != n else
                f" {other} agrees."),
             "The echelon form is identified where a VARMA(p, q) with spare orders is "
             "not: both are fitted on the same specifications, so they can be compared."]
    opts = [("fit it: exact ML from the least-squares estimates of the search; then "
             "check_residuals and evaluate", f'estimate({nq}, indices="{ind}")')]
    if alt != n:
        why = ("if the residuals of (A) show what it leaves out" if sum(alt) > sum(n)
               else "if (A)'s extra terms do not pay for themselves (LR, evaluate)")
        opts.append((f"{other}'s choice, {why}",
                     f'estimate({nq}, indices="{", ".join(map(str, alt))}")'))
    opts.append(("compare with the VARMA(p, q) of the matrices", f"identify_matrices({nq})"))
    shows = ["The Kronecker index of a series is the order of its own row; the echelon "
             "form fixes the rest of the zeros (Lutkepohl and Poskitt 1996). The order of "
             "the series is part of the model: A_0 is lower triangular in that order."]
    s.guion.add("N2", "identify_echelon", {"max_index": int(max_index),
                                           "criterion": criterion},
                f"indices ({ind}) by {criterion}, long VAR({sr.h}); {other} "
                f"({', '.join(map(str, alt))})")
    if lines and lines[0].startswith("# "):            # the envelope gives the title
        lines = lines[1:]
    return E.envelope("# N2 · The echelon form — Kronecker indices (Lutkepohl and "
                      "Poskitt 1996)", lines, shows, concl, opts)


# --------------------------------------------------------------------------- #
#  N3 / N4                                                                     #
# --------------------------------------------------------------------------- #

@mcp.tool()
def estimate(name: str, p: int = 0, q: int = 0, diagcov: bool = False,
             reason: str = "", links: str = "", start: str = "",
             cross: str = "additive", zeros: str = "", indices: str = "") -> str:
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

    `start`: where the cross terms start — "ols", the original drvarma's
    init_varma in the ladder: least squares of the VAR(p) seeds the cross AR
    terms and Q's covariances, the own models staying the univariate ones on
    both routes (the ladder's principle) — the DEFAULT
    when the installed drvarma has it (> 0.3.4); "zero"; or "preliminary",
    Jenkins and Alavi's preliminary estimates (the cross MA from the
    univariate residuals' cross covariances, the cross AR from Yule-Walker).
    From zero, exact ML can stop after two iterations below the nested model
    when the series' scales differ (drvarma BUG-0027, the US monetary VAR);
    from ols or preliminary it does not. Usually the same optimum in fewer iterations; on an
    ill-defined estimation (the MA wall) a second path worth comparing. Asked
    for a fit already made, another start optimises again and the higher
    logL is kept, the report giving both (BUG-0019); the same start reuses it,
    and the report says so. A fit below a model it nests, or one that stalled
    within a few iterations, is retried once from "ols" (or "preliminary"
    with an older drvarma), and the report says so. The
    echelon form starts at Lutkepohl and Poskitt's least-squares estimates
    ("echelon", its default).

    `cross`: how the cross MA enters — "additive" (default: a cross polynomial
    beside the univariate operators) or "residual", Jenkins and Alavi's form
    (3.22): a model for the univariate residuals, multiplied by each series'
    univariate MA. The same when the univariate models have no MA factors;
    when they have (an airline), the two are different candidates — on m6 the
    residual form converged inside where the additive one stopped on the MA
    wall. identify_matrices' method 2 proposes it.

    `zeros`: coefficients held at zero, by their printed names — Tiao and
    Box's simplification (simplify proposes them): cross ones "AR3[A<-B],
    MA1[B<-A]" on either route; a series' own "phi_A[B^4], theta_A[B^1]" on
    route V, and on route U in the echelon form (with `indices`), whose own
    AR(n_i)/MA(n_i) is sima's; otherwise route U's diagonal is the univariate
    model, art's. A fit already made with the same arguments is reused, not
    refitted.

    `indices`: the ECHELON FORM with these Kronecker indices, one per series
    in the files' order, e.g. "1, 2, 1" (identify_echelon proposes them).
    Series i gets a free AR(n_i)/MA(n_i) of its own, the cross terms follow
    Lutkepohl and Poskitt's (1996) table, and the contemporaneous AR0[i<-j]
    terms make A_0 lower triangular: the order of the series is part of the
    model. p and q are then max(n_i); leave them at 0. `links` and `zeros`
    restrict it further. On route U the free AR(n_i)/MA(n_i) replaces the
    univariate model's regular ARMA, and its seasonal and fixed-frequency
    factors multiply the whole row (the row FACTOR), checked by an LR test
    against the same rows with the factor's restriction dropped.
    """
    s = _sess.get(name)
    if s.gate is None:
        return "Run the gate first (run_gate)."
    lk = _links(links)
    zs = _zeros(zeros)
    try:
        ech = _indices(indices)
    except ValueError as e:
        return str(e)
    if ech:
        if cross == "residual":
            return ('cross="residual" (Jenkins and Alavi\'s 3.22) is not an echelon '
                    "form: leave cross at its default.")
        if len(ech) != len(s.series):
            return f"indices: give {len(s.series)}, one per series ({', '.join(_names(s))})."
        if (int(p), int(q)) not in ((0, 0), (max(ech), max(ech))):
            return f"With indices, p and q are max(n_i) = {max(ech)}: leave them at 0."
    key = _key(p, q, diagcov, lk, cross, zs, ech)
    try:
        if s.route == "V" and cross == "residual":
            return ('cross="residual" is Jenkins and Alavi\'s model for UNIVARIATE '
                    "residuals; route V has none. Use the default.")
        L, path_note = _fit_paths(s, key, start)
    except Exception as e:
        s.guion.add("N3", "estimate", {"p": p, "q": q, "diagcov": diagcov, "links": lk,
                                       "cross": cross, "indices": ", ".join(map(str, ech))},
                    f"failed: {e}", reason)
        return f"Estimation failed: {e}"
    s.fits[key] = L
    s.current = key
    s.kind = "VARMA"
    freq = s.series[0].freq
    txt = evidence.estimation_text(L, max(8, 2 * freq))
    if path_note:
        txt = path_note + "\n\n" + txt
    if ech:
        factored = [x.name for x in L.series if x.has_row_factor()]
        txt = (f"ROUTE {s.route} — the ECHELON FORM with Kronecker indices "
               f"({', '.join(f'{nm} {k}' for nm, k in zip(_names(s), ech))}), Lutkepohl "
               "and Poskitt (1996): each series' own AR(n_i)/MA(n_i) with the cross "
               "terms of their table, A_0 lower triangular (the AR0 terms; the order of "
               "the series is part of the model)."
               + (" On route U the own AR(n_i)/MA(n_i) replaces each univariate model's "
                  "regular ARMA." if s.route != "V" else "")
               + (f" The seasonal and fixed-frequency factors of {', '.join(factored)} "
                  "multiply their whole rows (the row FACTOR)." if factored else "")
               + f" Started at their least-squares estimates ({L.start_used}). The LR "
               "below is against the same model without cross terms; the univariates "
               "come at N5.\n\n" + txt)
        if factored:
            txt += "\n\n" + _factor_check(s, L)
    elif s.route == "V":
        txt = (f"ROUTE V — the full VARMA({p},{q}) of Tiao and Box: each series' own "
               f"AR({p})/MA({q}) estimated jointly with the cross terms. The LR below is "
               f"against the same model without cross terms (one AR({p})/MA({q}) per "
               "series), not against univariate models; those come at N5.\n\n" + txt)
    lr = "" if (p == 0 and q == 0 and diagcov) else " LR %.2f df %d p %.4f" % L.lr_test()
    s.guion.add("N3", "estimate", {"p": p, "q": q, "diagcov": diagcov, "links": lk,
                                   "start": L.start_used, "cross": cross,
                                   "zeros": ", ".join(zs),
                                   "indices": ", ".join(map(str, ech))},
                f"logL {L.result.logL:.4f}, {L.result.npar} parameters;{lr}", reason,
                kind="VARMA")
    return _estimate_envelope(name, s, L, txt, p, q, diagcov, lk, cross, zs, ech)


def _estimate_envelope(name, s, L, txt, p, q, diagcov, lk, cross, zs, ech):
    """N3's envelope (sima.envelope). Before, estimate ended with «Next:
    evaluate» and the guided lane skipped N4 — the residuals of the estimated
    model, each series' and each pair's — and N4s/N4t: whoever did not know the
    tool went from the estimate to the yardstick without ever seeing them."""
    from . import envelope as E
    freq = s.series[0].freq
    f = evidence.estimation_facts(L, max(8, 2 * freq))
    q_ = f'name="{name}"'
    spec = (f"p={p}, q={q}" + (", diagcov=True" if diagcov else "")
            + (f', links="{lk}"' if lk else "")
            + (f', cross="{cross}"' if cross != "additive" else "")
            + (f', zeros="{", ".join(zs)}"' if zs else "")
            + (f', indices="{", ".join(map(str, ech))}"' if ech else ""))
    shows = ["A coefficient marked * has |t| > 1.96. The LR is against the same model "
             "without cross terms, in sample: necessary, not sufficient — the cross terms "
             "have to pay for themselves out of sample (N5).",
             "The optimiser's stop says whether the point is a demonstrated maximum; the "
             "residuals' Hosking Q is a first look at what the model leaves: check_residuals "
             "reads them series by series and pair by pair, with their figures."]
    if f["not_started"]:
        # BUG-0011: no LR, no reading of a table that is the seeds
        return E.envelope(
            f"# N3 · NOT estimated — {_desc(s.current)}", txt,
            ["The search ended at its first step on the diagonal start: no cross term "
             "moved from its seed."],
            ["Nothing is concluded about cross dynamics: there is no estimate to read."],
            [("bring the files into the optimiser's band (art writes the factor that does "
              "it; a series in levels may need other units or a difference)",
              "art (outside sima)"),
             ("start the search elsewhere", f'estimate({q_}, {spec}, start="preliminary")'),
             ("other orders: back to the identification", f"identify_matrices({q_})")])
    concl = []
    if f["wall"]:
        concl.append("The fit stopped on the MA invertibility wall: not an optimum. Its "
                     "numbers are not to be read before studying it.")
    elif f["fold"]:
        # BUG-0008: the fold of the cast is a wall of one coefficient
        concl.append(f"The fit stopped at the fold of an own MA(1) ({', '.join(f['fold'])}): "
                     "not an optimum. Its numbers are not to be read before studying it.")
    elif not f["converged"]:
        concl.append(f"Optimiser: {f['stop']}. The point is not certified by the "
                     "gradient.")
    if f["lr_p"] is not None:
        concl.append(f"The cross terms are {'significant' if f['lr_p'] < 0.05 else 'NOT significant'}"
                     f" in sample against the diagonal system (LR = {f['lr']:.2f}, df = "
                     f"{f['lr_df']}, p = {f['lr_p']:.4f})"
                     + ("." if f["lr_p"] < 0.05 else ": the data do not ask for them here."))
    if f["n_cross"]:
        concl.append(f"{len(f['weak_cross'])} of {f['n_cross']} cross coefficients have "
                     "|t| <= 1.96" + (f" ({', '.join(f['weak_cross'][:6])}"
                                      + (", …" if len(f["weak_cross"]) > 6 else "") + ")"
                                      if f["weak_cross"] else "") + ".")
    if f["hosking_p"] is not None:
        concl.append("The residuals' Hosking Q "
                     + ("does not reject white noise" if f["hosking_p"] > 0.05 else
                        "REJECTS white noise: the model leaves dynamics")
                     + f" (p = {f['hosking_p']:.4f}).")
    opts = []
    if f["wall"] or f["fold"]:
        opts.append(("study the fit first: restarts from other points, and the MA "
                     "wall or the fold", f"study_estimation({q_})"))
    opts.append(("N4 — the residuals of this model: each series' diagnosis and the CCF "
                 "of each pair, with their figures", f"check_residuals({q_})"))
    if f["weak_cross"]:
        opts.append((f"N4s — simplify: drop the cross coefficients with small t "
                     f"({len(f['weak_cross'])} here)", f"simplify({q_})"))
    if f["n_cross"]:
        opts.append(("N4t — the structure: which series feed which, by LR, pair by pair",
                     f"structure({q_})"))
    opts.append(("N5 — the yardstick: does it forecast better than the univariates?",
                 f"evaluate({q_}, {spec}, estwin=...)"))
    return E.envelope(f"# N3 · Estimated — {_desc(s.current)}", txt, shows, concl, opts)


def _desc(key):
    p, q, dc, lk, cr, zs, ech = key
    head = (f"echelon form, indices {', '.join(map(str, ech))}" if ech
            else f"p = {p}, q = {q}")
    return (f"{head}, {'diagonal' if dc else 'full'} covariance"
            + (f", links {lk}" if lk else "") + (", residual form" if cr == "residual" else "")
            + (f", {len(zs)} coefficients at zero" if zs else ""))


def _fit_key(s, key):
    """The fit of a key, from the cache or fitted now (and cached)."""
    if key not in s.fits:
        L = _model_ladder(s, key)
        L.fit()
        s.fits[key] = L
    return s.fits[key]


def _lr(full, restr):
    from scipy.stats import chi2
    lr = max(0.0, 2.0 * (full.result.logL - restr.result.logL))
    df = int(full.result.npar - restr.result.npar)
    return {"lr": lr, "df": df, "p": float(chi2.sf(lr, df)) if df > 0 else 1.0}


def _estimate_call(name, key):
    p, q, dc, lk, cr, zs, ech = key
    head = (f'indices="{", ".join(map(str, ech))}"' if ech else f"p={p}, q={q}")
    return (f'estimate(name="{name}", {head}'
            + (", diagcov=True" if dc else "") + (f', links="{lk}"' if lk else "")
            + (', cross="residual"' if cr == "residual" else "")
            + (f', zeros="{", ".join(zs)}"' if zs else "") + ")")


@mcp.tool()
def simplify(name: str, t: float = 1.0) -> str:
    """N4s — Tiao and Box's (1981, §4) simplification by coefficient, on the
    current fit: the cross coefficients (and, on route V or in the echelon
    form, each series' own AR/MA coefficients) with |t| < `t` are held at
    zero, the model is refitted, and the restriction is tested by LR against
    the full fit, with AIC and BIC. The restricted fit is cached: adopting it
    (the estimate call in the menu) is instant. Route U's univariate models
    are never touched — they are art's; the echelon form's own part, which
    replaces their regular ARMA, is sima's, and is simplified like the rest. Several rounds are normal (Tiao and Box simplified
    the SCC model twice)."""
    import numpy as np
    s = _sess.get(name)
    try:
        L = _current(s)
    except KeyError as e:
        return str(e) if s.current_kind() == "VEC" else "Estimate a model first (estimate)."
    key = s.current
    r = L.result
    x, se = np.asarray(r.x, float), np.asarray(r.std_errors, float)
    cross_re = re.compile(r"(AR|MA)\d+\[.+<-.+\]")
    drop = []
    for nm, v, e in zip(r.names, x, se):
        ok = cross_re.fullmatch(nm) or (_own_is_free(s, key) and _OWN.fullmatch(nm))
        if ok and np.isfinite(e) and e > 0 and abs(v / e) < float(t):
            drop.append((nm, float(v), float(v / e)))
    f = {"t": float(t), "desc": _desc(key), "route": s.route, "drop": drop}
    if drop:
        key2 = key[:5] + (_zeros(list(key[5]) + [d[0] for d in drop]),) + key[6:]
        try:
            L2 = _fit_key(s, key2)
        except Exception as e:                               # noqa: BLE001
            return f"The restricted fit failed: {e}"
        n = np.asarray(r.residuals).shape[0]
        k1, k2 = r.npar, L2.result.npar
        f.update(_lr(L, L2), k_full=k1, k_r=k2, ll_full=r.logL, ll_r=L2.result.logL,
                 aic_full=-2 * r.logL + 2 * k1, aic_r=-2 * L2.result.logL + 2 * k2,
                 bic_full=-2 * r.logL + k1 * np.log(n), bic_r=-2 * L2.result.logL + k2 * np.log(n))
        x2, se2 = np.asarray(L2.result.x, float), np.asarray(L2.result.std_errors, float)
        f["left"] = [(nm, float(v / e)) for nm, v, e in zip(L2.result.names, x2, se2)
                     if (cross_re.fullmatch(nm) or (_own_is_free(s, key) and _OWN.fullmatch(nm)))
                     and np.isfinite(e) and e > 0 and abs(v / e) < float(t)]
        s.guion.add("N4s", "simplify", {"t": t, "model": _desc(key)},
                    f"{len(drop)} coefficients |t| < {t:g} to zero: "
                    f"LR {f['lr']:.2f} df {f['df']} p {f['p']:.4f}")
        return evidence.simplify_report(f, name, _estimate_call(name, key2))
    return evidence.simplify_report(f, name, "")


@mcp.tool()
def structure(name: str, alpha: float = 0.05) -> str:
    """N4t — Is the system simultaneous? (Tiao and Box 1981, §3.1, §5.2.) On
    the current fit: for each ordered pair, the LR test that series j does not
    enter series i's equation (all its cross AR and MA lags at zero); with up
    to 4 series, every triangular ordering (each series receives only from
    those before it). If an ordering stands, the system is a TRANSFER
    NETWORK — a triangular VARMA is a transfer function model — and sima
    offers the hand-back to mtram with the same .pre files; it does not hand
    back on its own. The verdict is only as good as the order of the fit:
    Tiao and Box's gas furnace shows a spurious feedback at low order."""
    import itertools
    s = _sess.get(name)
    try:
        L = _current(s)
    except KeyError as e:
        return str(e) if s.current_kind() == "VEC" else "Estimate a model first (estimate)."
    key = s.current
    p, q, dc, lk, cr, zs, ech = key
    if p == 0 and q == 0:
        return "The current fit has no cross dynamics (p = q = 0): nothing to test."
    names = _names(s)
    m = len(names)
    free = set(L.result.names)

    def pair_zeros(i, j):
        # AR0 is the echelon form's contemporaneous term (absent otherwise)
        return [f"{k}{l}[{names[i]}<-{names[j]}]" for k, lo, top in (("AR", 0, p), ("MA", 1, q))
                for l in range(lo, top + 1) if f"{k}{l}[{names[i]}<-{names[j]}]" in free]

    tests = {}

    def test(extra, label):
        if not extra:
            return {"label": label, "lr": 0.0, "df": 0, "p": 1.0}
        k2 = key[:5] + (_zeros(list(zs) + extra),) + key[6:]
        if k2 not in tests:
            tests[k2] = _lr(L, _fit_key(s, k2))
        return dict(tests[k2], label=label, key=k2)

    try:
        pairs = [test(pair_zeros(i, j), f"{names[j]} -> {names[i]}")
                 for i in range(m) for j in range(m) if i != j]
        orders = None
        if m <= 4:
            orders, seen = [], set()
            for perm in itertools.permutations(range(m)):
                pos = {v: k for k, v in enumerate(perm)}
                extra = sorted(z for i in range(m) for j in range(m)
                               if i != j and pos[j] > pos[i] for z in pair_zeros(i, j))
                tag = tuple(extra)
                if tag in seen:
                    continue
                seen.add(tag)
                t = test(extra, " -> ".join(names[v] for v in perm))
                t["arrows"] = ", ".join(f"{names[a]} -> {names[b]}"
                                        for a, b in zip(perm, perm[1:]))
                t["call"] = _estimate_call(name, t.get("key", key))
                orders.append(t)
    except Exception as e:                                   # noqa: BLE001
        return f"A restricted fit failed: {e}"
    pre = _yardstick_files(s) if s.route == "V" else s.files
    f = {"desc": _desc(key), "alpha": float(alpha), "pairs": pairs, "orders": orders,
         "pre": pre}
    stand = [t["label"] for t in (orders or []) if t["df"] == 0 or t["p"] >= alpha]
    s.guion.add("N4t", "structure", {"model": _desc(key), "alpha": alpha},
                ("orderings standing: " + "; ".join(stand)) if stand else
                "no triangular ordering stands: feedback")
    return evidence.structure_report(f, name)


@mcp.tool()
def check_residuals(name: str, nlags: int = 0) -> list:
    """N4 — Check the last estimated model as Jenkins and Alavi (1981, §5.2) do,
    and show it as art's diagnosis: the report, then the figures.

    The report: 1 · TABLE — (1) the large residuals, judged on the
    UNCORRELATED transformed residuals (the a_it correlate at lag 0, so one by
    one they cannot be judged), with their dates — a known cause goes to
    intervention analysis, in art, before anything else is read; (2) the
    residual correlation matrices R_k(a), with what is beyond the band; (3)
    the portmanteau matrix Q_ij, as a summary. 2 · WHAT IT SHOWS,
    3 · CONCLUSIONS, 4 · DECISION. If the matrices show structure, a model for
    the residuals is entertained and combined with the fitted one, as at
    identification.

    The figures, as drvus drew the diagnosis and their figure 7: fue's panel
    for each residual series (the residuals with +-2 bands, the acf with its
    Q, the pacf), and the residual ccf of each pair (GraphMaker's, with
    Hosking's P). `nlags` (the matrices) defaults to max(6, frequency). The
    portmanteaus keep at least 2 lags beyond the parameters: the legacy lags
    move up when a long model in annual data would leave none.
    """
    from . import figures
    s = _sess.get(name)
    try:
        L = _current(s)
    except KeyError as e:
        return [str(e)]
    r = L.result
    freq = s.series[0].freq
    K = int(nlags) or max(6, freq)
    s0 = L.series[L._act[0]]
    n = r.residuals.shape[0]
    names = _names(s)
    txt, facts = evidence.ja_checking(r.residuals, r.sigma, names, K, freq,
                                      lambda t: s0.date_of(s0.nobs - n + t + 1))
    s.guion.add("N4", "check_residuals", {"nlags": K, "model": str(s.current)},
                f"{facts['n_beyond']} residual correlations beyond the band; "
                f"{facts['large']} large transformed residuals")
    p_, q_, dc_, lk_, cr_, zs_, ech_ = s.current
    head_ = (f"echelon form, indices {', '.join(map(str, ech_))}" if ech_
             else f"cross p = {p_}, q = {q_}")
    desc = (f"{head_}, {'diagonal' if dc_ else 'full'} covariance"
            + (f", links {lk_}" if lk_ else "") + (f", cross MA {cr_}" if q_ else "")
            + (f", {len(zs_)} coefficients at zero" if zs_ else ""))
    lines = ["# Checking — Jenkins and Alavi (1981, §5.2)",
             f"*({desc}; n = {n})*", "",
             "## 1 · TABLE", "",
             "_[Claude: show the block below AS IT IS; do not build your own table]_", "",
             "```", txt, "```", "",
             "## 2 · WHAT IT SHOWS", ""]
    lines.append(f"- Residual correlations beyond the band: {facts['n_beyond']} "
                 f"(about {facts['expected']:.1f} expected by chance)"
                 + (": " + ", ".join(f"({names[i]}, {names[j]}) at {k}"
                                     for k, i, j in facts["beyond"]) if facts["beyond"] else "")
                 + ".")
    lines.append("- Portmanteau matrix: " + (
        "significant for " + ", ".join(f"({a}, {b})" for a, b in facts["significant_Q"])
        if facts["significant_Q"] else "nothing significant") + ".")
    nd = len(facts["large_dates"])
    lines.append(f"- Large transformed residuals (beyond 2): {nd} date(s)"
                 + (f" — {', '.join(facts['large_dates'])}; the largest {facts['worst']}, "
                    f"{facts['worst_z']:.1f} s.d" if nd else "") + ".")
    lines += ["", "## 3 · CONCLUSIONS", ""]
    structure = facts["n_beyond"] > facts["expected"] + 1 or facts["significant_Q"]
    lines.append("The residual matrices show structure the model does not carry: a "
                 "model for the residuals is entertained (as at identification)."
                 if structure else
                 "The residual matrices show no structure beyond chance: the model "
                 "carries the dynamics.")
    if facts["worst_z"] > 3.0:
        lines.append(f"A large residual stands out ({facts['worst']}, "
                     f"{facts['worst_z']:.1f} s.d.): with a known cause it is treated by "
                     "intervention in art, on the series' own model, before reading "
                     "anything else; without one it stays as an open caveat.")
    lines += ["", "## 4 · DECISION — alternatives", ""]
    opts = [("the yardstick (N5): does it forecast better than the univariates?",
             f'evaluate(name="{name}", p={p_}, q={q_}, estwin=...'
             + (f', links="{lk_}"' if lk_ else "") + (f', cross="{cr_}"' if q_ else "") + ")")]
    if facts["worst_z"] > 3.0:
        opts.append((f"intervene {facts['worst']} in art, rebuild the .pre and "
                     "climb the ladder again", "art: suggest_intervention_form(...)"))
    if structure:
        opts.append(("a model for the residuals: identify it as at N2",
                     f'plot_identification(name="{name}", method=2)'))
    opts.append(("Jenkins and Alavi's V(l) against the univariates (in sample)",
                 f'forecast_uncertainty(name="{name}")'))
    for t, (what, call) in enumerate(opts):
        lines.append(f"**{'ABCDEF'[t]})** {what}\n   `{call}`")
    lines += ["", _env.STOP]
    # the figures, as drvus' diagnosis: a panel per series, a ccf per pair
    items = [(fig, f"resid_{nm}") for nm, fig in figures.residual_panels(L)]
    from pyfug.graphics.ccf import ccf_default_lags
    npq = figures.residual_npq(L)
    K0 = min(ccf_default_lags(freq), n // 4)
    Kc = figures.q_lags(K0, npq, n)
    items.append((figures.residual_ccf_figure(L, Kc, freq), "ccf"))
    lines.append(f"\nThe residual ccf's P is GraphMaker's: Hosking's portmanteau over {Kc} lags "
                 f"with 4(K - (p + q)) = {4 * (Kc - npq)} degrees of freedom, p + q = {npq} "
                 "(the largest AR plus the largest MA order of the fitted model)"
                 + (f"; K moved up from GraphMaker's {K0} to leave at least "
                    f"{figures.MIN_DF_LAGS} lags beyond p + q." if Kc > K0 else ".")
                 + " The acf's Q of each series keeps the same minimum.")
    if not items[:-1]:
        lines.append("\n(pyfug is not installed: the per-series panels are missing.)")
    return _figures(s, items, "\n".join(lines))


@mcp.tool()
def lag_order(name: str, pmax: int = 3) -> str:
    """N3 — THE ORDER OF THE VAR, by likelihood ratio: VAR(0) -> VAR(1) -> ...
    -> VAR(pmax), each estimated by exact maximum likelihood on the same files
    and tested against the one before it (LR, chi-squared with the
    parameters the step adds). Tiao and Box's (1981) sequential reading — the
    order beyond which no step is significant — on the fitted models, with
    their least-squares M(l) beside it (identify_matrices has the whole
    table), and AIC and BIC as information.

    VAR(0) is the univariate models with a full innovation covariance (the
    contemporaneous link only). Every fit goes through the paths of estimate
    (BUG-0019): a fit that lies below the one it nests, or that stalled, is
    retried from the ols (or preliminary) start, and the table says which. Only LR:
    a Wald test rests on the Hessian, which a fit on a ridge does not give.
    The fits are cached: estimate(p=k) afterwards reuses the chosen one."""
    import numpy as np
    from scipy.stats import chi2
    from drvarma.identification_mv import stepwise_ar
    s = _sess.get(name)
    if s.gate is None:
        return "Run the gate first (run_gate)."
    pmax = int(pmax)
    if pmax < 1 or pmax > 12:
        return "pmax: from 1 to 12."
    rows, notes = [], []
    for p in range(0, pmax + 1):
        key = _key(p, 0)
        try:
            L, note = _fit_paths(s, key, "")
        except Exception as e:                               # noqa: BLE001
            return f"VAR({p}) could not be estimated: {e}"
        s.fits[key] = L
        r = L.result
        rows.append({"p": p, "logL": float(r.logL), "k": int(r.npar), "nit": int(r.nit),
                     "tc": int(r.termcode), "start": _start_of(L), "n": int(r.w.shape[0])})
        if note and "reused" not in note:
            notes.append(f"VAR({p}): " + note)
    for a, b in zip(rows, rows[1:]):
        lr = 2.0 * (b["logL"] - a["logL"])
        df = b["k"] - a["k"]
        b.update(lr=lr, df=df, pv=float(chi2.sf(max(lr, 0.0), df)) if df > 0 else float("nan"))
    for r in rows:
        r["aic"] = -2 * r["logL"] + 2 * r["k"]
        r["bic"] = -2 * r["logL"] + r["k"] * np.log(r["n"])
    # Tiao and Box's M(l), least squares on the stationary series
    try:
        D = _diagonal(s)
        W = D.cast(D.result.x)[4]
        sw = stepwise_ar(np.asarray(W, float), pmax)
        tb = [(float(m), float(pv)) for m, pv in zip(sw["M"], sw["pvalue"])]
        tb_df = sw["df"]
    except Exception:                                        # noqa: BLE001
        tb, tb_df = [], None
    m = len(s.series)
    table = [f"THE ORDER OF THE VAR — exact ML, the univariate models on the diagonal "
             f"(route {s.route}); each step against the one before it", "```",
             "   p      logL    k   it tc start          LR   df  p-value       AIC       BIC"
             + ("   M(l)  p-value" if tb else "")]
    for r in rows:
        line = (f"  {r['p']:2d} {r['logL']:9.2f} {r['k']:4d} {r['nit']:4d} {r['tc']:2d} "
                f"{r['start']:<11s}")
        if "lr" in r:
            line += f" {r['lr']:8.2f} {r['df']:4d} {r['pv']:8.4f}"
        else:
            line += " " * 23
        line += f" {r['aic']:9.2f} {r['bic']:9.2f}"
        if tb and r["p"] >= 1:
            mm, pv = tb[r["p"] - 1]
            line += f" {mm:7.2f} {pv:8.4f}"
        table.append(line)
    table.append("```")
    if tb:
        table.append(f"M(l): Tiao and Box's statistic (4.3), least squares on the stationary "
                     f"series, the WHOLE matrix Phi_l ({tb_df} d.f.); the LR tests the cross "
                     f"terms the step adds to the univariate models ({m}({m}-1) per lag in "
                     "route U).")
    table += notes
    sig = [r["p"] for r in rows[1:] if r["pv"] < 0.05]
    p_lr = max(sig) if sig else 0
    gaps = [p for p in range(1, p_lr) if p not in sig]
    p_aic = min(rows, key=lambda r: r["aic"])["p"]
    p_bic = min(rows, key=lambda r: r["bic"])["p"]
    shows = ["Each LR asks whether the lag the step adds carries cross dynamics the "
             "previous order does not: significant, the lag is needed; not, the shorter "
             "model holds. Tiao and Box read the column from the top and stop where no "
             "further step is significant; an isolated significant step after a silence "
             "is named, not taken blindly. AIC and BIC are information: BIC penalises "
             "parameters by ln n, AIC by 2."]
    concl = [f"By LR, the last significant step is VAR({p_lr})"
             + (f" (not significant on the way: {', '.join(map(str, gaps))})" if gaps else "")
             + f". AIC is lowest at VAR({p_aic}), BIC at VAR({p_bic})."]
    if p_lr == pmax:
        concl.append(f"The last step tested is significant: VAR({pmax + 1}) may be needed "
                     f'(lag_order(name="{name}", pmax={pmax + 1})).')
    if notes:
        concl.append("Some fits needed a second path (above): their logL is the better one "
                     "found, and the table uses it.")
    q = f'name="{name}"'
    cand = []
    for p in (p_lr, p_bic, p_aic):
        if p >= 1 and p not in cand:
            cand.append(p)
    opts = [(f"VAR({p})" + (" — the LR's order" if p == p_lr else "")
             + (" — BIC's" if p == p_bic else "") + (" — AIC's" if p == p_aic else ""),
             f"estimate({q}, p={p}, q=0)") for p in cand]
    if p_lr == 0:
        opts.append(("no lag carries cross dynamics: the contemporaneous link only, or the "
                     "univariates", f"estimate({q}, p=0, q=0)"))
    opts.append(("the identification by matrices first (Tiao and Box's whole M(l) table, "
                 "Jenkins and Alavi's methods)", f"identify_matrices({q})"))
    s.guion.add("N3", "lag_order", {"pmax": pmax},
                "; ".join(f"p{r['p']} logL {r['logL']:.2f}"
                          + (f" LR p {r['pv']:.4f}" if "pv" in r else "") for r in rows)
                + f"; LR order {p_lr}, AIC {p_aic}, BIC {p_bic}")
    return _env.envelope(f"# N3 · The order of the VAR, by LR — VAR(0) to VAR({pmax})",
                         table, shows, concl, opts)


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
    if s.current_kind() == "VEC":
        return ("The current model is a VEC: study_estimation reads a VARMA. For a VEC that "
                "stopped on a ridge, estimate_vec declares it and offers multistart.")
    if s.current is None or s.current not in s.fits:
        return "Estimate a model first (estimate)."
    p, q, diagcov, lk, cross, zs, ech = s.current
    L = s.fits[s.current]
    r = L.result
    freq = s.series[0].freq
    out = [f"STUDY of the fit "
           + (f"echelon {', '.join(map(str, ech))}, " if ech else f"p = {p}, q = {q}, ")
           + f"{'diagonal' if diagcov else 'full'} covariance" + (f", links {lk}" if lk else ""),
           f"  as estimated: logL {r.logL:.6f}, {r.nit} iterations, "
           + (f"STOPPED ON THE MA WALL ({r.ma_boundary} of {r.ma_nroots} roots)"
              if getattr(r, "ma_boundary", 0) else "not on the MA wall"), "",
           evidence.roots_text(r, freq), ""]
    fold = evidence.folded_own_ma(L.series, r)
    if fold:
        out[2:2] = ["  " + evidence.fold_text(fold), "  The joint roots below need not "
                    "show it: the free cross MA keep them inside."]
    # 2. the second path
    try:
        Ls = _model_ladder(s, s.current, lik="shea")
        rs = Ls.fit()
        out += ["SECOND PATH (Shea's likelihood, AS 242):",
                f"  logL {rs.logL:.6f}  ({rs.nit} iterations; "
                + (f"on the MA wall, {rs.ma_boundary} of {rs.ma_nroots} roots"
                   if rs.ma_boundary else "not on the MA wall")
                + ("; at the fold" if evidence.folded_own_ma(Ls.series, rs) else "") + ")"
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
                           if rk.ma_boundary else
                           "at the fold" if evidence.folded_own_ma(Lr.series, rk)
                           else "inside"))
            if not rk.logL > best + 1e-6:
                break
            x, best = rk.x.copy(), rk.logL
        out += [f"RESTARTS (retreat {retreat} towards the start, re-optimise):"] + rows
        out += [f"  highest reached: logL {best:.6f}  ({best - r.logL:+.6f} over the fit)", ""]
    i_menu = len(out)                    # the reading starts here (the envelope)
    out += ["MENU (the analyst decides):",
            "  a) Remove the near-common factor, or lower p or q, and re-estimate:",
            "     a model whose likelihood has an interior maximum.",
            "  b) Keep the model knowing it sits on the invertibility boundary: its",
            "     values are one point of a ridge, and they depend on the path.",
            "  c) If the restarts or the second path climbed, the fit as estimated",
            "     is not the top of the ridge; report the highest point as such,",
            "     stating that it is on the wall."]
    if fold:
        names_f = [n for n, _ in fold]
        ours = _own_is_free(s, s.current) and all(_OWN.fullmatch(n) for n in names_f)
        out += [f"  f) THE FOLD: {', '.join(names_f)} stopped on the invertibility",
                "     boundary of an own MA(1), where the cast folds (theta -> 1/theta).",
                "     Treat it as the wall: no optimum to report."]
        if ours:
            out += ["     Hold them at zero and re-estimate (with every own and cross MA",
                    "     dropped, the echelon form is a VAR):",
                    "     " + _estimate_call(name, (p, q, diagcov, lk, cross,
                                                     _zeros(list(zs) + names_f), ech)),
                    "     For: a model whose likelihood has an interior maximum. Against:",
                    "     an own MA(1) at -1 is the signature of over-differencing, whose",
                    "     cause is the series' d: the univariate decision (art)."]
        else:
            out += ["     The coefficient belongs to the univariate model: revise it in",
                    "     art (an MA(1) at -1 is the signature of over-differencing)."]
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
                f"fit logL {r.logL:.4f}; boundary {getattr(r, 'ma_boundary', 0)}"
                + (f"; at the fold: {', '.join(n for n, _ in fold)}" if fold else ""),
                "")
    from . import envelope as E
    nq = f'name="{name}"'
    extra = ((", diagcov=True" if diagcov else "") + (f', links="{lk}"' if lk else "")
             + (f', cross="{cross}"' if cross != "additive" else ""))
    opts = []
    if not ech:
        if p:
            opts.append((f"a lower AR order (p = {p - 1}): a model whose likelihood may have "
                         "an interior maximum", f"estimate({nq}, p={p - 1}, q={q}{extra})"))
        if q:
            opts.append((f"a lower MA order (q = {q - 1})",
                         f"estimate({nq}, p={p}, q={q - 1}{extra})"))
        opts.append(("keep it, knowing where it sits, and take it to the yardstick",
                     f"evaluate({nq}, p={p}, q={q}{extra}, estwin=...)"))
    opts.append(("report the highest point found as such, stating that it is on the wall",
                 f'record_decision({nq}, node="N4b", decision="...", reason="...")'))
    if 0.0 in wall or any(f in seasonal for f in wall if f > 0):
        opts.append(("revise the univariate model's d (or its seasonality) in art: the wall "
                     "is its signature", "art (outside sima)"))
    shows = ["The fit is restarted from other points and re-estimated by a second path "
             "(Shea's likelihood): if they climb, the reported point is not the top. A root "
             "on the invertibility wall makes the likelihood a ridge, whose point depends on "
             "the path."]
    return E.envelope("# N4b · Study of the fit", out[:i_menu], shows,
                      [l.strip() for l in out[i_menu:] if l.strip()], opts)


# --------------------------------------------------------------------------- #
#  N5                                                                          #
# --------------------------------------------------------------------------- #

@mcp.tool()
def evaluate(name: str, p: int = 0, q: int = 0, estwin: int = 0, horizon: int = 12,
             diagcov: bool = False, links: str = "", cross: str = "additive",
             zeros: str = "", indices: str = "", yardstick: str = "") -> str:
    """N5 — The yardstick: does the candidate forecast better than the univariates?

    Estimates the candidate AND the diagonal system (the univariate models) on
    the first `estwin` observations, holds the parameters fixed, and forecasts
    from every origin to the end of the data, `horizon` steps ahead. Compares
    RMSE and MAPE series by series and horizon by horizon. A VARMA that does not
    gain here has no reason to exist, whatever its in-sample significance.

    `estwin` counts observations of the FIRST series; leave enough data after it
    (at least a few dozen origins) or the comparison says little. `links`,
    `zeros` and `indices`: as in estimate, the same candidate.

    ON A VEC (the current model is one, estimate_vec): the VEC's rolling-origin
    forecasts (drvec's -estwin/-f: the fit on the first rows, parameters held,
    errors in each series' own units) against the univariates on the same
    origins, and against the VARMA in differences when one was estimated. THE
    RULE depends on the purpose recorded at N1c: a VETO when it is "forecast",
    a CAVEAT (always reported) for a "long run" claim. p, q and the VARMA
    arguments are then ignored.

    `yardstick` (route V): the analyst's univariate models, one fue file per
    series (a JSON list or comma-separated paths), e.g. their `.pre` from art.
    Without it the yardstick is route U's light builder, which takes the first
    of a tie in art's ranking; the report names the models either way. Once
    given it stays for the session (forecast_uncertainty and structure use it).
    On route U the yardstick is already the loaded files.
    """
    s = _sess.get(name)
    if s.gate is None:
        return "Run the gate first (run_gate)."
    if s.current_kind() == "VEC":
        from .mcp_vec import evaluate_vec
        return evaluate_vec(s, int(estwin), int(horizon))
    if yardstick.strip():
        if s.route != "V":
            return ("On route U the yardstick is the univariate models loaded with "
                    "load_pre: there is nothing to give.")
        try:
            _set_yardstick(s, yardstick)
        except Exception as e:                               # noqa: BLE001
            return f"The yardstick was not taken: {e}"
    if not int(estwin):
        return "Give estwin: the observations of the first series to estimate on."
    H = int(horizon)
    try:
        lk = _links(links)
        zs = _zeros(zeros)
        Lc = _model_ladder(s, _key(p, q, diagcov, lk, cross, zs, _indices(indices)),
                           estwin=estwin)
        Lc.fit()
        _rows, cand = Lc.recursive(H)
        Ld = _ladder(_yardstick_files(s) if s.route == "V" else s.files, 0, 0, True,
                     estwin=estwin)
        Ld.fit()
        _rows, diag = Ld.recursive(H)
    except Exception as e:
        return f"The evaluation failed: {e}"
    freq = s.series[0].freq
    # the horizons read: every year up to 5 for annual data; for seasonal data
    # 1, half a year, a year and two
    hs = (list(range(1, min(H, 5) + 1)) if freq == 1 else
          sorted({1, max(1, freq // 2), freq, 2 * freq} & set(range(1, H + 1))) or [1, H])
    ech = _indices(indices)
    head = f"ECHELON ({', '.join(map(str, ech))})" if ech else f"VARMA p={p} q={q}"
    label = (f"{head} ({'diagonal' if diagcov else 'full'} cov)"
             + (f", links {lk}" if lk else "")
             + (", residual-model form" if cross == "residual" else "")
             + (f", {len(zs)} coefficients at zero" if zs else ""))
    spec = (f"p={p}, q={q}" + (", diagcov=True" if diagcov else "")
            + (f', links="{lk}"' if lk else "")
            + (f', cross="{cross}"' if cross != "additive" else "")
            + (f', indices="{", ".join(map(str, ech))}"' if ech else ""))
    txt, facts = evidence.evaluation_text(cand, diag, label, hs, _names(s),
                                          call=name, spec=spec)
    if s.route == "V":
        txt = _yardstick_text(s) + "\n\n" + txt
    s.evaluations[(p, q, diagcov, lk, cross, zs, estwin, H)] = (cand, diag)
    s.guion.add("N5", "evaluate", {"p": p, "q": q, "diagcov": diagcov, "links": lk,
                                   "estwin": estwin, "horizon": H},
                f"lower RMSE in {facts['wins']} of {facts['cells']} cells")
    return txt


# --------------------------------------------------------------------------- #
#  N6                                                                          #
# --------------------------------------------------------------------------- #

def _current(s):
    if s.current_kind() == "VEC":
        raise KeyError("the current model is a VEC (estimate_vec): this tool reads a VARMA "
                       "on drvarma's ladder. The VEC's evidence is in estimate_vec, "
                       "test_restriction and long_run; to go back to a VARMA, estimate it "
                       "(a fit already made is cached)")
    if s.current is None or s.current not in s.fits:
        raise KeyError("no model estimated yet: run estimate")
    return s.fits[s.current]


@mcp.tool()
def forecast(name: str, horizon: int = 12) -> str:
    """N6 — Forecast every series in its level with the last estimated model.

    Each series goes back to its level with its own univariate model:
    deterministic terms (known in the future), its differencing, its Box-Cox.
    The 95% band is built on the transformed scale and mapped back.
    On a VEC (the current model is one): the VEC written in levels
    (drvec.to_levels_varma) and forecast by drvarma's forecaster — one
    forecaster for every system — with each file's deterministic path and
    Box-Cox; drvec's band multiplier.
    """
    s = _sess.get(name)
    if s.current_kind() == "VEC":
        from .mcp_vec import forecast_vec
        return forecast_vec(s, int(horizon))
    try:
        L = _current(s)
        fcs = L.forecast(int(horizon))
    except Exception as e:
        return f"Cannot forecast: {e}"
    s.guion.add("N6", "forecast", {"horizon": horizon, "model": str(s.current)},
                f"{horizon} steps", kind="VARMA")
    return evidence.forecast_text(fcs)


@mcp.tool()
def forecast_uncertainty(name: str, horizon: int = 0, estwin: int = 0) -> str:
    """N5/N6 — Jenkins and Alavi's comparison of forecast uncertainty (their
    Table VIII): the standard deviation of the forecast errors by lead time,
    V(l) = SUM psi_j Sigma psi_j', of the last estimated model against the
    univariate models, per cent for series in logs. In sample, parameters
    taken as known: a quick reading of where the multivariate model could
    help; `evaluate` is the test. `horizon` defaults to the frequency (4 for
    annual data).

    `estwin` (optional): re-estimate the model AND the univariate models on
    the first `estwin` observations of the first series, as Jenkins and Alavi
    did for their Table VIII (§6.3: the muskrat-mink models refitted on 48
    observations, the rest withheld). 0 = the last fit, on all the data.
    """
    s = _sess.get(name)
    try:
        L = _current(s)
        H = int(horizon) or max(s.series[0].freq, 4)
        if estwin:
            L = _model_ladder(s, s.current, estwin=int(estwin),
                              start=None if s.current[6] else "preliminary")
            L.fit()
            Ld = _ladder(_yardstick_files(s) if s.route == "V" else s.files, 0, 0, True,
                         estwin=int(estwin))
            Ld.fit()
        else:
            Ld = _diagonal(s)
        fm = L.forecast(H)
        fd = Ld.forecast(H)
    except Exception as e:                                   # noqa: BLE001
        return f"Cannot compute: {e}"
    series = [L.series[i] for i in L._act]
    leads = sorted({1, 2, 3, max(1, H // 2), H} & set(range(1, H + 1)))
    s.guion.add("N5", "forecast_uncertainty",
                {"horizon": H, "model": str(s.current), "estwin": int(estwin)},
                "V(l) against the univariate models"
                + (f", both refitted on the first {estwin} observations" if estwin else ""))
    head = ""
    if estwin:
        n = L.result.residuals.shape[0]
        s0 = L.series[L._act[0]]
        last = s0.date_of(int(estwin))
        head = (f"Refitted on the first {estwin} observations (to "
                + (f"{last[0]}" if s0.freq == 1 else f"{last[1]}/{last[0]}")
                + f"; {n} residuals), the model and the univariate models alike.\n\n")
    return head + evidence.uncertainty_text(fm, fd, series, leads)


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
    On a VEC: the responses of the LEVELS (drvec), in drvec's order — the
    VEC's normalisation order — and their permanent effect; the bands come
    only from the parametric bootstrap (irf_bands, a job), never from the
    covariance.
    """
    s = _sess.get(name)
    if s.current_kind() == "VEC":
        from .mcp_vec import irf_vec
        return irf_vec(s, int(horizon), bands)
    try:
        r = _current(s).result
    except Exception as e:
        return f"{e}"
    b, why = _bands(s, int(horizon), bands, ndraws)
    s.guion.add("N6", "impulse_response", {"horizon": horizon, "bands": b is not None},
                "Cholesky, files order", kind="VARMA")
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
    On a VEC it REFUSES: there the order is also the normalisation, so another
    order is another fit (estimate_vec with normalise_on).
    """
    import numpy as np
    from drvarma.irf import oirf
    s = _sess.get(name)
    if s.current_kind() == "VEC":
        vf = s.vec_fits[s.vec_current]
        return ("REFUSED on a VEC: drvec's file order is both the normalisation (beta on the "
                "last r series) and the Cholesky order, so another order is ANOTHER FIT, "
                "not a permutation of this one. Estimate it: "
                f'estimate_vec(name="{name}", r={vf.r}, normalise_on="...") — and, for its '
                "bands, a new irf_bands job.")
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
    On a VEC: the decomposition of the LEVELS' forecast errors (drvec), with
    the bootstrap's bands when irf_bands has run.
    """
    s = _sess.get(name)
    if s.current_kind() == "VEC":
        from .mcp_vec import fevd_vec
        return fevd_vec(s, int(horizon), bands)
    try:
        r = _current(s).result
    except Exception as e:
        return f"{e}"
    b, why = _bands(s, int(horizon), bands, ndraws)
    s.guion.add("N6", "variance_decomposition", {"horizon": horizon, "bands": b is not None},
                "Cholesky, files order", kind="VARMA")
    return evidence.fevd_text(r.phi, r.theta, r.sigma, _names(s), int(horizon), b, why)


# --------------------------------------------------------------------------- #
#  The record, and the way out of the old format                               #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
#  Figures (presentation of the same numbers; sima.figures)                    #
# --------------------------------------------------------------------------- #

def kind_tool(kind):
    if kind.startswith("ident"):
        return "plot_identification"
    if kind == "rankboot":
        return "plot_rank_bootstrap"
    return {"irf": "plot_impulse_response", "fevd": "plot_variance_decomposition",
            "ccf": "plot_residual_ccf"}.get(kind, "plot_forecast")


def _figure(s, fig, kind, path, note, report=None, node=None):
    """The figure INSIDE the answer (as art and mtram), and a PNG on disk.
    `note` is the guion's one line; `report` (default: the note) is what the
    analyst reads."""
    import base64
    import tempfile
    from . import figures
    if not path:
        d = s.guion.figures_dir()
        try:
            os.makedirs(d, exist_ok=True)
        except OSError:
            d = tempfile.gettempdir()
        path = os.path.join(d, f"sima_{s.name}_{kind}.png")
    p = path
    vec = kind == "ccf"                  # the CCF also in vectors (SVG, PDF)
    figures.save(fig, p, vectors=vec)
    # the node the figure belongs to: the identification is N2; the residual
    # CCFs are in-sample evidence (N4); the IRF, the FEVD and the forecasts are
    # the use of the model (N6)
    node = node or ("N2" if kind.startswith("ident") else "N4" if kind == "ccf" else "N6")
    files = {"png": [p]}
    if vec:
        files["vectors"] = figures.vector_paths(p)
    s.guion.add(node, kind_tool(kind), files, note, kind=s.current_kind())
    text = f"{report or note}\n" + "".join(
        f"{v.rsplit('.', 1)[1].upper()}: {v}\n" for v in files.get("vectors", [])) + f"PNG: {p}"
    try:
        from mcp.types import ImageContent, TextContent
        with open(p, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        return [TextContent(type="text", text=text),
                ImageContent(type="image", data=b64, mimeType="image/png")]
    except Exception:                                        # noqa: BLE001
        return [text]


def _figures(s, items, text):
    """Several figures INSIDE the answer, after the report (as art's
    diagnosis), each also written as a PNG next to the files; recorded at N4."""
    import base64
    import tempfile
    from . import figures
    d = s.guion.figures_dir()
    try:
        os.makedirs(d, exist_ok=True)
    except OSError:
        d = tempfile.gettempdir()
    paths, vectors = [], []
    for fig, kind in items:
        p = os.path.join(d, f"sima_{s.name}_{kind}.png")
        figures.save(fig, p, vectors=kind == "ccf")    # the CCF also in vectors
        paths.append(p)
        if kind == "ccf":
            vectors += figures.vector_paths(p)
    files = {"png": paths}
    if vectors:
        files["vectors"] = vectors
    s.guion.add("N4", "check_residuals", files, "diagnosis figures")
    text = (text + "\n" + "".join(f"{v.rsplit('.', 1)[1].upper()}: {v}\n" for v in vectors)
            + "\n".join(f"PNG: {p}" for p in paths))
    try:
        from mcp.types import ImageContent, TextContent
        out = [TextContent(type="text", text=text)]
        for p in paths:
            with open(p, "rb") as fh:
                out.append(ImageContent(type="image", data=base64.b64encode(fh.read()).decode(),
                                        mimeType="image/png"))
        return out
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
    On a VEC: the level responses (drvec), with the bootstrap's 90 % band
    from irf_bands when it has run.
    """
    from . import figures
    s = _sess.get(name)
    if s.current_kind() == "VEC":
        from .mcp_vec import plot_irf_vec
        return plot_irf_vec(s, int(horizon), bands, path, fevd=False)
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
    dashed. A row reads the same as in plot_impulse_response. On a VEC: the
    levels' decomposition (drvec), the bootstrap's band from irf_bands.
    """
    from . import figures
    s = _sess.get(name)
    if s.current_kind() == "VEC":
        from .mcp_vec import plot_irf_vec
        return plot_irf_vec(s, int(horizon), bands, path, fevd=True)
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
    pair by pair: GraphMaker's two-sided CCF (Treadway's, the suite's
    reference), titled "A - B" with A leading at k > 0, and Hosking's
    portmanteau below as GraphMaker labels it, P (not Ljung-Box's Q). What is
    left beyond the band is what the model does not carry.
    `nlags` defaults to twice the frequency. On a VEC: the residuals of its
    stationary form (nabla Y2 and the equilibrium errors, drvec's)."""
    from . import figures
    s = _sess.get(name)
    if s.current_kind() == "VEC":
        from .mcp_vec import plot_ccf_vec
        return plot_ccf_vec(s, int(nlags), path)
    try:
        L = _current(s)
    except KeyError as e:
        return [str(e)]
    freq = s.series[0].freq
    n = L.result.residuals.shape[0]
    K = int(nlags) or figures.q_lags(max(8, 2 * freq), figures.residual_npq(L), n)
    return _figure(s, figures.residual_ccf_figure(L, K, freq), "ccf", path,
                   f"Residual CCFs, {K} lags each side")


@mcp.tool()
def plot_identification(name: str, method: int = 2, nlags: int = 0, pairs: str = "",
                        path: str = "") -> list:
    """FIGURE — Jenkins and Alavi's (1981) identification, pair by pair: the
    figure of identify_matrices. For each pair of series, in GraphMaker's
    CCF panel (Treadway's, the one drtran reads), the correlation function R_k
    above the partial S_k, both two-sided, same lag axis and scale — as art's
    ACF over PACF.

    method=2 (default): the residuals of the univariate models (prewhitened,
    each series by ITS OWN model — Haugh's CCF, not a transfer function's).
    Band 2/sqrt(n); between the panels Haugh's S* (1976), the test that the
    two are independent, in total and by side (k > 0, k < 0: who leads).
    The CCF's cut-off after q suggests an MA(q) residual model.
    method=1: the stationary series w_t, not prewhitened. The CCF band is
    Bartlett's (3.13) for unrelated series, lag by lag: the series are not
    white, and a 2/sqrt(n) band would show their common cycles as cross terms.
    Here the partial is the decisive one: a cut-off after p suggests an AR(p).
    Each panel is titled "A - B", GraphMaker's order: A leads at k > 0. With three or more
    series the partial of a pair comes from the VAR of all of them — given the
    others — and `pairs` ("A-B, A-C") draws only those; read identify_matrices'
    determinants and + - . table first to choose them.
    `nlags` defaults to max(10, 2 x frequency); the partial stops at the order
    the sample supports (n / (3m)), marked on the panel."""
    import numpy as np
    from . import figures
    s = _sess.get(name)
    try:
        L = _diagonal(s)
    except Exception as e:                                   # noqa: BLE001
        return [f"Run the gate first ({e})."]
    if method not in (1, 2):
        return ["method is 1 (not prewhitened) or 2 (prewhitened)."]
    names = _names(s)
    sel = None
    if pairs.strip():
        sel = []
        for tok in pairs.split(","):
            a, _, b = tok.strip().partition("-")
            if a.strip() not in names or b.strip() not in names or a.strip() == b.strip():
                return [f"Unknown pair '{tok.strip()}': the series are {', '.join(names)}."]
            sel.append((names.index(a.strip()), names.index(b.strip())))
    freq = s.series[0].freq
    _mu, _phi, _theta, _qq, W, _ifa = L.cast(L.result.x)
    x = np.asarray(L.result.residuals if method == 2 else W, float)
    n, m = x.shape
    K = int(nlags) or max(10, 2 * freq)
    Kp = max(1, min(K, n // (3 * m)))
    fig = figures.identification_figure(x, names, K, method, freq, sel, Kp)
    # the figure is terse, as the originals; the report around it is art's:
    # the table as a block, what it shows, what it suggests, the decision
    sel = sel or [(i, j) for i in range(m) for j in range(i + 1, m)]
    _txt, facts = evidence.ja_identification(W, L.result.residuals, names, K, 2, freq)
    kind = ("prewhitened: the residuals of the univariate models" if method == 2
            else "not prewhitened: the stationary series w_t")
    lines = [f"# Identification — Jenkins and Alavi, method {method}",
             f"*({kind}; n = {n}, {K} lags each side)*", "",
             "## 1 · TABLE", "",
             "_[Claude: show the block below AS IT IS; do not build your own table]_", "",
             "```", evidence.ja_pair_table(x, names, sel, K, Kp, method), "```", "",
             "## 2 · WHAT IT SHOWS", "",
             "ccf: the correlation matrices R_k; pccf: the partial correlation matrices "
             "S_k (multivariate Yule-Walker). " + (
                 "S* is Haugh's (1976) test that the two prewhitened series are "
                 "independent, in total and by side." if method == 2 else
                 "The ccf band is Bartlett's (3.13) for unrelated series, lag by lag; "
                 "there is no portmanteau (the series are not white)."), "", "```"]
    lines += evidence.ja_pair_facts(x, names, sel, K, Kp, method)
    lines.append("```")
    if m > 2:
        lines.append("The pccf comes from the VAR of all the series: each partial "
                     "panel is given the other series.")
    if Kp < K:
        lines.append(f"The pccf goes up to lag {Kp}: the order the sample supports (n / 3m).")
    lines += ["", "## 3 · CONCLUSIONS", ""]
    if method == 2:
        q2, lk = facts["method2_q"], facts["links"]
        lines.append(
            f"The cross ccf cuts off after lag {q2}: an MA({q2}) model for the "
            f"residuals, the univariate models on the diagonal (Jenkins and Alavi's "
            f"(3.22))" + (f", on the links {', '.join(lk)}." if lk else ".")
            if q2 else "No cross cut-off in the residuals: the univariate models "
            "may carry the system (method 1 and N5 decide).")
        lines.append("The pccf cutting off at the same lag does not tell an AR from an "
                     "MA here: after prewhitening the residual model is an MA (3.26).")
    else:
        p1, lk = facts["method1_p"], facts["method1_links"]
        lines.append(
            f"The cross pccf cuts off after lag {p1}: a cross AR({p1})"
            + (f" on the links {', '.join(lk)}." if lk else ".")
            if p1 else "No cross cut-off in the pccf.")
        lines.append("The ccf of series that are not white decays or waves (their own "
                     "cycles leak into it); the pccf is the one to read here.")
    lines += ["", "## 4 · DECISION — alternatives", ""]
    opts = []
    if facts["method2_q"]:
        lk = facts["links"]
        opts.append(("the MA residual model (method 2)",
                     f'estimate(name="{name}", p=0, q={facts["method2_q"]}'
                     + (f', links="{", ".join(lk)}"' if lk else "") + ', cross="residual")'))
    if facts["method1_p"]:
        lk = facts["method1_links"]
        opts.append(("the cross AR (method 1)",
                     f'estimate(name="{name}", p={facts["method1_p"]}, q=0'
                     + (f', links="{", ".join(lk)}"' if lk else "") + ")"))
    other = 1 if method == 2 else 2
    opts.append((f"see method {other} before deciding (Jenkins and Alavi use both)",
                 f'plot_identification(name="{name}", method={other})'))
    opts.append(("the whole matrices: S_k(q), determinants, the + - . table",
                 f'identify_matrices(name="{name}")'))
    for t, (what, call) in enumerate(opts):
        lines.append(f"**{'ABCDEF'[t]})** {what}\n   `{call}`")
    if facts["method2_q"] and facts["method1_p"]:
        lines.append("\nBoth readings are present: Jenkins and Alavi estimate both, "
                     "compare them, and N5 (evaluate) decides.")
    lines += ["", _env.STOP]
    brief = (f"method {method}: " + (
        f"cross ccf cut-off after {facts['method2_q']} (MA residual model)" if method == 2
        else f"cross pccf cut-off after {facts['method1_p']} (cross AR)"))
    return _figure(s, fig, f"ident{method}", path, brief, report="\n".join(lines))


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
    file. On a VEC: the levels and the 95 % band of forecast (drvarma's
    forecaster on the VEC in levels), with ERR the level innovations.
    """
    import tempfile
    from . import figures
    s = _sess.get(name)
    if s.current_kind() == "VEC":
        from .mcp_vec import plot_forecast_vec
        return plot_forecast_vec(s, int(horizon), series, path)
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
        elif path:
            p = os.path.join(path, f"sima_{s.name}_forecast_{nm}.png")
        else:
            p = ""
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
    from .guion import NODES
    if node not in NODES:
        return (f"Recorded as step {e.n}. Note: \"{node}\" is not one of sima's nodes "
                f"({', '.join(NODES)}); the guion keeps it under its own name.")
    return f"Recorded as step {e.n}."


def _vec_desc(vf):
    return (f"VEC r = {vf.r}, p = {vf.p}, q = {vf.q}, case {vf.case}, order "
            + " → ".join(vf.order) + (", restricted" if vf.restriction else ""))


def _models(s):
    """{description: (kind, key)} of every model fitted in the session."""
    m = {_desc(k): ("VARMA", k) for k in s.fits}
    m.update({_vec_desc(vf): ("VEC", k) for k, vf in s.vec_fits.items()})
    return m


def _which(s, model):
    """(kind, key, description) of `model`: "current", "univariates", or a
    description (or an unambiguous part of one) of a fitted model."""
    from . import decisions as _dec
    m = (model or "current").strip()
    if m.lower() in ("univariates", "univariate", "diagonal"):
        return "UNIV", None, "the univariate models (the diagonal system)"
    if m.lower() == "current":
        kind, key = _dec.model_of(s)
        if key is None:
            raise KeyError("there is no current model: estimate one first")
        d = _desc(key) if kind == "VARMA" else _vec_desc(s.vec_fits[key])
        return kind, key, d
    ms = _models(s)
    hit = [d for d in ms if d == m] or [d for d in ms if m.lower() in d.lower()]
    if len(hit) != 1:
        raise KeyError(("no fitted model matches " if not hit else "several models match ")
                       + repr(model) + ". The session's: " + "; ".join(ms or ["none"]))
    return ms[hit[0]] + (hit[0],)


@mcp.tool()
def where(name: str) -> str:
    """Where the analysis stands (P3): the path walked, the decisions still
    OPEN with their options, what was adopted or set aside, and the protocol's
    next node. The answer to "what now?" at any point. It informs; it does not
    decide, and it records nothing. The map behind it:
    sima://doc/DECISION_NODES."""
    from . import status
    return status.where(_sess.get(name), name, _desc, _vec_desc)


@mcp.tool()
def hand_over(name: str) -> str:
    """N7 — Close the analysis (P7), in both lanes: the adopted model (or the
    univariates), the yardstick numbers that decided it, the caveats that stay
    open (a file not validated in art, a fit on the MA wall, the Cholesky order,
    a rank on theory, open decisions), what was set aside, and the call that
    writes the guion. Recorded at N7."""
    from . import status
    s = _sess.get(name)
    txt, ad, ncv = status.hand_over(s, name, _desc, _vec_desc)
    s.guion.add("N7", "hand_over", {}, f"adopted: {ad or 'nothing'}; {ncv} caveat(s) open")
    return txt


@mcp.tool()
def adopt(name: str, model: str = "current", why: str = "") -> str:
    """N5 (C8 for a VEC) — ADOPT the model the analysis keeps.

    `model`: "current" (the last one estimated), "univariates" (the diagonal
    system: no VARMA gained where it matters), or the description of a fitted
    one as the estimates name it ("p = 1, q = 0, full covariance"; a part of
    it that names only one fit is enough). `why` is required: the reason, with
    its evidence (the yardstick's numbers).

    The adopted model becomes the current one, and the final-stage tools
    (forecast, impulse_response, variance_decomposition and their plots) say
    so when they are asked about another. Adopting again replaces it."""
    s = _sess.get(name)
    if not why.strip():
        return "Say why (why=...): an adoption without its reason is not documented."
    try:
        kind, key, d = _which(s, model)
    except KeyError as e:
        return f"Cannot adopt: {e.args[0]}"
    if kind == "VARMA":
        s.current, s.kind = key, "VARMA"
    elif kind == "VEC":
        s.vec_current, s.kind = key, "VEC"
    s.adopted = (kind, key)
    by = "LLM" if s.lane == "autonomous" else "analyst"
    e = s.guion.add("C8" if kind == "VEC" else "N5", "adopt",
                    {"model": d, "decided_by": by}, why, f"adopted: {d} -- because {why}",
                    kind="" if kind == "UNIV" else kind)
    e.status = "adopted"
    return (f"Adopted (step {e.n}): {d}." + (
        " The univariate models are the result: say it plainly, it is a finding." if kind == "UNIV"
        else " It is the current model; the final-stage tools act on it.")
        + f' To close the analysis: hand_over(name="{name}") — the result, its yardstick '
        "and the caveats that stay open.")


@mcp.tool()
def abandon(name: str, model: str = "current", why: str = "") -> str:
    """N5 — SET ASIDE a candidate, and why (what a failed candidate contributes
    is the reason it failed). `model` as in adopt. The fit stays in the session
    (an LR can still use it); the guion marks it as a dead end."""
    s = _sess.get(name)
    if not why.strip():
        return "Say why (why=...): a candidate set aside without its reason is lost."
    try:
        kind, key, d = _which(s, model)
    except KeyError as e:
        return f"Cannot set aside: {e.args[0]}"
    if kind == "UNIV":
        return "The univariates are the yardstick, not a candidate: they are not set aside."
    s.abandoned.append((kind, key, why))
    by = "LLM" if s.lane == "autonomous" else "analyst"
    e = s.guion.add("C8" if kind == "VEC" else "N5", "abandon",
                    {"model": d, "decided_by": by}, why, f"set aside: {d} -- because {why}",
                    kind=kind)
    e.status = "dead-end"
    return (f"Set aside (step {e.n}): {d}. Back to the identification for another "
            f'candidate (identify_cross or identify_matrices(name="{name}")), or adopt one.')


@mcp.tool()
def export_guion(name: str, save: bool = True, html: bool = True) -> str:
    """The path of the analysis, node by node, with its evidence and decisions.

    This is what makes the analysis reviewable and repeatable: every tool call
    and every recorded decision, in order. Saved next to the first file as
    <first>.sima.json when `save`, so that the record travels with the data;
    with `html` (default) also <first>.sima.html, a self-contained page in
    art's style: the steps in a table, a section per node with the evidence,
    the decisions highlighted (who decided, what was set aside) and the
    figures drawn at each step (they are saved in figs/ next to the files).
    """
    s = _sess.get(name)
    txt = s.guion.render()
    if save:
        try:
            txt += f"\n\nSaved to {s.guion.save()}"
            if html:
                txt += f"\nHTML: {s.guion.save_html()}"
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


def _cli_flags():
    """-h/--help and --version answer and exit; without them `sima` would
    start the stdio server and seem to hang (drvarma BUG-0014)."""
    import sys
    args = sys.argv[1:]
    if any(a in ("-h", "--help") for a in args):
        print("usage: sima [-h] [--version]\n\n"
              "sima: the MCP server for simultaneous VARMA models (engine: drvarma).\n"
              "Speaks MCP over stdio: an MCP client (Claude Code, Claude Desktop)\n"
              "starts it; run by hand it waits for a client on stdin.\n\n"
              "options:\n"
              "  -h, --help  show this message and exit\n"
              "  --version   show the version and exit")
        sys.exit(0)
    if "--version" in args:
        from importlib.metadata import PackageNotFoundError, version
        try:
            v = version("sima-tseries")
        except PackageNotFoundError:
            v = "unknown"
        print(f"sima (sima-tseries) {v}")
        sys.exit(0)


def main():
    _cli_flags()
    mcp.run()


# the cointegration tools (N1c and the C nodes) register on the same server
from . import mcp_vec as _mcp_vec          # noqa: E402,F401
from .mcp_vec import (add_exogenous, estimate_vec, irf_bands, job_cancel,  # noqa: E402,F401
                      job_result, job_status, jobs_list, long_run, plot_rank_bootstrap,
                      prepare_vec, rank_test, sweep, test_restriction)


if __name__ == "__main__":
    main()
