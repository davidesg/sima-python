#!/usr/bin/env python3
"""Build the worked examples' job caches (docs/PLAN-vec.md C6).

Each example ships the folders of its long jobs (``art/sima_jobs/<id>/``), so
that the tutorial's bootstraps return at once: ``load_example`` copies them
and ``rank_test`` finds them by their content key. This script runs those
jobs in the examples' own folders, with the same tools the server serves,
and then strips each folder to what the cache needs and what reproduces
byte for byte on Linux x86_64 (the oracle's platform): ``job.json`` without
absolute paths or times, ``result.json``, and the engine's files.

    python3 tools/build_example_caches.py              # every example
    python3 tools/build_example_caches.py flour_prices

Rerunning a job reproduces the same bytes on Linux x86_64:
tests/test_example_caches.py checks it.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EX = os.path.join(ROOT, "examples")

# the long jobs each tutorial calls, with the arguments it calls them with
SPECS = {
    "flour_prices": dict(files=["art/BUFFALO_m01.pre", "art/MINNEAPOLIS_m01.pre",
                                "art/KANSASCITY_m01.pre"],
                         prepare=dict(purpose="long run", p=2, case="pre"),
                         rank=dict(B=499), vec=dict(r=1), irf=dict(N=499)),
    "jenkins_alavi": dict(files=["art/MUSKRAT_m03.pre", "art/MINK_m02.pre"],
                          prepare=dict(purpose="long run", p=2, case="2", mixed=True),
                          rank=dict(B=499)),
    "lutkepohl_e1": dict(files=["art/e1invest.pre", "art/e1income.pre", "art/e1cons.pre"],
                         prepare=dict(purpose="long run", p=2, case="2"),
                         rank=dict(B=499)),
    "martin_manjon_treadway": dict(files=["art/R0T_ar3.pre", "art/R30_ar3.pre", "art/R3_ar3.pre"],
                                   prepare=dict(purpose="long run", p=4, case="pre"),
                                   rank=dict(B=499),
                                   controls=[["art/R0T_ar3.pre", "art/R10_ar3.pre",
                                              "art/R3_ar3.pre"]]),
    "johansen_juselius": dict(files=["art/LRM_u.pre", "art/LRY_u.pre", "art/IBO_u.pre",
                                     "art/IDE_u.pre"],
                              prepare=dict(purpose="long run", p=2, case="2"),
                              rank=dict(B=499)),
}

KEEP = (".out", ".boot", ".irfboot", "result.json", "job.json")


def sanitize(folder):
    """Keep what a cache needs; drop absolute paths and times from job.json."""
    for f in os.listdir(folder):
        p = os.path.join(folder, f)
        if os.path.isdir(p):
            shutil.rmtree(p)
        elif not f.endswith(KEEP):
            os.remove(p)
    jp = os.path.join(folder, "job.json")
    with open(jp, encoding="utf-8") as fh:
        j = json.load(fh)
    j["files"] = [os.path.basename(f) for f in j["files"]]
    j["extra_files"] = [os.path.basename(f) for f in j.get("extra_files", [])]
    for k in ("pid", "created", "started", "ended", "session"):
        j.pop(k, None)
    j["shipped"] = "a worked example's cache (tools/build_example_caches.py)"
    with open(jp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(j, fh, indent=1, sort_keys=True)
        fh.write("\n")


def build(name, spec, wait=6 * 3600):
    os.environ.setdefault("SIMA_JOBS_HOME", tempfile.mkdtemp(prefix="sima-jobs-"))
    from sima import mcp_server as M
    fn = lambda f: getattr(f, "fn", f)                      # noqa: E731
    d = os.path.join(EX, name)
    files = [os.path.join(d, f) for f in spec["files"]]
    sess = f"build_{name}"
    print(fn(M.load_pre)(sess, json.dumps(files)).splitlines()[0])
    print(fn(M.run_gate)(sess).splitlines()[-1])
    fn(M.canonical_analysis)(sess)
    print(fn(M.prepare_vec)(sess, **spec["prepare"]).splitlines()[0])
    out = fn(M.rank_test)(sess, wait=wait, **spec["rank"])
    print(out[:1500])
    folders = []
    s = M._sess.get(sess)
    for jids in s.rank_jobs.values():
        for jid in jids:
            from sima import jobs
            folders.append(jobs.status(jid)["folder"])
    # the tutorial's other systems (a control): the same spec, their rank only
    for k, ctrl in enumerate(spec.get("controls", []), 1):
        cs = f"{sess}_c{k}"
        fn(M.load_pre)(cs, json.dumps([os.path.join(d, f) for f in ctrl]))
        fn(M.run_gate)(cs)
        fn(M.canonical_analysis)(cs)
        fn(M.prepare_vec)(cs, **spec["prepare"])
        print(fn(M.rank_test)(cs, wait=wait, **spec["rank"])[:600])
        for jids in M._sess.get(cs).rank_jobs.values():
            for jid in jids:
                from sima import jobs
                folders.append(jobs.status(jid)["folder"])
    if spec.get("vec"):
        print(fn(M.estimate_vec)(sess, theory="the tutorial's rank (see TUTORIAL.md)",
                                 **spec["vec"])[:400])
        if spec.get("irf"):
            print(fn(M.irf_bands)(sess, wait=wait, **spec["irf"])[:400])
            from sima import jobs
            folders.append(jobs.status(s.irf_jobs[s.vec_current])["folder"])
    for f in folders:
        sanitize(f)
        print("cache:", os.path.relpath(f, ROOT),
              sum(os.path.getsize(os.path.join(f, x)) for x in os.listdir(f)), "bytes")
    return folders


if __name__ == "__main__":
    names = sys.argv[1:] or list(SPECS)
    for nm in names:
        build(nm, SPECS[nm])
