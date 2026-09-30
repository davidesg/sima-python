# `sima` — MCP tool reference

*Generated from the docstrings by `tools/gen_tools_md.py`. Do not edit by hand — edit the docstring.*

**21 tools.** In an MCP server the docstring is what the model reads, so this page and the instruction the model receives are the same text by construction.

---

| tool | what it answers |
|---|---|
| [`check_residuals`](#check-residuals) | N4 — Check the last estimated model as Jenkins and Alavi (1981, §5.2) do. |
| [`estimate`](#estimate) | N3/N4 — Estimate a candidate: cross orders p, q; full or diagonal covariance. |
| [`evaluate`](#evaluate) | N5 — The yardstick: does the candidate forecast better than the univariates? |
| [`export_guion`](#export-guion) | The path of the analysis, node by node, with its evidence and decisions. |
| [`forecast`](#forecast) | N6 — Forecast every series in its level with the last estimated model. |
| [`forecast_uncertainty`](#forecast-uncertainty) | N5/N6 — Jenkins and Alavi's comparison of forecast uncertainty (their |
| [`identify_cross`](#identify-cross) | N2 — What the univariate models do NOT carry: residual cross-correlations. |
| [`identify_matrices`](#identify-matrices) | N2 — Jenkins and Alavi's (1981) two identifications, as matrices. |
| [`impulse_response`](#impulse-response) | N6 — Orthogonalised impulse responses of the last estimated model. |
| [`load_pre`](#load-pre) | N0 — Start a session from the univariate models: one fue file per series. |
| [`plot_forecast`](#plot-forecast) | FIGURE — The forecasts of the last estimated model in the format of FUF |
| [`plot_identification`](#plot-identification) | FIGURE — Jenkins and Alavi's (1981) identification, pair by pair: the |
| [`plot_impulse_response`](#plot-impulse-response) | FIGURE — The orthogonalised impulse responses of the last estimated model. |
| [`plot_residual_ccf`](#plot-residual-ccf) | FIGURE — The residual cross-correlations of the last estimated model, |
| [`plot_variance_decomposition`](#plot-variance-decomposition) | FIGURE — The forecast-error variance decomposition, in the IRF's layout. |
| [`record_decision`](#record-decision) | Record a decision, WHY, on WHAT evidence, and what was set aside. |
| [`reorder`](#reorder) | N6 — The impulse responses under ANOTHER Cholesky order, against the files'. |
| [`run_gate`](#run-gate) | N1 — The diagonal gate: does the joint cast reproduce the univariate models? |
| [`split_inp`](#split-inp) | Convert a multivariate drvarma .inp (deprecated) into one fue .inp per series. |
| [`study_estimation`](#study-estimation) | N4b — Study the current fit when the estimation may be ill-defined. |
| [`variance_decomposition`](#variance-decomposition) | N6 — Forecast-error variance decomposition of the last estimated model. |

---

## `check_residuals`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `nlags` | integer | no | `0` |

N4 — Check the last estimated model as Jenkins and Alavi (1981, §5.2) do.

    (1) The large residuals, judged on the UNCORRELATED transformed residuals
    (the a_it correlate at lag 0, so one by one they cannot be judged), with
    their dates — a known cause goes to intervention analysis, in art, before
    anything else is read. (2) The residual correlation matrices R_k(a), with
    what is beyond the band. (3) The portmanteau matrix Q_ij, as a summary.
    If the matrices show structure, a model for the residuals is entertained
    and combined with the fitted one, as at identification. `nlags` defaults
    to max(6, frequency).

---

## `estimate`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `p` | integer | yes | — |
| `q` | integer | yes | — |
| `diagcov` | boolean | no | `False` |
| `reason` | string | no | `` |
| `links` | string | no | `` |
| `start` | string | no | `zero` |
| `cross` | string | no | `additive` |

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

---

## `evaluate`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `p` | integer | yes | — |
| `q` | integer | yes | — |
| `estwin` | integer | yes | — |
| `horizon` | integer | no | `12` |
| `diagcov` | boolean | no | `False` |
| `links` | string | no | `` |
| `cross` | string | no | `additive` |

N5 — The yardstick: does the candidate forecast better than the univariates?

    Estimates the candidate AND the diagonal system (the univariate models) on
    the first `estwin` observations, holds the parameters fixed, and forecasts
    from every origin to the end of the data, `horizon` steps ahead. Compares
    RMSE and MAPE series by series and horizon by horizon. A VARMA that does not
    gain here has no reason to exist, whatever its in-sample significance.

    `estwin` counts observations of the FIRST series; leave enough data after it
    (at least a few dozen origins) or the comparison says little. `links`: as in
    estimate, the same restricted candidate.

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

---

## `forecast_uncertainty`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `horizon` | integer | no | `0` |

N5/N6 — Jenkins and Alavi's comparison of forecast uncertainty (their
    Table VIII): the standard deviation of the forecast errors by lead time,
    V(l) = SUM psi_j Sigma psi_j', of the last estimated model against the
    univariate models, per cent for series in logs. In sample, parameters
    taken as known: a quick reading of where the multivariate model could
    help; `evaluate` is the test. `horizon` defaults to the frequency (4 for
    annual data).

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
    file.

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
    figure of identify_matrices. One row per pair of series, in drvus' CCF
    panel (the one drtran reads), the correlation function R_k above the partial
    S_k, both two-sided, same lag axis and scale — as art's ACF over PACF.

    method=2 (default): the residuals of the univariate models (prewhitened,
    each series by ITS OWN model — Haugh's CCF, not a transfer function's).
    Band 2/sqrt(n); between the panels Haugh's S* (1976), the test that the
    two are independent, in total and by side (k > 0, k < 0: who leads).
    The CCF's cut-off after q suggests an MA(q) residual model.
    method=1: the stationary series w_t, not prewhitened. The CCF band is
    Bartlett's (3.13) for unrelated series, lag by lag: the series are not
    white, and a 2/sqrt(n) band would show their common cycles as cross terms.
    Here the partial is the decisive one: a cut-off after p suggests an AR(p).
    Lag k > 0: the second series leads; k < 0: the first. With three or more
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

---

## `plot_residual_ccf`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `nlags` | integer | no | `0` |
| `path` | string | no | `` |

FIGURE — The residual cross-correlations of the last estimated model,
    pair by pair: drvus' two-sided CCF (the suite's reference), with the
    Hosking Q. What is left beyond the band is what the model does not carry.
    `nlags` defaults to twice the frequency.

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
    dashed. A row reads the same as in plot_impulse_response.

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

---
