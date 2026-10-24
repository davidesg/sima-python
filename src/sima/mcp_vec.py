"""sima's tools for cointegrated systems: N1c and the C nodes (docs/PLAN-vec.md C3, C4).

Registered on the same server as the VARMA tools (``sima.mcp_server.mcp``):
one session, one guion. drvec is the engine, through its public API; the long
computations are jobs (``sima.jobs``).
"""
from __future__ import annotations

import json
import os

import numpy as np

from . import jobs, vec
from . import session as _sess
from .mcp_server import _figure, _names, mcp
from .provenance import line as _prov_line

WAIT = 20.0          # the short inline wait of a job tool, in seconds


# --------------------------------------------------------------------------- #
#  helpers                                                                     #
# --------------------------------------------------------------------------- #

def _files_by_name(s):
    return {x.name: x.path for x in s.series}


def _spec_files(s, order):
    by = _files_by_name(s)
    return [by[n] for n in order]


def _rank_spec(spec):
    return (int(spec["p"]), int(spec["q"]), str(spec["case"]),
            tuple(sorted(spec.get("nodrift") or ())), tuple(sorted(spec["order"])))


def _job_prov(st, res=None):
    p = {"key": st.get("key"), "folder": st.get("folder"), "seed": st.get("seed")}
    eng = st.get("engine")
    if eng:
        p["engine"] = f"{eng[0]} {eng[1]}" + (f" ({eng[2]})" if len(eng) > 2 and eng[2] else "")
    if res and res.get("provenance"):
        p["drvec_provenance"] = res["provenance"]
    return p


def _prov_text(st, res=None):
    from .provenance import base
    p = base()
    p.update(_job_prov(st, res))
    return _prov_line(p)


def _need_vec(s):
    if s.current_kind() != "VEC":
        raise KeyError("no VEC estimated yet: estimate_vec first")
    return s.vec_fits[s.vec_current]


def _session(name):
    try:
        return _sess.get(name), None
    except KeyError as e:
        return None, str(e)


def _job_text(jid, state, st, what, call, extra=""):
    """A job not finished within the wait: its id, its progress, the way back."""
    eng = st.get("engine") or ["?"]
    return "\n".join([
        f"# {what} — a JOB, running detached (it survives this conversation)",
        "", f"job id: `{jid}` ({state}; engine {eng[0]}; folder {st['folder']})",
        "", "Progress:", jobs.progress_text(st), "",
        "The result is not ready: NOTHING is reported until the run is finished — no "
        "provisional critical value, no partial table. Ask again with "
        f"`job_status(\"{jid}\")`, and take the result with `job_result(\"{jid}\")`; "
        f"or call `{call}` again (the same arguments return the same job, or its "
        "result once it exists). `job_cancel` stops it.", "",
        "Guided lane: tell the analyst roughly how long it takes (the rate above) and "
        "stop. Autonomous lane: poll job_status; DO NOT DECIDE THIS NODE until "
        "job_result has the final table." + (("\n\n" + extra) if extra else "")])


# --------------------------------------------------------------------------- #
#  N1c / C0                                                                    #
# --------------------------------------------------------------------------- #

@mcp.tool()
def prepare_vec(name: str, purpose: str = "", p: int = 0, q: int = 0, case: str = "pre",
                nodrift: str = "", mixed: bool = False) -> str:
    """N1c/C0 — The cointegration question, and the VEC's specification with its
    checks (docs/STUDY-vec.md §2.3-2.4, §3.1-3.2). Offered after
    canonical_analysis when TWO OR MORE series have d = 1, whatever its count:
    the question is the analyst's (in the autonomous lane, yours, with the
    reason written down). Feedback is not a precondition: it is tested inside
    the VEC (weak exogeneity).

    `purpose` is REQUIRED and recorded at N1c: "forecast" or "long run". It
    decides the yardstick's role later (C8): a VETO when the purpose is to
    forecast, a CAVEAT beside a long-run claim (an equilibrium, who corrects).

    The checks, each a refusal with its reason or a warning: d >= 2 (drvec
    models I(1) systems; back to art), D > 0 (drvec refuses a seasonal
    difference: deterministic seasonality in art, objective "multivariante"),
    a deterministic variable drvec refuses (its message), d = 0 series (the
    MIXED case: an option, `mixed=True`, never the default; they go in the Y1
    block and r >= their number), a file that moved at the gate, and the
    sample (drvec's window against the gate's).

    `p`: drvec's AR order on (nabla Y2, W) (0: proposed — the univariate AR
    order in nabla plus 1, or Tiao and Box's M(l) on the levels when
    canonical_analysis ran). `q`: the MA order (0 by default). `case`: 1, 2, 3
    or "pre" (default: each drift as its file's mean says). `nodrift`: series
    whose drift is held at 0 (case 3/pre). Never offered: drvec's refused
    options (-warma, -mawarma, -specs, -matest, -artest, -m 2, -rankadm, the
    instruments and the writers). Next: rank_test, the only way to a rank."""
    s, err = _session(name)
    if err:
        return err
    if s.gate is None:
        return "Run the gate first (run_gate): the univariate base is certified before anything."
    pur = purpose.strip().lower().replace("-", " ").replace("_", " ")
    if pur in ("longrun", "long"):
        pur = "long run"
    if pur not in ("forecast", "long run"):
        return ("N1c needs the model's PURPOSE before the rank: purpose=\"forecast\" or "
                "purpose=\"long run\". It decides the yardstick's role at C8: a veto when "
                "the model is to forecast; a caveat, reported always, beside a long-run "
                "claim (an equilibrium, who corrects). Ask the analyst (guided lane), or "
                "decide it and record why (autonomous lane).")
    try:
        cs = vec.case_arg(case)
    except ValueError as e:
        return str(e)
    names = _names(s)
    nd = vec.names_list(nodrift)
    bad = [n for n in nd if n not in names]
    if bad:
        return f"nodrift: no series {', '.join(bad)} (the series: {', '.join(names)})."
    if nd and str(cs) not in ("3", "pre"):
        return "nodrift holds a drift of case 3 (case=3 or case=\"pre\"); cases 1 and 2 have none."
    refuse, warn, facts = vec.checks(s, mixed=mixed)
    if refuse:
        s.guion.add("C0", "prepare_vec", {"purpose": pur, "mixed": mixed},
                    "refused: " + " | ".join(refuse))
        return ("# The cointegration question — the checks before the rank (C0)\n\n"
                "REFUSED, with the reasons:\n" + "\n".join(f"- {r}" for r in refuse)
                + ("\n\nWarnings:\n" + "\n".join(f"- {w}" for w in warn) if warn else ""))
    i0 = facts["i0"]
    order = [n for n in names if n not in i0] + i0
    p_ar, per = vec.p_rule(s.series)
    p_ml = None
    if s.canonical:
        p_ml = max(1, int(s.canonical.get("p_tb") or s.canonical.get("p") or 1))
    p_use = int(p) or (p_ml if (s.route == "V" and p_ml) or (p_ml and p_ml > p_ar) else p_ar)
    s.purpose = pur
    s.vec_spec = {"p": p_use, "q": int(q), "case": str(cs), "nodrift": nd, "order": order,
                  "mixed": bool(mixed), "i0": i0}
    s.guion.add("N1c", "prepare_vec", {"purpose": pur},
                f"{len(facts['i1'])} series with d = 1"
                + (f", {len(i0)} with d = 0 (mixed)" if i0 else "")
                + "; the rank will be tested", f"purpose: {pur}")
    s.guion.add("C0", "prepare_vec", {"p": p_use, "q": int(q), "case": str(cs),
                                      "nodrift": ", ".join(nd), "mixed": mixed},
                f"order {', '.join(order)}; " + ("; ".join(warn) if warn else "no warnings"))
    L = ["# The cointegration question (N1c) and the VEC's specification (C0)", "",
         f"PURPOSE, recorded: **{pur}** — at the yardstick (C8) the comparison with the "
         "univariates is " + ("a VETO." if pur == "forecast" else
                              "a CAVEAT, reported beside the long-run claim, not a veto."), "",
         "## 1 · TABLE", "", "```",
         f"  {'series':<14}{'d':>3}{'D':>3}  {'p rule (AR in nabla + 1)':>26}  block"]
    for x in s.series:
        blk = "Y1 (I(0): r >= its count)" if x.name in i0 else "nabla Y2 / Y1 by the rank"
        L.append(f"  {x.name:<14}{facts['d'][x.name]:>3}{facts['D'][x.name]:>3}  "
                 f"{per[x.name]:>26}  {blk}")
    L += ["",
          f"  p = {p_use}" + (" (as given)" if p else
                              f" (proposed: the AR rule gives {p_ar}"
                              + (f", Tiao and Box's M(l) on the levels {p_ml}" if p_ml else "")
                              + ")"),
          f"  q = {int(q)}; {vec.CASE_TEXT[str(cs)]}"
          + (f"; drift held at 0: {', '.join(nd)}" if nd else ""),
          f"  drvec's order for the rank test: {', '.join(order)}",
          f"  sample: {facts.get('nobs', '?')} observations"
          + (f", {facts['window']}" if facts.get("window") else ""),
          "```", "", "## 2 · WHAT IT SHOWS", ""]
    L.append("The rank is tested on these files as they are: drvec reads each file's "
             "series, calendar, Box-Cox, rescaling, deterministic terms and mean flag — "
             "not its ARMA (the bridge to the univariate models is the gate, N1).")
    L.append("p is drvec's AR order on (nabla Y2, W): with r = 0 the effective order on "
             "nabla Y is p - 1. Over-fitting p costs the rank test power; the last Gamma "
             "of the adopted fit is the check.")
    if str(cs) == "pre":
        L.append("case pre: the drift of each series is what its univariate model said "
                 "(a file without a mean holds it at zero). No asymptotic table exists for "
                 "it: the bootstrap is the only calibration.")
    if i0:
        L.append(f"THE MIXED CASE: {', '.join(i0)} is I(0), a stationary relation by itself "
                 f"(beta = its unit vector), so r >= {len(i0)}. drvec's VEC contains the "
                 "ladder's mixed-d model as B2 = 0 (test_restriction fixb2=0 tests it).")
    for w in warn:
        L.append(f"WARNING: {w}")
    L += ["", "## 4 · DECISION — alternatives", "",
          f"**A)** the rank, by parametric bootstrap (B = {vec.B_DEFAULT}; 999 when a 1 % "
          f"verdict matters; a JOB)\n   `rank_test(name=\"{name}\", B={vec.B_DEFAULT})`",
          f"**B)** another p, q or case first\n   `prepare_vec(name=\"{name}\", "
          f"purpose=\"{pur}\", p=..., case=\"2\")`",
          f"**C)** decline the question: the univariates' differences, the VARMA on "
          f"drvarma's ladder (N2)\n   `identify_cross(name=\"{name}\")`",
          "", "⏸ **Your decision.** (guided lane: I do not go on until you say)"]
    return "\n".join(L)


