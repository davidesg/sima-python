---
id: BUG-0002
title: The LR of estimate says «against the diagonal system (the univariates)» and it is against the same model without cross terms
status: fixed
severity: low
component: evidence
found_in: 0.1.0
fixed_in: 0.1.0
reported: 2026-10-14
reporter: David / Claude — lutkepohl_poskitt example in route U with art's models, echelon form
tags:
  - estimate
  - evidence
  - forma-echelon
references:
  - src/sima/evidence.py estimation_text (~l. 651): «against the diagonal system (the univariates)»
  - src/sima/mcp_server.py estimate (~l. 1135 and 1142): «against the same model without cross terms»
---

## Summary

The `estimate` report describes the same LR in two ways that do not match.
The header (mcp_server) says «The LR below is against the same model without
cross terms; the univariates come at N5», and the LR line (evidence) says
«against the diagonal system (the univariates)».

What is computed is the former (`L.lr_test()`, the same model without cross
terms). In route U with the echelon form it does not coincide with the
univariate models: with indices (0, 0, 0) the LR = 437.511 has 3 d.f. —only
the covariances of the innovations—, but the univariate models of Minneapolis
and Kansas City carry an AR(1) that the echelon form has replaced. In route V
there are no univariate models in the restricted model either, and the header
says so explicitly.

## Impact

Low: the number is correct. But the analyst reads that the system beats his
univariate models by 437 LR points when the comparison with the univariate
models is the one at N5, and here they do not even have the same own
dynamics.

## Reproduction

`PYTHONPATH=src python3 bugs/BUG-0002-repro/repro.py` — with the example's art
`.pre` files (Buffalo (0,1,0), Minneapolis and Kansas City AR(1)); it exits
with 1 while the bug is still open.

## Root cause

`evidence.estimation_text` writes the route U label with the classic ladder,
where the diagonal DOES consist of the univariate models; it was not updated
when route V and the echelon form arrived.

## Fix

`evidence.estimation_text`: «against the same model without cross terms (the
diagonal system): LR = …», which is what is computed and what the header says.
The comparison with the univariate models is the one at N5. Test:
`tests/test_echelon_route_u.py::test_the_lr_is_against_the_model_without_cross_terms`.

## Validation

The repro exits with 0: at (0, 0, 0) the LR line says «against the same model
without cross terms (the diagonal system): LR = 437.511, df = 3».
