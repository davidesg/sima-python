---
id: BUG-0017
title: A cache test that fails leaves its bootstrap running, detached, with nothing to stop it
status: fixed
severity: low
component: tests
found_in: 0.2.4
fixed_in: 0.2.5
reported: 2026-11-17
reporter: David / Claude — sima suite against drvarma 0.3.4
tags:
  - jobs
  - tests
references:
  - tests/test_example_caches.py (test_the_tutorial_rank_returns_at_once, _rerun)
  - BUG-0015 (the cache miss that triggers it)
  - bugs/BUG-0017-repro/repro.py
---

## Summary

`test_the_tutorial_rank_returns_at_once` launches the tutorial's rank test
with `wait=5`. When the cache does not match (a new drvarma, BUG-0015), the
job is launched, the test fails in its asserts, and the job keeps running,
detached as sima's jobs are, in the test's temporary folder. `_rerun` does the
same if its wait or an assert fails. On 16 and 17-Nov-2026, five of them were
still running eleven hours after the suite, competing for the CPU with
everything else.

## Impact

Low for the user; high for whoever runs the suite: it leaves the machine
loaded for hours without it being visible.

## Reproduction

`bugs/BUG-0017-repro/repro.py`: runs that test for lutkepohl_e1 under pytest
with a plugin that forces the cache miss, and looks for the processes left in
its temporary folder (and stops them). It exits with 1 while any remain.

## Fix

An `autouse` fixture in `tests/test_example_caches.py` cancels, when each test
ends (pass or fail), the jobs still alive in its `SIMA_JOBS_HOME`. The repro
exits with 0.
