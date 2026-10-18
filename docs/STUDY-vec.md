# Cointegrated systems in sima — a study

**Status: a study to be argued with, not a plan.** Written 2026-10-17. The
implementation plan comes after it, separately.

The question: sima 0.2.0 has to handle drvarma's stationary VARMA, as it does
now, and also hand cointegrated series to drvec and run the cointegration
studies itself. The decision of 2026-10-13 stands: **drvec's MCP is sima, not a
fourth assistant** (atsw-gui `docs/PROCESOS-drvec.md` §5.1, private; TODO.md).
This study does not reopen it. It revises the rest of that plan, PROCESOS §5.2–5.4. That
plan was written on 2026-10-11, before sima was published in its current form
and before drvec-python existed.

What was read for it:

| source | what it gave |
|---|---|
| `src/sima/mcp_server.py` (31 tools, the protocol in the server instructions), `session.py`, `evidence.py`, `docs/TOOLS.md`, `docs/STUDY-raw-entry.md`, `docs/STUDY-tiao-box.md`, the four examples | what sima is today |
| drvec-python 0.1.0 (`api.py`, `rank.py`, `irfboot.py`, `forecast.py`, `report.py`, `cli.py`, `README.md`, `docs/PORT.md`, `TODO.md`) | what the engine exposes, refuses and costs |
| drvarma 0.3.0 (branch `gsl-gensymmv`, `CHANGELOG.md`) | the eigensolvers drvec needs |
| drvec C (`engines/drvec/docs/USAGE.md`, `MODEL.md`, `VERSIONS.md`, `datasets/MANIFEST.md`; BUG-58..60 in atsw-gui PR #52) | the oracle and the public data |
| drtran-python `docs/ARCHITECTURE_MCP.md`, `src/drtran/mcp_server.py` (`_handoff_to_sima`) | how the assistants are separated and how mtram hands over |
| PROCESOS-drvec.md §2–§5 | the processes; only its general lessons are used here, none of its article's content |

---

## 1. What changed since PROCESOS §5

### 1.1 sima

- **Published** (sima-tseries 0.1.1 on PyPI, drvarma 0.2.0 under it). It has 31 tools,
  a written protocol (N0–N6) and the guided and autonomous lanes. It also has the
  guion (`record_decision`, `export_guion`, JSON + HTML) and four worked examples.
- **Three entries, not one.** Univariate files from art, the same files from
  mtram when its network has a cycle, and **raw data** (`load_data` →
  `characterize` → route U `build_univariate` or route V `write_specs`).
  PROCESOS §5.1 argued for a fourth assistant because "drvec starts from `.pre`,
  sima from raw series". The 2026-10-13 decision already corrected that. Today sima's
  normal input is the `.pre`.
- **The gate exists** (`run_gate`, N1). It is drvarma's diagonal ladder: each file
  is fitted alone, and the diagonal system must reproduce the sum of the univariate
  logLs. It also says whether each file is an optimum or a specification.
- **The canonical analysis exists** (`canonical_analysis`, N1b; Box and Tiao
  1977). It runs on the transformed levels when two or more series are
  differenced. It counts the components with √λ ≥ 0.90 against the differenced
  series. When there are fewer, its menu says "take the series to drvec
  (outside sima)". **That is the only place where sima names drvec today.** The flour-price
  and Lütkepohl–Poskitt tutorials end there: "testing that is drvec's ground".
- **`characterize`** (raw entry) already carries art's unit-root table per
  series: ADF and KPSS p-values at each d, and art's policy d.
- **Caches are in memory only.** `Session.fits` is keyed by the model's
  specification. There are no jobs, threads, subprocesses or progress reports.
  Nothing survives a server restart.
- **The guion records no engine version and no seed.**

### 1.2 drvec-python

- **It exists:** package `drvec` 0.1.0, packaged and not published, at
  `SRC/drvec-python`. On Linux x86_64 it is **byte-identical to drvec C 0.13**
  (atsw-gui `ae95446`) on every oracle case: `.out`, `.boot`, `.forecast` and
  `.irfboot`. Elsewhere there is a tolerance tier, and every *decision* must
  still be the C's. It reproduces the article's 211 runs with no decision
  changed (its TODO; private inputs).
- **It is not built on drvarma's Ladder.** sima's TODO says it is, and that is
  wrong. drvec has **its own ladder**, the C's (`fit.fit_r0_ladder`, the
  profile, the multistart search). From drvarma it takes the compiled exact
  likelihood (`_engine.elf_c`), the optimiser (`_qnewt`) and, from 0.3.0, GSL's
  eigensolvers (`gensymmv`, `eigen_nonsymm`). From fue it takes the reader and the
  univariate cast (`fue.load`, `cast_us_py`, `forecast._build_xi`, some of
  them private names, as drtran-python does). Dependencies: `fue>=0.1.18`,
  `drvarma>=0.3.0`.
- **The public API** (`drvec/__init__.py`):
  - `fit(pre_files, p, q, r, case=, ma=, diag_ar=, diag_cov=, fixb2row=, nodrift=, trend=, irfboot=, xsys=, xpre=, xlink=, forecast=, fdhess=, alpha=, weakex=, fixb2=, estwin=, multistart=)` → `FitResult`;
  - `rank_test(pre_files, p, q, case=, ma=, bootstrap=, boot_path=, progress=, nodrift=, multistart=)` → `RankTest`;
  - `rungs(...)`;
  - `read_pre`, `Data`, `Spec`, `Param`, `LineSearchRoundoff`.
- **What comes back structured, and what only as text.**
  - Structured:
    - `FitResult.loglik`, `npar`, `aic`, `bic`, `nobs`, `termcode`;
    - `params`, labelled `Param(label, kind, value, se)` with kind mean, alpha,
      gamma, theta, q or beta;
    - `lr_free` and `xs_df`, the logL of the free model for the restriction LRs;
    - `xl_base_ll` and `xl_bridge_ll` for `-xlink`;
    - `gate`, `fdhess`, `ma_on_boundary`;
    - `RankTest.ll`, `npar`, `lr(r)`, `critical_values(r)` (cases 1 and 2 only),
      `verdict(r)`;
    - `bootstraps[*]`, each with `.cv`, `.pvalue`, `.nok` and the replications.
  - **Text only:**
    - the α, β (B₂) and Π matrices, Γ, Θ and Σ, the residuals;
    - the level IRF and FEVD, the long-run gain and mean lag;
    - the Hosking Q and the multivariate JB;
    - the Granger rank condition and the normalisation share;
    - the forecasts (`forecast_text`, a CSV);
    - the rolling evaluation (`recursive_text`, a CSV);
    - the IRF bands (`irfboot_text`, a CSV).

    Inside the package they exist as arrays (`report._Fit`, `cast.shootx`,
    `report.level_irf_R`), but under private names.