# --------------------------------------------------------------------------- #
#  C1: the rank, a job                                                         #
# --------------------------------------------------------------------------- #

def _rank_result_text(s, jid, res, st):
    txt, r_hat = vec.rank_report(res, s.name if s else "", st.get("folder"),
                                 _prov_text(st, res))
    if s is not None and not any(e.tool == "rank_test" and e.args.get("job") == jid
                                 and e.node == "C1" and "final" in e.evidence
                                 for e in s.guion.entries):
        comps = "; ".join(f"r={c['h0']}: LR {c['lr']:.2f}, 95% {c['cv'][1]:.2f}, "
                          f"p {c['pvalue']:.3f}" for c in res["comparisons"] if c["cv"])
        s.guion.add("C1", "rank_test", {"job": jid, "B": res["B"], "p": res["p"],
                                        "case": res["case"]},
                    f"final: {comps}; proposed r-hat {r_hat}", prov=_job_prov(st, res))
    return txt


@mcp.tool()
def rank_test(name: str, B: int = 499, multistart: int = 0, seed: int = 0,
              wait: float = WAIT) -> str:
    """C1 — The cointegration rank, by PARAMETRIC BOOTSTRAP (drvec's sequential
    exact-LR test r -> r + 1, r = 0..M-2): THE ONLY WAY TO A RANK in sima. The
    bootstrap decides; the asymptotic table (cases 1 and 2 only) is shown as
    orientation and is never the verdict. Reads the critical values, not the
    p-value; proposes r-hat and never adopts it.

    A JOB (sima.jobs): it runs detached, at most cores - 1 at once, on drvec C
    when its binary is there (drvec's engine="auto"; the engine is in the
    result's provenance), cached by content: the same files, spec, B, engine
    and versions return the stored result at once. It waits up to `wait`
    seconds (about 20) and then returns the job id with its progress
    ("replication k of B, comparison r -> r + 1"); job_status/job_result
    follow it. Never a partial result as final.

    Uses prepare_vec's specification. `B`: 499 by default, 999 when a 1 %
    verdict matters; below 199 the result is labelled an exploration.
    `multistart`: more starts in every fit. `seed`: 0 is the C's (987654321);
    another seed is a MONTE CARLO CHECK of an edge-of-5 % verdict (always on
    the Python engine), never the default."""
    s, err = _session(name)
    if err:
        return err
    if not s.vec_spec:
        return f'Specify the VEC first: prepare_vec(name="{name}", purpose="...").'
    if int(B) < 1:
        return "B must be at least 1 (499 by default): the rank needs the bootstrap."
    spec = s.vec_spec
    args = vec.rank_args(spec, B, multistart)
    files = _spec_files(s, spec["order"])
    try:
        jid, state = jobs.submit("rank_test", args, files, seed=int(seed) or None,
                                 label=f"rank test B={B} p={spec['p']} case {spec['case']}",
                                 session=name)
    except Exception as e:                                   # noqa: BLE001
        return f"The rank test could not be submitted: {e}"
    s.rank_jobs.setdefault(_rank_spec(spec), [])
    if jid not in s.rank_jobs[_rank_spec(spec)]:
        s.rank_jobs[_rank_spec(spec)].append(jid)
    s.guion.add("C1", "rank_test", {"job": jid, "B": int(B), "p": spec["p"],
                                    "case": spec["case"], "seed": int(seed) or None},
                f"job {state}", prov=_job_prov(jobs.status(jid)))
    st = jobs.wait(jid, 0 if state == "cached" else float(wait))
    if st["status"] == "done":
        return _rank_result_text(s, jid, jobs.result(jid), st)
    if st["status"] in ("failed", "cancelled"):
        return f"The rank test {st['status']}: {st.get('error') or ''} (folder {st['folder']})."
    return _job_text(jid, state, st, "The rank test", f'rank_test(name="{name}", B={B})')


# --------------------------------------------------------------------------- #
#  the job tools                                                               #
# --------------------------------------------------------------------------- #

