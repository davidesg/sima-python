#!/usr/bin/env python3
"""BUG-0018: canonical_analysis read the levels with each model's harmonics and
interventions inside, and the order by M(l) it hands to prepare_vec as p came
out inflated.

The US monetary VAR, monthly 1990:01-2007:12 (FRED: IPB50001N, CPIAUCNS,
MCOILWTICO, FEDFUNDS), with the univariate models guided in art: IPI and IPC
carry harmonics and interventions (Katrina, the Gulf War), WTI an impulse,
FF none. With the deterministic terms inside, the contiguous order by M(l)
(p_run, prepare_vec's default p) is 14; without them, 4.

Exits 1 while the canonical analysis reads them inside (p_run 14), 0 when
it removes them (p_run 4) and still shows, for comparison, the reading with
the interventions inside.
"""
import json
import os
import sys
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = [os.path.join(HERE, f) for f in
         ("IPI_m07.pre", "IPC_m07.pre", "WTI_m03.pre", "FF_m03.pre")]


def main():
    warnings.simplefilter("ignore")
    import sima.mcp_server as M
    from sima import session as S
    fn = lambda f: getattr(f, "fn", f)                   # noqa: E731
    fn(M.load_pre)("bug18", json.dumps(FILES))
    g = fn(M.run_gate)("bug18")
    if "GATE FAILED" in g:
        print(g)
        return 2
    txt = fn(M.canonical_analysis)("bug18")
    c = S.get("bug18").canonical
    p_run = c.get("p_run", c["p"])
    print(f"order by M(l) handed to prepare_vec (p_run): {p_run}")
    fixed = p_run == 4 and "THE LEVELS READ (BUG-0018)" in txt and "for comparison" in txt
    print("FIXED: the levels without their deterministic terms" if fixed else
          "OPEN: the levels with their harmonics and interventions inside")
    return 0 if fixed else 1


if __name__ == "__main__":
    sys.exit(main())
