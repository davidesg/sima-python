#!/usr/bin/env python3
"""The echelon form with sima: Lutkepohl and Poskitt's flour prices, step by step.

Runs the protocol node by node with the SAME tools the MCP server serves (the
functions of `sima.mcp_server`), from the raw table `data/flour_prices.csv`
on route V: the vector first, as Lutkepohl and Poskitt (1996, §4.1) do. Every
report is written to `out/NN_<tool>.md`; the path of the analysis, with the
decisions and their reasons, is exported at the end as the guion.

    python3 examples/lutkepohl_poskitt/run.py            # the whole walkthrough
    python3 examples/lutkepohl_poskitt/run.py --upto 7   # stop after step 7

The decisions recorded are the ones taken in the analysis this example comes
from (2026-10-13), each with the evidence it rested on. Read
docs/MANUAL-echelon.md and TUTORIAL.md alongside.
"""
from __future__ import annotations

import argparse
import base64
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
DATA = os.path.join(HERE, "data", "flour_prices.csv")
NAME = "lutkepohl_poskitt"
LOGDIFF = "Buffalo: lam=0, d=1; Minneapolis: lam=0, d=1; KansasCity: lam=0, d=1"
# Lutkepohl and Poskitt's restricted VAR(1) and MA(1) (their Table 2): Kansas
# City's lag enters no equation, and Buffalo's lag does not enter Kansas City's
VAR_ZEROS = ("phi_KansasCity[B^1], AR1[Buffalo<-KansasCity], "
             "AR1[Minneapolis<-KansasCity], AR1[KansasCity<-Buffalo]")
MA_ZEROS = ("theta_KansasCity[B^1], MA1[Buffalo<-KansasCity], "
            "MA1[Minneapolis<-KansasCity], MA1[KansasCity<-Buffalo]")


