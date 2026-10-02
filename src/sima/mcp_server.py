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
                      every difference (cointegration, drvec's). A reading;
                      sima never changes a d.
N2  identify_cross    the residual CCFs of the diagonal system: the evidence of
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
N3  estimate          a candidate: cross orders p, q; full or diagonal
                      covariance; optionally `links`, the cross dynamics only
                      on the pairs identify_cross found (its option (d)).
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
8. Resources to ASK for when needed: sima://protocol (this text),
   sima://defects (sima's and the engine's defect registers; one report with
   sima://engine-defects/BUG-XXXX), sima://docs (the design documents and the
   user manual: sima://doc/MANUAL-jenkins-alavi), sima://examples and
   sima://example/<name> (a worked example's tutorial).
"""

mcp = FastMCP("sima — simultaneous VARMA on the ATSW ladder (drvarma)",
              instructions=_INSTRUCTIONS)


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


def _ladder(files, p, q, diagcov, estwin=None, links=None, start="zero",
            cross="additive", zeros=None, lik="elf"):
    from drvarma.ladder import Ladder
    return Ladder(list(files), p, q, diagcov=diagcov, estwin=estwin,
                  links=links or None, start=start, cross=cross,
                  zeros=list(zeros) if zeros else None, lik=lik)


_OWN = re.compile(r"(phi|theta)_(.+)\[B\^(\d+)\]")


def _zeros(text):
    """The canonical zeros: a sorted tuple of coefficient names, cross
    (AR3[A<-B]) and, in route V, own (phi_A[B^3], theta_A[B^1])."""
    if not text:
        return ()
    toks = text if isinstance(text, (list, tuple)) else text.split(",")
    return tuple(sorted({t.strip() for t in toks if t.strip()}))


def _split_zeros(s, zeros):
    """(cross names for the ladder, own lags {series: {"ar": set, "ma": set}})."""
    cross, own = [], {}
    names = _names(s)
    for z in zeros:
        m = _OWN.fullmatch(z)
        if not m:
            cross.append(z)
            continue
        if s.route != "V":
            raise ValueError(f"'{z}' is a coefficient of a univariate model: on route U "
                             "the diagonal is art's — simplify it there.")
        if m.group(2) not in names:
            raise ValueError(f"'{z}': no series {m.group(2)}")
        own.setdefault(m.group(2), {"ar": set(), "ma": set()})[
            "ar" if m.group(1) == "phi" else "ma"].add(int(m.group(3)))
    return cross, own


def _model_ladder(s, key, estwin=None, start="zero", lik="elf"):
    """The Ladder of a fit key (p, q, diagcov, links, cross, zeros) on its files."""
    p, q, dc, lk, cr, zs = key
    cross, own = _split_zeros(s, zs)
    return _ladder(_files_for(s, p, q, own), p, q, dc, estwin=estwin, links=lk,
                   start=start, cross=cr, zeros=cross, lik=lik)


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


def _files_for(s, p, q, own=None):
    """The files a candidate is estimated on. Route U: the session's (the
    univariate models on the diagonal). Route V: each series' specification
    with a free AR(p)/MA(q) of its own, written once per order — with cross
    orders p, q the ladder is the full VARMA(p, q), Tiao and Box's model."""
    if s.route != "V":
        return s.files
    from . import raw
    r = _sess.get_raw(s.v["raw"])
    own = own or {}
    paths = [raw.v_path(s.v["dir"], nm, p, q, own.get(nm)) for nm in r.names]
    if not all(os.path.exists(x) for x in paths):
        raw.write_v(s.v["dir"], r.names, r.data, r.chars, r.freq, r.start, p, q, own=own)
    return paths


