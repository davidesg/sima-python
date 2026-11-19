---
id: BUG-0018
title: canonical_analysis read the levels with each model's harmonics and interventions inside; in route U it inflated lam and the order by M(l), which went on to prepare_vec as p
status: fixed
severity: medium
component: evidence
found_in: 0.2.0
fixed_in: 0.2.5
reported: 2026-10-31
reporter: David / Claude — reanalysis of a quarterly trivariate system (Ecuador, 2003–2019); measured again on the US monetary VAR, 19-nov-2026
tags:
  - canonical_analysis
  - box-tiao
  - route-u
  - prepare_vec
references:
  - drvarma src/drvarma/ladder.py LadderSeries.levels ("Deterministic terms are not removed")
  - drvarma src/drvarma/ladder.py LadderSeries.stationary (w without the model's deterministic terms)
  - src/sima/mcp_server.py canonical_analysis (s.canonical feeds prepare_vec's p and estimate_vec's weights)
  - src/sima/levels.py (the fix)
  - docs/STUDY-tiao-box.md (E1)
  - bugs/BUG-0018-repro/repro.py
---

## Summary

In route U, `canonical_analysis` ran Box and Tiao's (1977) canonical analysis
on `LadderSeries.levels()`: each series' Box-Cox and seasonal differences
**with its deterministic terms inside** (harmonics, steps, impulses). The
report warned in one line ("Interventions are not removed from the levels"),
but the result was used as if they were not there:

- a harmonic is predictable by construction and a step acts as a local unit
  root: both push lam towards 1 and lengthen the order by M(l);
- `s.canonical` feeds **prepare_vec's default p** (`p_run` when it exceeds
  the AR rule) and the **weights estimate_vec shows beside beta**.

It was inconsistent with the rest of sima: Jenkins and Alavi's method 1 reads
`LadderSeries.stationary()`, which removes the model's deterministic terms, and
drvec has them in its likelihood. The canonical analysis was the one reading
that saw the series with them inside. Recorded in October in a working copy and
never committed; filed here with a public repro.

## Impact

Route U with deterministic terms in the `.pre` files, which is the normal case:
deterministic seasonality (art, purpose "multivariate") and any intervention.

- The contiguous order by M(l) is inflated. `prepare_vec` without `p` takes
  it when it exceeds the AR rule, so it proposes too many lags, which costs
  the rank test power.
- sqrt(lam) of a stationary component moves towards the 0.9 threshold.
- The weights shown beside beta mix the dynamics with the steps.

## Reproduction

`bugs/BUG-0018-repro/`: the US monetary VAR, monthly 1990:01–2007:12 (FRED:
IPB50001N, CPIAUCNS, MCOILWTICO, FEDFUNDS), with the univariate models guided
in art. IPI and IPC carry harmonics and interventions, WTI an impulse, FF
none.

```
load_pre("m", [IPI_m07, IPC_m07, WTI_m03, FF_m03]); run_gate("m"); canonical_analysis("m")
```

| levels | order by M(l) (`p_run`) | sqrt(lam) |
|---|---|---|
| as they were (the deterministic terms inside) | **14** | 0.948 / 0.992 / 0.998 / 1 |
| seasonality removed, interventions inside | 8 | 0.941 / 0.993 / 0.998 / 1 |
| seasonality and interventions removed | **4** | 0.946 / 0.995 / 0.998 / 1 |

`repro.py` exits 1 while `p_run` is 14, 0 when it is 4.

The original case (quarterly, n = 68) gave the same pattern: order 4 with the
terms inside, 2 without, and 2 is what the other identifications of that
system gave.

## Root cause

`LadderSeries.levels()` returns y = BoxCox(x) with the seasonal differences,
without subtracting the deterministic terms; `canonical_analysis` (route U)
passed it to `evidence.canonical_report` as it was.

## Resolution

In sima (`src/sima/levels.py`), with no new engine: `stationary()` is the
differences of the levels minus those of the deterministic terms, computed by
fue's cast with the model's own coefficients and time origin (the gate's). With
the coefficients of the terms to KEEP set to zero, the differences of the
levels minus w are exactly the differences of the terms to remove; integrated,
those terms in levels (up to a constant the canonical VAR absorbs).

- **Seasonality** (cos, sin, alter, seasonal dummies, Easter): always removed.
- **Interventions** (impulses, steps, ramps, their transfer functions, custom
  regressors): removed by default; `interventions="keep"` leaves them in.
  The answer always gives the other reading too (sqrt(lam) and the order),
  so the difference shows without asking for it. Analyst's decision,
  19-nov-2026.
- **Never mu nor a trend**: the cast does not subtract mu, and the drift is
  the common growth the analysis has to see (tested: IPC's cleaned levels keep
  its mu, 0.224).
- The table says, series by series, what was removed; the guion records the
  switch.

Route V's raw path (the characterization's levels) is unchanged and keeps its
warning. drvarma's `levels()` is unchanged (engines stay homologated).

## Validation

- `repro.py`: 1 on 0.2.4, 0 with the fix.
- `tests/test_bug_0018_canonical_levels.py`: the order 4, the switch (8 with
  the interventions kept), mu kept, a model without deterministic terms read
  exactly as before, the comparison placed before the decision.
- The suite's canonical tests (hog, flour, Johansen and Juselius) unchanged:
  their models carry no deterministic terms.
