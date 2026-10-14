"""BUG-0002: estimate in the echelon form on route U labels its LR «against the
diagonal system (the univariates)», while the header says «against the same
model without cross terms». The second is what is computed: at indices
(0, 0, 0) the LR has 3 df (the innovation covariances only), but the
univariates of Minneapolis and Kansas City carry an AR(1) that the echelon
form has replaced. The files are art's models of the lutkepohl_poskitt example.

    PYTHONPATH=src python3 bugs/BUG-0002-repro/repro.py   # exits 1 while open
"""
import json, os, sys
from sima import mcp_server as M
fn = lambda t: getattr(t, "fn", t)
HERE = os.path.dirname(os.path.abspath(__file__))
paths = [os.path.join(HERE, f) for f in
         ("Buffalo_rw.pre", "Minneapolis_ar1.pre", "KansasCity_ar1.pre")]
fn(M.load_pre)("bug2", json.dumps(paths))
fn(M.run_gate)("bug2")
out = fn(M.estimate)("bug2", indices="0,0,0")
lr = [l for l in out.splitlines() if "LR" in l]
print("\n".join(lr))
bad = any("the diagonal system (the univariates)" in l for l in lr)
print("LR line still says «the univariates»:", bad)
sys.exit(1 if bad else 0)