@mcp.tool()
def job_status(job_id: str) -> str:
    """A job's state — queued, running, done, failed or cancelled — its progress
    ("replication k of B, comparison r -> r + 1, ok/simfail/fitfail so far"
    for a rank test; the replications for the IRF bands; the cells for a sweep),
    the elapsed time and the rate. Never a provisional number: a finished
    comparison is said finished, an unfinished one shows its counts only. The
    result itself comes from job_result once the job is done. Jobs survive the
    server: an id from an earlier conversation still answers here."""
    try:
        st = jobs.status(job_id.strip())
    except jobs.JobError as e:
        return str(e)
    eng = st.get("engine") or ["?", "?"]
    out = [f"job `{st['id']}` — {st['tool']}" + (f" ({st['label']})" if st["label"] else ""),
           f"status: {st['status'].upper()}; engine {eng[0]} {eng[1] if len(eng) > 1 else ''};"
           f" slots {st['slots']}; folder {st['folder']}"]
    if st["status"] in ("running", "queued", "done"):
        out += ["progress:", jobs.progress_text(st)]
    if st["status"] == "done":
        out.append(f'Finished: job_result("{st["id"]}") gives the result.')
    if st["status"] == "queued":
        out.append(f"Waiting for a free slot (at most {jobs.budget()} at once: the cores "
                   "less one, counted with drvec's workers).")
    if st.get("error"):
        out.append(f"error: {st['error']}")
    return "\n".join(out)


@mcp.tool()
def job_result(job_id: str) -> str:
    """The FINAL result of a finished job, with its report: a rank test's table
    and proposed rank (recorded at C1), the IRF bands (then used by
    impulse_response and the plots), a sweep cell. A job that is not finished
    has no result: this tool says so and returns nothing partial — a decision
    waits for it (the autonomous lane does not decide a node before)."""
    jid = job_id.strip()
    try:
        st = jobs.status(jid)
        res = jobs.result(jid)
    except jobs.JobError as e:
        return f"{e}. job_status(\"{jid}\") shows its progress."
    s = None
    if st.get("session"):
        s, _e = _session(st["session"])
    if res.get("tool") == "rank_test":
        return _rank_result_text(s, jid, res, st)
    if res.get("tool") == "irf_bands":
        if s is not None:
            s.guion.add("C6", "irf_bands", {"job": jid, "N": res["N"]},
                        f"final: {res['nok']} ok of {res['N']}, K = {res['K']}",
                        prov=_job_prov(st, res), kind="VEC")
        return (f"IRF BANDS (job {jid}): {res['nok']} of {res['N']} replications ok "
                f"({res['nfail']} failed), responses to k = {res['K']}. "
                "impulse_response, variance_decomposition and their plots now draw them.\n"
                + _prov_text(st, res))
    if res.get("tool") == "fit_cell":
        return (f"SWEEP CELL (job {jid}): p = {res['p']}, case {res['case']}"
                + (f", estwin {res['estwin']}" if res.get("estwin") else "")
                + f": logL {res['loglik']:.4f}, {res['npar']} parameters, criterion "
                f"{res['termcode']}.\n" + _prov_text(st, res))
    return json.dumps(res, indent=1)[:4000]


@mcp.tool()
def job_cancel(job_id: str) -> str:
    """Cancel a job: a queued one leaves the queue; a running one has its whole
    process tree killed (the runner, drvec C or the Python pool) and its folder
    marked cancelled, with no result written. A finished job is not touched.
    The same call later starts it again from the beginning (a cancelled run
    leaves nothing to resume)."""
    try:
        st = jobs.cancel(job_id.strip())
    except jobs.JobError as e:
        return str(e)
    return f"job `{job_id.strip()}`: {st}."


@mcp.tool(name="jobs")
def jobs_list(name: str = "") -> str:
    """Every job sima knows on this machine (the registry, ~/.sima/jobs or
    SIMA_JOBS_HOME): id, tool, status, label and progress, the running and
    queued first. `name` keeps only one session's. Jobs outlive the server
    and the conversation; their folders (sima_jobs/<id>/, next to the first
    file) hold the engine's files and the result."""
    out = [f"JOBS (at most {jobs.budget()} slots at once):"]
    for st in jobs.all_jobs():
        if name and st.get("session") != name:
            continue
        out.append(f"  {st['id']}  {st['status']:<9} {st['tool']:<10} {st['label']}")
        if st["status"] in ("running", "queued"):
            out.append(jobs.progress_text(st))
    if len(out) == 1:
        out.append("  (none)")
    return "\n".join(out)



# --------------------------------------------------------------------------- #
#  C2: the adopted VEC                                                         #
# --------------------------------------------------------------------------- #

def _finished_rank(s, spec):
    """The finished rank tests of this spec in this session: [(jid, result)],
    largest B first; and the ids still running."""
    done, running = [], []
    for jid in s.rank_jobs.get(_rank_spec(spec), []):
        try:
            st = jobs.status(jid)
        except jobs.JobError:
            continue
        if st["status"] == "done":
            done.append((jid, jobs.result(jid), st))
        elif st["status"] in ("queued", "running"):
            running.append(jid)
    done.sort(key=lambda t: -t[1]["B"])
    return done, running


