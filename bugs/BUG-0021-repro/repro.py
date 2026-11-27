"""BUG-0021: estimate and structure run with no time bound, no progress and no
estimate of the cost, and a client that gives up loses the session.

With the engine, `structure` on the US monetary VAR(1) (IPI, IPC, WTI, FF,
1990-2007) takes about 7 minutes (433 s measured 2026-11-26): it fits every
restricted model of every triangular ordering. On the pure-Python port
(drvarma's faithful port of the C) the same call is hours, and so is a VAR(1) estimate.

In the P08, one group's `structure` passed 25 minutes; when the client
cancelled it, the server kept computing for over 80 minutes of CPU, and the
session, which does not survive a restart, was lost. Two other groups saw
estimate "not answer" for 30 minutes and left sima. An MCP client's tool
timeout (minutes) is far below that.

The repro checks that neither tool takes a time budget, and times structure
on the monetary VAR(1) with the engine, stopping at 150 s. Exits 1 while
there is no budget and structure passes 120 s.

    python3 bugs/BUG-0021-repro/repro.py
"""
import inspect
import json
import os
import signal
import sys
import time
import warnings

warnings.simplefilter("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
import tempfile                                          # noqa: E402
_T = tempfile.mkdtemp(prefix="bug21_")                   # structure's job, out of the repo
os.environ.setdefault("SIMA_JOBS_DIR", os.path.join(_T, "jobs"))
os.environ.setdefault("SIMA_JOBS_HOME", os.path.join(_T, "home"))
import sima.mcp_server as M                              # noqa: E402

budget = [n for f in (M.estimate, M.structure)
          for n in inspect.signature(f).parameters
          if any(w in n.lower() for w in ("timeout", "budget", "max_seconds", "deadline"))]
print("time-budget parameters in estimate/structure:", budget or "none")

D = os.path.join(HERE, "..", "BUG-0018-repro")
paths = json.dumps([os.path.join(D, f + ".pre") for f in ("IPI_m07", "IPC_m07", "WTI_m03", "FF_m03")])
M.load_pre("b21", paths)
M.run_gate("b21")
t = time.time()
M.estimate("b21", p=1, q=0)
print(f"estimate VAR(1): {time.time() - t:.0f} s")


def stop(*_):
    raise TimeoutError


signal.signal(signal.SIGALRM, stop)
signal.alarm(150)
t = time.time()
try:
    M.structure("b21")
    took = time.time() - t
    print(f"structure: {took:.0f} s")
except TimeoutError:
    took = 150.0
    print("structure: still running after 150 s")
bad = (not budget) and took > 120
print("OPEN" if bad else "fixed")
sys.exit(1 if bad else 0)
