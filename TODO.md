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

sima carries the three schools of multivariate identification. All three are
in 0.1.0, published with drvarma 0.2.0 on 2026-10-15 (atsw 2.0.0).

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
- [x] **The echelon form** (drvarma `docs/ECHELON_PLAN.md`; the seeded
      design, `ECHELON_SEEDED_DESIGN.md`, was measured and dropped). Done
      2026-10-12: `identify_echelon` and `estimate(indices=)` on route V,
      tested on a simulated system and on the gas furnace;
      `docs/MANUAL-echelon.md`.
      - [x] **0. Test the assumption before building**, as §8 asks: do the
            univariate orders predict the Kronecker indices? No: 0-49 %
            (drvarma `docs/STUDY-echelon-seed.md`). The indices are searched
            on the vector instead (Lutkepohl and Poskitt's stages I-II).
      - [x] **1. Seed the diagonal from the `.pre` models** (§3.2): the
            Ladder already does it. The diagonal of each row is the `.pre`'s
            own φᵢ(B)Φᵢ(Bˢ) and θᵢ(B)Θᵢ(Bˢ), kept as a product, and the gate
            requires the diagonal system evaluated there to give the sum of
            the univariate logLs. The check §7 asks for is the gate.
      - [x] **2. Unequal row orders**: drvarma's `Ladder(rows=)`.
      - [x] **3. The echelon restriction table** (`Ladder(echelon=)`, A_0
            in the cast) and **5, the index search** (`drvarma.echelon`,
            with the least-squares start), folded into drvarma's 3a-3b.
      - [x] **4. Multiplicative row factors** with the LR against the
            unrestricted row (decided with the user 2026-10-12: the factor
            multiplies the whole row; drvarma `ECHELON_PLAN.md` §4). Route U
            in `identify_echelon` and `estimate(indices=)`, with the factor's
            check.

## The worked examples of the three forms (done 2026-10-13)

- [x] `jenkins_alavi`: muskrat and mink, from art's univariate models.
- [x] `tiao_box`: their gas furnace on route V, from the raw table. M(l) of
      their Table 12, no feedback at AR(6), the spurious one at AR(2) (Table
      14), their restricted AR(6) and the transfer weights of Table 13.
- [x] `lutkepohl_poskitt`: their flour prices on route V, the differences of
      the logs. SC and HQ give (0, 0, 0) as their Table 1; their (1, 1, 1)
      and their two restricted models of five coefficients (Table 2), with
      the same estimates and standard errors.
- [x] `load_example` loads a raw table too (manifest key `raw`).
- [x] `MANUAL-echelon.md`: it said that in log levels sima chooses (1, 1, 1),
      "Lütkepohl and Poskitt's own result". Wrong: they work on the
      differences of the logs, and there their HQ gives (0, 0, 0). Corrected;
      Part 3 is now their example.

## drvec — its MCP is sima (decided 2026-10-13)

drvec (the VARMA-VEC; Johansen by exact ML) has its Python port:
`drvec-python`, package `drvec` 0.1.0 (packaged, not published),
byte-identical to drvec C 0.13 on Linux x86_64. It does not reuse drvarma's
Ladder: it carries the C's own ladder, on drvarma's compiled likelihood,
optimiser and (0.3.0) GSL eigensolvers, and reads the files with fue's
reader and cast (`fue>=0.1.18`, `drvarma>=0.3.0`).

**The current study is `docs/STUDY-vec.md` (2026-10-17).** It revises
PROCESOS-drvec.md §5.2–5.4 (atsw-gui, private), which was written before
sima was published and before the port existed. It covers the routing node,
the cointegration studies, the revised tools, the job runner, the public
examples and the open questions. The implementation plan comes after it.

- **Its MCP is sima**, not a fourth assistant (the user, 2026-10-13).
  PROCESOS §5.1 recommended a fourth one because drvec "starts from .pre, not
  from raw series like sima". But sima's normal input is the `.pre` files;
  the raw entry came later. The rest of what is particular to drvec is
  content inside sima: the long-run question, the non-standard inference,
  the tasks in the background.
- **Order: sima 0.1.0 closes without the VEC**, with the three forms and
  their examples. drvarma 0.2.0 and sima 0.1.0 are published, and the VEC
  comes in sima 0.2.0 with the port. The tools are added, nothing that
  exists changes.
- [x] **sima 0.2.0, phase C of `docs/PLAN-vec.md`** (2026-10-18, branch
      `sima-vec`): the kind tag, the purpose and the provenance (C1); the job
      runner `sima.jobs` (C2); N1c (C3); the tools of STUDY-vec §4.1 as the
      plan revised them (C4); the protocol, the rules and the docs (C5); the
      examples with their caches — `flour_prices`, `jenkins_alavi` (B = 499),
      `lutkepohl_e1`, `johansen_juselius` (C6); the tests (C7).
- [ ] **`study_estimation` for a VEC** (STUDY-vec Q12, later): 0.2.0 has the
      declaration ("not a demonstrated maximum") and `multistart`; the study
      along the ridge (E1's VARMA-VEC(2,1)) waits for drvec's own item.
- [ ] **Progress of the IRF bootstrap on drvec C**: drvec reports it at the
      end only (the C writes the bands file once); the job shows the elapsed
      time until then.
- [ ] **`export_tables`** (STUDY-vec Q8): deferred; the job folders and the
      guion JSON are the registry.
- [ ] **The free model of the restriction LRs** (STUDY-vec Q7): sima uses the
      best free fit it knows. If the gap ever changes a verdict, register the
      C's behaviour in atsw-gui `engines/drvec/docs/BUGS.md` with a repro.
- [ ] **The other public VECMs** (STUDY-vec §6.5): UK PPP/UIP, Finland,
      `vars`' Canada — not needed for 0.2.0.
- [ ] **The examples' caches off Linux x86_64**: the key holds the platform
      tier, so on macOS, Windows and aarch64 the tutorial's bootstraps run
      (minutes) instead of returning at once. Shipping a cache per tier would
      need those platforms' runs. The tier stays in the key (decided
      2026-10-18): a cache per tier, built on CI, is the way, not dropping it.
- [ ] **The yardstick through drvarma** (decided 2026-10-18, after 0.2.0):
      `evaluate` on a VEC reads drvec's own rolling `-estwin/-f` errors, while
      a forecast at one origin goes through `to_levels_varma`. They agree to
      1e-12, but it is two forecasters: route the rolling evaluation through
      `to_levels_varma` too.

## Later

- [ ] **Conditional forecasts** on a scenario for one series (the pass-through
      use: `MODELS_RESULTS.md` §4 of drvarma C).
- [ ] With `estwin`, the gate says "not an optimum" when the reason is that the
      sample is another (also in drvarma C and Python).

## Housekeeping

- [ ] `tools/gen_tools_md.py` is a copy of art's: make it a shared dev tool.
- [x] CI: `drvarma>=0.2.0` is on PyPI (2026-10-15). The tests workflow still
      installs fue, pyfug, drvarma and art from their repositories on purpose,
      to test against what comes next; the published set is tested by art's
      *Preflight atsw* with `origen=pypi`.
