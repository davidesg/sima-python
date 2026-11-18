---
id: BUG-0007
title: Route U writes .pre files that fue does not read (the provenance line inside the header)
status: fixed
severity: medium
component: raw
found_in: 0.2.0
fixed_in: 0.2.2
reported: 2026-11-12
reporter: David / Claude — integration of the VEC in sim_gui (atsw-gui, S10c)
tags:
  - raw
  - route-u
  - pre
references:
  - src/sima/raw.py (PROVENANCE, the insertion after write_pre)
---

## Summary

The raw entry (route U) writes each series' `.pre` with fue and then inserts
the provenance line («* Built by sima's raw entry (route U), not reviewed in
art») as the **fifth line**, inside the fixed header. fue reads that header
by position: the frequency line moves from line 6 to line 7 and the file is
rejected («line 7: the frequency must be 1, 4, 12 or 'number' (it is
'**')»).

## Impact

Route U's `.pre` files do not go back to fue nor to anything that validates
with its reader: drvarma (and therefore the sim_gui gate in atsw-gui) rejects
them. drvec tolerates them with its own reader, so sima's VEC runs and the
failure is not visible inside sima. It affects the four `.pre` files of the
`johansen_juselius` example.

## Reproduction

    python3 bugs/BUG-0007-repro/repro.py
    FUE=/path/to/fue python3 bugs/BUG-0007-repro/repro.py   # also runs fue

It exits with 1 while it is open: line 6 is not the frequency header and fue
does not read it. With the line removed, it exits with 0.

## Root cause

`raw.py`, after `model.write_pre(...)`: `lines.insert(4, PROVENANCE)`. Position
4 is inside the fixed block of fue's header.

## Fix

The provenance must not break the format: put it where fue admits free text
(or in a separate file, or in the guion), not among the fixed lines. The
`.pre` files of the `johansen_juselius` example have to be regenerated.

## Validation

The repro exits with 0 with the regenerated `.pre` files, and fue reads them.

## Resolution

fue's header is five lines that may carry anything (fue.c [3.0]); the fifth,
in the `.pre` that fue writes, is the blank line under the box.
`raw.build_one` puts the provenance there, instead of inserting it: the
frequency stays on the sixth and the `.pre` goes back to fue and to drvarma.
Route U's `.inp` already carried it within those five lines.

The four `.pre` files of `johansen_juselius` (and the repro's copy) have been
regenerated with `build_one` on `data/denmark.csv`: they come out identical to
the earlier ones with the blank line removed, and the `.out` files byte for
byte. Since the cache key carries the digest of the files, the rank test
folder goes from `sima_jobs/290f7ee278756890` to `sima_jobs/9f38d2e4a3c1b869`:
same payload (versions, engine, level) with the new digests, and `rank.out`,
`rank.boot` and `result.json` untouched —drvec reads the `.pre` files with
fue's cast, which skips the comments, so the numbers do not depend on that
line—. `example.json` points to the new folder. `tests/test_raw_entry.py`
checks that the provenance is on the fifth line and the frequency on the
sixth.
