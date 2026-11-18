---
id: BUG-0014
title: With different rescaling factors, α and its restriction (α = Aψ) were in engine units — a true restriction is rejected with p = 0.0072
status: fixed
severity: high
component: vec
found_in: 0.2.3
fixed_in: 0.2.4
reported: 2026-11-16
reporter: David / Claude — what was left of the scale round (atsw-gui docs/ESTUDIO-escala.md)
tags:
  - scale
  - vec
  - restriction
  - units
references:
  - src/sima/vec.py (alpha_reading; restriction_kw)
  - src/sima/scale.py (to_engine_alpha)
  - BUG-0012 (β, its restrictions and θ in the units of each series: α was left out)
  - bugs/BUG-0014-repro/repro.py
---

## Summary

BUG-0012 took the restrictions on β (`fixb2`, `fixb2row`) and θ to the units
of each series when the files do not share a rescaling factor. α stayed in the
engine's, on both sides:

- `estimate_vec` (`alpha_reading`) printed the engine's α: with Y at factor
  100 and X at 1, α_Y = 30.73, when in the units of the series it is 0.307;
- `test_restriction(alpha=...)` imposed α = Aψ in engine units.

Row i of α is the equation of series i: in the units in which it is presented
it is K_i times the engine's (K_i, the presentation factor of the series, up
to a factor common to the column that ψ absorbs). A restriction that links
rows —α_Y = c·α_X— is a different restriction in the engine:

```
refactor Y=100, X=100: alpha Y +0.3091, X +0.0263   H0 alpha = A psi: LR = 0.0,    p = 0.9997
refactor Y=100, X=1:   alpha Y +30.7322, X +0.0252  H0 alpha = A psi: LR = 7.2179, p = 0.0072
```

Same data, same fit, the same A (the α estimated with the common factor): a
restriction that holds exactly is rejected.

## Impact

High when it occurs: the test answers wrongly without warning. Only with
files of different factors (or λ); weak exogeneity —a row at zero— is the
same in both units and is not affected.

## Reproduction

`bugs/BUG-0014-repro/repro.py`, on the data of BUG-0012: it exits with 1 while
α is printed differently with mixed factors or the true restriction is
rejected.

## Fix

`scale.to_engine_alpha`: row i of A is divided by `cross(i, last)` (its
presentation factor, up to a common one). `restriction_kw` applies it when the
files do not share a factor; `alpha_reading` multiplies α by
`cross(i, the normalisation series)`, like θ, and says so. The t values do
not change. With a common factor nothing changes.
