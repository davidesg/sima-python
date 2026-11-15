#!/usr/bin/env python3
"""BUG-0013: estimate_vec says "standard errors from the finite-difference
Hessian" when drvec's fdhess failed and the table carries the BFGS ones.

Two synthetic I(1) series in logs, cointegrated, with refactor = 1 in both
files (what atsw-gui's GUI writes for a new series). drvec's -fdhess does not
come out (FitResult.fdhess.ok is False) and the standard errors are the BFGS
ones; sima's header says they are fdhess's. The t of beta is -28.4 here and
-10.5 for the same data at refactor = 100, where fdhess does come out.

Exits 1 while the header claims the finite-difference Hessian for a fit whose
fdhess is not ok; 0 when the header says what the table carries.
"""
import json
import os
import re
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _datos import coint, pre               # noqa: E402

import drvec                                # noqa: E402
import sima.mcp_server as S                 # noqa: E402
import sima.mcp_vec as V                    # noqa: E402


def main():
    y, x = coint()
    d = tempfile.mkdtemp()
    files = [pre(f"{d}/Y.pre", 100 * np.exp(y), 0.0, 1.0, 1, "Y"),
             pre(f"{d}/X.pre", 100 * np.exp(x), 0.0, 1.0, 1, "X")]
    r = drvec.fit(files, 1, 0, 1, case="pre", fdhess=True)
    ok = bool(getattr(r.fdhess, "ok", False))
    S.load_pre("v", json.dumps(files))
    S.run_gate("v")
    V.prepare_vec("v", "long run", 1, 0)
    est = V.estimate_vec("v", 1, theory="repro: the data are built cointegrated")
    claims = "standard errors from the finite-difference Hessian" in est
    b = re.search(r"Y in ec1\s+(-?[0-9.]+)\s+[0-9.]+\s+(-?[0-9.]+)", est)
    print(f"drvec fdhess ok: {ok};  sima's header claims fdhess: {claims};"
          f"  t of beta: {b.group(2) if b else '?'}")
    abierto = claims and not ok
    print("the header names a Hessian the table does not carry" if abierto else "ok")
    return 1 if abierto else 0


if __name__ == "__main__":
    sys.exit(main())
