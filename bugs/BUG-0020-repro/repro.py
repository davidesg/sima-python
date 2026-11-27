"""BUG-0020: when drvarma computes on its pure-Python port, no tool says so.

drvarma warns once with a RuntimeWarning, which goes to the MCP server's
stderr: no client shows it to the model or to the analyst. sima writes
"drvarma engine python" into the provenance of each script entry, which
nobody reads while working, and records neither the Python version nor the
reason the engine did not load. In the P08 five groups worked for hours on
the port without knowing why everything took 10-20 minutes (a faithful
port of the C: drvarma TODO.md, the speed study); two left sima for statsmodels or OLS.

The repro blocks the extension (as the py3-none-any wheel does), loads a
pair and asks load_pre for the engine; and checks that the provenance names
the interpreter. Exits 1 while open.

    python3 bugs/BUG-0020-repro/repro.py
"""
import json
import os
import sys
import warnings

sys.modules["drvarma._drvarma_engine"] = None          # what the pure wheel gives
warnings.simplefilter("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
import sima.mcp_server as M                              # noqa: E402
from sima import provenance                              # noqa: E402

D = os.path.join(HERE, "..", "BUG-0018-repro")
paths = json.dumps([os.path.join(D, f) for f in ("IPC_m07.pre", "IPI_m07.pre")])
out = M.load_pre("b20", paths)
out = out if isinstance(out, str) else "\n".join(map(str, out))
said = [l.strip() for l in out.splitlines()
        if any(w in l.lower() for w in ("python", "port", "slower", "motor", "lento"))]
prov = provenance.base()
print("provenance:", prov)
print("load_pre about the engine:", said or "NOTHING")
python_in_prov = any("python" == k or "python_version" in k for k in prov)
bad = (not said) or (not python_in_prov)
print("OPEN" if bad else "fixed")
sys.exit(1 if bad else 0)
