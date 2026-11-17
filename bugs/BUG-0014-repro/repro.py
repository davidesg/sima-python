#!/usr/bin/env python3
"""BUG-0014: with files that carry different rescaling factors, the alpha
restriction (alpha = A psi) is imposed in the engine's units, and alpha is
printed in them.

BUG-0012 took beta's restrictions (fixb2, fixb2row) and theta to each series'
units; alpha stayed. alpha's row i is the equation of series i, so in each
series' units it is K_i times the engine's, and a restriction that links two
rows (alpha_Y = c alpha_X) is a different restriction in the engine.

BUG-0012's data: two series in logs with log Y - log X stationary. With both
files at refactor = 100, alpha = A psi with A = the alpha estimated there holds
exactly (LR = 0). With Y at 100 and X at 1 -- the same data, the same fit --
the same A, in the series' units, must hold too. Exits 1 while it is rejected
(or alpha prints differently in the two); 0 when the two agree.
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


def corre(fy, fx, tag, A=None):
    y, x = coint()
    d = tempfile.mkdtemp()
    files = [pre(f"{d}/Y.pre", 100 * np.exp(y), 0.0, fy, 1, "Y"),
             pre(f"{d}/X.pre", 100 * np.exp(x), 0.0, fx, 1, "X")]
    S.load_pre(tag, json.dumps(files))
    S.run_gate(tag)
    V.prepare_vec(tag, "long run", 1, 0)
    est = V.estimate_vec(tag, 1, theory="repro: the data are built cointegrated")
    rows = re.findall(r"D\.(\w+) <- ec1\s+([+-][0-9.]+)\s+\(t", est)
    alpha = {nm: float(v) for nm, v in rows}
    order = [nm for nm, _ in rows]
    lr = p = None
    if A is not None:
        out = V.test_restriction(tag, alpha=json.dumps([[A[nm]] for nm in order]))
        m = re.search(r"LR = ([0-9.]+), df (\d+), p ([0-9.]+)", out)
        lr, p = (float(m.group(1)), float(m.group(3))) if m else (None, None)
    print(f"refactor Y={fy:g}, X={fx:g}: alpha " +
          ", ".join(f"{k} {v:+.4f}" for k, v in alpha.items()) +
          ("" if A is None else f"   H0 alpha = A psi: LR = {lr}, p = {p}"))
    return alpha, lr, p


def main():
    a_c, _, _ = corre(100.0, 100.0, "c")
    _, lr_c, p_c = corre(100.0, 100.0, "c2", A=a_c)
    a_m, lr_m, p_m = corre(100.0, 1.0, "m", A=a_c)
    same_alpha = all(abs(a_c[k] - a_m[k]) <= 0.01 * max(1.0, abs(a_c[k])) for k in a_c)
    ok = (p_m is not None and p_m > 0.05 and lr_c is not None and same_alpha)
    print("ok" if ok else "OPEN: the mixed files print another alpha, or reject the "
          "restriction the common ones hold")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
