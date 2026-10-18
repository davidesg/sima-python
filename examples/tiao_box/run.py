#!/usr/bin/env python3
"""Tiao and Box with sima: the gas furnace, step by step.

Runs the protocol node by node with the SAME tools the MCP server serves (the
functions of `sima.mcp_server`), from the raw table `data/gas_furnace.csv` on
route V: the vector first, as Tiao and Box (1981, §5.2) do, without telling the
method which series is the input. Every report is written to
`out/NN_<tool>.md`; the path of the analysis, with the decisions and their
reasons, is exported at the end as the guion.

    python3 examples/tiao_box/run.py            # the whole walkthrough
    python3 examples/tiao_box/run.py --upto 6   # stop after step 6

The decisions recorded are the ones taken in the analysis this example comes
from (2026-10-13), each with the evidence it rested on. Read
docs/STUDY-tiao-box.md and TUTORIAL.md alongside.
"""
from __future__ import annotations

import argparse
import base64
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
DATA = os.path.join(HERE, "data", "gas_furnace.csv")
NAME = "tiao_box"
LEVELS = "InputGasRate: lam=1, d=0; CO2: lam=1, d=0"
# Tiao and Box's restricted AR(6) (their 5.7): the input's own AR(3), no CO2 in
# the gas equation, a delay of three periods, and the CO2's own AR(4)
TB_ZEROS = ", ".join([f"phi_InputGasRate[B^{l}]" for l in (4, 5, 6)]
                     + [f"AR{l}[InputGasRate<-CO2]" for l in range(1, 7)]
                     + ["AR1[CO2<-InputGasRate]", "AR2[CO2<-InputGasRate]",
                        "phi_CO2[B^5]", "phi_CO2[B^6]"])


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
    shutil.rmtree(os.path.join(HERE, "data", "gas_furnace_sima"), ignore_errors=True)
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
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(f"# {n}. {title}\n\n" + "\n".join(text) + "\n")
        print(f"{n:2d}. {title:<62} -> out/{os.path.basename(path)}"
              + (f" (+{imgs} figure{'s' if imgs > 1 else ''})" if imgs else ""))
        return out

    def decide(node, decision, reason, evidence="", alternatives=""):
        if count[0] <= args.upto:
            _fn(M.record_decision)(NAME, node, decision, reason=reason, evidence=evidence,
                                   alternatives=alternatives, decided_by="analyst")

    # N0: the table, each series' transformation, the specifications
    step("N0r the raw table (no dates: an index from 1000)", M.load_data, NAME, DATA,
         freq=1, start="1000")
    step("N0c the transformation: the levels, as Tiao and Box", M.characterize, NAME,
         set=LEVELS)
    step("N0v route V: the specifications", M.write_specs, NAME)
    decide("N0c", "both series in levels, no transformation",
           "Tiao and Box (and Box and Jenkins) model the furnace in levels: a stationary "
           "engineering system. art's engine proposes logs for the CO2 from the domain "
           "rule; the mean-sd correlation is +0.06 in levels, nothing to correct.",
           alternatives="logs for the CO2, as art's rule proposes")
    step("N1 the gate", M.run_gate, NAME)

    # N2: identification on the vector
    step("N2 Tiao and Box's stepwise M(l)", M.identify_matrices, NAME, nlags=11)
    decide("N2", "a VAR(6), as Tiao and Box",
           "M(l) is significant up to l = 6 (1650, 665, 31.7, 22.5, 5.6, 12.9 in the "
           "paper) and not beyond.",
           evidence="M(l) table, chi-square(4) at 5 %: 9.5")

    # N3-N4: the VAR(6), its structure, the warning of Table 14
    step("N3 the full VAR(6)", M.estimate, NAME, 6, 0)
    step("N4t its structure: is there feedback?", M.structure, NAME)
    decide("N4t", "no feedback: InputGasRate -> CO2, a transfer function",
           "Dropping the CO2 from the gas equation costs nothing (LR 6.01, df 6); "
           "dropping the gas from the CO2 equation is rejected (LR 205). Tiao and Box: "
           "'a unidirectional relationship ... involving no feedback'.",
           alternatives="take it to mtram now: the transfer network is mtram's rung")
    step("N3 the warning of their Table 14: a VAR(2)", M.estimate, NAME, 2, 0)
    step("N4t its structure: a spurious feedback", M.structure, NAME)

    # N3: simplification
    step("N3 the VAR(6) again", M.estimate, NAME, 6, 0)
    step("N3 simplification by coefficient", M.simplify, NAME)
    step("N3 their restricted AR(6): the zeros of the system", M.estimate, NAME, 6, 0,
         zeros=TB_ZEROS)
    decide("N3", "Tiao and Box's restricted AR(6)",
           "Their zeros come from the fit and from the system: no feedback, the input's "
           "own AR(3), a delay of three periods. Against the full VAR(6): LR 17.4, df 13. "
           "The input's model is Box and Jenkins' (1.97, -1.37, .34); the delay "
           "coefficient -.53, theirs.",
           evidence="logL -2647.48 (15 parameters) against -2638.76 (28)",
           alternatives="simplify's 9 zeros (|t| < 1), a purely statistical cut")

    # N4-N5
    step("N4 its checking", M.check_residuals, NAME)
    step("N5 the yardstick, estimated on 200 observations", M.evaluate, NAME, 6, 0, 200,
         horizon=3, zeros=TB_ZEROS)
    decide("N5", "the restricted AR(6): the gas forecasts the CO2",
           "Out of sample the CO2 gains a quarter to nearly 40 % of its RMSE over its "
           "univariate model (ratios .76, .64, .61). The gas gains too (.82-.92), but its "
           "equation has no CO2 in it: that is its own AR(3), Box and Jenkins' model, "
           "against the ARMA(1, 1) route U's light builder gave it.",
           alternatives="hand the network to mtram, where the input is declared")
    step("the guion: the path, its evidence and its decisions", M.export_guion, NAME)
    print(f"\nReports and figures in {OUT}")


if __name__ == "__main__":
    main()
