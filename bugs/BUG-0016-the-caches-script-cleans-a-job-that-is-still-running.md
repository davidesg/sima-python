---
id: BUG-0016
title: tools/build_example_caches.py cleans a job's folder without checking that it has finished — the job loses its files and fails
status: fixed
severity: low
component: tools
found_in: 0.2.4
fixed_in: 0.2.5
reported: 2026-11-17
reporter: David / Claude — rebuild of the caches for drvarma 0.3.4
tags:
  - jobs
  - cache
  - tools
references:
  - tools/build_example_caches.py (build, sanitize)
  - bugs/BUG-0016-repro/repro.py
---

## Summary

`build()` collects the folders of the rank jobs when `rank_test(wait=6 h)`
returns, and `sanitize()` deletes every subfolder in them (the `c/` where
drvec C writes), the pid and the times. It does not check that the job has
finished. On 16-Nov-2026 the control system of martin_manjon_treadway (R0T,
R10, R3) failed like this:

```
FileNotFoundError: .../sima_jobs/d58cc15755040c25/c/drvecjob.boot
```

Its `job.json` already carried the script's `"shipped"` mark. Rerun on its
own, it gave the same result as before. Why `rank_test` returned before the
job finished remains unexplained.

## Impact

Low: it only affects whoever rebuilds the caches. But it costs hours, and a
failed job can be mistaken for a different result.

## Reproduction

`bugs/BUG-0016-repro/repro.py`: a small rank test on Lütkepohl's E1, launched
with `wait=0` (it returns while running), and then `sanitize()` on its folder.
It exits with 1 while the job ends up failed.

## Fix

`build()` waits for each job to finish (`jobs.wait`) and requires `done`
before cleaning; `sanitize` refuses a job that has not ended `done`. The repro
exits with 0.
