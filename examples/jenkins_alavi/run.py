#!/usr/bin/env python3
"""Jenkins and Alavi (1981) with sima: the muskrat-mink example, step by step.

Runs the protocol node by node with the SAME tools the MCP server serves (the
functions of `sima.mcp_server`), starting from the two univariate models built
in art (`art/MUSKRAT_m03.pre`, `art/MINK_m02.pre`). Every report is written to
`out/NN_<tool>.md` and every figure to `out/figs/`; the path of the analysis,
with the decisions and their reasons, is exported at the end as the guion.

    python3 examples/jenkins_alavi/run.py            # the whole walkthrough
    python3 examples/jenkins_alavi/run.py --upto 6   # stop after step 6

The decisions recorded are the ones taken in the analysis this example comes
from (2026-09-29/30), each with the evidence it rested on. Read
docs/MANUAL-jenkins-alavi.md alongside: it explains every step.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
FILES = [os.path.join(HERE, "art", "MUSKRAT_m03.pre"),
         os.path.join(HERE, "art", "MINK_m02.pre")]
NAME = "muskrat_mink"
LINKS = "MUSKRAT<-MINK, MINK<-MUSKRAT"


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

    # N2: identification, the two methods of Jenkins and Alavi
    step("N2 residual CCFs of the diagonal system", M.identify_cross, NAME)
    step("N2 Jenkins and Alavi's matrices, methods 1 and 2", M.identify_matrices, NAME)
    step("N2 figure, method 2 (prewhitened)", M.plot_identification, NAME, method=2)
    step("N2 figure, method 1 (not prewhitened)", M.plot_identification, NAME, method=1)
    decide("N2", "estimate both candidates: MA(1) residual model (method 2) and cross AR(2) "
           "(method 1), full covariance",
           "Method 2: the cross ccf cuts off after lag 1 on both sides (predator-prey); "
           "method 1: the cross pccf cuts off after 2. Jenkins and Alavi estimated both, "
           "(5.8) and (5.9). r(0) = 0.38 asks for the full covariance.",
           evidence="ccf +1 -0.36, -1 +0.35; pccf(w) +1 -0.64, +2 +0.32; S*(21) = 45.7",
           alternatives="one candidate only: rejected, the two readings disagree")

    # N3-N4: the two candidates, their optimum, their checking
    step("N3 candidate A: the MA(1) residual model, form (3.22)", M.estimate, NAME, 0, 1,
         False, links=LINKS, cross="residual", start="preliminary")
    step("N4 checking of A", M.check_residuals, NAME)
    step("N3 candidate B: the cross AR(2)", M.estimate, NAME, 2, 0, False, links=LINKS,
         start="preliminary")
    step("N4 checking of B", M.check_residuals, NAME)
    decide("N4", "both candidates pass the checking; no intervention",
           "Residual matrices clean, portmanteau not significant. The largest residual, "
           "1908 (their 1906), has no known cause; Jenkins and Alavi did not intervene.",
           evidence="A: 1 lag beyond the band of 1.2 expected; B: none; 1908 -3.9 s.d.",
           alternatives="intervene 1908 in art: left as an open caveat")

    # N5: the yardstick, and Jenkins and Alavi's own experiment (§6.3)
    step("N5 Table VIII in sample, B on all the data", M.forecast_uncertainty, NAME,
         horizon=3)
    step("N5 Table VIII as in §6.3: B refitted on 48 observations", M.forecast_uncertainty,
         NAME, horizon=3, estwin=48)
    step("N5 out of sample, B, estimated on 48", M.evaluate, NAME, 2, 0, 48, horizon=3,
         links=LINKS)
    step("N5 out of sample, A, estimated on 48", M.evaluate, NAME, 0, 1, 48, horizon=3,
         links=LINKS, cross="residual")
    decide("N5", "forecasting: the univariate models; the system: B, as a structural "
           "description (Jenkins and Alavi's Lotka-Volterra reading)",
           "In sample B lowers V(l) as their Table VIII; out of sample, which they could "
           "not run, B loses in every cell and A ties: the cross dynamics are real but do "
           "not forecast better with 48 years.",
           evidence="V(1) muskrat 25.7 -> 18.2 in sample; RMSE ratios B 1.02-1.42, A 0.98-1.08",
           alternatives="keep B for forecasting: rejected by N5")

    step("the guion: the path, its evidence and its decisions", M.export_guion, NAME)
    print(f"\nReports and figures in {OUT}")


if __name__ == "__main__":
    main()