def _yardstick_files(s):
    """Route V's yardstick: the univariate models of route U's builder, for N5
    only (they never enter the system). Built once, next to the specs."""
    from . import raw
    r = _sess.get_raw(s.v["raw"])
    pres = [os.path.join(s.v["dir"], f"{nm}_u.pre") for nm in r.names]
    if not all(os.path.exists(x) for x in pres):
        raw.build_univariate(r.names, r.data, r.chars, r.freq, r.start, s.v["dir"])
    return pres


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
def load_example(name: str = "jenkins_alavi", session: str = "", dest: str = "") -> str:
    """N0 for a worked example: copy its files to a working folder (`dest`,
    default ~/sima-examples/<name>; files already there are kept) and load its
    univariate models, as load_pre does. From here the analysis is the usual
    one — run_gate, then node by node, the analyst deciding at every pause.

    Before going on, READ its tutorial, `sima://example/<name>`: at each step
    it says what to look at and what the original analysis found, which you
    add after each report ("In the paper: ..."). The tools do not change in a
    tutorial; the explanation of the method is the manual it names.
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
    for rel in list(m["files"]) + list(m.get("also", [])) + [m["tutorial"]]:
        o, d = os.path.join(src, rel), os.path.join(dest, rel)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        if os.path.exists(d):
            kept += 1
        else:
            shutil.copy2(o, d)
    session = session or name
    files = [os.path.join(dest, r) for r in m["files"]]
    loaded = _fn_load_pre(session, _json.dumps(files))
    out = [f"# Worked example — {m['title']}", "", m["summary"], "",
           f"Files in `{dest}`" + (f" ({kept} already there, kept as they were)" if kept else "")
           + f"; session `{session}`.", "",
           "## The plan", ""] + [f"- {p}" for p in m.get("plan", [])] + [
           "", "## For the assistant", "",
           f"Read the tutorial now: `sima://example/{name}`. Lead it in the guided "
           "lane, ONE node at a time: present each report as always, then add what "
           "the original analysis found at that step, and stop at the pause. The "
           f"method is explained in `sima://doc/{m['manual']}`.", "",
           "## The univariate models, loaded", "", loaded, "",
           f"Next: run_gate(\"{session}\")."]
    return "\n".join(out)


def _fn_load_pre(name, paths_json):
    return getattr(load_pre, "fn", load_pre)(name, paths_json)


@mcp.tool()
def load_data(name: str, path: str, freq: int = 0, start: str = "") -> str:
    """N0r — RAW DATA: an analyst with series and no univariate models
    (docs/STUDY-raw-entry.md). An Excel (.xlsx/.xls) or CSV table, one column
    per series in ORIGINAL levels (never transformed or differenced), a header
    row with the names, and optionally a first column of dates (a year, or
    year-period: 1972-08, 1972Q3).

    `freq`: 1, 4 or 12 (0: inferred from the date column). `start`: the first
    date, "1972-08" or "1850" (empty: from the date column). The table must be
    complete on one common calendar: missing values are refused, with where.
    Next: characterize — each series' transformation with art's engine."""
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
    s.guion.add("N0r", "load_data", {"path": path, "freq": f, "start": list(st)},
                f"{len(names)} series, {data.shape[0]} observations")
    return (evidence.raw_table_text(names, data, f, st, nonpos, path)
            + "\n\nNo univariate models: this is the raw entry. Next: characterize — "
            f'each series\' transformation, with art\'s engine (characterize("{name}")).')


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
           "says whether they need every difference jointly; then identify_cross."
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
def canonical_analysis(name: str, p: int = 0, near: float = 0.90) -> str:
    """N1b — Box and Tiao's (1977) canonical analysis of the transformed LEVELS
    (each series' Box-Cox and seasonal differences; NOT its regular ones):
    the combinations of the series ordered from least to most predictable.
    Nearly white ones are relations among the series that stay stable over
    time; nearly non-stationary ones (sqrt(lam) >= `near`, the scale of a
    root: for an AR(1) component lam = phi^2) their common growth.
    When two or more series are differenced and fewer components look
    non-stationary, the joint model may not need every difference — the
    question of cointegration, which is drvec's (Johansen's test); sima only
    reads it and never changes a d on its own. `p` is the VAR order (0: the
    last significant M(l) of Tiao and Box's stepwise table on the levels). Run
    it after the gate, before the identification, when two or more series are
    differenced; with raw data (load_data, characterize), right after
    characterize, on the characterization's levels."""
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
    lev = [x.levels() for x in s.series]
    n = min(len(v) for v in lev)
    X = np.column_stack([v[-n:] for v in lev])          # aligned at the end
    d = [int(x.model.d or 0) for x in s.series]
    txt, facts = evidence.canonical_report(X, _names(s), d, s.series[0].freq,
                                           int(p), float(near), call=name)
    s.guion.add("N1b", "canonical_analysis", {"p": facts["p"], "near": near},
                f"lam {', '.join(f'{v:.3f}' for v in facts['lam'])}; "
                f"{facts['near_one']} near 1 of {facts['differenced']} differenced"
                + ("; stationary combinations possible (drvec)" if facts["question"] else ""))
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
    txt, facts = evidence.cross_identification(L.result.residuals, _names(s), K, freq)
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
                                            int(qmax), freq, route=s.route)
    s.guion.add("N2", "identify_matrices", {"nlags": K, "qmax": qmax},
                f"method 2: MA({facts['method2_q']}) residual model"
                + (f", links {', '.join(facts['links'])}" if facts["links"] else "")
                + f"; method 1: R_k cut {facts['method1_q']}, S_k cut {facts['method1_p']}")
    return txt


# --------------------------------------------------------------------------- #
#  N3 / N4                                                                     #
# --------------------------------------------------------------------------- #

