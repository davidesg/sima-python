# Changelog — sima-tseries

## 0.1.0 — unreleased

### Worked examples in real time: `examples`, `load_example`

- `load_example("jenkins_alavi")` copies the example's files to
  `~/sima-examples/<name>/` (keeping any already there) and loads its
  univariate models; the analysis goes on node by node with the usual pauses.
  `examples()` lists them. The assistant follows the tutorial,
  `sima://example/<name>` (`examples/<name>/TUTORIAL.md`): what to look at at
  each step and what the original analysis found, added after each report.
  The tools do not change in a tutorial. `sima://examples` is the index; the
  first question offers an example to a new user.
- The examples travel with the package (`tools/sync_material.py` copies them to
  `src/sima/material/examples/`; `pyproject.toml` ships them).

### The manual chapter and the example: Jenkins and Alavi

- `docs/MANUAL-jenkins-alavi.md` (served as `sima://doc/MANUAL-jenkins-alavi`): the method of
  Jenkins and Alavi (1981), how sima implements it tool by tool, and their
  muskrat-mink example with the paper's numbers alongside.
- `examples/jenkins_alavi/`: the two univariate models built in art (`.pre`
  and `.out`), the data, and `run.py`, the walkthrough node by node with
  sima's tools, recording the decisions; tested by
  `tests/test_example_jenkins_alavi.py`.
- `forecast_uncertainty(estwin=)`: the model and the univariate models
  refitted on the first observations, as their §6.3 (Table VIII on 48).
- The guion keeps one line for `plot_identification`, not its whole report.

### `evaluate`: two defects of the report

- The RMSE columns of series in hundreds of thousands (muskrat skins) ran
  into each other ("249170.1660227388.1493"); decimals now follow magnitude.
- Annual data showed only h = 1 and 2 (the seasonal rule of horizons); it now
  shows every year up to 5.

### `check_residuals` is art's diagnosis

