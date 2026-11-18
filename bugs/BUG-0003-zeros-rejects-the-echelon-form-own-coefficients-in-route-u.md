---
id: BUG-0003
title: In route U, zeros (and simplify) reject the own coefficients of the echelon form, which are no longer art's
status: fixed
severity: medium
component: server
found_in: 0.1.0
fixed_in: 0.1.0
reported: 2026-10-14
reporter: David / Claude — lutkepohl_poskitt example in route U with art's models, echelon form
tags:
  - estimate
  - simplify
  - zeros
  - forma-echelon
references:
  - src/sima/mcp_server.py _split_zeros (~l. 342): `if s.route != "V": raise`
  - src/sima/mcp_server.py simplify (~l. 1213, 1230): `s.route == "V" and _OWN.fullmatch(nm)`
  - src/sima/mcp_server.py _model_ladder (~l. 382): own="free" if there are indices and the route is not V
---

## Summary

In route U, `estimate(indices=..., zeros="theta_Buffalo[B^1], ...")` fails with

    'theta_Buffalo[B^1]' is a coefficient of a univariate model: on route U
    the diagonal is art's — simplify it there.

In the echelon form that is not true. `_model_ladder` passes `own="free"` and
the `estimate` header itself says «On route U the own AR(n_i)/MA(n_i)
replaces each univariate model's regular ARMA». The φ_i/θ_i of the echelon
form are sima's, not art's, and «simplify it there» has nowhere to be done.

Consequence in the example: the VAR(1) inside (1, 1, 1) —the echelon form
without its MA part, Lütkepohl and Poskitt's step— cannot be written.
`simplify` on an echelon fit in route U has the same filter
(`s.route == "V"`), so it never proposes removing an own coefficient either,
even though in (1, 1, 1) θ_Minneapolis and θ_KansasCity are at −1.000.

## Impact

Medium: the echelon form in route U cannot be simplified through its own
coefficients, which is exactly where the overfitting is (two own MA terms at
the wall). It has to be worked around with route V or with the classic
ladder, which is not the same model.

## Reproduction

`PYTHONPATH=src python3 bugs/BUG-0003-repro/repro.py` — with the example's art
`.pre` files (Buffalo (0,1,0), Minneapolis and Kansas City AR(1)); it exits
with 1 while the bug is still open.

## Root cause

The criterion «own = art's» is per route (`s.route != "V"`) and should be per
model: own coefficients are art's only when the row keeps the univariate
model's ARMA (`own="spec"`). With Kronecker indices in route U (`own="free"`)
the own part is free, as in route V.

## Fix

In `_split_zeros` and in the two filters of `simplify`, accept the own
coefficients when `s.route == "V"` **or** the fit is an echelon form
(non-empty indices). Check that `_files_for` / the Ladder apply the own zero
to the free part of the row and not to the row factor (seasonal or of fixed
frequency), which is still art's. Update the `estimate` docstring («own ...
on route V only») and MANUAL-jenkins-alavi §2.5.

## Validation

Fixed in sima and in drvarma:

- drvarma (`ladder` branch): `LadderSeries.with_regular(k, zeros=)` and
  `Ladder(..., own="free", own_zeros=)` fix at zero lags of the free own
  part, which are also left out of the least squares of the start.
- sima: `_own_is_free` —route V, or echelon form with indices— decides
  whether `zeros` and `simplify` reach the own coefficients; in route U
  without indices they are still art's.

The repro exits with 0. In the example, the VAR(1) inside (1, 1, 1) in route U
gives logL −667.677245, the same as route V, and its restricted VAR(1)
−669.129921, the one in their Table 2; `simplify` proposes
`phi_KansasCity[B^1]`, as they do. Tests:
`tests/test_echelon_route_u.py` (sima) and
`test_echelon_rowfactor.py::test_own_zeros_hold_the_free_own_lags_at_zero`
(drvarma). MANUAL-echelon §2.3 and §5.3, MANUAL-jenkins-alavi §2.5.
