---
id: BUG-0004
title: In route V, evaluate measures against light univariate models it chooses on its own, without saying which they are or accepting the analyst's
status: fixed
severity: medium
component: server
found_in: 0.1.0
fixed_in: 0.1.0
reported: 2026-10-14
reporter: David / Claude — lutkepohl_poskitt example, route V (tutorial) versus route U with art's models
tags:
  - evaluate
  - ruta-v
  - vara-de-medir
references:
  - src/sima/mcp_server.py _yardstick_files (~l. 473): the `<SERIE>_u.pre` files of raw.build_univariate
  - src/sima/mcp_server.py evaluate (~l. 1541, 1560)
---

## Summary

In route V the N5 yardstick is the `<SERIE>_u.pre` files that
`raw.build_univariate` builds the first time, «light; not reviewed in art».
The builder chooses within art's tie: in the example, Buffalo (0,1,0),
Minneapolis MA(1) θ −0.25 and Kansas City MA(1) θ −0.20. The analyst's models
in art are (0,1,0), AR(1) and AR(1).

The N5 ratio depends on that choice:

| RMSE h = 1 (72 estimation months) | restricted VAR(1) | light yardstick | art's AR(1) |
|---|---|---|---|
| Minneapolis | 7.035 | 7.478 → **0.941** | 7.046 → ≈ 1.00 |
| Kansas City | 7.424 | 7.422 → 1.000 | 7.224 → 1.03 |

The tutorial's only gain (0.94 in Minneapolis) disappears against art's
AR(1). The report does not say which models are the yardstick (only the path
of the file) and `evaluate` has no way of receiving others.

## Impact

Medium: N5 is the node that decides whether the VARMA has a reason to exist.
A yardstick chosen silently within a tie can manufacture or erase a gain of
the size of the ones being read (5 %).

## Reproduction

`PYTHONPATH=src python3 bugs/BUG-0004-repro/repro.py` — with the example's
`flour_prices.csv`: route V, Lütkepohl and Poskitt's restricted VAR(1), N5
with 72 months and h = 6; it exits with 1 while the bug is still open. The art
figure (7.046) comes from the route U session with art's `.pre` files
(BUG-0002-repro).

## Fix

1. The N5 report in route V names the yardstick, series by series: its ARIMA
   and the file, and if it is the light builder's, which one it took and among
   which of art's tie (`yardstick.json`, which it writes when building it). It
   also says that the ratios depend on that choice and how to give another.
2. `evaluate(yardstick=...)` accepts the analyst's univariate models, one fue
   file per series: the same series and the same transformation (λ, d, D) as
   the specifications, or it is rejected with the reason. It stays in the
   session: `forecast_uncertainty` and `structure` use it too. In route U the
   yardstick is already the loaded files.

Step 9 of the `lutkepohl_poskitt` tutorial tells it. Tests:
`tests/test_yardstick.py` (3).

## Validation

The repro exits with 0. With art's `.pre` files as the yardstick, the same
evaluation gives for Minneapolis at h = 1 RMSE 7.035 versus 7.046 (ratio
0.999), which the report noted from route U; with the light yardstick, 7.035
versus 7.478 (0.941), and the report now says that this yardstick is the MA(1)
the builder took, the first of the tie.
