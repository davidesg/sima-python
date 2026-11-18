---
id: BUG-0006
title: rank_test does not say that the model under H0 is not I(1, r); it presents it as a failed bootstrap
status: fixed
severity: medium
component: vec
found_in: 0.2.0
fixed_in: 0.2.0
reported: 2026-10-28
reporter: David / Claude — review of the drvec documentation in sima
tags:
  - rank_test
  - drvec
  - bootstrap
references:
  - drvec-python src/drvec/api.py rank_test (Bootstrap(..., i1r=...)), src/drvec/rank.py i1r_check
  - atsw-gui #93 (drvec C, BUG-64): the I(1, r) check before simulating
  - src/sima/vec.py job_rank_test, propose_rank, rank_report
---

## Summary

drvec C 0.13 (800a540) checks, before simulating, that the model fitted under
H0 is I(1, r) (Cavaliere, Rahbek and Taylor 2012, algorithm 1, step ii): all
the AR roots of [∇Y2 ; W] outside the unit circle and the long-run covariance
of ∇Y2 non-singular. If it is not, it draws no sample and says so in
`Bootstrap.i1r` (the smallest AR root and the rank measure).

sima did not read that field. The comparison came out with 0 replications, a
row of NaN and «fewer than 10 replications ok, no critical value», and the
only alternative was «rerun with a larger B». It read as a failed bootstrap
when it is a finding about the model, and a larger B does not change it.

## Impact

Any rank_test whose model under H0 is not I(1, r): a misread order of
integration (I(2), a d to revise) or a lost common trend. The analyst received
wrong advice (raise B) and no clue to the cause.

## Reproduction

    PYTHONPATH=src python3 bugs/BUG-0006-repro/repro.py   # exits with 1 while it is open

It forces the check at r = 1 of Lütkepohl's E1 (like the drvec test,
tests/test_rank.py::test_a_model_that_is_not_i1r_is_said_and_not_simulated) and
looks at the report.

## Root cause

`vec.job_rank_test` copied from each `Bootstrap` the LR, the replications and
the critical values, but not `i1r`; `propose_rank` and `rank_report` only
distinguished «critical values yes / no».

## Fix

`job_rank_test` stores `i1r`. `propose_rank` proposes no rank and says why;
`rank_report` puts in the table «the model under H0 is not I(1, r): not
simulated», explains which of the two conditions fails, and offers to reread
the orders of integration, another specification, or adopting the rank from
theory. The plot_rank_bootstrap figure annotates it.

## Validation

The repro exits with 0. `tests/test_vec_i1r.py`.
