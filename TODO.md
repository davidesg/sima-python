# sima — TODO

The goal: bring sima to art's level as an assistant, on the ladder. 0.1.0 has
the protocol, the gate, the evidence, the yardstick and the guion. What is
missing, in order:

## Next

- [x] **Studying an ill-defined estimation** (decided 2026-09-28; done the same day: `study_estimation`). When a fit
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

- [x] **Autonomous lane in writing** (2026-09-28) (as art's `CARRIL AUTÓNOMO`): the order of
      the nodes, what to decide at each, and the report handed over at the end.
- [x] **Figures** (2026-09-29, `sima.figures`): the IRF as an ACF-like panel per
      (response, shock) with the band dashed; the FEVD in the same layout on
      0-100 %; drvus' residual CCFs (drvarma's `_draw_ccf_panel`, reused); the
      forecasts in levels. Tools `plot_*`, the image inside the answer.
- [x] **IRF/FEVD bands** for the ladder model (2026-09-28, `Ladder.irf_fevd_bands`). drvarma's `irf_fevd_bands` still
      needs the result of the multivariate-`.inp` path; the ladder needs its own
      (Monte Carlo on the ladder parameters, or the delta method).
- [x] **Restricted cross terms** (2026-09-29): `identify_cross` proposes the
      directed pairs with short leads as option (d); `estimate`/`evaluate`
      take `links`. Engine: `Ladder(links=)`, and drvarma C's `-links`.
- [x] **Reorder** tool (2026-09-28): permutes the fitted model, no re-estimation.
- [x] **HTML guion** (2026-09-29): `export_guion` also writes
      `<first>.sima.html` in art's style; the figures go to `figs/` next to
      the files and appear at their node.
- [x] **Resources** (2026-09-29): `sima://protocol`, `sima://defects` (sima's
      and the engine's registers, read with `fue.bugs`), one report by
      `sima://defects/{id}` or `sima://engine-defects/{id}`, `sima://docs`.
      Packaged by `tools/sync_material.py` here and in drvarma.

## The three VARMA identification forms — 0.1.0

sima carries the three schools of multivariate identification. All three go
into 0.1.0, and drvarma 0.2.0 is tagged once they are done (sima depends on
drvarma 0.2.0, see `docs/PUBLISHING.md`).

- [x] **Jenkins and Alavi (1981), phase 1** (`docs/DESIGN-jenkins-alavi.md`),
      Python first, in the order A → B → E → D → C → F, all done:
      - [x] A: the statistics (drvarma `identification_mv`);
      - [x] B: `identify_matrices`;
      - [x] E: their checking;
      - [x] D: the preliminary estimates;
      - [x] C: the residual-model form;
      - [x] F: V(l) against the univariates;
      - [x] validated on muskrat–mink.
      - [ ] `docs/MANUAL-jenkins-alavi.md` §2.5 still says an own parameter
            cannot be held at zero. `estimate(zeros=)` does that on route V
            since Tiao and Box C: update it.
- [x] **Tiao and Box (1981) and Box and Tiao (1977)**
      (`docs/STUDY-tiao-box.md`; done 2026-10-02):
      - [x] A: the stepwise autoregression table with M(l), `stepwise_ar`,
            under method 1 in `identify_matrices`; gas furnace Table 12(b);
      - [x] E1: the canonical analysis on the levels, `canonical_analysis`
            (N1b); hog Tables 4.2 and 4.3;
      - [x] B: the structural reading, `structure`: triangular orderings and
            mtram offered, never taken;
      - [x] C: simplification by coefficient, `simplify` and `zeros=`;
      - [x] the flour prices example.
      - Postponed (decided 2026-10-11): D, ESCC for mixed orders (Tiao and
        Tsay 1983); and E2, the canonical analysis of the fitted model, which
        is optional.
- [ ] **The echelon form, seeded from the univariate models** (drvarma
      `docs/ECHELON_SEEDED_DESIGN.md`, §7). Stages 0-3 go into this version
      (decided 2026-10-11). The design note predates the new sima and names
      pieces of the old server (`characterize_series`, `_SEED`), so it has
      to be placed on the Ladder first.
      - [ ] **0. Test the assumption before building**, as §8 asks: do the
            univariate orders predict the Kronecker indices? Simulate systems
            with known indices, fit the univariates, and compare. If the seed
            is systematically wrong, stop and rethink before stage 1.
      - [x] **1. Seed the diagonal from the `.pre` models** (§3.2): the
            Ladder already does it. The diagonal of each row is the `.pre`'s
            own φᵢ(B)Φᵢ(Bˢ) and θᵢ(B)Θᵢ(Bˢ), kept as a product, and the gate
            requires the diagonal system evaluated there to give the sum of
            the univariate logLs. The check §7 asks for is the gate.
      - [ ] **2. Unequal row orders**: p_i per equation, by zeroing rows
            (on `zeros=`; the likelihood already accepts them). In the
            Ladder, the degree of a row is the larger of its own diagonal
            (from the `.pre`, seasonal lags included) and its cross terms.
      - [ ] **3. The echelon restriction table**, which turns stage 2 into an
            identified form.
      - Review after stage 3: whether to go on to **4**, multiplicative row
        factors with the LR against the unrestricted row, and **5**, the
        index search.

## Later

- [ ] **Conditional forecasts** on a scenario for one series (the pass-through
      use: `MODELS_RESULTS.md` §4 of drvarma C).
- [ ] With `estwin`, the gate says "not an optimum" when the reason is that the
      sample is another (also in drvarma C and Python).

## Housekeeping

- [ ] `tools/gen_tools_md.py` is a copy of art's: make it a shared dev tool.
- [ ] CI: the tests need `drvarma>=0.2.0` from PyPI; until it is published the
      workflow installs drvarma from its repository.
