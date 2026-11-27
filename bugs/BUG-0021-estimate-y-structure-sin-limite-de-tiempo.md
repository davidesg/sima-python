---
id: BUG-0021
title: estimate and structure run with no time budget, no progress and no estimate of their cost; structure takes ~7 minutes on a four-series VAR(1) even with the engine, and a client that gives up loses the session
status: fixed
severity: medium
component: server
found_in: 0.2.4
fixed_in: unreleased (after 0.2.4)
reported: 2026-11-27
reporter: David / Claude — the P08 run of the course (UCM)
tags:
  - estimate
  - structure
  - performance
  - mcp
references:
  - src/sima/mcp_server.py estimate (:1696), structure (:2077)
  - src/sima/parallel.py (the subprocess the ladder runs in)
  - drvarma TODO.md, the speed study of the pure-Python port; drvarma bugs/BUG-0031 (why users get it)
  - bugs/BUG-0021-repro/repro.py
---

## Summary

Neither tool takes a time budget, reports progress, or says beforehand what it
will cost. `structure` fits the restricted model of every triangular ordering.
On the US monetary VAR(1) (IPI, IPC, WTI, FF, 1990-2007) it takes about 7
minutes with the compiled engine (433 s, measured 2026-11-26), and hours on
the pure-Python port. An MCP client's tool timeout is minutes, so the client
gives up while the server keeps computing, and the session, which does not
survive a restart, is lost.

## Impact

In the P08:
- one group's `structure` passed 25 minutes. Cancelled from the client, the
  server kept on for more than 80 minutes of CPU, had to be killed, and the
  session was lost;
- two groups saw `estimate` "not answer" for 30 minutes and left sima;
- one group's monetary script ends at an estimate with p = q = 0 (9.4 min).

All of them were on the port (BUG-0020), but 7 minutes with the engine is
already over several clients' limits.

## Reproduction

`python3 bugs/BUG-0021-repro/repro.py` checks the signatures for a budget
argument and times `structure` on the monetary VAR(1) with the engine,
stopping at 150 s. It exits 1 while there is no budget and `structure` passes
120 s.

```
time-budget parameters in estimate/structure: none
estimate VAR(1): 39 s
structure: still running after 150 s
OPEN
```

## Root cause

The tools are synchronous calls with no notion of cost. `structure` refits
from scratch every restricted model, with the finite-difference Hessian of
each, although only its logL enters the LR test.

## Fix

- Say the cost before running: number of fits × the measured time of one
  likelihood evaluation, and on the port refuse beyond a threshold unless
  asked.
- A `max_seconds` budget for `estimate` and `structure` that returns the best
  point so far, labelled as such, and cancels the subprocess when the client
  cancels.
- In `structure`, skip the standard errors of the restricted fits and seed
  each from the unrestricted optimum.
- Run long jobs as the existing job mechanism does (`jobs`/`job_status`), so
  that the session survives the client's timeout.

## Validation

The repro passes: `structure` under 120 s with the engine on the monetary
VAR(1), or a budget that bounds it.

## Resolution (2026-11-27)

- **Measured first.** On the US monetary VAR(1), with the engine and 3
  processes: `estimate` 28 s, `structure` 279 s (36 refits, ~23 s each). A
  drvarma `Ladder.restricted()` that skipped the gate, the diagonal system
  and the Hessian of each refit gave the same logL to the bit but only 255 s
  (-9 %): the cost is the optimisation of each restricted model. It was not
  merged. Seeding each refit from the unrestricted optimum would cut it, but
  it changes the start, so it is an engine study (C + battery first), in
  TODO.md.
- **The budget.** `structure(max_seconds=600)` predicts its cost from the time
  the current fit took (`estimate` records it) and, beyond the budget, does
  not start: it says the prediction, whether the port is computing, and the
  call to run it anyway (`max_seconds=0`).
- **A job.** The refits run as a detached sima job (`structure_fits`, the
  rank test's mechanism): they survive the client's timeout and the server,
  `job_status` shows the fits done, `job_cancel` kills the tree. `structure`
  waits up to `wait` seconds (20) and otherwise returns the job id; the same
  call again reads the finished job (the fits are not refitted).
- **Not done:** `estimate` has no budget; on the port it now opens with the
  engine notice (BUG-0020), and the abi3 wheels (drvarma BUG-0031) remove the
  usual cause. `tests/test_bug0021_structure_presupuesto.py`.

