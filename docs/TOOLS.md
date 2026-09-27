# `sima` — MCP tool reference

*Generated from the docstrings by `tools/gen_tools_md.py`. Do not edit by hand — edit the docstring.*

**11 tools.** In an MCP server the docstring is what the model reads, so this page and the instruction the model receives are the same text by construction.

---

| tool | what it answers |
|---|---|
| [`estimate`](#estimate) | N3/N4 — Estimate a candidate: cross orders p, q; full or diagonal covariance. |
| [`evaluate`](#evaluate) | N5 — The yardstick: does the candidate forecast better than the univariates? |
| [`export_guion`](#export-guion) | The path of the analysis, node by node, with its evidence and decisions. |
| [`forecast`](#forecast) | N6 — Forecast every series in its level with the last estimated model. |
| [`identify_cross`](#identify-cross) | N2 — What the univariate models do NOT carry: residual cross-correlations. |
| [`impulse_response`](#impulse-response) | N6 — Orthogonalised impulse responses of the last estimated model. |
| [`load_pre`](#load-pre) | N0 — Start a session from the univariate models: one fue file per series. |
| [`record_decision`](#record-decision) | Record a decision and its reason in the guion. |
| [`run_gate`](#run-gate) | N1 — The diagonal gate: does the joint cast reproduce the univariate models? |
| [`split_inp`](#split-inp) | Convert a multivariate drvarma .inp (deprecated) into one fue .inp per series. |
| [`variance_decomposition`](#variance-decomposition) | N6 — Forecast-error variance decomposition of the last estimated model. |

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

N3/N4 — Estimate a candidate: cross orders p, q; full or diagonal covariance.

    Each series keeps its univariate model on the diagonal (its ARMA factors are
    re-estimated jointly, its deterministic terms stay as in its file). Reports
    the parameters, the LR test against the univariates (in sample: necessary,
    not sufficient), the innovation correlations, the residual portmanteau and
    how the optimiser stopped. `reason` is recorded in the guion: say why this
    candidate.

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

N5 — The yardstick: does the candidate forecast better than the univariates?

    Estimates the candidate AND the diagonal system (the univariate models) on
    the first `estwin` observations, holds the parameters fixed, and forecasts
    from every origin to the end of the data, `horizon` steps ahead. Compares
    RMSE and MAPE series by series and horizon by horizon. A VARMA that does not
    gain here has no reason to exist, whatever its in-sample significance.

    `estwin` counts observations of the FIRST series; leave enough data after it
    (at least a few dozen origins) or the comparison says little.

---

## `export_guion`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `save` | boolean | no | `True` |

The path of the analysis, node by node, with its evidence and decisions.

    This is what makes the analysis reviewable and repeatable: every tool call
    and every recorded decision, in order. Saved next to the first file as
    <first>.sima.json when `save`, so that the record travels with the data.

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

## `impulse_response`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `horizon` | integer | no | `12` |

N6 — Orthogonalised impulse responses of the last estimated model.

    Cholesky in the ORDER OF THE FILES: an identifying assumption, stated in the
    output. With a strong contemporaneous correlation, reload the files in
    another order and compare before reading a response as a finding.

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

## `record_decision`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `node` | string | yes | — |
| `decision` | string | yes | — |

Record a decision and its reason in the guion.

    Every node that opens a decision (which files, which candidate, keep the
    VARMA or stay with the univariates, which Cholesky order) should leave one:
    the decision, and the evidence it rests on. Example: node "N5", decision
    "stay with the univariates: the VARMA gains in no cell at h >= 6". In the
    autonomous lane this is where your reasoning is written down.

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

## `variance_decomposition`

**Arguments**

| name | type | required | default |
|---|---|---|---|
| `name` | string | yes | — |
| `horizon` | integer | no | `12` |

N6 — Forecast-error variance decomposition of the last estimated model.

    For each series and horizon, the share of its forecast-error variance that
    comes from each series' innovation: how much of what is not predictable in
    one series is really the other's surprise. Same Cholesky order as
    impulse_response, and the same caveat: with correlated innovations the
    shares of the first series in the order are inflated by construction.

---
