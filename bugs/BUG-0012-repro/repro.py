#!/usr/bin/env python3
"""BUG-0012: with files that carry different rescaling factors, the VEC's
restriction is imposed in the engine's units: a true beta = -1 is rejected.

Two synthetic I(1) series in logs with log Y - log X stationary, so the
cointegrating vector is (1, -1). With both files at refactor = 100,
test_restriction(fixb2="-1") gives LR = 0.03, p = 0.87. With Y at 100 and X at
1 -- the same data and the same fit -- beta prints -0.009955 (it is -0.9955 in
the series' units), alpha 30.73 with t = 306, and the same call gives
LR = 37.5, p = 0.0000. Nothing in load_pre, prepare_vec or estimate_vec says
the files do not share a factor (drvec C warns; the port does not).

Exits 1 while the mixed files reject the hypothesis the common files accept;
0 when the two agree (or sima refuses / converts the restriction).
"""
import json
import os
import re
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _datos import coint, pre               # noqa: E402

import sima.mcp_server as S                 # noqa: E402
import sima.mcp_vec as V                    # noqa: E402


def corre(fy, fx, tag):
    y, x = coint()
    d = tempfile.mkdtemp()
    files = [pre(f"{d}/Y.pre", 100 * np.exp(y), 0.0, fy, 1, "Y"),
             pre(f"{d}/X.pre", 100 * np.exp(x), 0.0, fx, 1, "X")]
    S.load_pre(tag, json.dumps(files))
    S.run_gate(tag)
    V.prepare_vec(tag, "long run", 1, 0)
    est = V.estimate_vec(tag, 1, theory="repro: the data are built cointegrated")
    b = re.search(r"Y in ec1\s+(-?[0-9.]+)\s+[0-9.]+\s+(-?[0-9.]+)", est)
    a = re.search(r"D\.Y <- ec1\s+(-?[0-9.]+)\s+[0-9.]+\s+(-?[0-9.]+)", est)
    out = V.test_restriction(tag, fixb2="-1")
    p = re.search(r"LR = ([0-9.]+), df 1, p ([0-9.]+)", out)
    warned = bool(re.search(r"refactor|rescaling factor", est, re.I))
    print(f"refactor Y={fy:g}, X={fx:g}: beta = {b.group(1) if b else '?'}"
          f"  alpha = {a.group(1) if a else '?'} (t {a.group(2) if a else '?'})"
          f"  H0 beta = -1: LR = {p.group(1) if p else '?'}, p = {p.group(2) if p else '?'}"
          f"  warned: {warned}")
    return float(p.group(2)) if p else None


def main():
    comun = corre(100.0, 100.0, "c")
    mixto = corre(100.0, 1.0, "m")
    abierto = comun is not None and mixto is not None and comun > 0.05 and mixto < 0.05
    print("the same hypothesis is accepted with a common factor and rejected with mixed ones"
          if abierto else "ok")
    return 1 if abierto else 0


if __name__ == "__main__":
    sys.exit(main())
