---
id: BUG-0011
title: A VARMA whose search never left the diagonal start is presented as an estimate, and its LR = 0 as proof that there is no cross dynamics
status: fixed
severity: high
component: estimate
found_in: 0.2.2
fixed_in: 0.2.3
reported: 2026-11-15
reporter: David / Claude — audit of the scale across the whole ladder
tags:
  - scale
  - optimiser
  - varma
references:
  - src/sima/mcp_server.py (estimate), src/sima/evidence.py (the table and the LR line)
  - drvarma ladder.py (Ladder.fit, the state of the search)
  - art BUG-0257, drtran BUG-68 (the scale that causes it)
  - bugs/BUG-0011-repro/repro.py
---

## Summary

With two series around 10 000 and λ = −1, estimated by fue with
`refactor = 100` (what art writes), the stationary series is worth
99.99 ± 0.0001 and the optimizer stops at its first step. sima presents it as
a fit:

```
optimiser: stopped: the last step found no lower point (1 iterations)
  AR1[Y<-X]      0.000000    0.100000     0.00
  AR1[X<-Y]      0.000000    0.100000     0.00
against the same model without cross terms (the diagonal system): LR = 0.000, df = 3, p = 1.0000
```

The cross coefficients are the seed (0) and their standard errors the
search's seed (0.1000). The same files with `refactor = 10 000` give
AR1[Y<-X] = 0.4577 (t = 12.2) and LR = 120.9.

## Impact

High: «there is no cross dynamics, p = 1» is a scientific conclusion and here
it is an artefact of the scale. Nothing distinguishes it from a result. The
same with the wheels' C engines as with the pure-Python ones (audit of
15-Nov-2026). With the same data, mtram (drtran) does estimate the transfer on
this sample and not on another of 160 observations: the case is marginal for
drtran and it is not for drvarma's ladder.

## Reproduction

`bugs/BUG-0011-repro/repro.py`: synthetic series. It exits with 1 while sima
gives LR = 0.000 for the files with `refactor = 100`.

## Root cause

Two things. The scale (art BUG-0257): μ ≈ 100 with a dispersion of 1e-4
cannot be moved by relative steps. And, sima's own: a search that ends at the
first iteration without improving on the start is not a fit, and `estimate`
treats it as one.

## Fix

`evidence.estimation_text`: a search that ends at its first iteration with
the likelihood of the diagonal start (LR = 0) is not presented as a fit. sima
says «NOT ESTIMATED: the search did not start», with no table or LR, that this
is not evidence that there is no cross dynamics, and the scale notes of the
files (`sima.scale.load_notes`, the rule of `fue.scale`), which are the usual
cause. `load_pre` gives those same notes on loading, before getting here.

## Validation

The repro exits with 0. `tests/test_bug_0011_0012_0013_escala.py`.
