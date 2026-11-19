---
id: BUG-0019
title: estimate reused the cached fit whatever the start, so the second path never ran, and it kept a VAR(2) below the VAR(1) it nests as if it were an optimum
status: fixed
severity: high
component: server
found_in: 0.2.5-dev (f9a04f8)
fixed_in: 0.2.5
reported: 2026-11-19
reporter: David / Claude — trial run of sima 0.2.5 (rodaje), US monetary VAR 1990–2007 (IPI, IPC, WTI, the rate)
tags:
  - estimate
  - cache
  - start
  - optimiser
references:
  - src/sima/mcp_server.py _key (p, q, diagcov, links, cross, zeros, indices) — no start
  - src/sima/mcp_server.py estimate, _fit_paths (the fix)
  - drvarma bugs/BUG-0027 (the zero start stops after 2 iterations below the nested VAR(1); the C does the same)
  - bugs/BUG-0019-repro/repro.py
---

## Summary

Two defects of `estimate`, found together in the trial run:

1. **The fit cache ignored `start`.** The key is `(p, q, diagcov, links,
   cross, zeros, indices)`. A second call with the same orders and
   `start="preliminary"` returned the fit already made from the zero start —
   the same logL, the same iterations — without optimising again and without
   saying so. The docstring offers `start="preliminary"` precisely as "a
   second path worth comparing" for a doubtful optimum, and says a fit "with
   the same arguments" is reused: `start` is an argument.
2. **A fit below a model it nests was presented as an optimum.** From the zero
   start, drvarma stops the GS1 VAR(2) after 2 iterations (termcode 3) at
   logL −1793.05, below the VAR(1)'s −1744.88 (drvarma BUG-0027). sima read
   it as any other fit: "the cross terms are NOT significant in sample
   (LR = 6.17, df = 30, p = 1.0000)" — the opposite of the truth (LR ≈ 103
   against the diagonal system).

## Impact

The remedy the tool offers for a doubtful optimum was never applied, and the
analyst read the same result twice as if it were an independent
confirmation. The telemetry of the trial run shows it: the two calls with
`start="preliminary"` took 4–6 ms, against 20–60 s for a real fit. Without
`study_estimation` (Shea's path, −1741.28) the analyst would have concluded
that the VAR(2) adds nothing — and an order selection or any test on that fit
would be false.

Found by the analyst asking for VAR(1) → VAR(2) → VAR(3) in four systems (FF,
GS1, GS2, GS3): only GS1's VAR(2) stalls; with the other rates both starts
reach the same logL. The VAR(1)s of FF and GS1 stopped on the step size; the
preliminary start converges there by another path (97 and 104 iterations,
termcode 1), which the cache also hid.

## Reproduction

`bugs/BUG-0019-repro/`: the four `.pre` (IPI m07, IPC m07, WTI m03, GS1 m01;
FRED data, models guided in art).

```
load_pre; run_gate; estimate(p=1); estimate(p=2); estimate(p=2, start="preliminary")
```

`repro.py` exits 1 while the session's VAR(2) lies below its VAR(1): on 0.2.4
it stays at −1793.05.

## Root cause

`_key` leaves `start` out, and `estimate` served `s.fits[key]` whenever the
key was there. Nothing compared a fit with the models it nests.

## Resolution

`_fit_paths` (`src/sima/mcp_server.py`):

- The cache keeps the **best optimum known** for a specification; the start is
  a path, not part of the model. Asked again **with the same start**, the fit
  is reused and the report says so ("PATH: … reused, not optimised again").
  **With another start**, it is optimised again and the higher logL is kept,
  the report giving both.
- **The guard.** A fit that lies **below a model it nests** already fitted in
  the session, or that **stalled** (termcode 3 within 5 iterations), is
  retried once from the preliminary start: an impossible point is a failed
  search, not a decision for the analyst. The report says it ("⚠ THE FIRST
  PATH FAILED …"). If it is still below, "⚠ NOT AN OPTIMUM: … run
  study_estimation".
- Not the echelon form, which starts at its own least-squares estimates.

The engine's side — why the zero start stalls — is drvarma BUG-0027. The C
does the same (`drvmlest.c` returns 1.0 at an inadmissible point, "the
article's strategy, sec. 3"); the engines move together, so it is not
patched here.

## Validation

- `repro.py`: 1 on 0.2.4, 0 with the fix.
- `tests/test_bug_0019_paths.py`: the same start reuses and says so; the guard
  (unit, on nested keys); the stall triggers the retry.