- **Long tasks.** `rank_test(progress=)` calls `progress(b, replication)` after
  each replication, and `replication.h0` says which comparison it belongs to.
  **`irfboot` has no callback, and nothing can be cancelled.** The bootstrap seed is
  fixed at the C's 987654321 (`rng.SEED`). `Rng(seed)` takes another, but
  no public function passes one. The `-irfboot` horizon is fixed at 10 lags
  (n < 40) or 20.
- **Cost.** The port is about 12× slower than the C (6× to 15× by case; TODO,
  `tools/time_bootstrap.py`). Muskrat–mink: `-lrtest -bootstrap 20`, one
  comparison, 5.8 s, about 0.3 s per replication, so B = 999 takes about 5 min.
  Lütkepohl's E1 (M = 3): one fit takes 13.7 s; `-bootstrap 20` with two
  comparisons takes 112 s, about 2.8 s per replication and comparison, so
  B = 499 takes about 47 min and B = 999 about 1.5 h. The largest bootstrap of a real
  study took about 1.5 h in the C, which is about 17 h in Python on one core.
- **Refused in v1, by name, and they stay refused.** The MCP must not offer them:
  1. `-warma`, `-mawarma`, `-specs`. With them goes the MA class menu: the
     only class is `ma="free"`.
  2. `-matest`, `-artest`.
  3. The rank test combined with `-alpha`, `-weakex`, `-fixb2`, `-diagar` or
     `-diagcov`; `-rungs` with `-case pre` or `-nodrift`.
  4. `-m 2` and `-rankadm` (flawed in the C).
  5. The instruments (`-eval`, `-noladder`, the `-seed*` family) and the writers
     (`-writeres`, `-writeinp`).

  Also refused, as the C itself declares them not yet done:
  - the rank test with `-xsys`, `-xlink` or `-trend`;
  - `-xlink` with `-f`, `-estwin` or `-irfboot`;
  - `-xsys` with q > 0, `-alpha`, `-weakex` or `-fixb2row`;
  - `-irfboot` with `-trend` or `-estwin`;
  - `-trend` with `-f` or `-estwin`;
  - a `.pre` with D > 0 (the C ignores it, the port refuses it);
  - an A of deficient rank in `-alpha` (BUG-58: the C crashes, the port refuses).
- **The C's open defects** (BUG-58..60, PR #52), and what they mean for sima:
  - BUG-58 is the `-alpha` rank check above;
  - BUG-59 is cosmetic: the "Input Data File" line is truncated;
  - under BUG-60 the port's `.boot` differs from the C's in one replication
    when a drift is held (`-case pre`, `-nodrift`). The p-value and the
    percentiles are the same.

  Three more matter for the reading:
  - the C's `-fdhess` step sits below the likelihood's noise, so the standard
    errors carry about 0.1–0.5 % of numerical noise;
  - `-estwin` dates its header wrong;
  - E1 `2 1 1 -mean -case 2` is a ridge, not a maximum: every start stops on
    criterion 3.

### 1.3 Three facts that change what PROCESOS assumed

1. **drvec does not read the univariate ARMA** (PORT §7). From each file it takes the
   series, the calendar, λ, the rescaling factor, the deterministic block
   and the mean flag (for `-case pre`). Its own gate (`FitResult.gate`, r = 0
   with everything diagonal) is a **factorisation identity**: "not a
   comparison with the .pre models, which this route does not read"
   (`gate_contract`). So PROCESOS §3.1's "identity of crossing" is not a bridge
   to art's models in the port. **The bridge to the univariate models is
   sima's `run_gate`**, and it stays N1 for both branches.
2. **D > 0 is refused.** A seasonal series enters drvec only with
   *deterministic* seasonality in its `.pre`. art's autonomous lane already asks
   for this when the objective is "multivariante" (it forces deterministic
   seasonality "for a VECM"). The check belongs at sima's routing node.
3. **Alignment.** drvec lines the files up on the intersection of their dates.
   drvarma's ladder requires a common last date and trims the starts. Once
   `load_pre` has accepted the files the two windows are the same; sima must say
   so in the report rather than assume it.

### 1.4 PROCESOS §5.2–5.4, item by item

| PROCESOS item | status | why |
|---|---|---|
| §5.1 the MCP is sima | **holds** | decided 2026-10-13 |
| `load_pre` with roles, alignment, crossing identity | **changes** | `load_pre` and `run_gate` exist and stay. The roles (which series β is normalised on) move to the fit, because they depend on r (§3.4). The crossing identity is sima's gate, not drvec's (§1.3) |
| `propose_order` | **changes** | folded into a preparation node (§4), with two sources: the `.pre` AR order in ∇ + 1, or Tiao and Box's M(l) on the levels (`canonical_analysis` already computes it) |
| `set_case` | **changes** | folded into the same node |
| `rank_test` (asynchronous) | **holds** | engine: `drvec.rank_test(bootstrap=, progress=)` |
| `job_status` / `job_result` / `job_cancel` | **holds, all new** | sima has no jobs; drvec has no cancellation (§5) |
| `estimate` with `-fdhess`, α, β, s.e., θ, half-lives, diagnosis | **holds**, but needs structured accessors drvec does not expose (§4.2) | half-lives are not in drvec at all |
| `test_restriction` | **holds** | `fit(weakex=, alpha=, fixb2=, fixb2row=)`. The C's free model in these LRs is a weaker fit than the adopted one (§3.5) |
| `add_exogenous` | **holds** | `fit(xpre=, xlink=)` or `fit(xsys=)`, with their refusals |
| `impulse_response` / `variance_decomposition` | **extend sima's** | same tool names, dispatched on the model's kind (§4) |
| `irf_bands` (asynchronous) | **holds** | `fit(irfboot=N)`. No progress callback (§5) |
| `sweep` (asynchronous) | **holds** | a grid of `fit`/`rank_test` calls, each cached |
| `forecast` / `evaluate` | **extend sima's** | `fit(forecast=, estwin=)`; the yardstick against the univariates (§3.11) |
| `specs` | **obsolete** | `-specs` is refused in v1 (group 1) |
| `record_decision` / `export_guion` | **reuse** | sima's, plus engine versions and seeds (§3.13) |
| `export_tables` (LaTeX from a run registry) | **defer** | an article's need. The on-disk job cache plus the guion JSON is the registry (§7, Q8) |
| `plot_*` | **extend** | the bootstrap distribution of the LR against the observed one is new; the others extend sima's |
| §5.3 behaviour rules | **hold** | §3.13 restates them with sima's protocol |
| §5.4 long tasks | **holds, made concrete** | §5. A server that dies with its client cannot hold a 17-hour job in-process |

---

## 2. sima's new scope: where the routing decision goes

### 2.1 The question, said as sima's