@mcp.tool()
def estimate_vec(name: str, r: int, normalise_on: str = "", theory: str = "",
                 multistart: int = 0) -> str:
    """C2 — The adopted VEC at rank r (drvec.fit with -fdhess: the standard
    errors from the Hessian at the optimum). REFUSES without a FINISHED
    rank_test for the same specification (p, q, case, drifts, files), unless
    the analyst adopts r on THEORY: `theory` says why, and it is written in
    the guion as such, with the bootstrap's numbers beside it when they exist.
    A rank other than the bootstrap's proposal needs `theory` too. r = 0 is
    the VARMA in differences (drvarma, N2); r = M is not a VEC.

    THE ROLES are asked for: `normalise_on` names the r series beta is
    normalised on (the Y1 block); drvec's order is the others in the
    session's order, then these. That order is also the Cholesky order of the
    level responses, so another normalisation is ANOTHER FIT (this tool
    again), never a reorder. Default: the last r of prepare_vec's order (the
    I(0) series in the mixed case).

    Reports drvec's .out blocks verbatim (parameters, the VEC's matrices, the
    normalisation share, the residual diagnostics), alpha read from the matrix
    (Johansen's sign), the canonical weights beside beta-hat, and the
    optimiser's stopping criterion: a fit that stopped on a ridge (E1's
    2 1 1 -case 2) is declared NOT A DEMONSTRATED MAXIMUM, with `multistart`
    and a lower q offered. The .out's Wald tests are not citable (they depend
    on the normalisation): restrictions go by LR (test_restriction)."""
    s, err = _session(name)
    if err:
        return err
    spec = s.vec_spec
    if not spec:
        return f'Specify the VEC first: prepare_vec(name="{name}", purpose="...").'
    M = len(spec["order"])
    r = int(r)
    if r == 0:
        return ("r = 0 is no VEC: the univariates' differences are right jointly. The VARMA "
                f'in differences is drvarma\'s ladder, in this session: identify_cross(name="{name}").')
    if not 0 < r < M:
        return (f"r must be in 1..{M - 1}: drvec fits r <= M - 1; r = M is a stationary "
                "VARMA in levels (route V with d = 0, or art), not a VEC.")
    done, running = _finished_rank(s, spec)
    th = theory.strip()
    if done:
        jid, res, st = done[0]
        r_hat, why, tie = vec.propose_rank(res)
        rank_note = (f"rank_test job {jid} (B = {res['B']}): proposed r-hat "
                     f"{r_hat} — {why}")
        if r_hat != r and not th:
            return (f"The bootstrap proposes r = {r_hat} ({why}), not r = {r}. A rank against "
                    "the bootstrap is the analyst's, on THEORY: give `theory` (why), and it is "
                    "written in the guion as such, beside these numbers."
                    + (f" (A tie at r = {', '.join(map(str, tie))}: estimating both ranks is "
                       "the rule; say so in theory.)" if tie else ""))
        if r_hat != r:
            rank_note += f". ADOPTED r = {r} ON THEORY, against it: {th}"
    else:
        if not th:
            return ("No finished rank test for this specification"
                    + (f" (job {', '.join(running)} is still running: job_status)" if running
                       else "") + ". The rank is decided by the parametric bootstrap: "
                    f'rank_test(name="{name}"). Adopting r without it is a claim on THEORY: '
                    "give `theory` (why), and it is written in the guion as such.")
        rank_note = f"NO BOOTSTRAP: r = {r} ADOPTED ON THEORY — {th}"
    nrm = vec.names_list(normalise_on)
    if nrm:
        bad = [n for n in nrm if n not in spec["order"]]
        if bad or len(nrm) != r or len(set(nrm)) != r:
            return (f"normalise_on: give {r} distinct series of {', '.join(spec['order'])}"
                    + (f" ({', '.join(bad)} is not one)" if bad else "") + ".")
    else:
        nrm = spec["order"][M - r:]
    order = vec.drvec_order(spec["order"], nrm)
    if spec["i0"] and not set(spec["i0"]) <= set(nrm):
        return (f"The mixed case: {', '.join(spec['i0'])} is I(0) and must be in the Y1 block "
                f"(normalise_on), so r >= {len(spec['i0'])}.")
    key = vec.vec_key(order, spec["p"], spec["q"], r, spec["case"], spec["nodrift"],
                      None, multistart)
    try:
        if key in s.vec_fits:
            vf = s.vec_fits[key]
        else:
            f = vec.fit_vec(_spec_files(s, order), order, spec["p"], spec["q"], r,
                            spec["case"], spec["nodrift"], None, multistart)
            vf = vec.VecFit(key, f, _spec_files(s, order), order, spec["p"], spec["q"], r,
                            spec["case"], spec["nodrift"], {}, int(multistart),
                            done[0][0] if done else "", th)
            s.vec_fits[key] = vf
    except Exception as e:                                   # noqa: BLE001
        s.guion.add("C2", "estimate_vec", {"r": r, "normalise_on": ", ".join(nrm)},
                    f"failed: {e}", kind="VEC")
        return f"The VEC could not be estimated: {e}"
    s.vec_current = key
    s.kind = "VEC"
    from .provenance import of_drvec
    prov = {"drvec_provenance": of_drvec(vf.fit.provenance)}
    if done:
        prov.update({k: v for k, v in _job_prov(done[0][2]).items() if k != "seed"})
    s.guion.add("C2", "estimate_vec", {"r": r, "normalise_on": ", ".join(nrm),
                                       "p": spec["p"], "q": spec["q"], "case": spec["case"],
                                       "multistart": int(multistart)},
                f"logL {vf.fit.loglik:.4f}, {vf.fit.npar} parameters, criterion "
                f"{vf.fit.termcode}; {rank_note}",
                f"r = {r} on theory: {th}" if (th and (not done or "ON THEORY" in rank_note))
                else "", prov=prov, kind="VEC")
    canon = vec.canonical_beside_beta(s.canonical, order, vf) if s.canonical else ""
    from .provenance import base
    p = base()
    p.update(prov)
    return vec.estimate_report(vf, name, rank_note, canon, _prov_line(p), s.purpose)


# --------------------------------------------------------------------------- #
#  C3: restrictions, by LR                                                     #
# --------------------------------------------------------------------------- #

def _matrix(text, M):
    t = text.strip()
    if os.path.exists(os.path.expanduser(t)):
        import drvec.api as _api                              # drvec's own reader
        return [list(r) for r in _api.load_alpha_A(os.path.expanduser(t), M)]
    A = json.loads(t)
    return [[float(v) for v in row] for row in A]


@mcp.tool()
def test_restriction(name: str, weakex: str = "", alpha: str = "", fixb2: str = "",
                     fixb2row: str = "", gamma: str = "", adopt: bool = False) -> str:
    """C3 — A restriction on alpha, beta or Gamma of the current VEC, tested by
    LIKELIHOOD RATIO (never by the .out's Wald, which depends on the
    normalisation): LR, its degrees of freedom and chi2 p-value, both logLs.

    `weakex`: a series' name — weak exogeneity, its row of alpha at zero ("who
    corrects": it does not adjust to the equilibrium). `alpha`: alpha = A psi,
    A as a JSON matrix (rows in drvec's order, as estimate_vec prints it) or a
    file in drvec's format ("M sa", then M rows) — jointly for several
    series. `fixb2`: every entry of B2 held at this VALUE (required: without
    one drvec holds B2 at its static OLS value, which is not a test); fixb2=0
    in the mixed case is the ladder's model. `fixb2row`: rows of B2 held,
    "NAME=value, NAME2=value". weakex/alpha combine with fixb2row (the joint
    LR). `gamma`: NO FEEDBACK in the short run, "R30,R3 <- R0T" (the equations,
    then the regressors; "A <- B; C <- D" for several): Gamma_k[eq][reg] = 0 at
    every lag (drvec -gzero; p >= 2, q = 0). With weakex/alpha on the same
    inputs it is the CONDITIONAL model's joint test (weak exogeneity and no
    feedback, Johansen 1992): when it holds, the report offers mtram with the
    same files and the roles. gamma does not combine with fixb2/fixb2row.

    drvec fits the free model of these LRs as the C does (one est() from a
    cold start for alpha and weakex; no ladder for fixb2row), so its free logL
    can be below the adopted VEC's and the LR understated: sima takes the BEST
    FREE FIT it knows, says which, and shows both when they differ. `adopt`:
    the restricted VEC becomes the current model. Not available (drvec):
    restrictions on one cointegrating vector, a bootstrap of this LR, a rank
    under a restriction."""
    s, err = _session(name)
    if err:
        return err
    try:
        base = _need_vec(s)
    except KeyError as e:
        return str(e)
    if base.restriction:
        return ("The current VEC is itself restricted: test against the free one — "
                f'estimate_vec(name="{name}", r={base.r}) makes it current again (cached).')
    restr, calls, labels = {}, [], []
    order = base.order
    s_ = base.M - base.r
    if weakex.strip():
        nm = weakex.strip()
        if nm not in order:
            return f"weakex: no series {nm} ({', '.join(order)})."
        restr["weakex"] = nm
        calls.append(f'weakex="{nm}"')
        labels.append(f"weak exogeneity of {nm} (its alpha row = 0)")
    if alpha.strip():
        if restr.get("weakex"):
            return "weakex and alpha are one restriction each on alpha: give one (alpha = A psi covers both)."
        try:
            restr["alpha"] = _matrix(alpha, base.M)
        except Exception as e:                               # noqa: BLE001
            return f"alpha: {e}"
        calls.append(f"alpha='{alpha.strip()}'")
        labels.append("alpha = A psi")
    if fixb2.strip():
        if fixb2.strip().lower() in ("true", "ols", "yes"):
            return ("fixb2 needs a VALUE: without one drvec holds B2 at its static OLS "
                    "estimate, a data-chosen restriction, which is not a test.")
        try:
            restr["fixb2"] = float(fixb2)
        except ValueError:
            return f"fixb2: '{fixb2}' is not a number."
        restr["_df"] = s_ * base.r
        calls.append(f'fixb2="{fixb2.strip()}"')
        labels.append(f"every entry of B2 = {restr['fixb2']:g}")
    if fixb2row.strip():
        if "fixb2" in restr:
            return "fixb2row holds rows of B2; fixb2 holds all of it: give one."
        rows = {}
        for tok in fixb2row.split(","):
            if "=" not in tok:
                return f"fixb2row: 'NAME=value', got {tok.strip()!r}."
            nm, v = (t.strip() for t in tok.split("=", 1))
            if nm not in base.y2():
                return (f"fixb2row: {nm} is not in the nabla Y2 block "
                        f"({', '.join(base.y2())}): B2's rows are those series.")
            rows[nm] = float(v)
        restr["fixb2row"] = rows
        calls.append(f'fixb2row="{fixb2row.strip()}"')
        labels.append("rows of B2 held: " + ", ".join(f"{k} = {v:g}" for k, v in rows.items()))
    if gamma.strip():
        if "fixb2" in restr or "fixb2row" in restr:
            return ("gamma does not combine with fixb2/fixb2row (drvec refuses it): test "
                    "them in separate calls.")
        if base.p < 2:
            return "gamma: at p = 1 there is no Gamma (drvec's p is the AR order on (nabla Y2, W))."
        if base.q > 0:
            return "gamma: drvec holds entries of Gamma only with q = 0 (the MA walks do not carry the mask yet)."
        try:
            restr["gamma"] = vec.parse_gamma(gamma, order)
        except ValueError as e:
            return str(e)
        calls.append(f'gamma="{gamma.strip()}"')
        labels.append("no feedback: " + ", ".join(f"{e} <- {g}" for e, g in restr["gamma"])
                      + f" held at 0 for k = 1..{base.p - 1}")
    if not restr:
        return "Give a restriction: weakex, alpha, fixb2 (a value), fixb2row or gamma."
    restr["_call"] = ", ".join(calls)
    clean = {k: v for k, v in restr.items() if not k.startswith("_")}
    key = vec.vec_key(order, base.p, base.q, base.r, base.case, base.nodrift, clean,
                      base.multistart)
    try:
        if key in s.vec_fits:
            rv = s.vec_fits[key]
        else:
            f = vec.fit_vec(base.files, order, base.p, base.q, base.r, base.case,
                            base.nodrift, clean, base.multistart)
            rv = vec.VecFit(key, f, base.files, order, base.p, base.q, base.r, base.case,
                            base.nodrift, clean, base.multistart, base.rank_job, base.theory)
            s.vec_fits[key] = rv
    except Exception as e:                                   # noqa: BLE001
        return f"drvec refused or failed: {e}"
    label = "; ".join(labels)
    from .provenance import base as _base, of_drvec
    pv = _base()
    pv["drvec_provenance"] = of_drvec(rv.fit.provenance)
    txt, f = vec.restriction_report(base, rv.fit, restr, name, label, _prov_line(pv))
    s.guion.add("C3", "test_restriction", {"restriction": label, "adopt": adopt},
                f"LR {f['lr']:.2f} df {f['df']} p {f['p']:.4f} (free logL {f['ll_free']:.4f}"
                + (f"; drvec's free {f['ll_free_drvec']:.4f}" if f["ll_free_drvec"] is not None
                   and abs(f["ll_free_drvec"] - f["ll_free"]) > 1e-6 else "") + ")",
                prov={"drvec_provenance": pv["drvec_provenance"]}, kind="VEC")
    if adopt:
        s.vec_current = key
        txt += f"\n\nADOPTED: the restricted VEC ({label}) is now the current model."
    return txt


