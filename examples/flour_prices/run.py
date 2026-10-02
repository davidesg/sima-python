#!/usr/bin/env python3
"""Tiao and Box's tools with sima: the flour-price example, step by step.

Runs the protocol node by node with the SAME tools the MCP server serves (the
functions of `sima.mcp_server`), starting from the two univariate models built
with art's engine (`art/BUFFALO_m01.pre`, `art/MINNEAPOLIS_m01.pre`,
`art/KANSASCITY_m01.pre`). Every report is written to
`out/NN_<tool>.md` and every figure to `out/figs/`; the path of the analysis,
with the decisions and their reasons, is exported at the end as the guion.

    python3 examples/flour_prices/run.py            # the whole walkthrough
    python3 examples/flour_prices/run.py --upto 6   # stop after step 6

The decisions recorded are the ones taken in the analysis this example comes
from (2026-10-02), each with the evidence it rested on. Read
docs/STUDY-tiao-box.md and TUTORIAL.md alongside.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
FILES = [os.path.join(HERE, "art", f"{c}_m01.pre")
         for c in ("BUFFALO", "MINNEAPOLIS", "KANSASCITY")]
NAME = "flour_prices"


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

    # N0-N1: the univariate models, certified
    step("N0 load the univariate models (art's .pre)", M.load_pre, NAME, json.dumps(FILES))
    step("N1 the diagonal gate", M.run_gate, NAME)

    # N1b: Box and Tiao (1977) on the levels
    step("N1b canonical analysis of the levels (Box and Tiao 1977)", M.canonical_analysis,
         NAME)
    decide("N1b", "go on with the univariates' differences, the caveat recorded",
           "Two components near 1 (sqrt(lam) .92, .97) for three differenced series: "
           "possibly one stationary combination, a contrast between markets (root .87; "
           "Tiao and Tsay's AR(1) contrast with phi .88). A reading, not a test; the "
           "test is drvec's.",
           evidence="lam .758 .854 .943; M(1) 462, M(2) 31 on the levels",
           alternatives="drvec now (Johansen): the natural next step, outside sima")

    # N2: identification
    step("N2 residual CCFs of the diagonal system", M.identify_cross, NAME)
    step("N2 Jenkins and Alavi's matrices, with Tiao and Box's M(l)", M.identify_matrices,
         NAME)
    decide("N2", "estimate the VAR(1) Tiao and Box's M(l) asks for, full covariance",
           "Method 2: nothing beyond lag 0 (innovations correlate .96, .85, .88). Method "
           "1: R_k cuts off after 1, S_k never does (the over-differencing pattern, Box "
           "and Tiao 1977 §4.4); M(l) significant only at l = 1.",
           evidence="M(1) = 38.0 (9 d.f.), M(2) = 1.9",
           alternatives="the VMA(1) R_k suggests: a second candidate, left out")

    # N3-N5
    step("N3 the VAR(1)", M.estimate, NAME, 1, 0, False)
    step("N4 its checking", M.check_residuals, NAME)
    step("N5 the yardstick, estimated on 72 months", M.evaluate, NAME, 1, 0, 72, horizon=6)
    decide("N5", "the univariate models with a full covariance; the system's structure "
           "is in the levels: drvec",
           "Out of sample the VAR(1) gains nothing worth a model (RMSE ratios .93-1.01): "
           "in the differences the joint model adds little. What ties the markets is in "
           "the levels (the canonical analysis; Tiao and Tsay's model).",
           evidence="RMSE ratio h=1: .99 .93 1.00; h=6: 1.01 1.00 1.00",
           alternatives="keep the VAR(1): rejected by N5")

    step("the guion: the path, its evidence and its decisions", M.export_guion, NAME)
    print(f"\nReports and figures in {OUT}")


if __name__ == "__main__":
    main()
