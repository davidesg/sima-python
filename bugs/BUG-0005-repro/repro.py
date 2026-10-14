"""BUG-0005: identify_echelon's choice depends on max_index through the common
sample (t0 = h + n_max: T 95 with n_max 3, T 92 with n_max 6), and the report
does not say on how many observations the table was computed. On the flour
prices the choice flips: (1, 0, 0) with max_index 3, (0, 0, 0) with 6, with
EITHER set of univariate models (flour_prices' MA(1), or art's random walk and
AR(1)) — the univariate ARMA plays no part. MANUAL-echelon §5.1 and the
lutkepohl_poskitt tutorial's aside attribute the (1, 0, 0) to route U.

    PYTHONPATH=src python3 bugs/BUG-0005-repro/repro.py   # exits 1 while open
"""
import json, os, re, sys
from sima import mcp_server as M
fn = lambda t: getattr(t, "fn", t)
HERE = os.path.dirname(os.path.abspath(__file__))
sets = {"MA(1) x3 (flour_prices)": ("BUFFALO_m01.pre", "MINNEAPOLIS_m01.pre",
                                    "KANSASCITY_m01.pre"),
        "RW, AR(1), AR(1) (art)": ("Buffalo_rw.pre", "Minneapolis_ar1.pre",
                                   "KansasCity_ar1.pre")}
choice, shows_T = {}, True
for k, (label, files) in enumerate(sets.items()):
    nm = f"bug5_{k}"
    fn(M.load_pre)(nm, json.dumps([os.path.join(HERE, f) for f in files]))
    fn(M.run_gate)(nm)
    for mi in (3, 6):
        out = fn(M.identify_echelon)(nm, max_index=mi)
        c = re.search(r"Chosen by SC: (\(.*?\))", out).group(1)
        l0 = next(l for l in out.splitlines() if l.strip().startswith("(0, 0, 0)"))
        choice[(label, mi)] = c
        shows_T &= bool(re.search(r"\bT\s*=?\s*\d+|\d+ observations", out))
        print(f"{label:<26} max_index {mi}: {c}   {l0.split()[4]} = log|S| (0,0,0)")
flips = any(choice[(l, 3)] != choice[(l, 6)] for l in sets)
print("the choice changes with max_index:", flips)
print("the report says the sample size of the table:", shows_T)
sys.exit(1 if (flips and not shows_T) else 0)
