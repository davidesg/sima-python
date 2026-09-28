# sima — TODO

The goal: bring sima to art's level as an assistant, on the ladder. 0.1.0 has
the protocol, the gate, the evidence, the yardstick and the guion. What is
missing, in order:

## Next

- [ ] **Studying an ill-defined estimation** (decided 2026-09-28). When a fit
      stops on the MA invertibility wall, drvarma C 5.0 says so as a fact
      (`OPTIMIZER STOPPED at the MA invertibility boundary`,
      `MA boundary: k of n inverse roots at modulus >= 1`) and adds no
      verdict. Studying it is sima's job, with the LLM. The motivating case is
      drvarma's bench case c2 (see its BUGS.md): no interior maximum, and a
      ridge that climbs along the wall from ℓ 66.21 to 71.22.
      - *Evidence:*
        - the AR/MA inverse roots with modulus and frequency;
        - the pairs that nearly cancel;
        - a second path: Shea's likelihood, `-lik shea` in the C (the Python
          port has no Shea yet);
        - restarts along the wall, pulling the MA roots inside and
          re-optimising, to see whether the ridge keeps rising.
      - *Menu, not a verdict:*
        - remove the common factor, or lower p or q;
        - or keep a model on the boundary, knowing it is one.
      - *Engine prerequisites in drvarma-python:*
        - `Ladder.fit` should expose the same fact (a `ma_boundary` count on
          `Fit`, as the C writes it);
        - a restart from a given point, which `estimate_w` does not accept
          today.

- [ ] **Autonomous lane in writing** (as art's `CARRIL AUTÓNOMO`): the order of
      the nodes, what to decide at each, and the report handed over at the end.
- [ ] **Figures**: residual CCF panels (the old sima's `_draw_ccf_panel` moves
      here, as presentation), forecast fans, IRFs.
- [ ] **IRF/FEVD bands** for the ladder model. drvarma's `irf_fevd_bands` still
      needs the result of the multivariate-`.inp` path; the ladder needs its own
      (Monte Carlo on the ladder parameters, or the delta method).
- [ ] **Restricted cross terms**: estimate only the pairs the evidence points at
      (today p, q apply to every pair). Needs an engine option in
      `drvarma.ladder` (a mask on the cross coefficients).
- [ ] **Reorder** tool: reload in another Cholesky order and compare IRFs.
- [ ] **HTML guion** (as art's `export_guion_html`).
- [ ] **Resources**: `sima://defects` from `bugs/` (with `fue.bugs`, no copy),
      `sima://protocol`.

## Later

- [ ] **Echelon VARMA** (Kronecker indices) as a specification form: see
      drvarma's `docs/ECHELON_SEEDED_DESIGN.md`. The specification should be a
      file both engines read (like drtran's `.cns`), not code in one of them.
- [ ] **Conditional forecasts** on a scenario for one series (the pass-through
      use: `MODELS_RESULTS.md` §4 of drvarma C).
- [ ] With `estwin`, the gate says "not an optimum" when the reason is that the
      sample is another (also in drvarma C and Python).

## Housekeeping

- [ ] `tools/gen_tools_md.py` is a copy of art's: make it a shared dev tool.
- [ ] CI: the tests need `drvarma>=0.2.0` from PyPI; until it is published the
      workflow installs drvarma from its repository.
