---
id: BUG-0008
title: An own MA(1) stops at θ = −1, the fold of the cast, and estimate reports it as converged, with significant t values and «Next: evaluate»
status: fixed
severity: medium
component: evidence
found_in: 0.1.0
fixed_in: 0.2.2
reported: 2026-10-16
reporter: David / Claude — lutkepohl_poskitt example, route V, indices (1, 1, 1)
tags:
  - estimate
  - forma-echelon
  - pared-MA
references:
  - drvarma src/drvarma/ladder.py _ma_boundary (~l. 55), canonicalize (~l. 448), _fit (~l. 1143)
  - src/sima/mcp_server.py estimate (~l. 1250, the wall warning)
---

## Summary

In the echelon form (1, 1, 1) of the flour prices (route V), two own MA(1)
terms end at **exactly −1.000000**:

- θ_Minneapolis: s.e. 0.112, t −8.94 *
- θ_KansasCity: s.e. 0.197, t −5.07 *

The optimizer says «converged» (termcode 1) and the standard errors are from
fdhess. `estimate` warns of nothing and proposes «Next: evaluate».

The joint wall does not detect it: the largest inverse root of the system's
MA has modulus 0.99916, outside the tolerance of 5e-5, so `ma_boundary` = 0.
But the point is not an interior maximum: it is the fold of the cast.

## Impact

Medium. The report presents as significant two coefficients that are on the
boundary, and their standard errors are not valid. The protocol («never
report a point on the wall as an optimum», N4b `study_estimation`) is not
triggered, because the only warning depends on `ma_boundary`. It happens to
any own MA(1) whose likelihood pushes towards non-invertibility while the
cross terms keep the joint MA inside.

## Reproduction

`PYTHONPATH=src python3 bugs/BUG-0008-repro/repro.py`. It loads the example,
follows route V and estimates the indices (1, 1, 1). It exits with 1 while
there is an own θ at |θ| = 1 with no warning or with an asterisk.

## Root cause

The own MA(1) folds: a |x| > 1 is read as 1/x, which is the invertible form.
With the rest fixed, the cast gives the same model on both sides:

| θ_Minneapolis | −0.9999 | −1.0 | −1.0001 |
|---|---|---|---|
| largest joint MA root | 0.999097 | 0.999160 | 0.999097 |

The likelihood is symmetric around −1, so the gradient vanishes there by
construction. The quasi-Newton stops at that point and declares convergence
(criterion 1). The curvature that fdhess measures at a fold is not that of a
maximum.

`_ma_boundary` only looks at the roots of the joint Θ₁ matrix. With free MA
cross terms, an own θ at ±1 does not put a joint root on the circle, and the
fold goes by without anyone seeing it.

## Fix

Proposed, not applied:

1. drvarma: count as boundary, in addition to the joint wall, every folded
   own coefficient that stops at |θ| ≥ 1 − MA_WALL_TOL. For example
   `Fit.own_fold`; or include it in `converged`, as BUG-0010 did with the
   wall.
2. sima `estimate`: if there is a fold, remove the asterisk from those
   coefficients, change the «Next» to `study_estimation` and say it in the
   optimizer block: «stopped at the fold of an own MA(1): not an interior
   optimum».
3. `study_estimation`: treat the fold like the wall, with a profile in the
   own θ and the alternative without the MA part (the VAR(1), which is what
   the example did).

## Validation

The repro exits with 0. There will be a test on the example's (1, 1, 1), and
another in drvarma that checks that an own θ at ±1 does not count as
convergence.

## Resolution

In sima, without touching drvarma (a proven engine is not fixed for a latent
defect: its result is read). `evidence.folded_own_ma` walks, like the cast's
`canonicalize`, the free own regular MA(1) terms (and the fixed-frequency MA
terms, whose fold is at c2 = −1) and returns those that stop less than
`MA_WALL_TOL` (5e-5) from |θ| = 1.

- `estimate`: if there is a fold, the optimizer line no longer says
  «converged» but that it stopped where the gradient vanishes at the fold;
  below it, «STOPPED AT THE FOLD OF AN OWN MA(1)» with the coefficients,
  which is neither an interior optimum nor a convergence. Those coefficients
  lose the asterisk (`<- fold`) and the «Next» goes from `evaluate` to
  `study_estimation`, as with the joint wall.
- `study_estimation`: states the fold in the header, marks it in the second
  path and in the restarts, and adds option f) to the menu: treat it like the
  wall and re-estimate with those θ at zero (`zeros=`; with the whole MA out,
  the echelon form is the VAR the example chose). If the θ belongs to the
  univariate model (route U outside the echelon form), it refers to art.

Fits that do not stop at the fold do not change (neither numbers nor text).
Test: `tests/test_fold.py` (the detection on a synthetic result and the
example's (1, 1, 1)). The repro exits with 0.