def _fn(tool):
    return getattr(tool, "fn", tool)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--upto", type=int, default=99, help="stop after this step")
    args = ap.parse_args()
    try:
        from sima import mcp_server as M
    except ImportError:
        sys.exit("sima is not importable: pip install sima-tseries (or run from the repo "
                 "with PYTHONPATH=src)")
    os.makedirs(os.path.join(OUT, "figs"), exist_ok=True)
    # route V writes its specifications next to the data: start clean
    shutil.rmtree(os.path.join(HERE, "data", "flour_prices_sima"), ignore_errors=True)
    count = [0]

    def step(title, tool, *a, **kw):
        """Run one tool, write its report (and its figures), print a line."""
        count[0] += 1
        n = count[0]
        if n > args.upto:
            return None
        if tool.__name__.startswith("plot_") and "path" not in kw:
            kw["path"] = os.path.join(OUT, "figs", f"{n:02d}_{tool.__name__}.png")
        out = _fn(tool)(*a, **kw)
        parts = out if isinstance(out, list) else [out]
        text, imgs = [], 0
        for c in parts:
            if isinstance(c, str):
                text.append(c)
            elif getattr(c, "type", "") == "text":
                text.append(c.text)
            elif getattr(c, "type", "") == "image":
                imgs += 1
                p = os.path.join(OUT, "figs", f"{n:02d}_{tool.__name__}_{imgs}.png")
                with open(p, "wb") as fh:
                    fh.write(base64.b64decode(c.data))
        path = os.path.join(OUT, f"{n:02d}_{tool.__name__}.md")
        with open(path, "w") as fh:
            fh.write(f"# {n}. {title}\n\n" + "\n".join(text) + "\n")
        print(f"{n:2d}. {title:<62} -> out/{os.path.basename(path)}"
              + (f" (+{imgs} figure{'s' if imgs > 1 else ''})" if imgs else ""))
        return out

    def decide(node, decision, reason, evidence="", alternatives=""):
        if count[0] <= args.upto:
            _fn(M.record_decision)(NAME, node, decision, reason=reason, evidence=evidence,
                                   alternatives=alternatives, decided_by="analyst")

    # N0: the table, each series' transformation, the specifications
    step("N0r the raw table", M.load_data, NAME, DATA)
    step("N0c the transformation: rates of change, as Lutkepohl and Poskitt",
         M.characterize, NAME, set=LOGDIFF)
    step("N0v route V: the specifications", M.write_specs, NAME)
    # (the guion opens with the specifications: the transformation's reason goes here)
    decide("N0c", "the first differences of the logs, for the three cities",
           "Lutkepohl and Poskitt (1996, §4.1): 'Because the original series appear to "
           "be nonstationary, we use rates of change (first differences of logarithms).'",
           alternatives="the log levels (Tiao and Tsay's choice; the flour_prices example)")
    step("N1 the gate", M.run_gate, NAME)

    # N2: the Kronecker indices
    step("N2 the echelon index search (n_max 6, as theirs)", M.identify_echelon, NAME,
         max_index=6)
    decide("N2", "fit the search's (0, 0, 0), then Lutkepohl and Poskitt's (1, 1, 1)",
           "SC and HQ choose (0, 0, 0), as their full search with HQ does (Table 1). AIC, "
           "from the same table, chooses (1, 1, 1), as theirs. They go on with (1, 1, 1), "
           "'an intermediate value': understating may need changes later, overstating "
           "may not converge.",
           evidence="log|S| 5.4205 (0,0,0), 4.9739 (1,1,1), dim 18; AIC (T 92) 5.42 against 5.37",
           alternatives="stop at (0, 0, 0): correlated random walks")

    # N3: the fits
    step("N3 the search's choice, (0, 0, 0)", M.estimate, NAME, indices="0, 0, 0")
    step("N3 their choice, (1, 1, 1): the full VARMA(1, 1)", M.estimate, NAME,
         indices="1, 1, 1")
    step("N3 the VAR(1), (1, 1, 1) without MA", M.estimate, NAME, 1, 0)
    step("N3 simplification by coefficient", M.simplify, NAME)
    step("N3 their restricted VAR(1): five coefficients", M.estimate, NAME, 1, 0,
         zeros=VAR_ZEROS)
    step("N3 their restricted MA(1): five coefficients", M.estimate, NAME, 0, 1,
         zeros=MA_ZEROS)
    decide("N3", "the restricted VAR(1)",
           "The full (1, 1, 1) has 18 coefficients, most of them small, and a pair of MA "
           "roots at modulus 0.999, nearly non-invertible. Their restricted VAR(1) and MA(1) keep five each and fit almost "
           "as well; the VAR(1) a little better (log|S| 5.000 against 5.027, theirs "
           "4.985 and 5.004). Against (0, 0, 0) the VAR(1) gives LR 37.6, df 5: the "
           "search's choice underfits.",
           evidence="logL -669.13 (VAR), -670.47 (MA), -687.91 (0,0,0), -659.17 (1,1,1)",
           alternatives="the restricted MA(1), as good; the full (1, 1, 1)")
    step("N3 the restricted VAR(1), again the current fit", M.estimate, NAME, 1, 0,
         zeros=VAR_ZEROS)

    # N4-N5
    step("N4 its checking", M.check_residuals, NAME)
    step("N5 the yardstick, estimated on 72 months", M.evaluate, NAME, 1, 0, 72,
         horizon=6, zeros=VAR_ZEROS)
    decide("N5", "the restricted VAR(1) describes the system; to forecast, the "
           "univariates do as well",
           "Out of sample the restricted VAR(1) gains nothing worth a model (RMSE ratios "
           ".94-1.03): the dynamics are significant in sample (LR 37.6 against (0, 0, 0)) "
           "and small. Lutkepohl and Poskitt cite Grubb (1992), where the MA(1) for the "
           "differences 'did quite well'.",
           evidence="RMSE ratio h=1: 1.03 .94 1.00; h=6: 1.01 1.00 1.00",
           alternatives="keep the VAR(1) to forecast: rejected by N5")
    step("the guion: the path, its evidence and its decisions", M.export_guion, NAME)
    print(f"\nReports and figures in {OUT}")


if __name__ == "__main__":
    main()