The question is not "is this system cointegrated?". It is this: **how many unit
roots does the system have, against how many series the univariate models
difference?** With m series of which k are differenced (d = 1) in their files:

- if the system has k unit roots, the univariate differences are right
  jointly. That is drvarma's VARMA on the files as they are (the ladder);
- if it has fewer, k − (unit roots) combinations of the levels are
  stationary. Differencing all k series over-differences the system, and the
  model belongs in levels with the error correction: drvec.

A series with d = 0 is already stationary. It is a cointegrating relation by
itself (β = its unit vector). So a mixed system has rank at least the number
of its I(0) series, and drvec places such a series in the Y₁ block, the one β is
normalised on.

### 2.2 The evidence, and what each piece weighs

| evidence | where | what it can say | what it cannot |
|---|---|---|---|
| each series' d | the `.pre` (art's decision), or `characterize` (ADF + KPSS at each d, art's policy) | which series are I(1) one at a time | anything joint |
| the canonical analysis of the levels | `canonical_analysis` (N1b) | how many components are near non-stationary, and the weights of the least predictable ones, which are candidate stationary relations | a test. √λ ≥ 0.90 is a convention. The flour tutorial shows the count changing with the threshold |
| **the rank test by parametric bootstrap** | drvec `rank_test(bootstrap=B)` | the inference: the sequential exact-LR test r → r + 1, calibrated by simulation from the fitted model under H₀ | r = M (§2.5); a rank under restrictions or with exogenous inputs (refused) |
| the asymptotic table | the same output, cases 1 and 2 only | orientation | the decision. drvec's LR is the exact one: under H₀ it sits about log T below Johansen's conditional LR and can be negative. At n ≈ 100 the sequential test over-rejects (drvec `HOMOLOGATION.md`). Case 3 and `-case pre` have no table |
| theory | the analyst | a relation that must exist, or a rank the domain fixes | anything without being written in the guion |

**The bootstrap decides the rank.** Theory may prevail, and then it is
recorded with the bootstrap's numbers beside it. In practice the bootstrap has
overturned the asymptotic reading, and a bootstrap verdict at the edge of 5 %
has been settled by theory. Both are legitimate when written down.

### 2.3 The node

The routing goes **right after N1b, before N2**, as a new node **N1c, the
cointegration question**. It is where the levels have just been read and nothing
has been built on the differences yet:

```
N0 load_pre / raw entry ─ N1 run_gate ─ N1b canonical_analysis ─ N1c the cointegration question
                                                                   │
                     ┌─────────────────────────────────────────────┼───────────────────────┐
                     │ k < 2, or the analyst declines              │ the rank is tested     │
                     ▼                                             ▼                        │
                N2 identify_cross … (drvarma, as today)    C0 prepare_vec (p, case, checks)  │
                                                           C1 rank_test (job) ── r̂ ────────┤
                                                                   │                        │
                       r = 0 ──► back to N2: the differences are right (drvarma)            │
                       r = M−1 not rejected and theory says M ──► art / route V in levels   │
                       0 < r < M ──► C2 estimate_vec ─ C3 restrictions ─ C4 inputs ─ C5 long run
                                     ─ C6 IRF/FEVD (bands: job) ─ C7 robustness (job)
                                     ─ C8 the yardstick (evaluate) ─ N6 forecast …
```

- **When N1c is offered.** When two or more series have d = 1 (in the files, or
  in `characterize`), **whatever the canonical count**. The count changes the
  wording, not whether the question is asked. When the canonical analysis finds
  fewer near-unit components than differenced series, the menu leads with the
  rank test. When it finds as many, the menu leads with going on to N2 and keeps
  the rank test as an alternative. PROCESOS's rule was "≥ 2 I(1) series with
  feedback". This study recommends dropping "with feedback" (§7, Q1): feedback is what
  the weak-exogeneity tests answer *inside* the VEC (§3.6), not a precondition.
- **Route V.** The `.inp` specifications carry exactly what drvec reads:
  λ, d, the deterministic terms, the mean flag. They go to drvec as they are.
  `fue.load` reads an `.inp` like a `.pre`; this needs a test, not a change.
- **Route U and the `.pre` route.** The same files go to drvec. Their ARMA is
  ignored there (§1.3). The rule "p = the AR order in ∇ + 1" reads it.

### 2.4 The checks before the rank (C0)

Each check is a refusal with its reason, or a warning. None is skipped silently:

- a series with **d ≥ 2**: drvec models I(1) systems only. Refuse, and send that
  series to art;
- a series with **D > 0**: refused by drvec. Its seasonality must be
  deterministic, so send it back to art with the objective "multivariante";
- a deterministic variable drvec refuses (a non-standard one; `easter` off
  monthly data): drvec's message, passed on;
- **d = 0 series**: they go in the Y₁ block, and r ≥ their number. Say it;
- a file that is a **specification** (it moved at the gate): the warning
  sima already gives;
- the **sample**: drvec's window equals the gate's, or the report says why
  not.

### 2.5 The outcomes

- **r̂ = 0: no stationary combination.** The univariate differences are right
  jointly. Go back to N2 (drvarma, the ladder on the same files), with the
  rank test recorded as the evidence that the differences hold. drvec's r = 0
  fit is a VAR(p − 1) in differences (drvec `MODEL.md` §5.2). The ladder is
  richer, because it keeps each series' ARMA on the diagonal, so the
  differenced VARMA is drvarma's job.
- **0 < r̂ < M: cointegration.** The C nodes, in drvec.
- **Full rank cannot be tested in drvec.** The sequential test compares
  r → r + 1 for r = 0 … M − 2. drvec fits r ≤ M − 1 and never M, since r = M is a
  stationary VARMA in levels. If every comparison rejects, the conclusion is
  "at least M − 1", and the last step, M − 1 against M, is the question of
  whether a single common trend exists. That is a univariate-type unit-root
  question. sima answers it with what it has:
  - the canonical analysis: no component near 1?;
  - art's unit-root table per series;
  - and, if the levels look stationary, the VARMA in levels on drvarma, which is
    route V with d = 0, or the series back to art.

  Tiao and Tsay's ARMA(1,1) in levels for the flour prices is this case's
  precedent. The study recommends **not** extending drvec to fit r = M (§7, Q9).
- **A mixed system (some d = 0).** drvarma's ladder already models it: each
  series keeps its own d. In drvec it is a VEC with the I(0) series in Y₁ and
  their rows of B₂ at zero. **drvec's VEC contains the mixed-d ladder as the
  case B₂ = 0**, and `fit(fixb2=0.0)` tests that by LR. Mauricio (2006) fits
  muskrat–mink this way, with r = 1 (§6.2).
- **A tie** (a bootstrap p-value within two Monte Carlo errors of 5 %, or a
  verdict that flips between nearby p): estimate **both ranks** and compare.
  Compare their restrictions, their IRFs and their yardstick. This is the
  autonomous lane's existing tie rule ("estimate both and compare, not on
  paper").

### 2.6 The handovers

- **mtram → sima.** mtram's call stays the same: `load_pre` with the SAME
  `.pre` files (`_handoff_to_sima`). The routing is sima's, at N1c. mtram
  only adds one line when two or more of the files have d = 1: "sima will ask
  the cointegration question (the canonical analysis, then the rank by
  bootstrap) before a VARMA in differences". mtram tests nothing about it. A
  cycle plus I(1) series is therefore not a different handover. It is the same
  handover, and the routing happens at sima's N1c.
- **sima → mtram, from the VEC.** Suppose every series but one is weakly
  exogenous (§3.6) and the short run has no feedback. Then the system is a
  conditional model, a transfer network on I(1) inputs. sima offers mtram, as
  `structure` does today, and never goes there itself. With inputs of the same
  order, drvec's own `-xsys` is the in-VEC version (§3.7).
- **sima → art.** The routing check sends a series back to art for:
  - d ≥ 2, or D > 0;
  - a univariate d that the joint reading contradicts. "Back to art:
    reconsider a series' d with this reading in hand" is already in
    `canonical_analysis`'s menu.

  sima never changes a d itself.

---

## 3. The cointegration studies

Each study below says what it is, which drvec call backs it, **what it
claims**, and the rule that governs it. They share three conditions. Every
result is conditional on the transformation and the deterministic terms of
the files. Every result after C1 is conditional on r. And every result is
in-sample until C8.

### 3.1 The order p (C0)

- **Rule** (from PROCESOS, general): p = the AR order of the univariate models
  in ∇ + 1. drvec's p is the AR order on Ȳ = (∇Y₂, W), so with r = 0 the effective
  order on ∇Y is p − 1. On route V there is no ARMA. The levels VAR order from
  Tiao and Box's stepwise M(l), which `canonical_analysis` already prints, gives
  p directly: a levels VAR(k) is p = k.
- **Check:** the last Γ in the adopted fit. Over-fitting p costs the rank test
  power.
- **Claims:** nothing. It is a specification choice, recorded.

### 3.2 The deterministic case (C0)

`case` = 1, 2, 3 or `"pre"`, plus `nodrift`; `trend` (case 4) is for a single
fit only.

| case | E[∇Y₂] | E[W] | asymptotic table | rank test |
|---|---|---|---|---|
| 1 | 0 | 0 | MacKinnon–Haug–Michelis | yes |
| 2 | 0 | ≠ 0 | Osterwald-Lenum | yes |
| 3 | ≠ 0 | ≠ 0 | none | bootstrap only |
| `pre` | each file's mean flag | ≠ 0 | none | bootstrap only |
| `trend` | — | trend in β | — | **refused** |

- **Default on the `.pre` route: `"pre"`.** The drift of each series is what
  its univariate model said. When it differs from case 2 or 3, the report
  explains why.
- **Claims:** none on its own. A conclusion that changes with the case is a
  finding, and §3.10 runs the cases side by side.

### 3.3 The rank (C1, a job)

- **Engine:** `drvec.rank_test(files, p, q, case=, nodrift=, bootstrap=B,
  progress=)`. It runs r = 0 … M − 1, the LR of each step r → r + 1, and B
  replications per step. Each replication is simulated under H₀ from the
  fitted rank-r model and refitted at r and r + 1 by the same route as the data.
  Negative LR* are kept. Replications that fail are counted.
- **Output:**
  - per r: logL, npar, LR, the asymptotic critical values (cases 1 and 2),
    the bootstrap's 90/95/99 % values, the p-value and `reps`;
  - the Monte Carlo error √(p(1−p)/B) and the p-value floor 1/(B+1);
  - the proposed r̂, read **from the critical values**;
  - the `.boot` file;
  - a figure: the LR* distribution against the observed LR.
- **B:** 499 by default. Use 999 when a 1 % verdict matters. Below 199 the
  tool says the result is an exploration.
- **Claims:** the number of stationary relations, at the stated p, q, case
  and sample. It is a sequential λ-max-type test on the **exact** likelihood,
  not Johansen's trace.
- **Rules:**
  - the bootstrap decides; the asymptotic table is shown and marked as
    orientation;
  - read the critical values, not the p-value;
  - `reps` well below B is a warning;
  - the tool **proposes** r̂ and never adopts it. In the guided lane the analyst
    decides. In the autonomous lane the LLM decides and records why, with
    theory allowed to prevail in writing.

### 3.4 The adopted fit and the normalisation (C2)

- **Engine:** `drvec.fit(files, p, q, r, case=, fdhess=True)`. Use `-fdhess`
  whenever a standard error will be quoted: the BFGS ones are not the
  Hessian's at the optimum.
- **The roles are asked for, explicitly.** drvec's file order is
  [∇Y₂ ; Y₁]: the **last r** series are the ones β is normalised on. A
  different order gives a different, equally valid model, with no error.
  So the tool takes `normalise_on` (r names) and builds drvec's order: the
  other series in the session's order, then these. It repeats the roles in
  its output.
- **Three consequences:**
  - the file order is also drvec's **Cholesky order** for the level IRFs
    (§3.9). Normalisation and orthogonalisation are coupled in drvec;
  - the order is set at C2, not at `load_pre`, because it depends on r;
  - sima's `reorder` (a permutation without refitting) cannot apply to a VEC:
    another order is another fit.
- **Output:**
  - the `.out` blocks verbatim (engine English);
  - α **read from the matrix**, never from `-weakex`'s ψ, which has the
    opposite sign;
  - β (B₂ and the identity on Y₁) and Π, with standard errors;
  - the diagnosis (Hosking Q, multivariate JB), the Granger rank condition
    (q > 0) and the normalisation share ("the Y₁ block carries x % of the
    weight", DUBIOUS below 5 %);
  - the criterion the optimiser stopped on.
- **Ill-defined fits.** E1 `2 1 1` is the example: a ridge, criterion 3
  everywhere. They get the same treatment as sima's `study_estimation`:
  - say it is not a demonstrated maximum;
  - offer `multistart`;
  - offer a lower q;
  - never present the point as an optimum.

  This is a later extension of `study_estimation` (§7, Q12).

### 3.5 Restrictions on α and β, by LR (C3)

- **Engine:**
  - `fit(r=…, weakex=i)` gives αᵢ = 0;
  - `fit(alpha=A)` gives α = Aψ;
  - `fit(fixb2=v)` sets every entry of B₂ to v. **With a value only**: without
    one it is the static OLS value, and that is not a test;
  - `fit(fixb2row={i: v})` sets a row of B₂;
  - combinations give the joint LR.
- **Output:**
  - LR = 2[L(free) − L(restricted)], its degrees of freedom and its χ²
    p-value;
  - both logLs;
  - the Wald statistics the `.out` prints, labelled **not citable**: they
    depend on the normalisation.
- **A finding of this study.** drvec does not fit the free model of these LRs
  as it fits the adopted model:
  - for `-alpha` and `-weakex` it is **one est() from the cold start**, with
    no search and no ladder;
  - for `-fixb2row` it is the cold start and the search, with no ladder.

  That is the C's behaviour, faithfully ported. The free logL can therefore be
  below sima's cached free fit at the same r and case, and then the LR is
  understated. sima should take the best free logL it knows, say which one it
  used, and show both whenever they differ (§7, Q7).
- **Not available:**
  - restrictions per cointegrating vector (Johansen's H-form on one column
    of β): drvec only has "all of B₂" and "a row of B₂";
  - a bootstrap of the restriction LR;
  - a rank test under a restriction (refused, group 3).
- **Claims:** an asymptotic χ² test given r. β is superconsistent; α and the
  short run are standard.

### 3.6 Weak exogeneity (C3)

`weakex=i` series by series, and jointly for several series with `alpha=A`.

- **Claims:** series i does not adjust to the equilibrium ("who corrects").
- **Signs:**
  - α < 0 on the normalised variable corrects;
  - on the others, the correction has the sign of −β.
- A system where every series but one is weakly exogenous points to a
  conditional model (§2.6).

### 3.7 Exogenous inputs (C4)

The dispatch depends on d, as in drtran:

- **an input of another order** (I(0) on I(1) outputs): `fit(xpre=, xlink=)`.
  It is subtracted in levels and its `.pre` stays frozen. `-xpre` and `-xlink`
  go together. The network has one line `OUT <- IN b r s` per link, r ≤ 2. The
  VEC without inputs is fitted first. ω = 0 must reproduce it (the bridge,
  `xl_bridge_ll`), and the LR against it is the test;
- **an input of the same order:** `fit(xsys=[i])`. It sits in the system with
  αᵢ = 0 and none of the others' short run. The LR is strong exogeneity
  (`lr_free`, `xs_df`). The input cannot be in Y₁.

Their refusals are inherited (§1.2). In particular there is no rank test with
inputs: the rank comes from C1, without the inputs.

### 3.8 The long run, read (C5)

From the adopted fit:

- θ, the long-run coefficient. It is β normalised, read with its sign;
- the standard errors of α and β, from `-fdhess`;
- **half-lives.** Two definitions, both computed by sima, since drvec computes
  neither (§4.2):
  - the textbook ln 0.5 / ln(1 − |α|), for the correcting variable. It is
    exact only for one relation with no short-run dynamics, so it is
    orientation only;
  - the half-life of the **equilibrium error** β′Y in the fitted model's
    own response, from the same weights as the level IRF. This one is the
    model's.
- the permanent/transitory decomposition (Gonzalo and Ng). In a real study
  it was computed outside the engine. It is a candidate (§7, Q6).

**Claims:** descriptive, with point values. Bands only through the bootstrap
(§3.9).

### 3.9 Impulse responses and FEVD in levels (C6)

- **Point:** the `.out`'s "Impulse Response of the Levels", "Long-Run Gain
  and Mean Lag" and FEVD.
  - The gain matrix has rank M − r.
  - The self-check max |β′·gain| must be zero.
  - The Cholesky order is drvec's file order (§3.4).
- **Bands:** `fit(irfboot=N)`, a job. N simulations of the fitted model, each
  **refitted as the data were**: same r, same restrictions, same ladder.
  Efron percentiles at 90 and 95 %, written to the `.irfboot` CSV.
- **No delta method and no covariance Monte Carlo.** This is unlike sima's
  VARMA bands today. The level responses are a long non-linear chain that
  converges to the permanent effect, and a linearisation is what not to trust
  at these sizes.
- **Claims:** responses conditional on r, the restrictions and the
  orthogonalisation order. Reordering means a refit and a new job.

### 3.10 Robustness (C7, a job)

A **sweep**: a grid over the same files of:

- p;
- the case (2, 3, `pre`, `trend` for a single fit);
- alternative univariate files (with and without interventions, other
  variants);
- the subsample and the recursive estimate (`estwin` over a range).

**Output:** a table of logL, the LR of interest, θ and α per cell. Each cell is
a cached job.

**Claims:** none beyond its cells. What it preserves is **the list of what was
run and why**, in the guion.

### 3.11 The yardstick (C8)

drvec's `fit(estwin=E, forecast=H)` is the existing yardstick, made concrete
for the VEC:

- the fit on rows 1..E of ∇Y;
- parameters held fixed;
- origins rolled to the end;
- errors in **original levels**, one CSV row per origin, horizon and series.

That is sima's `evaluate` design. Two things need settling:

- sima's `estwin` counts observations of the first series, and drvec's counts
  rows of ∇Y: one apart;
- `-xlink`, `-irfboot` and `-trend` cannot be evaluated this way (refused).

**Recommendation:** the VEC is compared on the same origins against both the
univariate models (sima's yardstick) and the differenced VARMA, if one was
estimated.

**A tension with a recorded rule.** sima's rule 1 says "a VARMA that does not
forecast better than the univariates out of sample has no reason to exist".
A VEC also makes a **long-run claim**, the equilibrium and who corrects, which
can stand without a forecasting gain. The study does not change the rule. It
asks (§7, Q10).

### 3.12 How the cointegration studies relate to `canonical_analysis`

- Both read stationary combinations of the levels.
  - Box and Tiao order the components by predictability, under a least-squares
    VAR on the levels. The least predictable ones are candidate stationary
    relations, and their weights are candidate β's.
  - Johansen's reduced-rank estimator is also a canonical problem: between ∇Y
    and the lagged levels, given the short run. Done by exact maximum
    likelihood and calibrated by bootstrap, it is the **test**.
- **The canonical analysis comes first and reads; the rank test decides.** It
  also supplies two things:
  - p: its M(l) on the levels;
  - a **consistency check**: once β̂ is estimated, `estimate_vec` prints the
    canonical weights of the least predictable component beside it,
    normalised the same way.
- **They can disagree.** A near-unit √λ can come from a nearly singular
  innovation covariance (Box and Tiao §5.1), and the threshold is a
  convention. A disagreement is reported, not resolved by sima.
- `canonical_analysis`'s menu changes:
  - its option "drvec (outside sima)" becomes the call to the cointegration
    node;
  - its facts (λ, the weights, p) stay in the session for C0 and C2.

### 3.13 The school's rules, applied here

- **Guided or autonomous**, the same nodes either way. The cointegration
  decisions are N1c (whether to test), C1 (r), C2 (the roles), C3 (each
  restriction), C4 (each input) and C8 (keep the VEC or not). In the
  autonomous lane each one gets a `record_decision` with its numbers, `decided_by="LLM"`, and
  **never in batch**. A rank is not decided before its bootstrap exists.
- **The bootstrap decides the rank**, and theory may prevail in writing.
- **LR, not Wald**, for every restriction. The printed Wald is labelled not
  citable.
- **Engine refusals are not removed** without the analyst, and the MCP does not
  offer the five refused groups.
- **Every result carries its provenance:**
  - drvec, drvarma and fue versions;
  - the engine backend (`drvarma._engine.engine_backend()`, `_gsl.backend()`);
  - the platform tier: byte-identical with the C on Linux x86_64, tolerance
    elsewhere;
  - the seed (987654321, the C's, fixed);
  - the cache key and the run folder.

  sima's guion records none of this today. Add it for every engine, not only
  drvec.
- **Mixed output, as in mtram:**
  - the `.out` blocks verbatim, in English, the C's format, which is a
    property of the port;
  - sima's narrative around them;
  - the LLM translates the whole into the user's language.
- **Tables as the tool returns them.** The `.out` blocks are never rebuilt.
- **No `.pre` for the system.** The VEC's estimates are not univariate
  optima, as on route V. The model lives in its `.out`, its run folder and the
  guion. drvec's `-writeinp` is refused anyway.

---

## 4. The tools

### 4.1 The revised list

Legend: **new** · **ext** (an existing sima tool, extended) · **reuse**
(unchanged). "job" means it returns a job id at once, or the result inline if it
is cached or finishes within a short wait (§5.3).

| tool | kind | node | sync | inputs → outputs | drvec call |
|---|---|---|---|---|---|
| `load_pre`, `load_data`, `characterize`, `build_univariate`, `write_specs`, `run_gate` | reuse | N0–N1 | sync | as today | — (drvarma, art) |
| `canonical_analysis` | ext | N1b | sync | + keeps λ, the weights and p in the session; its menu calls `prepare_vec`; the question is asked whenever k ≥ 2 | — |
| `prepare_vec` | **new** | N1c/C0 | sync | p (rule, or M(l)), case (default `pre`, explained), nodrift → the checks of §2.4, the d = 0 series and their Y₁ placement, the proposed spec | `drvec.read_pre` (eligibility) |
| `rank_test` | **new** | C1 | **job** | p, q, case, nodrift, B, multistart → the table of §3.3, `.boot`, Monte Carlo error, proposed r̂, provenance | `drvec.rank_test(bootstrap=, progress=, boot_path=)` |
| `job_status`, `job_result`, `job_cancel`, `jobs` | **new** | — | sync | id → status, progress (k of B, comparison r → r + 1), elapsed, final result only when done | — (sima's runner) |
| `estimate_vec` | **new** | C2 | sync (job above a size) | r, p, q, case, nodrift, `normalise_on`, multistart, fdhess = True → the `.out` blocks, α, β, Π with s.e., diagnosis, Granger condition, normalisation share, canonical weights beside β̂, roles repeated | `drvec.fit(..., fdhess=True)` |
| `test_restriction` | **new** | C3 | sync | weakex, alpha (matrix or file), fixb2 (value required), fixb2row → LR, df, p, both logLs (and the best free one known, §3.5), Wald not citable | `drvec.fit(weakex=/alpha=/fixb2=/fixb2row=)` |
| `add_exogenous` | **new** | C4 | sync | input files, links "OUT <- IN b r s" → the dispatch by d, the network file written, the bridge, the LR, the refusals | `drvec.fit(xpre=, xlink=)` / `fit(xsys=)` |
| `long_run` | **new** (or inside `estimate_vec`) | C5 | sync | — → θ, both half-lives, β′Y's response, permanent/transitory (if adopted, Q6) | accessors (§4.2) |
| `impulse_response`, `variance_decomposition` | ext | C6/N6 | sync | on a VEC: the level responses, gain, mean lag and FEVD from the `.out`; `bands=True` points to `irf_bands` and never draws covariance bands | `fit` (point) |
| `irf_bands` | **new** | C6 | **job** | N → percentiles at 90/95 %, `.irfboot`; conditional on r and the restrictions | `drvec.fit(irfboot=N)` |
| `sweep` | **new** | C7 | **job** | a grid (p, case, alternative files, estwin range) → a table, one cached job per cell | `fit` / `rank_test` in a loop |
| `forecast` | ext | N6 | sync | on a VEC: H steps in levels with the theoretical bands | `fit(forecast=H)` |
| `evaluate` | ext | C8/N5 | sync or job | on a VEC: estwin, H → the rolling evaluation against the univariates (and the differenced VARMA) on the same origins | `fit(estwin=, forecast=)` |
| `plot_rank_bootstrap` | **new** | C1 | sync | → the histogram of LR* per comparison, with the observed LR and the critical values | from the job's `.boot` |
| `plot_impulse_response`, `plot_variance_decomposition`, `plot_forecast`, `plot_residual_ccf` | ext | C6/N6 | sync | on a VEC: the bands from `irf_bands` when they exist | accessors (§4.2) |
| `reorder` | ext | — | sync | on a VEC: refuse with the reason (another order is another normalisation and another fit) and give the `estimate_vec` call | — |
| `record_decision`, `export_guion` | reuse (+ provenance) | all | sync | + engine versions, seed, cache keys, run folders | — |
| `study_estimation` | ext (later) | C2 | sync or job | on a VEC stopped on criterion 3: multistart, a lower q, the declaration | `fit(multistart=)` |

**Not offered:**
- `specs`, `matest`/`artest`, `eval` and the seed and writer options (refused);
- `rungs` (an instrument; the gate is sima's);
- `export_tables` (deferred, Q8).

**Count:** about 12 new tools (`prepare_vec`, `rank_test`, four job tools,
`estimate_vec`, `test_restriction`, `add_exogenous`, `long_run`, `irf_bands`,
`sweep`, `plot_rank_bootstrap`) and about 10 extended. As TODO.md said: "the
tools are added, nothing that exists changes". The exception is the menus and
texts of `canonical_analysis` and `run_gate`.

### 4.2 What drvec-python does not expose yet

**Needed for sima 0.2.0.** None of these changes a number, so byte identity
with the C is untouched:

1. **Structured matrices on `FitResult`:** α, B₂/β, Π, Γ, Θ, Σ, the
   residuals, and the stationary representation (φ, θ on Ȳ). Today sima would
   have to reassemble them from `params` labels or call private functions
   (`report._Fit`, `cast.shootx`).
2. **The level IRF, FEVD and gain as arrays.** `report.level_irf_R`,
   `level_irf_fevd` and `compute_psi_weights` exist as private functions.
3. **The IRF bootstrap as arrays**, and a **progress callback** for
   `irf_bootstrap` like `rank_test`'s.
4. **Diagnostics as numbers:** Hosking Q (statistic, df, p) and JB. Today they
   exist as `.out` text only.
5. **Forecasts as arrays** (point, bands, dates). `forecast_vec` returns text
   and CSV.
6. **The restriction LRs with their df**, rather than `lr_free` alone, which
   leaves the df to the caller.

**Useful later:**

7. **A `seed=` on `rank_test` and `fit(irfboot=)`**, defaulting to the C's. It
   allows a Monte Carlo variability check without breaking parity (Q5).
8. **A parallel bootstrap.** Generate the B simulated samples in sequence,
   which consumes the generator in the C's order (fits consume no numbers,
   PROCESOS §3.4 and `rank.py`), then fit them in a process pool. The result is
   bit-identical with a 3–4× speed-up on this machine's 4 cores (Q4).
9. **An `irfboot` horizon** parameter. It is fixed at 10 or 20 today.
10. **A public "levels cast" in fue**, so that drvec and drtran stop using
    fue's private names (drvec's TODO).

**sima computes itself until the engine has them:** the half-life of β′Y and
Gonzalo–Ng (Q6).

---

## 5. Long tasks

### 5.1 What exists

- **sima: nothing.**
  - Every tool is synchronous.
  - The only cache is `Session.fits`, in memory.
  - No progress is reported.
  - A stdio MCP server lives as long as its client, so anything running inside
    it dies when the client closes.
- **drvec:**
  - `rank_test(progress=)` reports per replication, and `Replication.h0` gives
    the comparison;
  - `irfboot` reports nothing;
  - there is no cancellation;
  - the results are **deterministic** (fixed seed, every number from the same
    stream), so a cache keyed on the inputs is exact, not approximate.
- **MCP:** progress notifications live only within a call. A job of hours
  needs polling.

### 5.2 What it costs

From §1.2, on one core:
- a bivariate B = 999 takes minutes;
- three series at B = 499 take about an hour;
- the largest real case takes about 17 hours.

A single fit can take 15 s at M = 3. That is the size where a synchronous tool
starts to be a bad idea.

### 5.3 The design proposed

- **Each job is a detached subprocess**, not a thread: `python -m
  sima.jobs run <folder>`, started by the tool. The GIL would serialise threads,
  and a detached process survives the client and the server.
  - At most `cores − 1` jobs run at once; the rest wait in the queue.
  - Cancelling a job kills its process and marks the folder cancelled.
- **One folder per run** (drvec writes `BASE.out`, and two runs in one folder
  overwrite each other): `<first file's folder>/<session>_sima/vec/<key>/`. It
  holds:
  - `job.json` (call, status, start, end, versions);
  - `progress.json`;
  - the `.out`, `.boot`, `.irfboot` and `.forecast` files;
  - `result.json` (the structured result).
- **The cache key:** sha256 over
  - the tool and its canonical arguments;
  - the **content** of every input file (`.pre`, `-xpre`, the network, the A
    matrix);
  - the versions of drvec, drvarma and fue;
  - the engine backend (compiled or fallback);
  - the platform tier;
  - the seed.

  Same key and a result present: it is returned without running. Same key and
  a job running: that job's id is returned. Anything changed: a new run.
- **Progress.**
  - Rank: "replication k of B, comparison r → r + 1, ok/simfail/fitfail
    so far".
  - IRF bands: elapsed time only, until drvec has the callback (§4.2, item 3).
- **Partial results are never reported as final.** As in the C, a finished
  comparison is reported as finished, while the later ones are still running.
  An unfinished comparison shows its counts only, never its provisional
  critical values.
- **A short wait.** A job tool waits up to about 20 s before returning the job
  id, so a cached or small job comes back inline. The guided lane stops at
  the job id and tells the analyst roughly how long it will take, from the
  measured rate. The autonomous lane polls (`job_status`) and **does not
  decide the node** until `job_result` has the final table.
- **The examples ship their cache.** `load_example` copies the job folders,
  so the tutorial's bootstraps return at once. Rerunning them reproduces the
  same bytes on Linux x86_64. That is also a test.

---

## 6. Worked examples, public data only

### 6.1 `flour_prices`: where sima's example already ends

- **Data:** Tiao and Tsay (1989), three cities, monthly, 100 observations. The
  example ships three art ARIMA(0,1,1) models in logs with no mean, and
  `data/flour_prices.csv`.
- **What is known:**
  - the canonical analysis gives two components near 1 for three differenced
    series, with the contrast between markets at √λ 0.87 (Tiao and Tsay's
    φ = 0.88, "not very stable");
  - the differenced VAR does not beat the univariates.

  The tutorial closes with "the next step is a test of the stationary
  combination, drvec's".
- **The continuation:**
  1. N1c;
  2. `prepare_vec`: p from M(l) on the levels, which is 2; case `pre`, which
     here holds every drift, since no file has a mean;
  3. `rank_test` with B = 499;
  4. then, if r = 1, the β of the contrast against the canonical weights;
  5. weak exogeneity by market;
  6. the yardstick against the univariates and the differenced VAR(1).
- **The result is not known before running it.** The tutorial must report
  what the bootstrap says, including "r = 0" if that is the answer.
- **This is the flagship example.** It is the only one where sima's own story
  leads into drvec.

### 6.2 `jenkins_alavi`: the mixed system, and drvec's own reference

- **Data:** muskrat and mink, 1850–1911, 62 years (Jones 1914; Reinsel 1997;
  Mauricio 2006 §4, the paper drvec replicates; `engines/drvec/datasets/mauricio/`).
  art's models are ARIMA(6,1,1) for ln muskrat and AR(4) for ln mink: one d = 1
  and one d = 0. So `canonical_analysis` says the question "does not arise",
  and under the rule of §2.3 sima would not ask it.
- **The lesson is §2.5's mixed case:**
  - muskrat goes in ∇Y₂ and mink in Y₁;
  - r ≥ 1 by the univariate d's;
  - the ladder's model is the VEC with B₂ = 0, and `fixb2=0` tests it.
- **What the oracle already shows:** at p = 2, case 2, the rank test does
  **not** reject r = 0 (LR 8.42 against the 10 % critical value of 13.75; the
  bootstrap with B = 20 gives 11.16 and p 0.29). That conflicts with the
  univariate d's: mink stationary implies r ≥ 1. It teaches the test's power at
  n = 61 and the role of the other evidence. It **must be rerun with B ≥ 499**
  before it goes in a tutorial.
- **Usable files:**
  - drvec's fixtures `mmpre.*.pre` are placeholders (random walks, λ = 1)
    and must not be confused with art's models;
  - the example's art models are the right input.

### 6.3 Lütkepohl's E1: the textbook three-variable case

- **Data:** West German investment, income and consumption, quarterly
  1960–1982, 92 observations (Lütkepohl 2005; JMulTi). It is in
  `engines/drvec/datasets/lutkepohl/e1.dat` and in drvec-python's tests: three
  fue random walks with drift in logs.
- **What the oracle shows** (`e1boot`, B = 20 only): r = 0 rejected (LR 58.65,
  p at the floor), r = 1 not rejected (6.02, p 0.43), so r̂ = 1.
- **What it teaches beyond the rank:**
  - the ill-defined fit `2 1 1 -mean -case 2` (a ridge, criterion 3, a gate
    that rounding flips). That is C2's `study_estimation` case;
  - the cost: about 47 min at B = 499 in Python, so it is the queue's
    demonstration.
- **Route:** the raw entry (`load_data` → `characterize` → route U or V), with
  the `[raw]` extra.

### 6.4 Johansen and Juselius's Danish money demand: restrictions and weak exogeneity

- **Data:** LRM, LRY, IBO and IDE (and LPY), quarterly 1974–1987, 55
  observations (Johansen and Juselius 1990; Johansen 1995 ch. 7). It is in
  `engines/drvec/datasets/urca_denmark.csv` and `gretl/denmark.gdt`, both
  tracked in the public repo, with their sources in its `MANIFEST.md`.
- **What it teaches:** the published case for:
  - a restricted constant (case 2);
  - restrictions on β;
  - weak exogeneity.

  With n = 55, the asymptotic table is least trustworthy here, so the bootstrap
  matters most.
- **Seasonality:** the series need deterministic seasonality in their `.pre`
  (quarterly cos, sin and alter), which is §2.4's D > 0 check made concrete.
- **Cost:** M = 4 means three comparisons. It is the expensive example, best
  shipped with its cache.

### 6.5 Further public data, if wanted

The tracked `urca_*` and `vars_*` sets with their published VECMs:
- UK PPP/UIP (Johansen and Juselius 1992);
- Finland;
- `vars`' Canada.

None is needed for 0.2.0.

---

## 7. Open questions, with a recommendation each

1. **The trigger for N1c.** PROCESOS said "≥ 2 I(1) series with feedback".
   *Recommendation:* "≥ 2 series with d = 1", offered after
   `canonical_analysis` whatever its count, with the menu's emphasis set by
   the count. Drop "with feedback": it is tested inside the VEC (weak
   exogeneity), not assumed before it. The mixed case (§6.2) is offered as an
   option when exactly one series is differenced and another is not, never as
   the default route.
2. **One session or two.** *Recommendation:* the same session and the same
   guion, with a model-kind tag ("VARMA" or "VEC") on each fit, so that
   `forecast` and the IRF tools dispatch on the current model. A cointegration
   study and its fallback to the differenced VARMA are one analysis.
3. **How jobs run.** *Recommendation:* detached subprocesses with an on-disk
   cache keyed by content (§5.3), not in-process threads. It is the only design
   that survives the client and uses more than one core.
4. **A parallel bootstrap inside drvec** (simulate in sequence, fit in
   parallel, bit-identical). *Recommendation:* yes, in drvec, together with the
   accessors of §4.2. drvec 0.1.0 is not uploaded yet, and the release is
   joint, so it costs no extra release. If it slips, sima 0.2.0 still works,
   one core per job.
5. **Exposing the seed.** *Recommendation:* add an optional `seed=` to drvec
   (default: the C's), and stamp every result with it. It is offered only in a
   "Monte Carlo check" of an edge-of-5 % rank, never by default.
6. **Where the half-life of β′Y and Gonzalo–Ng live.** *Recommendation:* in
   sima first, as evidence computed from drvec's structured matrices (an
   engine "ships numbers and never argues"; these are readings). Move them
   into drvec only if the C gets them, to keep the port's parity story simple.
7. **The free model in drvec's restriction LRs** (one est() for `-alpha` and
   `-weakex`; no ladder for `-fixb2row`). *Recommendation:* sima reports the LR
   against the best free logL it knows and shows both when they differ. Also
   register the C's behaviour in atsw-gui's `engines/drvec/docs/BUGS.md` with a
   repro if the gap turns out to change a verdict. Do not change the port alone.
8. **`export_tables` and a run registry.** *Recommendation:* defer. The job
   folders plus the guion JSON already are the registry. LaTeX tables are an
   article's tool, not sima's.
9. **Full rank (r = M).** *Recommendation:* do not extend drvec. When every
   comparison rejects, sima says "at least M − 1" and sends the last question
   to the univariate unit-root evidence and to drvarma's VARMA in levels.
10. **The yardstick rule for a VEC.** Rule 1 says that a model that does not
    forecast better than the univariates has no reason to exist.
    *Recommendation:* keep it for any forecasting use. For a long-run claim
    (an equilibrium, who corrects), report the yardstick as a caveat, not a
    veto, and record the purpose at N1c ("forecast" or "long run"). This
    touches a rule that "is not negotiated", so it is the user's decision.
11. **sima's dependency on drvec.** *Recommendation:* a hard dependency, not an
    extra. drvec is pure Python and needs only what sima already pulls (fue,
    drvarma), at the versions sima 0.2.0 must require anyway (fue ≥ 0.1.18,
    drvarma ≥ 0.3.0).
12. **`study_estimation` for the VEC** (E1's ridge). *Recommendation:* in
    0.2.0, only the declaration ("not a demonstrated maximum") and a
    `multistart` option on `estimate_vec`. The full study (restarts along the
    ridge) comes later, with drvec's own open item on E1.
13. **Tool names.** *Recommendation:* separate `estimate_vec`, `rank_test`,
    `test_restriction`, `add_exogenous`, `irf_bands` and `sweep`, rather than a
    rank argument on `estimate`. They make different claims, as the
    assistants' architecture argues. Extend only the N6 tools, whose question
    does not change.

---

## 8. Dependencies and release order

Already decided, restated:
1. **fue 0.1.18**: the deterministic component by `lib/fuedet`.
2. **drvarma 0.3.0**: GSL's eigensolvers. Unreleased, branch `gsl-gensymmv`.
3. **drvec 0.1.0**: byte-identical to C 0.13. The accessors of §4.2 go in
   before it, if accepted (Q4).
4. **sima 0.2.0**: this study's tools. It requires `drvec>=0.1.0`,
   `drvarma>=0.3.0` and `fue>=0.1.18`.
5. **The atsw release**, with drvec added to the umbrella and the tag
   `drvec-v0.13`.

No tags and no uploads until then; the release is joint. BUG-58..60 (PR #52)
are C defects with their repros and do not block. The port refuses BUG-58's
input, and BUG-59 and BUG-60 do not change a verdict.

## 9. What this study does not do

It writes no code and does not order the work. The implementation plan comes
next, separately. It should start from §4.2 (what drvec must expose), §5.3
(the runner) and §6.1 (the flour prices continuation), the one example where
sima's own analysis already ends at drvec.
