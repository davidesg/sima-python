---
id: BUG-0015
title: The key of a job carries the version of drvarma (and of fue) — every drvarma release invalidates the example caches
status: wontfix
severity: medium
component: jobs
found_in: 0.2.3
fixed_in: by design (0.2.5)
reported: 2026-11-17
reporter: David / Claude — release of drvarma 0.3.4 and sima 0.2.4
tags:
  - jobs
  - cache
  - examples
references:
  - src/sima/jobs.py (make_key: "versions" of drvec, drvarma and fue)
  - docs/PUBLISHING.md, step 4
  - bugs/BUG-0015-repro/repro.py
---

## Summary

`jobs.make_key` puts the versions of drvec, drvarma and fue into the key of
every job. The rank bootstrap is drvec's (its C or its Python port): with the
same data, arguments, drvec and engine, a new drvarma gives the same result
and a different key.

```
key with drvarma 0.3.3: 77c69e8ba807def9
key with drvarma 0.3.4: 18f437d856c82dfb
```

## Impact

Medium. drvarma 0.3.4 only changed an HTML page. Even so, with it on PyPI,
the seven caches of sima 0.2.3 stopped matching: the tutorials repeated the
bootstrap (minutes instead of instantly) until sima 0.2.4 came out with the
caches rebuilt. It cost 4 h of machine time and cancelling the drvarma release
during a class. Every drvarma release ties up sima's.

## Reproduction

`bugs/BUG-0015-repro/repro.py`: the key of the same rank test with drvarma
0.3.3 and 0.3.4. It exits with 1 while they differ.

## Root cause

The key stores the versions so that any change that could move the result
invalidates it. With the C engine, the bootstrap replications are the C's,
which reads the `.pre` files itself. But the observed fits and the LR
statistic are computed by drvec's Python port **also with the C engine**
(«the port's observed fits are done, they ran while the C did»,
`drvec.rank_test`). And that port uses drvarma's optimizer and likelihood
(`_qnewt`, `elf_c`) and reads the `.pre` files with fue (`cast_us`,
`forecast`). A version of drvarma or of fue can, therefore, move the observed
LR without touching a byte of the C.

## Decision: it is so by design (17-Nov-2026)

Removing drvarma and fue from the key when the engine is C (the first
proposal) is not safe, because of the above. A fingerprint of the code the
bootstrap uses would be finer, but fragile (which modules count, and the
compiled extension). The key stays as it is, and the cost is taken on in the
protocol: `docs/PUBLISHING.md`, step 4. A release of fue or of drvarma is
followed by one of sima with the caches rebuilt. With BUG-0016 fixed,
rebuilding them no longer fails halfway.

The repro stays as a guard, with its sense inverted: it exits with 0 while the
drvarma version changes the key, and with 1 if someone removes it.
