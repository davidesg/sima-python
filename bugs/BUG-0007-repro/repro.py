"""BUG-0007: platform_tier() says "exact" on every Linux x86_64, whatever its
libc. The tier goes into the cache key of a job (jobs.make_key), and it is the
claim that a key which matches is the SAME computation. It is not across libm
versions: in the clean-install test of atsw 2.1.0 (2026-10-30, ten
distributions in podman, the wheels from PyPI) the bytes of
tests/test_example_caches.py::test_rerunning_the_mixed_case_reproduces_its_bytes
differ on AlmaLinux 8 (glibc 2.28) and Rocky 9 (glibc 2.34), and drvec's .out
on those two and on Alpine (musl), while glibc 2.35 to 2.41 reproduce them.
So an example's cache, built on glibc >= 2.35, is served on glibc 2.28 as if it
had been computed there.

The repro asks platform_tier() with the libc of each of those platforms.
Expected: "exact" only where the bytes were measured to agree.

    PYTHONPATH=src python3 bugs/BUG-0007-repro/repro.py   # exits 1 while open
"""
import platform
import sys
from unittest import mock

from sima import provenance

measured = {("glibc", "2.28"): "differ", ("glibc", "2.34"): "differ",
            ("musl", "1.2.5"): "differ", ("glibc", "2.35"): "agree",
            ("glibc", "2.41"): "agree"}
wrong = []
with mock.patch.object(sys, "platform", "linux"), \
     mock.patch.object(platform, "machine", lambda: "x86_64"):
    for libc, bytes_ in measured.items():
        with mock.patch.object(platform, "libc_ver", lambda *a, **k: libc):
            tier = provenance.platform_tier()
        ok = (tier == "exact") == (bytes_ == "agree")
        print(f"{libc[0]} {libc[1]:5s}: tier {tier:9s} bytes {bytes_:6s} {'ok' if ok else 'WRONG'}")
        wrong += [] if ok else [libc]
sys.exit(1 if wrong else 0)
