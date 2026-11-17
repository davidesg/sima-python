#!/usr/bin/env python3
"""BUG-0016: tools/build_example_caches.py sanitizes a job's folder without
checking that the job has ended; a job still running loses its working files
and fails.

build() takes the folders of the session's rank jobs after rank_test(wait=6 h)
returns, and sanitize() removes every subfolder -- the job's c/, where drvec C
writes -- and the job's pid and times. On 2026-11-16 the control system of
martin_manjon_treadway (R0T, R10, R3) failed that way:
"FileNotFoundError: .../d58cc15755040c25/c/drvecjob.boot", its job.json
already marked "shipped". Rebuilt alone, it gave the same result as before.

Here: a small rank test on Lutkepohl's E1, submitted with wait=0 (it returns
while the job runs), then the script's sanitize() on its folder. Exits 1 while
the job ends failed (or sanitize does not refuse); 0 when sanitize refuses a
job that has not ended, or the job still ends done.
"""
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
os.environ.setdefault("SIMA_JOBS_HOME", tempfile.mkdtemp(prefix="sima-jobs-"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from sima import jobs                                   # noqa: E402
from sima import mcp_server as M                        # noqa: E402
import build_example_caches as B                        # noqa: E402

fn = lambda f: getattr(f, "fn", f)                      # noqa: E731


def main():
    d = tempfile.mkdtemp(prefix="bug16-")
    src = os.path.join(ROOT, "examples", "lutkepohl_e1", "art")
    files = []
    for f in ("e1invest.pre", "e1income.pre", "e1cons.pre"):
        shutil.copy(os.path.join(src, f), d)
        files.append(os.path.join(d, f))
    s = "bug16"
    fn(M.load_pre)(s, json.dumps(files))
    fn(M.run_gate)(s)
    fn(M.prepare_vec)(s, purpose="long run", p=2, case="2")
    fn(M.rank_test)(s, B=200, wait=0)
    jid = [j for js in M._sess.get(s).rank_jobs.values() for j in js][-1]
    folder = jobs.status(jid)["folder"]
    st0 = jobs.status(jid)["status"]
    refused = False
    try:
        B.sanitize(folder)
    except Exception as e:                               # noqa: BLE001
        refused = True
        print("sanitize refused:", e)
    st = jobs.wait(jid, 1800)
    print(f"job {jid}: {st0} when sanitized -> {st['status']} {st.get('error', '')[:120]}")
    if st["status"] not in jobs.FINAL:
        jobs.cancel(jid)
    ok = refused or st["status"] == "done"
    print("FIXED" if ok else "OPEN: the script sanitized a running job, and the job failed")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
