#!/usr/bin/env python3
"""BUG-0017: a cache test that fails leaves its bootstrap running, detached,
with nothing that stops it.

test_the_tutorial_rank_returns_at_once submits the tutorial's rank test with
wait=5. When the cache does not match (a new drvarma, BUG-0015), the job is
submitted, the test fails on its assertions, and the job -- detached, as
sima's jobs are meant to be -- goes on in the test's temporary folder. On
2026-11-16/17 five of them ran for eleven hours after the suite, competing
for the CPU with everything else.

Runs that test for lutkepohl_e1 under pytest with a plugin that forces the
miss, then looks for runners left in its temporary folder (and stops them).
Exits 1 while any is left; 0 when the test stops its own jobs.
"""
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def runners(tag):
    out = subprocess.run(["ps", "-eo", "pid=,args="], capture_output=True, text=True).stdout
    return [l.split(None, 1) for l in out.splitlines()
            if tag in l and ("sima.jobs run" in l or "drvec" in l)]


def main():
    base = tempfile.mkdtemp(prefix="bug17-")
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(
        [HERE, os.path.join(ROOT, "src"), os.environ.get("PYTHONPATH", "")]))
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                        "-p", "_fuerza_fallo", "--basetemp", base,
                        "tests/test_example_caches.py::"
                        "test_the_tutorial_rank_returns_at_once[lutkepohl_e1]"],
                       cwd=ROOT, env=env, capture_output=True, text=True)
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-300:])
    time.sleep(3)
    left = runners(base)
    for pid, _ in left:
        try:
            os.kill(int(pid), 15)
        except OSError:
            pass
    print(f"runners left in {base}: {len(left)}")
    print("FIXED" if not left else "OPEN: the failed test left its bootstrap running")
    return 0 if not left else 1


if __name__ == "__main__":
    sys.exit(main())
