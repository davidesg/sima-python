---
id: BUG-0012
title: With files of different rescaling factors, everything that crosses series is in engine units — a true β = −1 is rejected with p = 0.0000 and nothing warns
status: fixed
severity: high
component: vec
found_in: 0.2.2
fixed_in: 0.2.3
reported: 2026-11-15
reporter: David / Claude — audit of the scale across the whole ladder
tags:
  - scale
  - vec
  - restriction
  - units
references:
  - src/sima/mcp_vec.py (test_restriction: fixb2, fixb2row, alpha), src/sima/vec.py:441-444, :852, :914-919 (theta)
  - src/sima/evidence.py (the VARMA table: the cross terms), :920 (the 0.005 cutoff of the canonical weights)
  - src/sima/mcp_server.py:622-627 (_set_yardstick compares lambda, d, D; not the factor)
  - atsw-gui gui/sim/src/pagina.c:27-30, :397-401 (the GUI's rule: each thing in the units of its series)
  - atsw-gui engines/drvec/src/drvec.c:7282-7294 (the C's warning)
  - bugs/BUG-0012-repro/repro.py
---

## Summary

Each `.pre` brings its rescaling factor and the system is built in
w = factor·BoxCox(z). If the factors do not coincide, each coefficient between
series carries the ratio of the two, and sima presents it and tests it as is.
Two series in logarithms with log Y − log X stationary (β = (1, −1)):

```
factor Y=100, X=100:  beta = -0.994222   alpha = 0.309104 (t 2.299)    H0 beta = -1: LR = 0.03, p = 0.8692
factor Y=100, X=1:    beta = -0.009955   alpha = 30.732151 (t 306.595) H0 beta = -1: LR = 37.46, p = 0.0000
```

The same data and the same fit (the same likelihood in units of y). In the
VARMA, the cross term AR1[Y<-X] comes out 45.84 instead of 0.4584. Neither
`load_pre`, nor `prepare_vec`, nor `estimate_vec` says that the files do not
share a factor; drvec C warns about it and the port does not (drvec
`bugs/py-pre-mixed-refactors-silent`).

## Impact

High. `test_restriction(fixb2="-1")` actually tests β = −factor_Y1/factor_i,
and rejects a true hypothesis with nothing indicating it; «theta, the
long-run coefficients» reads a hundred times off; the standard errors degrade
(t of α 306 versus 2.3: the Hessian's steps are not commensurable, already
measured in drvec C, `HOMOLOGATION.md`). It happens today without anyone doing
anything odd: the atsw-gui GUI writes factor 1 in every new series and art
writes 100, so it is enough to mix one file from each origin.

## Reproduction

`bugs/BUG-0012-repro/repro.py`: synthetic series. It exits with 1 while the
mixed files reject the hypothesis that the common-factor ones accept.

## Root cause

sima does not look at the files' factor except for three per-series
conversions (the forecast's s.d., the residuals of the figures). Everything
that crosses series is taken from the engines in their units.

## Fix

`sima.scale`, with the rule of `fue.scale` (`display_cross`):

- **on loading** (`load_pre`) it says whether the files do not share a factor
  or λ, and whether any of them falls outside the optimizer's scale band;
- **what sima writes** is in the units of each series: the cross terms of the
  VARMA table (`AR1[Y<-X]`) and θ, the long-run coefficients;
- **what the analyst imposes** (`fixb2`, `fixb2row`) is understood in those
  units and taken to the engine's before passing it to drvec. If the series on
  which the relations are normalised do not share a factor, a row cannot carry
  a single value and that is said.

drvec's `.out` stays in engine units: it is the C's. drvec now warns, like the
C, that the files do not share a factor (drvec 0.1.2). An `alpha` restriction
stays in engine units.

## Validation

The repro exits with 0: with Y at 100 and X at 1, H0: β = −1 gives LR = 0.02,
p = 0.885 (before 37.46 and 0.0000); with a common factor, 0.03 and 0.869.
