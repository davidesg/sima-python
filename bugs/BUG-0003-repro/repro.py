"""BUG-0003: on route U, `zeros` rejects the own coefficients of the ECHELON
FORM («is a coefficient of a univariate model ... simplify it there»), though
in the echelon form those coefficients are no longer art's: the free
AR(n_i)/MA(n_i) replaces each univariate model's regular ARMA (own="free").
The VAR(1) inside (1, 1, 1) — the echelon form without its MA part — cannot
be written. The files are art's models of the lutkepohl_poskitt example.

    PYTHONPATH=src python3 bugs/BUG-0003-repro/repro.py   # exits 1 while open
"""
import json, os, sys
from sima import mcp_server as M
fn = lambda t: getattr(t, "fn", t)
HERE = os.path.dirname(os.path.abspath(__file__))
paths = [os.path.join(HERE, f) for f in
         ("Buffalo_rw.pre", "Minneapolis_ar1.pre", "KansasCity_ar1.pre")]
fn(M.load_pre)("bug3", json.dumps(paths))
fn(M.run_gate)("bug3")
names = ("Buffalo", "Minneapolis", "KansasCity")
zeros = [f"theta_{a}[B^1]" for a in names] + \
        [f"MA1[{a}<-{b}]" for a in names for b in names if a != b]
out = fn(M.estimate)("bug3", indices="1,1,1", zeros=", ".join(zeros))
print(out.splitlines()[0])
bad = "is a coefficient of a univariate model" in out
print("echelon own zeros rejected on route U:", bad)
sys.exit(1 if bad else 0)
