"""BUG-0001: load_pre's table shows a random walk, (0,1,0), as «AR 1».
Buffalo_rw.pre is art's (0,1,0) for Buffalo (the lutkepohl_poskitt example);
Minneapolis_ar1.pre an AR(1), for contrast.

    PYTHONPATH=src python3 bugs/BUG-0001-repro/repro.py   # exits 1 while open
"""
import json, os, re, sys
from sima import mcp_server as M
fn = lambda t: getattr(t, "fn", t)
HERE = os.path.dirname(os.path.abspath(__file__))
paths = [os.path.join(HERE, f) for f in ("Buffalo_rw.pre", "Minneapolis_ar1.pre")]
out = fn(M.load_pre)("bug1", json.dumps(paths))
row = next(l for l in out.splitlines() if "Buffalo" in l)
print(row)
p = int(re.search(r"AR (\d+)", row).group(1))
print("AR order shown for a (0,1,0):", p)
sys.exit(1 if p != 0 else 0)
