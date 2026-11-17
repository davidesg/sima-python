#!/usr/bin/env python3
"""BUG-0015: the job key holds drvarma's (and fue's) version, so every drvarma
release invalidates the examples' bootstrap caches, though the bootstrap does
not run on drvarma.

jobs.make_key puts {"drvec", "drvarma", "fue"} versions in the key of every
job. The rank test's bootstrap is drvec's (its C, or its Python port): with
the same data, arguments, drvec and engine, a new drvarma gives the same
result and another key. With drvarma 0.3.4 (a change to an HTML page) the
seven caches of sima 0.2.3 stopped matching: every tutorial reran its
bootstrap until sima 0.2.4 shipped them rebuilt (2026-11-16/17).

BY DESIGN (decided 2026-11-17): drvec's port computes the observed fits and
the LR with drvarma's optimizer and fue's reader even when the bootstrap runs
in C, so their versions belong in the key. This is now a guard: exits 0 while
drvarma's version changes the key; 1 if someone takes it out.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

from sima import jobs, provenance            # noqa: E402


def main():
    pre = os.path.join(ROOT, "examples", "jenkins_alavi", "art", "MUSKRAT_m03.pre")
    args = {"B": 499, "p": 2, "q": 0, "case": "2"}
    eng = ("c", "0.13", "bundled")
    real = provenance._version
    keys = []
    for v in ("0.3.3", "0.3.4"):
        provenance._version = lambda k, v=v: v if k == "drvarma" else real(k)
        keys.append(jobs.make_key("rank_test", args, [pre], eng)[0])
    provenance._version = real
    same = keys[0] == keys[1]
    print(f"key with drvarma 0.3.3: {keys[0][:16]}\nkey with drvarma 0.3.4: {keys[1][:16]}")
    print("drvarma's version is in the key, as designed (BUG-0015)" if not same else
          "WRONG: drvarma's version left the key -- the observed LR depends on it")
    return 1 if same else 0


if __name__ == "__main__":
    sys.exit(main())
