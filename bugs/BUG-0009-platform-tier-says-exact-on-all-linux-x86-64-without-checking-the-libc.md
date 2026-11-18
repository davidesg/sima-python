---
id: BUG-0009
title: platform_tier() says «exact» on all Linux x86_64 without checking the libc; an example's cache is served on a libm that does not reproduce it
status: fixed
severity: low
component: jobs
found_in: 0.2.0
fixed_in: 0.2.2
reported: 2026-10-30
reporter: David / Claude — clean-install test of atsw 2.1.0 on ten distributions
tags:
  - jobs
  - cache
  - platform
references:
  - src/sima/provenance.py platform_tier
  - src/sima/jobs.py make_key (the tier goes into the key)
  - tests/test_example_caches.py::test_rerunning_the_mixed_case_reproduces_its_bytes
  - drvec-python bugs/py-tests-exact-libc (the same criterion in its tests)
---

## Summary

`platform_tier()` returns `"exact"` when `sys.platform == "linux"` and the
machine is x86_64, without checking the libc. The tier goes into the key of a
job's cache, and a key that matches is presented as «the same computation, not
an approximation». Across libm versions it is not: in the clean-install test
of atsw 2.1.0 (2026-10-30, ten distributions in podman, the PyPI wheels), the
bytes of the mixed case of `test_example_caches` differ on AlmaLinux 8
(glibc 2.28) and Rocky 9 (glibc 2.34), and drvec's `.out` files also on Alpine
(musl). From glibc 2.35 to 2.41 (Ubuntu 22.04 and 24.04, Debian 12 and 13,
openSUSE 15.6, Fedora 41) they are reproduced byte for byte.

## Impact

Low. The example caches are built on glibc ≥ 2.35 and served on glibc 2.28 or
musl as if they had been computed there. The measured differences are in the
twelfth digit (a `-7.567e-12` versus `-7.539e-12`, a `-0.000000` versus
`0.000000`): they do not change any conclusion, but the key's promise («same
key, same bytes») is not kept, and the bytes test of the mixed case fails on
those platforms. On Alpine the cache does not match anyway, because the
bootstrap engine (Python, without drvec's C) is in the key.

## Reproduction

`bugs/BUG-0009-repro/repro.py` asks `platform_tier()` with the libc of each
measured platform and compares with what was measured. It exits with 1 while
some libc whose bytes differ gives `"exact"`.

    PYTHONPATH=src python3 bugs/BUG-0009-repro/repro.py

## Root cause

`provenance.platform_tier` decides the tier by system and architecture. Byte
identity also depends on the libm, which is part of the libc.

## Fix

Proposed: `"exact"` only with glibc ≥ 2.35 on Linux x86_64, the measured
boundary. On musl, `platform.libc_ver()` returns `('', '')`: it has to be
detected separately (`/etc/alpine-release` or `os.confstr`), not taken for
glibc. If the boundary moves, it is measured again with the same test in
containers.

## Validation

The repro, and the bytes test of the mixed case on AlmaLinux 8, Rocky 9 and
Alpine (it is skipped instead of failing), with the example's cache not served
there.

## Resolution

`platform_tier()` gives `"exact"` only on Linux x86_64 with a glibc within the
measured interval, `EXACT_GLIBC = ((2, 35), (2, 41))` in `provenance.py`;
outside it, and with musl (which `platform.libc_ver()` does not recognise as
glibc), it gives `"tolerance"`. The closed interval has been taken rather than
«≥ 2.35»: a glibc later than 2.41 is not measured, and it moves to `"exact"`
when the same test in containers measures it (the constant is widened). On
those platforms the key no longer matches that of the example caches and the
bytes tests are skipped.
