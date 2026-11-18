---
id: BUG-0010
title: test_never_a_partial_result waits a fixed 0.6 s for the job's first progress; on a loaded machine it fails
status: fixed
severity: low
component: tests
found_in: 0.2.0
fixed_in: 0.2.2
reported: 2026-10-30
reporter: David / Claude — clean-install test of atsw 2.1.0 on ten distributions
tags:
  - jobs
  - tests
  - flaky
references:
  - tests/test_jobs.py::test_never_a_partial_result
  - src/sima/jobs.py submit (status "running" after Popen), Ticks
---

## Summary

`submit()` marks the job as `"running"` as soon as it has launched the
process, before the child (`python -m sima.jobs run`) has imported sima, numpy
and drvec. Until the child writes its first `progress.json`,
`status()["progress"]` is `{}`. The test waits a fixed 0.6 s after seeing
`"running"` and already demands the four keys of the progress. In the
clean-install test of atsw 2.1.0 (2026-10-30, three containers at once on four
cores) it failed like this on Debian 12 and on Alpine:
`assert set() == {'done', 'total', 'what', 'updated'}`.

## Impact

Low: it is the test, not the code. What the user sees in that interval is a
«running» job with no counts yet, which is true. But the test fails
intermittently on loaded CI and on slow machines.

## Reproduction

`bugs/BUG-0010-repro/repro.py` makes the child start 1 s late (a
`sitecustomize` that sleeps only in `python -m sima.jobs run`, as on a loaded
machine) and runs the test. It exits with 1 while it fails.

    PYTHONPATH=src python3 bugs/BUG-0010-repro/repro.py

## Root cause

A fixed time in the test, where what has to be waited for is a state: the
first progress written.

## Fix

Proposed: that the test wait, with a long timeout, until `progress` has counts
(as `_wait_status` waits for a state), and only then check that they are
counts and that `done < total`. The job's `steps` must leave enough margin for
it not to finish in the meantime.

## Validation

The repro, and the test under load.

## Resolution

The test waits for the state, not a time: `_wait_progress` (in
`tests/test_jobs.py`, next to `_wait_status`) polls `status()["progress"]`
every 0.1 s until it brings counts, with a timeout of 60 s, and only then
checks the four keys and that `done < total`. The job (200 steps of 0.05 s)
leaves some 10 s of margin from its first progress. The `jobs` code does not
change: a «running» job with no counts yet is true.