# --------------------------------------------------------------------------- #
#  C4: exogenous inputs                                                        #
# --------------------------------------------------------------------------- #

@mcp.tool()
def add_exogenous(name: str, series: str = "", inputs: str = "", links: str = "",
                  adopt: bool = False) -> str:
    """C4 — Exogenous inputs to the current VEC, dispatched by their order of
    integration, as in drtran. The VEC without inputs is the base, and the
    LR against it is the test.

    An input of the SAME order (I(1), a series of the system): `series`
    names it; it stays in the system with its alpha row at zero and none of
    the others' short run (drvec -xsys: STRONG exogeneity, the LR against the
    free VEC). It cannot be in the Y1 block, and drvec needs q = 0.

    An input of ANOTHER order (an I(0) input on I(1) outputs): `inputs` are
    its fue files (a JSON list or comma-separated; their .pre stays frozen)
    and `links` the network, "OUT <- IN b r s; OUT2 <- IN b r s" (r <= 2): it
    is subtracted in levels (drvec -xpre/-xlink). drvec fits the VEC without
    the inputs first; with omega = 0 the bridge must reproduce it. Refused by
    drvec (inherited): a rank test with inputs (the rank is C1's, without
    them), -xlink with forecasts or bootstraps, -xsys with q > 0 or with a
    restriction on alpha. `adopt` makes the fit with inputs current."""
    s, err = _session(name)
    if err:
        return err
    try:
        base = _need_vec(s)
    except KeyError as e:
        return str(e)
    if base.restriction:
        return "Add inputs to the free VEC: estimate_vec makes it current again (cached)."
    restr, label = {}, ""
    if series.strip():
        xs = vec.names_list(series)
        bad = [n for n in xs if n not in base.order]
        if bad:
            return f"series: {', '.join(bad)} is not in the system ({', '.join(base.order)})."
        inY1 = [n for n in xs if n in base.y1()]
        if inY1:
            return (f"{', '.join(inY1)} is in the Y1 block (beta is normalised on it): an input "
                    "does not adjust, so it cannot be the series a relation is solved for. "
                    "Re-estimate with another normalise_on first.")
        restr["xsys"] = xs
        label = f"{', '.join(xs)} as a strongly exogenous input in the system (-xsys)"
    elif inputs.strip():
        from .mcp_server import _paths
        paths = [os.path.abspath(os.path.expanduser(p)) for p in _paths(inputs)]
        try:
            net = vec.parse_links(links)
        except ValueError as e:
            return str(e)
        try:
            from drvarma.ladder import load
            ds = {x.name: int(x.model.d or 0) for x in load(paths)}
        except Exception as e:                               # noqa: BLE001
            return f"The inputs could not be read: {e}"
        same = [n for n, d in ds.items() if d >= 1]
        note = ""
        if same:
            note = (f"NOTE: {', '.join(same)} is I(1), of the system's order: the in-VEC "
                    "version is -xsys (load it into the session with the others and use "
                    "`series`). Here it is subtracted in levels as given.")
        import hashlib
        text = "\n".join(net) + "\n"
        d = os.path.join(os.path.dirname(os.path.abspath(base.files[0])), "sima_jobs")
        os.makedirs(d, exist_ok=True)
        netpath = os.path.join(d, f"xlink_{hashlib.sha256(text.encode()).hexdigest()[:12]}.txt")
        with open(netpath, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        restr["xpre"] = paths
        restr["xlink"] = netpath
        label = "inputs in levels (-xpre/-xlink): " + "; ".join(net) + (f". {note}" if note else "")
    else:
        return "Give `series` (an input of the system's order) or `inputs` with `links`."
    key = vec.vec_key(base.order, base.p, base.q, base.r, base.case, base.nodrift,
                      {k: (tuple(v) if isinstance(v, list) else v) for k, v in restr.items()},
                      base.multistart)
    try:
        if key in s.vec_fits:
            rv = s.vec_fits[key]
        else:
            f = vec.fit_vec(base.files, base.order, base.p, base.q, base.r, base.case,
                            base.nodrift, restr, base.multistart)
            rv = vec.VecFit(key, f, base.files, base.order, base.p, base.q, base.r, base.case,
                            base.nodrift, restr, base.multistart, base.rank_job, base.theory)
            s.vec_fits[key] = rv
    except Exception as e:                                   # noqa: BLE001
        return f"drvec refused or failed: {e}"
    f = rv.fit
    rl = f.restriction_lr
    L = [f"# Exogenous inputs (C4) — {label}", "", "```"]
    if rl is not None and rl.kind == "xlink":
        L.append(f"the VEC without the inputs: logL {rl.ll_restricted:.4f} (the adopted VEC: "
                 f"{base.fit.loglik:.4f})")
        if rl.ll_bridge is not None:
            L.append(f"the bridge (omega = 0 at that optimum): logL {rl.ll_bridge:.4f}, "
                     f"difference {rl.ll_bridge - rl.ll_restricted:+.2e}")
        L.append(f"with the inputs: logL {rl.ll_free:.4f}; LR = {rl.lr:.4f}, df {rl.df}, "
                 f"p {rl.pvalue:.4f}")
    elif rl is not None:
        L.append(f"the free VEC: logL {rl.ll_free:.4f}; with the input restricted: "
                 f"{rl.ll_restricted:.4f}; LR (strong exogeneity) = {rl.lr:.4f}, df {rl.df}, "
                 f"p {rl.pvalue:.4f}")
    else:
        L.append(f"logL {f.loglik:.4f} (drvec printed no LR)")
    L += ["```", ""]
    if rl is not None:
        L.append(("The inputs " if rl.kind == "xlink" else "Strong exogeneity ")
                 + ("are significant" if rl.pvalue < 0.05 and rl.kind == "xlink" else
                    "is rejected" if rl.pvalue < 0.05 else
                    "add nothing at 5 %" if rl.kind == "xlink" else "is not rejected at 5 %")
                 + f" (LR {rl.lr:.2f}, chi2({rl.df}), p {rl.pvalue:.4f}).")
        if rl.kind == "xlink" and rl.ll_bridge is not None and \
                abs(rl.ll_bridge - rl.ll_restricted) > 1e-6:
            L.append("WARNING: the bridge does not reproduce the VEC without inputs: the "
                     "LR is not against the model it claims to extend.")
    L += ["The rank stays C1's, tested without the inputs (drvec refuses a rank test "
          "with them).", "", "⏸ **Your decision.** (guided lane: I do not go on until you say)"]
    s.guion.add("C4", "add_exogenous", {"what": label, "adopt": adopt},
                (f"LR {rl.lr:.2f} df {rl.df} p {rl.pvalue:.4f}" if rl is not None
                 else f"logL {f.loglik:.4f}"), kind="VEC")
    if adopt:
        s.vec_current = key
        L.append("\nADOPTED: the VEC with these inputs is now the current model.")
    return "\n".join(L)


# --------------------------------------------------------------------------- #
#  C5: the long run                                                            #
# --------------------------------------------------------------------------- #

@mcp.tool()
def long_run(name: str, horizon: int = 0) -> str:
    """C5 — The long run of the current VEC, read: theta (beta normalised, with
    its sign: Y1 = theta' Y2 + a stationary error), and two half-lives, both
    computed by sima because drvec computes neither — the TEXTBOOK one,
    ln 0.5 / ln(1 - |alpha|) on the variable the relation is solved for
    (orientation: exact only for one relation with no short-run dynamics),
    and the MODEL's, the half-life of the equilibrium error beta'Y in the
    fitted model's own response (the same weights as the level IRF; its norm
    over the shocks, which does not depend on the Cholesky order). Then
    Gonzalo and Ng's permanent/transitory decomposition: alpha_perp (the
    common trends), the share of each level's forecast-error variance due to
    the permanent shocks, and the self-check that a transitory shock has no
    long-run effect. Point values: bands only through the bootstrap
    (irf_bands). `horizon`: how far the responses go (0: 60 periods, or 8
    years of seasonal data)."""
    s, err = _session(name)
    if err:
        return err
    try:
        vf = _need_vec(s)
    except KeyError as e:
        return str(e)
    freq = s.series[0].freq
    try:
        lr = vec.long_run(vf, int(horizon) or None, freq)
    except Exception as e:                                   # noqa: BLE001
        return f"The long run could not be computed: {e}"
    s.guion.add("C5", "long_run", {"horizon": lr["K"]},
                "; ".join(f"relation {t['relation']}: textbook "
                          + (f"{t['half_life']:.1f}" if t["half_life"] else "undefined")
                          for t in lr["textbook"]) + "; model "
                + ", ".join(str(m["half_life"]) for m in lr["model"]), kind="VEC")
    from .provenance import base
    return vec.long_run_report(vf, lr, name, freq, _prov_line(base()))


# --------------------------------------------------------------------------- #
#  C6: the IRF bands, a job                                                    #
# --------------------------------------------------------------------------- #

def _bands(s, vf):
    """The finished irf_bands of this VEC, or (None, why)."""
    jid = s.irf_jobs.get(vf.key)
    if not jid:
        return None, "no irf_bands job for this VEC"
    try:
        st = jobs.status(jid)
        if st["status"] != "done":
            return None, f"irf_bands job {jid} is {st['status']} (job_status)"
        return jobs.result(jid), None
    except jobs.JobError as e:
        return None, str(e)


@mcp.tool()
def irf_bands(name: str, N: int = 499, seed: int = 0, wait: float = WAIT) -> str:
    """C6 — Bands for the level responses and the FEVD of the current VEC, by
    PARAMETRIC BOOTSTRAP (drvec -irfboot N): N simulations of the fitted
    model, each REFITTED as the data were — same r, same restrictions, same
    ladder — and Efron's percentiles (90 % and 95 %). No delta method and no
    covariance Monte Carlo: the level responses are a long non-linear chain
    to the permanent effect, and a linearisation is what not to trust here.

    A JOB, like rank_test: detached, cached by content, on drvec C when its
    binary is there (the engine in the provenance); a short wait (`wait`
    seconds), then the job id. Once finished, impulse_response,
    variance_decomposition and their plots draw the bands. The bands are
    conditional on r, the restrictions and the orthogonalisation order (drvec's
    file order): reordering is a refit and a new job. The horizon is drvec's
    (10 lags when n < 40, else 20). `seed`: 0 is the C's; another is a Monte
    Carlo check (Python engine)."""
    s, err = _session(name)
    if err:
        return err
    try:
        vf = _need_vec(s)
    except KeyError as e:
        return str(e)
    if vf.restriction.get("xpre"):
        return "drvec refuses -irfboot with -xlink inputs (not yet in the C)."
    if int(N) < 20:
        return ("N must be at least 20: drvec computes no bands from fewer than 20 good "
                f"replications ({vec.B_DEFAULT} by default).")
    args = vec.fit_args(vf, N=int(N))
    try:
        jid, state = jobs.submit("irf_bands", args, vf.files, seed=int(seed) or None,
                                 extra_files=list(vf.restriction.get("xpre") or []),
                                 label=f"IRF bands N={N} r={vf.r}", session=name)
    except Exception as e:                                   # noqa: BLE001
        return f"The IRF bootstrap could not be submitted: {e}"
    s.irf_jobs[vf.key] = jid
    st = jobs.wait(jid, 0 if state == "cached" else float(wait))
    if st["status"] == "done":
        return getattr(job_result, "fn", job_result)(jid)
    if st["status"] in ("failed", "cancelled"):
        return f"The IRF bootstrap {st['status']}: {st.get('error') or ''}."
    return _job_text(jid, state, st, "The IRF bands", f'irf_bands(name="{name}", N={N})')


# --------------------------------------------------------------------------- #
#  C7: the sweep                                                               #
# --------------------------------------------------------------------------- #

def _ints(text):
    import re
    return [int(t) for t in re.findall(r"-?\d+", str(text or ""))]


@mcp.tool()
def sweep(name: str, p: str = "", case: str = "", estwin: str = "", B: int = 0,
          wait: float = WAIT) -> str:
    """C7 — Robustness: a grid of fits over the same files, one CACHED JOB per
    cell, around the current VEC (its r, restrictions and normalisation).
    `p`: AR orders, e.g. "1,2,3"; `case`: "2, 3, pre, trend" (trend, case
    4, for a single fit only); `estwin`: subsamples, rows 1..E of nabla Y
    ("60, 70, 80"; the recursive estimate). Empty: the current one.
    `B` > 0 adds a rank test per (p, case) cell, with its bootstrap (jobs
    too). The table — logL, parameters, the stopping criterion, theta and
    alpha per cell; r-hat for the rank cells — fills as the cells finish:
    call it again with the same grid (the cells are cached). It claims
    nothing beyond its cells: what it preserves is the list of what was run,
    and why, in the guion."""
    s, err = _session(name)
    if err:
        return err
    try:
        vf = _need_vec(s)
    except KeyError as e:
        return str(e)
    ps = _ints(p) or [vf.p]
    cases = vec.names_list(case) or [str(vf.case)]
    for c in cases:
        if c not in vec.CASES + ("trend",):
            return f"case: {c} is not one of 1, 2, 3, pre, trend."
    ews = _ints(estwin) or [0]
    cells = []
    for pp in ps:
        for c in cases:
            if c == "trend" and str(vf.case) not in ("3", "pre"):
                pass
            for e in ews:
                args = vec.fit_args(vf, p=int(pp), case=c, estwin=int(e))
                try:
                    jid, _st = jobs.submit("fit_cell", args, vf.files, bootstrap=False,
                                           label=f"sweep p={pp} case {c}"
                                           + (f" estwin {e}" if e else ""), session=name)
                except Exception as ex:                      # noqa: BLE001
                    return f"A cell could not be submitted: {ex}"
                cells.append(("fit", pp, c, e, jid))
            if B and c != "trend":
                spec = dict(s.vec_spec, p=int(pp), case=c)
                ra = vec.rank_args(spec, int(B))
                jid, _st = jobs.submit("rank_test", ra, _spec_files(s, spec["order"]),
                                       label=f"sweep rank p={pp} case {c} B={B}", session=name)
                s.rank_jobs.setdefault(_rank_spec(spec), [])
                if jid not in s.rank_jobs[_rank_spec(spec)]:
                    s.rank_jobs[_rank_spec(spec)].append(jid)
                cells.append(("rank", pp, c, 0, jid))
    import time
    t0 = time.time()
    while time.time() - t0 < float(wait):
        if all(jobs.status(c[4])["status"] in jobs.FINAL for c in cells):
            break
        time.sleep(0.5)
    L = [f"# Sweep (C7) around the VEC r = {vf.r} — {len(cells)} cell(s), one job each", "",
         "```", f"  {'cell':<26}{'status':<10}{'logL':>12}{'npar':>6}{'crit':>5}"
         "  theta / alpha  (or the rank)"]
    pend = []
    for kind, pp, c, e, jid in cells:
        st = jobs.status(jid)
        lab = f"p={pp} case {c}" + (f" estwin {e}" if e else "") + (" RANK" if kind == "rank" else "")
        if st["status"] != "done":
            L.append(f"  {lab:<26}{st['status']:<10}   job {jid}")
            pend.append(jid)
            continue
        res = jobs.result(jid)
        if kind == "rank":
            r_hat, why, _t = vec.propose_rank(res)
            L.append(f"  {lab:<26}{'done':<10}{'':>12}{'':>6}{'':>5}  r-hat {r_hat} (B = "
                     f"{res['B']})")
        else:
            th = np.asarray(res["theta"])
            al = np.asarray(res["alpha"])
            L.append(f"  {lab:<26}{'done':<10}{res['loglik']:>12.4f}{res['npar']:>6}"
                     f"{res['termcode']:>5}  theta " + " ".join(f"{v:+.3f}" for v in th.ravel())
                     + " | alpha " + " ".join(f"{v:+.3f}" for v in al.ravel()))
    L += ["```", ""]
    if any(e for _k, _p, _c, e, _j in cells):
        L.append("The estwin cells are fitted on fewer rows: their logL is not comparable "
                 "with the full sample's; read theta and alpha's stability.")
    L.append("Criterion: the optimiser's stopping rule (1, 2: the gradient or the step; "
             "3 or more: not a demonstrated maximum).")
    if pend:
        L.append(f"{len(pend)} cell(s) still running: call sweep again with the same grid, "
                 "or job_status. Nothing is read from an unfinished cell.")
    s.guion.add("C7", "sweep", {"p": ",".join(map(str, ps)), "case": ",".join(cases),
                                "estwin": ",".join(map(str, ews)), "B": int(B)},
                f"{len(cells)} cells, {len(cells) - len(pend)} finished", kind="VEC")
    return "\n".join(L)


# --------------------------------------------------------------------------- #
#  C1's figure                                                                 #
# --------------------------------------------------------------------------- #

@mcp.tool()
def plot_rank_bootstrap(name: str, job_id: str = "", path: str = "") -> list:
    """FIGURE — The rank test's bootstrap: for each comparison r -> r + 1, the
    histogram of the B bootstrap statistics LR*, the OBSERVED LR (solid), the
    bootstrap's 90/95/99 % critical values (dashed) and, for cases 1 and 2,
    the asymptotic 5 % value (dotted: orientation only). From the finished
    rank test of the current specification (the one with the largest B), or
    `job_id`'s. Read from the job's .boot file with drvec's own reader."""
    from drvec import c_engine
    from . import figures
    s, err = _session(name)
    if err:
        return [err]
    if job_id.strip():
        try:
            jid = job_id.strip()
            res, st = jobs.result(jid), jobs.status(jid)
        except jobs.JobError as e:
            return [str(e)]
    else:
        if not s.vec_spec:
            return ["No rank test: prepare_vec, then rank_test."]
        done, running = _finished_rank(s, s.vec_spec)
        if not done:
            return ["No finished rank test for this specification"
                    + (f" (running: {', '.join(running)})" if running else "") + "."]
        jid, res, st = done[0]
    if res.get("tool") != "rank_test":
        return [f"job {jid} is not a rank test."]
    boot = c_engine.read_boot(os.path.join(st["folder"], "rank.boot"))
    fig = figures.rank_bootstrap_figure(res["comparisons"], boot, res["names"])
    note = (f"Rank bootstrap (job {jid}, B = {res['B']}): "
            + "; ".join(f"r={c['h0']}: LR {c['lr']:.2f} vs 95% {c['cv'][1]:.2f}"
                        for c in res["comparisons"] if c["cv"]))
    return _figure(s, fig, "rankboot", path, note, node="C1")


# --------------------------------------------------------------------------- #
#  the final-stage tools on a VEC (called by the extended VARMA tools)         #
# --------------------------------------------------------------------------- #

def _pct_keys(pct):
    ks = sorted(pct, key=float)
    lo = next((k for k in ks if float(k) == 5.0), ks[1])
    hi = next((k for k in ks if float(k) == 95.0), ks[-2])
    return lo, hi


def irf_vec(s, H, bands=True):
    vf = s.vec_fits[s.vec_current]
    b, why = _bands(s, vf) if bands else (None, "bands=False")
    txt = vec.irf_report(vf, int(H), b, why)
    s.guion.add("C6", "impulse_response", {"horizon": H, "bands": b is not None},
                f"levels, drvec's order {', '.join(vf.order)}", kind="VEC")
    return txt


def fevd_vec(s, H, bands=True):
    vf = s.vec_fits[s.vec_current]
    b, why = _bands(s, vf) if bands else (None, "bands=False")
    txt = vec.fevd_report(vf, int(H), b, why)
    s.guion.add("C6", "variance_decomposition", {"horizon": H, "bands": b is not None},
                f"levels, drvec's order {', '.join(vf.order)}", kind="VEC")
    return txt


def forecast_vec(s, H):
    vf = s.vec_fits[s.vec_current]
    try:
        fc, dates = vec.forecast_vec(vf, int(H))
    except Exception as e:                                   # noqa: BLE001
        return f"Cannot forecast the VEC: {e}"
    s.guion.add("N6", "forecast", {"horizon": H, "model": f"VEC r={vf.r}"},
                f"{H} steps, drvarma's forecaster on the VEC in levels", kind="VEC")
    return vec.forecast_report(vf, fc, dates, s.series[0].freq)


def evaluate_vec(s, estwin, H):
    """C8 — the yardstick for the VEC: drvec's rolling-origin errors against the
    univariates (and the VARMA in differences, if one was estimated) on the
    same origins; the rule per the purpose recorded at N1c."""
    from . import evidence
    from .mcp_server import _ladder, _model_ladder, _yardstick_files
    vf = s.vec_fits[s.vec_current]
    if not estwin:
        return "Give estwin: the observations of the first series to estimate on."
    if vf.restriction.get("xpre"):
        return "drvec refuses -estwin with -xlink inputs: the yardstick needs the VEC without them."
    try:
        kw = vf.call_kw()
        import drvec
        f = drvec.fit(list(vf.files), vf.p, vf.q, vf.r, estwin=int(estwin) - 1,
                      forecast=int(H), **kw)
        vrows = vec.recursive_rows(f.recursive_text(), int(f.data.nobs_raw))
        origins = {o for o, *_r in vrows}
        freq = s.series[0].freq
        s0 = s.series[0]
        last = s0.date_of(s0.nobs_full)
        cand = vec.summary_on(vrows)
        Ld = _ladder(_yardstick_files(s) if s.route == "V" else s.files, 0, 0, True,
                     estwin=int(estwin))
        Ld.fit()
        rows, _sm = Ld.recursive(int(H))
        diag = vec.summary_on(vec.ladder_rows(rows, freq, last), origins)
        varma = None
        if s.current is not None and s.current in s.fits:
            Lv = _model_ladder(s, s.current, estwin=int(estwin))
            Lv.fit()
            rows, _sm = Lv.recursive(int(H))
            varma = vec.summary_on(vec.ladder_rows(rows, freq, last), origins)
    except Exception as e:                                   # noqa: BLE001
        return f"The evaluation failed: {e}"
    freq = s.series[0].freq
    hs = (list(range(1, min(H, 5) + 1)) if freq == 1 else
          sorted({1, max(1, freq // 2), freq, 2 * freq} & set(range(1, H + 1))) or [1, H])
    names = _names(s)
    label = f"VEC r={vf.r} VARMA({vf.p},{vf.q}) " + vec.CASE_TEXT[str(vf.case)].split(":")[0]
    txt, facts = evidence.evaluation_text(cand, diag, label, hs, names)
    txt = (txt.replace("The VARMA has the lower RMSE", "The VEC has the lower RMSE")
           .replace("keep the VARMA", "keep the VEC"))
    mism = [k for k in diag if k in cand and diag[k]["n"] != cand[k]["n"]]
    L = ["# The yardstick for the VEC (C8)", "",
         "The VEC fitted on the first rows (drvec -estwin: rows 1..estwin - 1 of nabla Y, "
         "the same observations as the univariates' first estwin), its parameters held, "
         "forecasts from every origin to the end (drvec -f), errors in each series' own "
         "units; the univariates (the diagonal system) on the same window and the SAME "
         f"origins: drvec's, {len(origins)} of them (an origin is kept when all {H} steps "
         "can be checked).",
         "", "```", txt, "```"]
    if mism:
        L.append(f"NOTE: the origins differ in {len(mism)} cells (n): read with care.")
    if varma is not None:
        vt, vfacts = evidence.evaluation_text(cand, varma, label, hs, names)
        vt = vt.replace("against the univariates (diagonal system),",
                        "against the VARMA in differences (the session's current VARMA),")
        vt = vt.replace("RMSE uni", "RMSE varma").replace("MAPE uni", "MAPE varma")
        L += ["", "Against the VARMA in differences estimated in this session:", "```",
              vt.split("\n\n")[0], "```",
              f"The VEC has the lower RMSE in {vfacts['wins']} of {vfacts['cells']} cells "
              "against it."]
    L += ["", vec.yardstick_rule(s.purpose, facts["wins"], facts["cells"])]
    s.guion.add("C8", "evaluate", {"estwin": estwin, "horizon": H, "purpose": s.purpose},
                f"VEC lower RMSE in {facts['wins']} of {facts['cells']} cells against the "
                f"univariates ({'veto' if s.purpose == 'forecast' else 'caveat'})", kind="VEC")
    return "\n".join(L)


def plot_irf_vec(s, H, bands, path, fevd=False):
    from . import figures
    vf = s.vec_fits[s.vec_current]
    b, why = _bands(s, vf) if bands else (None, "bands=False")
    G = vf.fit.fevd(int(H) - 1) if fevd else vf.fit.level_irf(int(H))
    lo = hi = None
    if b:
        pct = b["fevd_pct" if fevd else "irf_pct"]
        kl, kh = _pct_keys(pct)
        lo, hi = np.asarray(pct[kl]), np.asarray(pct[kh])
    fig = figures.vec_irf_figure(G, vf.order, s.series[0].freq, lo, hi,
                                 b["nok"] if b else 0, fevd=fevd)
    note = ("VEC: " + ("variance decomposition of the levels" if fevd else
                       "impulse responses of the levels")
            + (f" (no band: {why})" if why else " (90 % bootstrap band)"))
    return _figure(s, fig, "fevd" if fevd else "irf", path, note, node="C6")


def plot_ccf_vec(s, nlags, path):
    from . import figures
    vf = s.vec_fits[s.vec_current]
    f = vf.fit
    freq = s.series[0].freq
    a = np.asarray(f.residuals, float)
    npq = vf.p + vf.q
    K = int(nlags) or figures.q_lags(max(8, 2 * freq), npq, a.shape[0])
    fig = figures.residual_ccf_arrays(a, list(f.residual_names), K, freq, npq)
    return _figure(s, fig, "ccf", path, f"VEC residual CCFs (nabla Y2 and the equilibrium "
                   f"errors), {K} lags each side", node="C2")


def plot_forecast_vec(s, H, series, path):
    import drvec
    from . import figures
    vf = s.vec_fits[s.vec_current]
    try:
        fc, _dates = vec.forecast_vec(vf, int(H))
        lv = drvec.to_levels_varma(vf.fit)
    except Exception as e:                                   # noqa: BLE001
        return [f"Cannot forecast the VEC: {e}"]
    by = {x.name: x for x in s.series}
    wanted = [series] if series and series != "all" else list(vf.order)
    if series and series != "all" and series not in vf.order:
        return [f"No series named {series!r}; the session has {', '.join(vf.order)}."]
    out = []
    for nm in wanted:
        i = vf.order.index(nm)
        x = by[nm]
        lam, ref = float(lv.lambdas[i]), float(lv.refactors[i])
        sc = (100.0 if lam == 0.0 else 1.0) / ref
        hist = np.asarray(x.ts.data, float)[-int(H):]
        err = sc * np.asarray(lv.a, float)[-int(H):, i]
        sig = sc * float(np.sqrt(lv.sigma[i, i]))
        first = x.date_of(x.nobs - int(H) + 1)
        fig = figures.vec_forecast_figure(nm, hist, fc[i]["level"], fc[i]["low"],
                                          fc[i]["high"], err, sig, x.freq, first)
        p = ""
        if path and len(wanted) == 1 and not os.path.isdir(path):
            p = path
        elif path:
            p = os.path.join(path, f"sima_{s.name}_forecast_{nm}.png")
        out += _figure(s, fig, f"forecast_{nm}", p, f"VEC forecasts of {nm}, {H} steps",
                       node="N6")
    return out
