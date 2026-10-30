"""BUG-0008: tests/test_jobs.py::test_never_a_partial_result assumes the
runner has written its first progress 0.6 s after the job says "running". It
says "running" as soon as submit() has spawned the process (jobs.py, the
_update_job after Popen), before the child has imported sima, numpy and drvec;
until it has, status()["progress"] is {}. On a loaded machine the import takes
longer than 0.6 s: the test failed so on Debian 12 and Alpine in the
clean-install test of atsw 2.1.0 (2026-10-30, three containers at once on four
cores), with `assert set() == {'done', 'total', 'what', 'updated'}`.

The repro makes the runner start 1 s late (a sitecustomize that sleeps only in
`python -m sima.jobs run`, as a loaded machine does) and runs that test.
Expected: the test waits for the first progress, not for a fixed time.

    PYTHONPATH=src python3 bugs/BUG-0008-repro/repro.py   # exits 1 while open
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
env = dict(os.environ)
env["PYTHONPATH"] = os.pathsep.join([os.path.join(HERE, "lento"), os.path.join(ROOT, "src")]
                                    + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                    "tests/test_jobs.py::test_never_a_partial_result"],
                   cwd=ROOT, env=env, capture_output=True, text=True)
print("\n".join(l for l in p.stdout.splitlines() if l.startswith(("E ", "FAILED", "1 ")))[:1200])
sys.exit(1 if p.returncode else 0)
