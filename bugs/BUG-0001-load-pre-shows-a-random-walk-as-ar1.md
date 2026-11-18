---
id: BUG-0001
title: load_pre shows a random walk (0,1,0) as «AR 1» in the table of the models
status: fixed
severity: low
component: server
found_in: 0.1.0
fixed_in: 0.1.0
reported: 2026-10-14
reporter: David / Claude — lutkepohl_poskitt example in route U with art's models
tags:
  - load_pre
  - evidence
references:
  - src/sima/evidence.py series_table (l. 28): p, q = s.orders()
  - drvarma src/drvarma/ladder.py Ladder.orders (~l. 236): len(phi) of the expanded polynomial
---

## Summary

The N0 table («The univariate models») gives `AR 1` to Buffalo, whose art
`.pre` is a (0,1,0): ∇ln Buffalo = a_t. fue needs a placeholder AR when the
model has no operator at all —an AR(1) with the coefficient FIXED at 0.0—, and
`Ladder.orders()` (drvarma) returns `len(phi)` of the expanded polynomial,
which counts that placeholder as an order.

## Impact

Low: only the table. The gate and the estimates are not affected (the
coefficient is fixed at zero and the identity logL_joint = Σ logL_i is exact).
But the analyst reads «AR 1» for a model he built with no AR. It is the same
confusion art has in `_lleva_arma` (art BUG-0248, point 5).

## Reproduction

`PYTHONPATH=src python3 bugs/BUG-0001-repro/repro.py` — with Buffalo's (0,1,0)
`.pre` and Minneapolis's AR(1) from the example; it exits with 1 while the bug
is still open.

## Root cause

drvarma `Ladder.orders()`: `len(phi)` of the expanded polynomial, without
checking whether the coefficients are free. `orders()` is used only by this
table.

## Fix

In drvarma (`LadderSeries.orders()`, `ladder` branch): a side (AR or MA) whose
factors have all their coefficients fixed at zero has no order; it is fue's
placeholder. A free coefficient seeded at zero —art's `.inp`— does count. Test
in drvarma: `tests/test_ladder_orders.py`; in sima:
`tests/test_echelon_route_u.py::test_load_pre_does_not_count_the_placeholder`.

## Validation

The repro exits with 0: Buffalo `AR 0`, Minneapolis `AR 1`.
