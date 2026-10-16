"""BUG-0006: an own MA(1) coefficient stops at exactly -1 (the fold of the
cast, x -> 1/x) and estimate reports a convergence, a t value starred as
significant and "Next: evaluate". The joint MA is not on the wall (largest
inverse root 0.99916), so ma_boundary is 0 and nothing flags it.

Lutkepohl and Poskitt's flour prices, route V, echelon indices (1, 1, 1):
theta_Minneapolis and theta_KansasCity end at -1.000000 (termcode 1, fdhess
standard errors 0.112 and 0.197, t -8.94 and -5.07 with their asterisks).

    PYTHONPATH=src python3 bugs/BUG-0006-repro/repro.py   # exits 1 while open
"""
import re, sys, tempfile
import numpy as np
from sima import mcp_server as M
from sima.session import _SESSIONS
fn = lambda t: getattr(t, "fn", t)
fn(M.load_example)("lutkepohl_poskitt", session="bug6", dest=tempfile.mkdtemp())
fn(M.characterize)("bug6")
fn(M.write_specs)("bug6", overwrite=True)
fn(M.run_gate)("bug6")
out = fn(M.estimate)("bug6", indices="1, 1, 1")
r = list(_SESSIONS["bug6"].fits.values())[-1].result
own = {m.group(1): float(m.group(2)) for m in
       re.finditer(r"^\s+(theta_\w+)\[B\^1\]\s+(-?\d+\.\d+)", out, re.M)}
folded = [k for k, v in own.items() if abs(abs(v) - 1.0) < 1e-6]
root = np.abs(np.linalg.eigvals(np.asarray(r.theta)[0])).max()
print("own MA(1):", own)
print("at |theta| = 1 (the fold):", folded)
print(f"termcode {r.termcode}, ma_boundary {r.ma_boundary}, largest joint MA root {root:.5f}")
flagged = bool(re.search(r"fold|boundary|wall|at -1|not a (convergence|maximum)", out, re.I))
starred = any(re.search(rf"^\s+{k}\[B\^1\].*\*\s*$", out, re.M) for k in folded)
print("the report flags it:", flagged, "| starred as significant:", starred)
sys.exit(1 if folded and (not flagged or starred) else 0)
