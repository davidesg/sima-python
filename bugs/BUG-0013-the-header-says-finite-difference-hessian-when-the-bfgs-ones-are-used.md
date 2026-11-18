---
id: BUG-0013
title: estimate_vec says «standard errors from the finite-difference Hessian» when drvec's fdhess did not come out and the table carries the BFGS ones
status: fixed
severity: medium
component: vec
found_in: 0.2.2
fixed_in: 0.2.3
reported: 2026-11-15
reporter: David / Claude — audit of the scale across the whole ladder
tags:
  - standard-errors
  - provenance
  - scale
references:
  - src/sima/vec.py:561 (the sentence, hard-coded)
  - drvec api.FitResult.fdhess (.ok)
  - bugs/BUG-0013-repro/repro.py
---

## Summary

The `estimate_vec` header has «standard errors from the finite-difference
Hessian» written into it. With two series in logarithms and factor 1 in both
files (what the atsw-gui GUI writes), drvec's `-fdhess` does not come out
(`FitResult.fdhess.ok` is False) and the standard errors are the BFGS ones.
The header says the opposite.

It is not cosmetic: the t of β is −28.4 with factor 1 and −10.5 with factor
100, the same data and the same fit. With factor ≥ 10 fdhess comes out and its
standard errors are stable from 10 to 10⁴; with ≤ 1 it does not come out.

## Impact

Medium: the provenance of a standard error is part of the result, and sima
warns elsewhere that the BFGS ones are not to be quoted.

## Reproduction

`bugs/BUG-0013-repro/repro.py`. It exits with 1 while the header names the
finite-difference Hessian in a fit whose fdhess is not ok.

## Fix

The header says what the table carries: the finite-difference Hessian when
`FitResult.fdhess.ok`, and otherwise, that they are the BFGS ones because the
other did not come out and that this is what happens with a scale outside the
optimizer's band.

## Validation

The repro exits with 0.