@mcp.tool()
def estimate(name: str, p: int, q: int, diagcov: bool = False,
             reason: str = "", links: str = "", start: str = "zero",
             cross: str = "additive", zeros: str = "") -> str:
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

    `start`: where the cross terms start — "zero" (default) or "preliminary",
    Jenkins and Alavi's preliminary estimates (the cross MA from the
    univariate residuals' cross covariances, the cross AR from Yule-Walker).
    Usually the same optimum in fewer iterations; on an ill-defined estimation
    (the MA wall) a second path worth comparing.

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
    route V only (route U's diagonal is the univariate model, art's). A fit
    already made with the same arguments is reused, not refitted.
    """
    s = _sess.get(name)
    if s.gate is None:
        return "Run the gate first (run_gate)."
    lk = _links(links)
    zs = _zeros(zeros)
    key = (int(p), int(q), bool(diagcov), lk, cross, zs)
    try:
        if s.route == "V" and cross == "residual":
            return ('cross="residual" is Jenkins and Alavi\'s model for UNIVARIATE '
                    "residuals; route V has none. Use the default.")
        if key in s.fits:
            L = s.fits[key]
        else:
            L = _model_ladder(s, key, start=start)
            L.fit()
    except Exception as e:
        s.guion.add("N3", "estimate", {"p": p, "q": q, "diagcov": diagcov, "links": lk,
                                       "cross": cross}, f"failed: {e}", reason)
        return f"Estimation failed: {e}"
    s.fits[key] = L
    s.current = key
    freq = s.series[0].freq
    txt = evidence.estimation_text(L, max(8, 2 * freq))
    if s.route == "V":
        txt = (f"ROUTE V — the full VARMA({p},{q}) of Tiao and Box: each series' own "
               f"AR({p})/MA({q}) estimated jointly with the cross terms. The LR below is "
               f"against the same model without cross terms (one AR({p})/MA({q}) per "
               "series), not against univariate models; those come at N5.\n\n" + txt)
    lr = "" if (p == 0 and q == 0 and diagcov) else " LR %.2f df %d p %.4f" % L.lr_test()
    s.guion.add("N3", "estimate", {"p": p, "q": q, "diagcov": diagcov, "links": lk,
                                   "start": L.start_used, "cross": cross,
                                   "zeros": ", ".join(zs)},
                f"logL {L.result.logL:.4f}, {L.result.npar} parameters;{lr}", reason)
    nxt = "Next: evaluate — the candidate against the univariates."
    if getattr(L.result, "ma_boundary", 0):
        nxt = ("The fit stopped on the MA invertibility wall: study it before "
               "reading its numbers (study_estimation).")
    return txt + "\n\n" + nxt


def _desc(key):
    p, q, dc, lk, cr, zs = key
    return (f"p = {p}, q = {q}, {'diagonal' if dc else 'full'} covariance"
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
    p, q, dc, lk, cr, zs = key
    return (f'estimate(name="{name}", p={p}, q={q}'
            + (", diagcov=True" if dc else "") + (f', links="{lk}"' if lk else "")
            + (', cross="residual"' if cr == "residual" else "")
            + (f', zeros="{", ".join(zs)}"' if zs else "") + ")")


@mcp.tool()
def simplify(name: str, t: float = 1.0) -> str:
    """N4s — Tiao and Box's (1981, §4) simplification by coefficient, on the
    current fit: the cross coefficients (and, on route V, each series' own
    AR/MA coefficients) with |t| < `t` are held at zero, the model is
    refitted, and the restriction is tested by LR against the full fit, with
    AIC and BIC. The restricted fit is cached: adopting it (the estimate call
    in the menu) is instant. Route U's diagonal is never touched — it is the
    univariate model, art's. Several rounds are normal (Tiao and Box simplified
    the SCC model twice)."""
    import numpy as np
    s = _sess.get(name)
    try:
        L = _current(s)
    except KeyError:
        return "Estimate a model first (estimate)."
    key = s.current
    r = L.result
    x, se = np.asarray(r.x, float), np.asarray(r.std_errors, float)
    cross_re = re.compile(r"(AR|MA)\d+\[.+<-.+\]")
    drop = []
    for nm, v, e in zip(r.names, x, se):
        ok = cross_re.fullmatch(nm) or (s.route == "V" and _OWN.fullmatch(nm))
        if ok and np.isfinite(e) and e > 0 and abs(v / e) < float(t):
            drop.append((nm, float(v), float(v / e)))
    f = {"t": float(t), "desc": _desc(key), "route": s.route, "drop": drop}
    if drop:
        key2 = key[:5] + (_zeros(list(key[5]) + [d[0] for d in drop]),)
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
                     if (cross_re.fullmatch(nm) or (s.route == "V" and _OWN.fullmatch(nm)))
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
    except KeyError:
        return "Estimate a model first (estimate)."
    key = s.current
    p, q, dc, lk, cr, zs = key
    if p == 0 and q == 0:
        return "The current fit has no cross dynamics (p = q = 0): nothing to test."
    names = _names(s)
    m = len(names)
    free = set(L.result.names)

    def pair_zeros(i, j):
        return [f"{k}{l}[{names[i]}<-{names[j]}]" for k, top in (("AR", p), ("MA", q))
                for l in range(1, top + 1) if f"{k}{l}[{names[i]}<-{names[j]}]" in free]

    tests = {}

    def test(extra, label):
        if not extra:
            return {"label": label, "lr": 0.0, "df": 0, "p": 1.0}
        k2 = key[:5] + (_zeros(list(zs) + extra),)
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
    p_, q_, dc_, lk_, cr_, zs_ = s.current
    desc = (f"cross p = {p_}, q = {q_}, {'diagonal' if dc_ else 'full'} covariance"
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
    lines += ["", "⏸ **Your decision.** (guided lane: I do not go on until you say)"]
    # the figures, as drvus' diagnosis: a panel per series, a ccf per pair
    items = [(fig, f"resid_{nm}") for nm, fig in figures.residual_panels(L)]
    from drvarma.plots import ccf_default_lags
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
    p, q, diagcov, lk, cross, zs = s.current
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
        Ls = _model_ladder(s, s.current, lik="shea")
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
             diagcov: bool = False, links: str = "", cross: str = "additive",
             zeros: str = "") -> str:
    """N5 — The yardstick: does the candidate forecast better than the univariates?

    Estimates the candidate AND the diagonal system (the univariate models) on
    the first `estwin` observations, holds the parameters fixed, and forecasts
    from every origin to the end of the data, `horizon` steps ahead. Compares
    RMSE and MAPE series by series and horizon by horizon. A VARMA that does not
    gain here has no reason to exist, whatever its in-sample significance.

    `estwin` counts observations of the FIRST series; leave enough data after it
    (at least a few dozen origins) or the comparison says little. `links` and
    `zeros`: as in estimate, the same restricted candidate.
    """
    s = _sess.get(name)
    if s.gate is None:
        return "Run the gate first (run_gate)."
    H = int(horizon)
    try:
        lk = _links(links)
        zs = _zeros(zeros)
        Lc = _model_ladder(s, (int(p), int(q), bool(diagcov), lk, cross, zs),
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
    label = (f"VARMA p={p} q={q} ({'diagonal' if diagcov else 'full'} cov)"
             + (f", links {lk}" if lk else "")
             + (", residual-model form" if cross == "residual" else "")
             + (f", {len(zs)} coefficients at zero" if zs else ""))
    txt, facts = evidence.evaluation_text(cand, diag, label, hs, _names(s))
    if s.route == "V":
        txt = ("ROUTE V: the yardstick is univariate models built by route U's builder "
               "(art's engine, light; not reviewed in art), "
               f"{os.path.join(s.v['dir'], '<SERIES>_u.pre')} — they never entered the "
               "system.\n\n" + txt)
    s.evaluations[(p, q, diagcov, lk, cross, zs, estwin, H)] = (cand, diag)
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
            L = _model_ladder(s, s.current, estwin=int(estwin), start="preliminary")
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

def kind_tool(kind):
    if kind.startswith("ident"):
        return "plot_identification"
    return {"irf": "plot_impulse_response", "fevd": "plot_variance_decomposition",
            "ccf": "plot_residual_ccf"}.get(kind, "plot_forecast")


def _figure(s, fig, kind, path, note, report=None):
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
    figures.save(fig, p)
    # the node the figure belongs to: the identification is N2; the residual
    # CCFs are in-sample evidence (N4); the IRF, the FEVD and the forecasts are
    # the use of the model (N6)
    node = "N2" if kind.startswith("ident") else "N4" if kind == "ccf" else "N6"
    s.guion.add(node, kind_tool(kind), {"png": [p]}, note)
    text = f"{report or note}\nPNG: {p}"
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
    paths = []
    for fig, kind in items:
        p = os.path.join(d, f"sima_{s.name}_{kind}.png")
        figures.save(fig, p)
        paths.append(p)
    s.guion.add("N4", "check_residuals", {"png": paths}, "diagnosis figures")
    text = text + "\n" + "\n".join(f"PNG: {p}" for p in paths)
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
    pair by pair: GraphMaker's two-sided CCF (Treadway's, the suite's
    reference), titled "A - B" with A leading at k > 0, and Hosking's
    portmanteau below as GraphMaker labels it, P (not Ljung-Box's Q). What is
    left beyond the band is what the model does not carry.
    `nlags` defaults to twice the frequency."""
    from . import figures
    s = _sess.get(name)
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
    lines += ["", "⏸ **Your decision.** (guided lane: I do not go on until you say)"]
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
    return f"Recorded as step {e.n}."


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


def main():
    mcp.run()


if __name__ == "__main__":
    main()
