#!/usr/bin/env python3
"""BUG-0011: a VARMA whose search never left the diagonal start is reported as
an estimate, and its LR = 0 as evidence that there is no cross dynamics.

Two synthetic series about 10 000, lambda = -1, each an AR(1) with a mean fitted
by fue with refactor = 100 (what art writes). Their stationary series is
99.99 +- 0.0001: the optimiser stops at its first step. sima prints the cross
coefficients at 0 with the search's seed (0.1000) as standard error, and

    against the same model without cross terms: LR = 0.000, df = 3, p = 1.0000

The same files with refactor = 10 000 give AR1[Y<-X] = 0.4577 (t = 12.2) and
LR = 120.9. Exits 1 while sima reports LR = 0.000 for the refactor = 100 files;
0 when it estimates them or says the search did not start.
"""
import json
import os
import re
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _datos import pre, transfer            # noqa: E402

import sima.mcp_server as S                 # noqa: E402


def corre(factor, tag):
    e, x = transfer()
    d = tempfile.mkdtemp()
    files = [pre(f"{d}/Y.pre", 1e4 * np.exp(e), -1.0, factor, 0, "Y"),
             pre(f"{d}/X.pre", 1e4 * np.exp(x), -1.0, factor, 0, "X")]
    S.load_pre(tag, json.dumps(files))
    S.run_gate(tag)
    out = S.estimate(tag, 1, 0)
    lr = re.search(r"LR = ([0-9.]+), df = 3", out)
    cross = re.search(r"AR1\[Y<-X\]\s+(-?[0-9.]+)\s+([0-9.]+)\s+(-?[0-9.]+)", out)
    opt = re.search(r"optimiser: (.*)", out)
    print(f"refactor={factor:g}: {opt.group(1) if opt else '?'}")
    print(f"   AR1[Y<-X] = {cross.group(1) if cross else '?'} (t {cross.group(3) if cross else '?'})"
          f"   LR against the diagonal = {lr.group(1) if lr else 'not reported'}")
    return float(lr.group(1)) if lr else None


def main():
    malo = corre(100.0, "a")
    corre(1e4, "b")
    abierto = malo is not None and malo < 1e-3
    print("a search that never started is reported as LR = 0" if abierto else "ok")
    return 1 if abierto else 0


if __name__ == "__main__":
    sys.exit(main())
