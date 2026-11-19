#!/usr/bin/env python3
"""BUG-0019: estimate left a VAR(2) BELOW the VAR(1) it nests, and the remedy
it offers -- the second path, start="preliminary" -- never ran: the fit cache
ignored `start` and served the failed fit again, without saying so.

The US monetary VAR, monthly 1990:01-2007:12, route U (IPI, IPC, WTI, GS1;
the .pre guided in art; FRED data). From the zero start drvarma stops the
VAR(2) after 2 iterations at logL -1793.05 (drvarma BUG-0027), below the
VAR(1)'s -1744.88; the preliminary start reaches -1741.28.

Exits 1 while the session's VAR(2) lies below its VAR(1), or while asking for
the preliminary start does not reach the optimum; 0 when both hold.
(Several minutes: three or four fits.)
"""
import json
import os
import sys
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = [os.path.join(HERE, f) for f in
         ("IPI_m07.pre", "IPC_m07.pre", "WTI_m03.pre", "GS1_m01.pre")]


def main():
    warnings.simplefilter("ignore")
    import sima.mcp_server as M
    from sima import session as S
    fn = lambda t: getattr(t, "fn", t)                   # noqa: E731
    fn(M.load_pre)("bug19", json.dumps(FILES))
    fn(M.run_gate)("bug19")
    fn(M.estimate)("bug19", p=1, q=0)
    fn(M.estimate)("bug19", p=2, q=0)
    fn(M.estimate)("bug19", p=2, q=0, start="preliminary")
    s = S.get("bug19")
    l1 = s.fits[M._key(1, 0)].result.logL
    l2 = s.fits[M._key(2, 0)].result.logL
    print(f"VAR(1) logL {l1:.4f}; VAR(2) logL {l2:.4f} (the optimum: -1741.2755)")
    fixed = l2 >= l1 - 1e-3 and l2 > -1741.3
    print("FIXED: the VAR(2) is not below the VAR(1)" if fixed else
          "OPEN: the VAR(2) stays below the VAR(1) it nests")
    return 0 if fixed else 1


if __name__ == "__main__":
    sys.exit(main())
