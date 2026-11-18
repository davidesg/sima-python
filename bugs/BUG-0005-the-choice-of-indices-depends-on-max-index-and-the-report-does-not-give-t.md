---
id: BUG-0005
title: identify_echelon changes its choice with max_index (the common sample shrinks) without saying on how many observations the table is computed; the MANUAL attributes it to route U
status: fixed
severity: medium
component: evidence
found_in: 0.1.0
fixed_in: 0.1.0
reported: 2026-10-14
reporter: David / Claude — lutkepohl_poskitt example, comparison with the flour_prices aside
tags:
  - identify_echelon
  - forma-echelon
  - docs
references:
  - drvarma src/drvarma/echelon.py search (~l. 387): t0 = h + n_max + degree of the factors
  - src/sima/mcp_server.py identify_echelon (~l. 938)
  - docs/MANUAL-echelon.md §5.1; examples/lutkepohl_poskitt/TUTORIAL.md, «An aside: route U on the same data»
---

## Summary

Lütkepohl and Poskitt's search compares all the candidates on a common sample
that starts at t0 = h + n_max. When `max_index` goes up the sample shrinks
(flour prices, h = 1: T 95 with n_max 3, T 92 with n_max 6) and the whole
table changes: log|S| of (0, 0, 0) goes from 5.3605 to 5.4205 and the choice
of SC and HQ goes from **(1, 0, 0)** to **(0, 0, 0)**.

The report does not give T or the sample, so two calls that differ only in
`max_index` give two answers with no explanation. The initial suspicion, that
the route U search depended on the ARMA of the univariate models, was false:
with the MA(1) models of `flour_prices` and with art's models (random walk,
AR(1), AR(1)) the tables are identical for the same `max_index`.

The documentation had already fallen into the confusion. MANUAL-echelon §5.1
says that in route U «the search on the differences chooses (1, 0, 0), with
both criteria», and the aside in the lutkepohl_poskitt tutorial presents it as
what route U changes. It is the `max_index` (3 by default versus 6 in the
tutorial, Lütkepohl and Poskitt's).

## Impact

Medium: node N2 decides the indices, and on short data the limit of the
search, which looks like a mere cap, changes the answer. The analyst has no
way of seeing it, and the MANUAL gives him a wrong explanation.

## Reproduction

`PYTHONPATH=src python3 bugs/BUG-0005-repro/repro.py` — the two sets of
univariate models (MA(1) of flour_prices and art's), max_index 3 and 6; it
exits with 1 while the choice changes without the report giving the T of the
table.

## Root cause

drvarma `echelon.search`: `t0 = h + n_max + _lag_of(filters)`. It is the
design (a common sample so that the criteria are comparable), but neither
drvarma nor sima exposes it.

## Fix

1. The header of the table states the sample: «T = 92 (1972.10 – 1980.11):
   long VAR(h) + n_max»; and a line when the choice with a smaller
   `max_index` would be different, or at least the warning that the sample
   depends on `max_index`.
2. MANUAL-echelon §5.1 and the tutorial's aside: the (1, 0, 0) / (0, 0, 0)
   difference comes from `max_index` (T 95 versus 92), not from the route.
   With n_max 6 both sets of univariate models give (0, 0, 0).

## Validation

Fixed in sima (`identify_echelon`), without touching drvarma: after the table,
«The table is computed on T = 92 of the 99 observations of the stationary
vector: every candidate on the same sample, which starts after the long VAR's
1 lag plus max_index = 6. A different max_index changes that sample, and on a
short series it can change the choice.» The repro exits with 0; test
`tests/test_echelon.py::test_identify_echelon_says_its_sample`. Point 2
(MANUAL §5.1 and the tutorial's aside) was corrected in PR #5.