- The report in art's four sections (the checking table as a block, what it
  shows, the conclusions, the alternatives with their calls), then the
  figures drvus drew in its diagnosis (and Jenkins and Alavi's figure 7):
  fue's panel for each residual series (pyfug `plot_combined`, the call of
  art's `figura_residuos`: residuals with +-2 bands, acf with its Q, pacf) and
  the residual ccf of each pair in GraphMaker's panel. Several images in one
  answer; the PNGs go to the case's `figs/`.
- The residual ccf's P has GraphMaker's degrees of freedom, 4(K - (p + q)),
  p + q the largest AR plus the largest MA order of the fitted model; when
  none are left the label says so instead of a number.
- The portmanteaus keep at least 2 lags beyond the parameters
  (`figures.q_lags`): the legacy lags (fug's for the acf's Q, GraphMaker's for
  the ccf's P) move up when a long model in annual data would leave none —
  Q with at least 2 d.f., a pair's P with at least 8.

### `plot_identification` reports as art does

- The answer is art's report around the figure: 1 · TABLE (a block to show as
  it is: per pair, lag by lag, ccf and pccf with * beyond the band, the band
  itself when it follows the lag, Haugh's S*), 2 · WHAT IT SHOWS (per side:
  the bars beyond the band, who leads, the cut-off, the isolated ones; S* by
  side), 3 · CONCLUSIONS (the method's reading), 4 · DECISION (the
  alternatives with their calls, and the pause); then the figure. The
  instructions tell the assistant to present it in that order and to give
  its preference as a suggestion, with the argument against.

### The CCFs are GraphMaker's

- `plot_residual_ccf` and `plot_identification` draw drvarma's CCF panel,
  now GraphMaker's (Treadway's, the one drtran's GUI draws): titled "A - B"
  with A leading at k > 0, Hosking's P (not Q) with its degrees of freedom,
  dotted bands, a dashed vertical at lag 0.
- Terse, as the originals: `plot_identification` says the method in one line,
  the pair once above with "ccf" centred under it, "pccf" over the partial, and between the panels
  only "S* ( d.f. ) = value" (method 2; nothing under the others). What they
  mean, the sides of Haugh's test and the conditioning of the partials go in
  the tool's text.

### Jenkins and Alavi's identification as a figure (`plot_identification`)

- One row per pair of series, in drvus' CCF panel (the one drtran reads): the
  correlation function R_k above the partial S_k, both two-sided, on the same
  lag axis and scale — the CCF over its partial as art's ACF over PACF, which
  scales with m where the m x m grid does not. `method=2`: the univariate residuals,
  band 2/sqrt(n), and between the panels Haugh's S* (1976) — the
  independence test of two prewhitened series, in total and by side — where
  fue puts its Q. `method=1`: the stationary series, with
  Bartlett's band (3.13) lag by lag — at 2/sqrt(n) the common ten-year cycle
  of muskrat and mink would read as cross terms. With three or more series
  the partial of a pair is given the others (the VAR of all), and `pairs`
  draws only those chosen; the partial stops at the order the sample
  supports. Recorded at N2.

### The residual-model form, and Jenkins and Alavi's Table VIII

- `estimate(cross="residual")` (and `evaluate`, `study_estimation`): the
  cross MA as a model for the univariate residuals (3.22), multiplied by each
  series' univariate MA; method 2 of `identify_matrices` proposes it. The
  session keeps the two forms as different candidates.
- `forecast_uncertainty`: V(l) of the model against the univariate models by
  lead time, per cent for series in logs (their Table VIII); in sample —
  `evaluate` is the test.
- Validated on their own data, muskrat and mink (1850–1911): fue's univariate
  models reproduce theirs (ARIMA(6,1,1) and AR(4)); the prewhitened r(0) is
  0.38 (theirs 0.42), the lag-1 cross correlations have their signs (more
  muskrat, more mink next year; more mink, fewer muskrat), method 2 reads an
  MA(1) residual model and method 1 a cross AR of order 2, as they found; the
  fitted cross terms carry the predator–prey signs of their (5.10).

### `estimate(start="preliminary")`

- The cross terms can start at Jenkins and Alavi's preliminary estimates
  (drvarma's `Ladder(start=)`): usually the same optimum in fewer iterations,
  and a second path to compare on an ill-defined estimation. The report and
  the guion say which start was used.

### Jenkins and Alavi's checking (`check_residuals`)

- [§5.2] The large residuals judged on the UNCORRELATED transformed residuals
  a* = Q'a (the a_it correlate at lag 0, so one by one they cannot be judged),
  with their dates, the entry to interventions; the residual correlation
  matrices R_k(a); the portmanteau matrix Q_ij, as a summary. A shock of
  opposite sign in two correlated series, ordinary in each, stands out (their
  butter price and purchases).

### Jenkins and Alavi's identification (`identify_matrices`)

- Their two methods [§3.3–3.4], from the ladder: method 2 on the residuals of
  the diagonal system (the univariate models' residuals, prewhitened): the
  correlation matrices R_k, which suggest an MA residual model and its links;
  method 1 on the stationary series of the same files: R_k with Bartlett's
  standard errors, S_k (multivariate Yule-Walker) and Alavi's S_k(q), with the
  determinants for three or more series. The whole-matrix reading (theirs)
  and the off-diagonal one (the cross terms the ladder adds). Then the
  comparison as a menu, with their warning (3.26) when a cross AR shows.
- A cut-off is the end of the initial run of significant lags; isolated lags
  beyond the band are listed apart (one in twenty is chance).
- Phase 1 (B) of `docs/DESIGN-jenkins-alavi.md`; engine:
  `drvarma.identification_mv`.

### MCP resources: what the model can ask for

- `sima://protocol`, the instructions, to reread them mid-analysis.
- `sima://defects`: sima's register and the ENGINE's (drvarma), where the
  defects of the ladder live; one report whole with `sima://defects/{id}` or
  `sima://engine-defects/{id}` (the registers number independently).
- `sima://docs`, `sima://doc/{name}`.
- Read with `fue.bugs`. The material ships inside the package
  (`tools/sync_material.py`, run by the CI before building), so an
  installation serves it; checked on a built wheel.

### The guion as HTML

- `export_guion` writes, besides `<first>.sima.json`, `<first>.sima.html`: a
  self-contained page in art's style — the steps in a table, one section per
  node with the evidence, the decisions highlighted (who decided, what was set
  aside) and the figures at their node (the residual CCFs in N4; the IRF, the
  FEVD and the forecasts in N6). `html=False` skips it.
- The figures are saved in `figs/` next to the first file (no longer in the
  temporary directory) and recorded in the guion, so the page, its figures
  and the JSON travel with the data.

### Figures, in the school's design

- `plot_impulse_response`: the orthogonalised IRF drawn as what it is, a
  function of the lag like an ACF — one panel per (response, shock), thick
  impulses at h = 0..H, the seasonal grid, only the left axis, and the 95 %
  Monte-Carlo band dashed, following h.
- `plot_variance_decomposition`: the same layout and impulses on a fixed
  0-100 % axis with the horizontal axis at 0, its band per horizon shaded
  between the dashed lines; a row reads as in the IRF.
- `plot_residual_ccf`: drvus' two-sided CCF of every residual pair, reusing
  drvarma's panel (the suite's reference), with the Hosking Q.
- `plot_forecast`: the format of FUF (atsw-gui `fufplot.c`) and art
  (`fue.report_forecast`): the annual rate of change (%) of the last H
  observations and the H forecasts with +-1 sigma (the LEVEL with +-2 sigma
  when the series is not in logs), and the ERR panel of the residuals under
  their dates. One figure PER SERIES by default, so the forecast report can go
  series by series; `series` picks one, "all" gives the grid.
- As art and mtram, the image comes inside the answer and is also written as
  a PNG. The numbers are those of the matching text tools. Each figure was
  approved one by one (2026-09-29).

### Restricted cross terms: `links`

- `identify_cross` lists the directed pairs that showed a lead at a short lag
  and offers them as option (d), with the exact `links` string. On m6: 5 of 30
  pairs.
- `estimate` and `evaluate` take `links` ("A<-B, C<-A": B enters the equation
  of A); the report lists them and the LR counts only them. The session keys a
  fit by (p, q, diagcov, links). Engine: drvarma's `Ladder(links=)`, the same
  as the C's `-links`.

### The covariance parameters carry no t-ratio (drvarma BUG-0008)

- `estimate` lists the innovation covariance parameters (`log(Q[b]/Q[a])`,
  `Q[b,a]`) apart, with no s.e., t or star: they are concentrated out and
  parametrised free of scale, so a t on them tests nothing. The correlations
  are what to read.

### The MA wall: one tolerance for both sides

- `roots_text` marks, and `wall_frequencies` lists, an MA root within 5e-5 of
  the unit circle, as the engines now report it (drvarma `MA_WALL_TOL`).

### `reorder`: the impulse responses under another Cholesky order

- **Nothing is re-estimated.** The reduced form does not depend on the
  order; only the orthogonalisation does.
- **What it shows:** every response in the files' order and in the new one,
  side by side, with the largest change and the sign changes per shock, and
  the innovation correlations that make the order matter.
- With a diagonal covariance it says the order changes nothing.

### IRF and FEVD with bands

`impulse_response` and `variance_decomposition` show 95% Monte-Carlo bands by
default. The bands come from drvarma's `Ladder.irf_fevd_bands`, and each
output says how many draws were rejected. A response whose band covers zero is
not a finding. `bands=False` gives the point estimates only.

### The autonomous lane, in writing

- **The instructions spell it out, as art's do:** the nodes one at a time,
  what to decide at each, "never decide nodes in batch", and what to hand
  over at the end.
- **`record_decision` keeps the whole decision:** `reason`, `evidence`,
  `alternatives` and `decided_by`. A decision without its reason is not
  documented.

### Studying an ill-defined estimation — `study_estimation` (N4b)

- **When.** drvarma reports a fit that stops on the MA invertibility wall as
  a fact (`Fit.ma_boundary`). `estimate` now says so and points to the new
  tool.
- **What the tool shows,** as evidence:
  - the AR and MA inverse roots of the joint model, with modulus and
    period;
  - the pairs that nearly cancel;
  - a **second path**: the same model optimised with Shea's exact
    likelihood;
  - **restarts**: from the stop, a step back towards the start, then
    `Ladder.refit`, repeated while ℓ rises.
- **The menu.** It ends with a menu and no verdict: remove the common
  factor or lower p and q; keep the boundary model knowing it is one; report
  the highest point reached. When the wall root is at frequency 0 or at a
  seasonal frequency, it adds over-differencing as an option, since that is
  the univariate model's decision (art).
- **The motivating case** is drvarma C's bench case c2, where the ridge
  climbs along the wall from ℓ 66.21 to 71.22.
- **Needs drvarma's ladder branch:** `lik`, `refit`, `x_start` and
  `ma_boundary`.

The first version of sima as its own package. Until now sima lived inside
drvarma (`drvarma.mcp_server`) and worked on raw series. From here:

- **The assistant leaves the engine.** The rule is that everything the model
  reads belongs to the assistant, and the engine ships numbers and never
  argues (`art-python/docs/ASSISTANT_LAYER_PROPOSAL.md`). drvarma's old
  server stays there, deprecated, as `sima-legacy`.
- **The entry is the ladder, never raw data.** `load_pre` takes one fue file
  per series (a `.pre` optimum or an `.inp` specification), read by fue's
  parser, and each series keeps its univariate model on the diagonal of the
  VARMA (`drvarma.ladder`). It is also where mtram sends a system whose
  network has a cycle.
- **The protocol, N0–N6:**
  - load;
  - the diagonal gate, which stops the analysis if it fails;
  - cross identification from the residual CCFs of the diagonal system;
  - estimation with the LR against the univariates;
  - the out-of-sample yardstick against the univariates;
  - forecast, IRF and FEVD.
- **Evidence and a menu, not a verdict.** Each decision node returns the
  options with their arguments for and against.
- **The guion** records every node, its evidence and the decision, next to
  the data (`<first>.sima.json`).
- Instructions for the guided and autonomous lanes, and tests of **what it
  says** as well as of the numbers:
  - the pinned LR is the C's (205.982 for the CPI VAR(1));
  - the yardstick is fue's forecasts;
  - a failed gate stops the analysis;
  - the Cholesky order is named an assumption.
