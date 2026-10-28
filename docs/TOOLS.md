# `sima` — MCP tool reference

*Generated from the docstrings by `tools/gen_tools_md.py`. Do not edit by hand — edit the docstring.*

**44 tools.** In an MCP server the docstring is what the model reads, so this page and the instruction the model receives are the same text by construction.

---

| tool | what it answers |
|---|---|
| [`add_exogenous`](#add-exogenous) | C4 — Exogenous inputs to the current VEC, dispatched by their order of |
| [`build_univariate`](#build-univariate) | N0u — ROUTE U from raw data (docs/STUDY-raw-entry.md): build each |
| [`canonical_analysis`](#canonical-analysis) | N1b — Box and Tiao's (1977) canonical analysis of the transformed LEVELS |
| [`characterize`](#characterize) | N0c — Each raw series' transformation, with art's engine and in art's |
| [`check_residuals`](#check-residuals) | N4 — Check the last estimated model as Jenkins and Alavi (1981, §5.2) do, |
| [`estimate`](#estimate) | N3/N4 — Estimate a candidate: cross orders p, q; full or diagonal covariance. |
| [`estimate_vec`](#estimate-vec) | C2 — The adopted VEC at rank r (drvec.fit with -fdhess: the standard |
| [`evaluate`](#evaluate) | N5 — The yardstick: does the candidate forecast better than the univariates? |
| [`examples`](#examples) | The worked examples that come with sima, to see how it works in real |
| [`export_guion`](#export-guion) | The path of the analysis, node by node, with its evidence and decisions. |
| [`forecast`](#forecast) | N6 — Forecast every series in its level with the last estimated model. |
| [`forecast_uncertainty`](#forecast-uncertainty) | N5/N6 — Jenkins and Alavi's comparison of forecast uncertainty (their |
| [`identify_cross`](#identify-cross) | N2 — What the univariate models do NOT carry: residual cross-correlations. |
| [`identify_echelon`](#identify-echelon) | N2 — the third form, the ECHELON VARMA of Lutkepohl and Poskitt (1996), |
| [`identify_matrices`](#identify-matrices) | N2 — Jenkins and Alavi's (1981) two identifications, as matrices. |
| [`impulse_response`](#impulse-response) | N6 — Orthogonalised impulse responses of the last estimated model. |
| [`irf_bands`](#irf-bands) | C6 — Bands for the level responses and the FEVD of the current VEC, by |
| [`job_cancel`](#job-cancel) | Cancel a job: a queued one leaves the queue; a running one has its whole |
| [`job_result`](#job-result) | The FINAL result of a finished job, with its report: a rank test's table |
| [`job_status`](#job-status) | A job's state — queued, running, done, failed or cancelled — its progress |
| [`jobs`](#jobs) | Every job sima knows on this machine (the registry, ~/.sima/jobs or |
| [`load_data`](#load-data) | N0r — RAW DATA: an analyst with series and no univariate models |
| [`load_example`](#load-example) | N0 for a worked example: copy its files to a working folder (`dest`, |
| [`load_pre`](#load-pre) | N0 — Start a session from the univariate models: one fue file per series. |
| [`long_run`](#long-run) | C5 — The long run of the current VEC, read: theta (beta normalised, with |
| [`plot_forecast`](#plot-forecast) | FIGURE — The forecasts of the last estimated model in the format of FUF |
| [`plot_identification`](#plot-identification) | FIGURE — Jenkins and Alavi's (1981) identification, pair by pair: the |
| [`plot_impulse_response`](#plot-impulse-response) | FIGURE — The orthogonalised impulse responses of the last estimated model. |
| [`plot_rank_bootstrap`](#plot-rank-bootstrap) | FIGURE — The rank test's bootstrap: for each comparison r -> r + 1, the |
| [`plot_residual_ccf`](#plot-residual-ccf) | FIGURE — The residual cross-correlations of the last estimated model, |
| [`plot_variance_decomposition`](#plot-variance-decomposition) | FIGURE — The forecast-error variance decomposition, in the IRF's layout. |
| [`prepare_vec`](#prepare-vec) | N1c/C0 — The cointegration question, and the VEC's specification with its |
| [`rank_test`](#rank-test) | C1 — The cointegration rank, by PARAMETRIC BOOTSTRAP (drvec's sequential |
| [`record_decision`](#record-decision) | Record a decision, WHY, on WHAT evidence, and what was set aside. |
| [`reorder`](#reorder) | N6 — The impulse responses under ANOTHER Cholesky order, against the files'. |
| [`run_gate`](#run-gate) | N1 — The diagonal gate: does the joint cast reproduce the univariate models? |
| [`simplify`](#simplify) | N4s — Tiao and Box's (1981, §4) simplification by coefficient, on the |
| [`split_inp`](#split-inp) | Convert a multivariate drvarma .inp (deprecated) into one fue .inp per series. |
| [`structure`](#structure) | N4t — Is the system simultaneous? (Tiao and Box 1981, §3.1, §5.2.) On |
| [`study_estimation`](#study-estimation) | N4b — Study the current fit when the estimation may be ill-defined. |
| [`sweep`](#sweep) | C7 — Robustness: a grid of fits over the same files, one CACHED JOB per |
| [`test_restriction`](#test-restriction) | C3 — A restriction on alpha, beta or Gamma of the current VEC, tested by |
| [`variance_decomposition`](#variance-decomposition) | N6 — Forecast-error variance decomposition of the last estimated model. |
| [`write_specs`](#write-specs) | N0v — ROUTE V from raw data (docs/STUDY-raw-entry.md): the vector |

---

## `add_exogenous`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `series` | string | no | `` |
| `inputs` | string | no | `` |
| `links` | string | no | `` |
| `adopt` | boolean | no | `False` |

C4 — Exogenous inputs to the current VEC, dispatched by their order of
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
    restriction on alpha. `adopt` makes the fit with inputs current.

---

## `build_univariate`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `out_dir` | string | no | `` |
| `overwrite` | boolean | no | `False` |

N0u — ROUTE U from raw data (docs/STUDY-raw-entry.md): build each
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
    `overwrite`.

---

## `canonical_analysis`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `p` | integer | no | `0` |
| `near` | number | no | `0.9` |

N1b — Box and Tiao's (1977) canonical analysis of the transformed LEVELS
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

---

## `characterize`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `set` | string | no | `` |

N0c — Each raw series' transformation, with art's engine and in art's
    order: lambda (Box-Cox, 0 or 1), d (ADF + KPSS, art's policy: one step at a
    time), seasonality (HAC F-test; harmonics proposed when detected) and a
    preliminary outlier scan (reported, not treated). Each series keeps its
    OWN lambda and d — no joint consensus: forcing them alike was the old
    sima's first fault.

    `set` records the analyst's changes on top of the proposal:
    "MINK: lam=0, d=0; MUSKRAT: d=1, harmonics=no" (keys lam, d, D,
    harmonics). It is the starting point of both routes (U: the univariate
    models first; V: the vector first).

---

## `check_residuals`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `nlags` | integer | no | `0` |

N4 — Check the last estimated model as Jenkins and Alavi (1981, §5.2) do,
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

---

## `estimate`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `p` | integer | no | `0` |
| `q` | integer | no | `0` |
| `diagcov` | boolean | no | `False` |
| `reason` | string | no | `` |
| `links` | string | no | `` |
| `start` | string | no | `` |
| `cross` | string | no | `additive` |
| `zeros` | string | no | `` |
| `indices` | string | no | `` |

N3/N4 — Estimate a candidate: cross orders p, q; full or diagonal covariance.

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

    `start`: where the cross terms start — "zero" (the default for the
    VARMA) or "preliminary", Jenkins and Alavi's preliminary estimates (the
    cross MA from the univariate residuals' cross covariances, the cross AR
    from Yule-Walker). Usually the same optimum in fewer iterations; on an
    ill-defined estimation (the MA wall) a second path worth comparing. The
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

---

## `estimate_vec`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `r` | integer | yes | — |
| `normalise_on` | string | no | `` |
| `theory` | string | no | `` |
| `multistart` | integer | no | `0` |

C2 — The adopted VEC at rank r (drvec.fit with -fdhess: the standard
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
    on the normalisation): restrictions go by LR (test_restriction).

---

## `evaluate`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `p` | integer | no | `0` |
| `q` | integer | no | `0` |
| `estwin` | integer | no | `0` |
| `horizon` | integer | no | `12` |
| `diagcov` | boolean | no | `False` |
| `links` | string | no | `` |
| `cross` | string | no | `additive` |
| `zeros` | string | no | `` |
| `indices` | string | no | `` |
| `yardstick` | string | no | `` |

N5 — The yardstick: does the candidate forecast better than the univariates?

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

---

## `examples`

The worked examples that come with sima, to see how it works in real
    time: each is a real analysis, from the univariate models built in art,
    run node by node with the same tools and pauses as any other.
    load_example(<name>) starts one.

---

## `export_guion`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `save` | boolean | no | `True` |
| `html` | boolean | no | `True` |

The path of the analysis, node by node, with its evidence and decisions.

    This is what makes the analysis reviewable and repeatable: every tool call
    and every recorded decision, in order. Saved next to the first file as
    <first>.sima.json when `save`, so that the record travels with the data;
    with `html` (default) also <first>.sima.html, a self-contained page in
    art's style: the steps in a table, a section per node with the evidence,
    the decisions highlighted (who decided, what was set aside) and the
    figures drawn at each step (they are saved in figs/ next to the files).

---

## `forecast`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `horizon` | integer | no | `12` |

N6 — Forecast every series in its level with the last estimated model.

    Each series goes back to its level with its own univariate model:
    deterministic terms (known in the future), its differencing, its Box-Cox.
    The 95% band is built on the transformed scale and mapped back.
    On a VEC (the current model is one): the VEC written in levels
    (drvec.to_levels_varma) and forecast by drvarma's forecaster — one
    forecaster for every system — with each file's deterministic path and
    Box-Cox; drvec's band multiplier.

---

## `forecast_uncertainty`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `horizon` | integer | no | `0` |
| `estwin` | integer | no | `0` |

N5/N6 — Jenkins and Alavi's comparison of forecast uncertainty (their
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

---

## `identify_cross`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `nlags` | integer | no | `0` |

N2 — What the univariate models do NOT carry: residual cross-correlations.

    Reads the CCFs of the residuals of the diagonal system, pair by pair. Those
    residuals are each series' own innovations — prewhitened by construction —
    so a cross-correlation beyond the band is evidence of a dynamic between the
    series. Contemporaneous correlation points to a full innovation covariance;
    lead-lag correlation points to cross orders p (and q). Returns the evidence
    and the menu of candidates, each with its argument. It does not choose.

    `nlags` defaults to twice the frequency (24 for monthly data).

---

## `identify_echelon`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `max_index` | integer | no | `3` |
| `criterion` | string | no | `SC` |

N2 — the third form, the ECHELON VARMA of Lutkepohl and Poskitt (1996),
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

---

## `identify_matrices`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `nlags` | integer | no | `0` |
| `qmax` | integer | no | `2` |

N2 — Jenkins and Alavi's (1981) two identifications, as matrices.

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

---

## `impulse_response`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `horizon` | integer | no | `12` |
| `bands` | boolean | no | `True` |
| `ndraws` | integer | no | `800` |

N6 — Orthogonalised impulse responses of the last estimated model.

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

---

## `irf_bands`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `N` | integer | no | `499` |
| `seed` | integer | no | `0` |
| `wait` | number | no | `20.0` |

C6 — Bands for the level responses and the FEVD of the current VEC, by
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
    Carlo check (Python engine).

---

## `job_cancel`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `job_id` | string | yes | — |

Cancel a job: a queued one leaves the queue; a running one has its whole
    process tree killed (the runner, drvec C or the Python pool) and its folder
    marked cancelled, with no result written. A finished job is not touched.
    The same call later starts it again from the beginning (a cancelled run
    leaves nothing to resume).

---

## `job_result`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `job_id` | string | yes | — |

The FINAL result of a finished job, with its report: a rank test's table
    and proposed rank (recorded at C1), the IRF bands (then used by
    impulse_response and the plots), a sweep cell. A job that is not finished
    has no result: this tool says so and returns nothing partial — a decision
    waits for it (the autonomous lane does not decide a node before).

---

## `job_status`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `job_id` | string | yes | — |

A job's state — queued, running, done, failed or cancelled — its progress
    ("replication k of B, comparison r -> r + 1, ok/simfail/fitfail so far"
    for a rank test; the replications for the IRF bands; the cells for a sweep),
    the elapsed time and the rate. Never a provisional number: a finished
    comparison is said finished, an unfinished one shows its counts only. The
    result itself comes from job_result once the job is done. Jobs survive the
    server: an id from an earlier conversation still answers here.

---

## `jobs`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | no | `` |

Every job sima knows on this machine (the registry, ~/.sima/jobs or
    SIMA_JOBS_HOME): id, tool, status, label and progress, the running and
    queued first. `name` keeps only one session's. Jobs outlive the server
    and the conversation; their folders (sima_jobs/<id>/, next to the first
    file) hold the engine's files and the result.

---

## `load_data`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `path` | string | yes | — |
| `freq` | integer | no | `0` |
| `start` | string | no | `` |

N0r — RAW DATA: an analyst with series and no univariate models
    (docs/STUDY-raw-entry.md). An Excel (.xlsx/.xls) or CSV table, one column
    per series in ORIGINAL levels (never transformed or differenced), a header
    row with the names, and optionally a first column of dates (a year, or
    year-period: 1972-08, 1972Q3).

    `freq`: 1, 4 or 12 (0: inferred from the date column). `start`: the first
    date, "1972-08" or "1850" (empty: from the date column). The table must be
    complete on one common calendar: missing values are refused, with where.
    Next: characterize — each series' transformation with art's engine.

---

## `load_example`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | no | `jenkins_alavi` |
| `session` | string | no | `` |
| `dest` | string | no | `` |

N0 for a worked example: copy its files to a working folder (`dest`,
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

---

## `load_pre`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `paths_json` | string | yes | — |

N0 — Start a session from the univariate models: one fue file per series.

    `paths_json` is a JSON list of paths to fue files — `.pre` (optima, from art
    or fue) or `.inp` (specifications) — in the order you want the system (it is
    also the Cholesky order of the impulse responses). This is how you arrive
    from mtram when it found a cycle: load the SAME `.pre` files it had.

    The files are read by fue's own parser and recognised by their content. The
    series must share their frequency and their LAST date (BUG-2): different
    start dates are aligned at the end; different ends are refused.

---

## `long_run`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `horizon` | integer | no | `0` |

C5 — The long run of the current VEC, read: theta (beta normalised, with
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
    years of seasonal data).

---

## `plot_forecast`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `horizon` | integer | no | `24` |
| `series` | string | no | `` |
| `path` | string | no | `` |

FIGURE — The forecasts of the last estimated model in the format of FUF
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

---

## `plot_identification`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `method` | integer | no | `2` |
| `nlags` | integer | no | `0` |
| `pairs` | string | no | `` |
| `path` | string | no | `` |

FIGURE — Jenkins and Alavi's (1981) identification, pair by pair: the
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
    the sample supports (n / (3m)), marked on the panel.

---

## `plot_impulse_response`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `horizon` | integer | no | `24` |
| `bands` | boolean | no | `True` |
| `ndraws` | integer | no | `500` |
| `path` | string | no | `` |

FIGURE — The orthogonalised impulse responses of the last estimated model.

    Drawn as what an impulse response is, a function of the lag like an ACF:
    one panel per (response, shock), thick impulses at h = 0..H, the seasonal
    grid, and the 95 % Monte-Carlo band dashed (it follows h). Cholesky in the
    order of the files, as impulse_response. The numbers are impulse_response's.
    On a VEC: the level responses (drvec), with the bootstrap's 90 % band
    from irf_bands when it has run.

---

## `plot_rank_bootstrap`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `job_id` | string | no | `` |
| `path` | string | no | `` |

FIGURE — The rank test's bootstrap: for each comparison r -> r + 1, the
    histogram of the B bootstrap statistics LR*, the OBSERVED LR (solid), the
    bootstrap's 90/95/99 % critical values (dashed) and, for cases 1 and 2,
    the asymptotic 5 % value (dotted: orientation only). From the finished
    rank test of the current specification (the one with the largest B), or
    `job_id`'s. Read from the job's .boot file with drvec's own reader.

---

## `plot_residual_ccf`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `nlags` | integer | no | `0` |
| `path` | string | no | `` |

FIGURE — The residual cross-correlations of the last estimated model,
    pair by pair: GraphMaker's two-sided CCF (Treadway's, the suite's
    reference), titled "A - B" with A leading at k > 0, and Hosking's
    portmanteau below as GraphMaker labels it, P (not Ljung-Box's Q). What is
    left beyond the band is what the model does not carry.
    `nlags` defaults to twice the frequency. On a VEC: the residuals of its
    stationary form (nabla Y2 and the equilibrium errors, drvec's).

---

## `plot_variance_decomposition`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `horizon` | integer | no | `24` |
| `bands` | boolean | no | `True` |
| `ndraws` | integer | no | `500` |
| `path` | string | no | `` |

FIGURE — The forecast-error variance decomposition, in the IRF's layout.

    Panel (i, j): the % of the h-step forecast-error variance of i due to the
    shock of j, h = 1..H, as impulses on a 0-100 axis with the 95 % band
    dashed. A row reads the same as in plot_impulse_response. On a VEC: the
    levels' decomposition (drvec), the bootstrap's band from irf_bands.

---

## `prepare_vec`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `purpose` | string | no | `` |
| `p` | integer | no | `0` |
| `q` | integer | no | `0` |
| `case` | string | no | `pre` |
| `nodrift` | string | no | `` |
| `mixed` | boolean | no | `False` |

N1c/C0 — The cointegration question, and the VEC's specification with its
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
    canonical_analysis ran, up to its first run of non-significant lags). `q`: the MA order (0 by default). `case`: 1, 2, 3
    or "pre" (default: each drift as its file's mean says). `nodrift`: series
    whose drift is held at 0 (case 3/pre). Never offered: drvec's refused
    options (-warma, -mawarma, -specs, -matest, -artest, -m 2, -rankadm, the
    instruments and the writers). Next: rank_test, the only way to a rank.

---

## `rank_test`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `B` | integer | no | `499` |
| `multistart` | integer | no | `0` |
| `seed` | integer | no | `0` |
| `wait` | number | no | `20.0` |

C1 — The cointegration rank, by PARAMETRIC BOOTSTRAP (drvec's sequential
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
    the Python engine), never the default.

---

## `record_decision`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `node` | string | yes | — |
| `decision` | string | yes | — |
| `reason` | string | no | `` |
| `evidence` | string | no | `` |
| `alternatives` | string | no | `` |
| `decided_by` | string | no | `analyst` |

Record a decision, WHY, on WHAT evidence, and what was set aside.

    Every node that opens a decision (which files, which candidate, keep the
    VARMA or stay with the univariates, what to do with a fit on the MA wall,
    which Cholesky order) should leave one. Example: node "N5", decision "stay
    with the univariates", reason "the VARMA gains in no cell at h >= 6",
    evidence "RMSE ratio 1.02-1.11 over 36 origins", alternatives "VARMA(1,0)
    full: better in sample (LR p 0.01), worse out of sample". In the
    AUTONOMOUS lane this is where your reasoning is written down, with
    decided_by="LLM"; a decision without its reason is not documented.

---

## `reorder`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `order_json` | string | yes | — |
| `horizon` | integer | no | `12` |

N6 — The impulse responses under ANOTHER Cholesky order, against the files'.

    The reduced-form model (Phi, Theta, Sigma) does not depend on the order of
    the series; only the orthogonalisation does. So nothing is re-estimated:
    the model is permuted, the responses recomputed, and put back in the
    files' order to compare cell by cell. A response that changes sign or
    size with the order is an assumption, not a finding. With a diagonal
    covariance the order does not matter at all, and the tool says so.
    `order_json`: the series names in the new order, e.g. '["WTI", "IPC_ES"]'.
    On a VEC it REFUSES: there the order is also the normalisation, so another
    order is another fit (estimate_vec with normalise_on).

---

## `run_gate`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |

N1 — The diagonal gate: does the joint cast reproduce the univariate models?

    Each series is fitted alone on the common window; the diagonal system is
    then evaluated at those optima. The identity logL_joint = SUM logL_i is
    exact. If it fails, the analysis STOPS: nothing estimated on top of a joint
    model that does not reproduce its parts can be trusted.

    It also says whether each file is an OPTIMUM (it does not move when
    re-estimated) or a SPECIFICATION (it moves), which decides whether the
    yardstick is the analyst's certified model or not.

---

## `simplify`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `t` | number | no | `1.0` |

N4s — Tiao and Box's (1981, §4) simplification by coefficient, on the
    current fit: the cross coefficients (and, on route V or in the echelon
    form, each series' own AR/MA coefficients) with |t| < `t` are held at
    zero, the model is refitted, and the restriction is tested by LR against
    the full fit, with AIC and BIC. The restricted fit is cached: adopting it
    (the estimate call in the menu) is instant. Route U's univariate models
    are never touched — they are art's; the echelon form's own part, which
    replaces their regular ARMA, is sima's, and is simplified like the rest. Several rounds are normal (Tiao and Box simplified
    the SCC model twice).

---

## `split_inp`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `path` | string | yes | — |
| `out_dir` | string | yes | — |
| `mean` | boolean | no | `True` |
| `harmonics` | boolean | no | `False` |
| `ar` | integer | no | `0` |
| `ma` | integer | no | `0` |

Convert a multivariate drvarma .inp (deprecated) into one fue .inp per series.

    Each file is a SPECIFICATION with the old file's transformation (and, if
    asked, an estimated mean, seasonal harmonics, a free regular AR/MA). Take
    each one through art to build its univariate model, then come back with the
    .pre files: the univariate models are the seed and the yardstick.

---

## `structure`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `alpha` | number | no | `0.05` |

N4t — Is the system simultaneous? (Tiao and Box 1981, §3.1, §5.2.) On
    the current fit: for each ordered pair, the LR test that series j does not
    enter series i's equation (all its cross AR and MA lags at zero); with up
    to 4 series, every triangular ordering (each series receives only from
    those before it). If an ordering stands, the system is a TRANSFER
    NETWORK — a triangular VARMA is a transfer function model — and sima
    offers the hand-back to mtram with the same .pre files; it does not hand
    back on its own. The verdict is only as good as the order of the fit:
    Tiao and Box's gas furnace shows a spurious feedback at low order.

---

## `study_estimation`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `restarts` | integer | no | `6` |
| `retreat` | number | no | `0.97` |

N4b — Study the current fit when the estimation may be ill-defined.

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

---

## `sweep`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `p` | string | no | `` |
| `case` | string | no | `` |
| `estwin` | string | no | `` |
| `B` | integer | no | `0` |
| `wait` | number | no | `20.0` |

C7 — Robustness: a grid of fits over the same files, one CACHED JOB per
    cell, around the current VEC (its r, restrictions and normalisation).
    `p`: AR orders, e.g. "1,2,3"; `case`: "2, 3, pre, trend" (trend, case
    4, for a single fit only); `estwin`: subsamples, rows 1..E of nabla Y
    ("60, 70, 80"; the recursive estimate). Empty: the current one.
    `B` > 0 adds a rank test per (p, case) cell, with its bootstrap (jobs
    too). The table — logL, parameters, the stopping criterion, theta and
    alpha per cell; r-hat for the rank cells — fills as the cells finish:
    call it again with the same grid (the cells are cached). It claims
    nothing beyond its cells: what it preserves is the list of what was run,
    and why, in the guion.

    At C1, before any VEC (prepare_vec's specification, `B` required, no
    `estwin`): the RANK over p, each order its own bootstrap — what rank_test
    offers when n / (M p) is small and the verdict can flip with p.

---

## `test_restriction`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `weakex` | string | no | `` |
| `alpha` | string | no | `` |
| `fixb2` | string | no | `` |
| `fixb2row` | string | no | `` |
| `gamma` | string | no | `` |
| `adopt` | boolean | no | `False` |

C3 — A restriction on alpha, beta or Gamma of the current VEC, tested by
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
    under a restriction.

---

## `variance_decomposition`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `horizon` | integer | no | `12` |
| `bands` | boolean | no | `True` |
| `ndraws` | integer | no | `800` |

N6 — Forecast-error variance decomposition of the last estimated model.

    For each series and horizon, the share of its forecast-error variance that
    comes from each series' innovation: how much of what is not predictable in
    one series is really the other's surprise. Same Cholesky order as
    impulse_response, and the same caveat: with correlated innovations the
    shares of the first series in the order are inflated by construction.
    With `bands` (default): 95% Monte-Carlo bands at the last horizon.
    On a VEC: the decomposition of the LEVELS' forecast errors (drvec), with
    the bootstrap's bands when irf_bands has run.

---

## `write_specs`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `out_dir` | string | no | `` |
| `overwrite` | boolean | no | `False` |

N0v — ROUTE V from raw data (docs/STUDY-raw-entry.md): the vector
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
    univariate optima.

---
