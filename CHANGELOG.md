# Changelog — sima-tseries

## 0.2.0 — unreleased

**Cointegrated systems: sima takes in drvec** (docs/STUDY-vec.md, the study;
docs/PLAN-vec.md, the plan and the user's decisions of 2026-10-17/18). One
session and one guion hold the VARMA and the VEC: each fit carries a kind
tag, VARMA or VEC, and the final-stage tools dispatch on the current one.

- **N1c, the cointegration question** (`prepare_vec`): offered after
  `canonical_analysis` whenever two or more series have d = 1, whatever the
  canonical count (the count sets the menu's emphasis). It records the model's
  PURPOSE, "forecast" or "long run", and runs the checks before the rank (d >= 2,
  D > 0, drvec's refusals, a moved file, the window). The mixed I(0)/I(1) case
  is an option (`mixed=True`), never the default. `canonical_analysis`'s menu
  calls it instead of "drvec (outside sima)"; `run_gate` and `load_pre` name it.
  Its default p from Tiao and Box's M(l) on the levels is the contiguous
  order: it stops at the first run of two non-significant M(l), and a lag
  significant alone beyond it is reported and offered, not taken (shakedown,
  Martín Manjón and Treadway 1985-1995: (R0T, R0) proposed 15, now 4; the gas
  furnace's single gap at 5 keeps its 6). `canonical_analysis` names the
  isolated lags.
- **C1 at small n: the rank is conditional on p.** When n / (M p) is below 15,
  `rank_test`'s report says the verdict can flip with the order (shakedown,
  Martín Manjón and Treadway: 2016-2020 and 2022-2026 reject r = 0 at p = 2
  and not at p = 3 or 4) and offers first `sweep(name, p="p-1,p,p+1", B=...)`.
  `sweep` now runs before any VEC: over prepare_vec's specification it reads
  the RANK only, one cached rank job per order, with each comparison's LR,
  95 % value and p per cell (also in the VEC's sweep).
- **No feedback in the short run, by LR** (`test_restriction(gamma="R30,R3 <-
  R0T")`, drvec's `-gzero`): Gamma_k[equation][regressor] = 0 at every lag.
  With weakex/alpha on the same series it is the conditional model's joint
  test (weak exogeneity and no feedback, Johansen 1992); when it holds, the
  report names the output and the inputs and offers mtram with the same
  files. In two series weakex + gamma is `add_exogenous(series=...)` (-xsys):
  the same model, checked. Shakedown, Martín Manjón and Treadway 1985-2008:
  R0T | (R30, R3), LR 7.83, 8 df, p .45. Needs drvec-python with `-gzero`.
- **The rank by parametric bootstrap** (`rank_test`, C1), the only way to a
  rank: drvec's sequential exact LR, the bootstrap's critical values, the
  Monte Carlo error, a proposed r-hat that the analyst adopts or not; the
  asymptotic table shown as orientation only. `estimate_vec` (C2) refuses
  without a finished rank test for the same specification, unless the rank
  is adopted on theory (`theory=`, written in the guion as such).
  A comparison whose fitted model under H0 is not I(1, r) is said as such
  (BUG-0006): drvec checks it before simulating (Cavaliere, Rahbek and
  Taylor 2012, Algorithm 1 step ii; drvec C 800a540) and draws no sample, and
  the report names the failing condition (an AR root on the unit circle, or a
  common trend lost) instead of "fewer than 10 replications", proposes no
  rank and offers the integration orders, another specification or the rank
  on theory. The shipped caches' `result.json` carry the new field.
- **The C nodes**: `estimate_vec` (the roles asked for: `normalise_on`; drvec's
  .out blocks verbatim; the canonical weights beside beta; a fit on a ridge
  declared, never an optimum), `test_restriction` (LR with its df and p,
  against the best free fit known as well as drvec's), `add_exogenous`
  (-xsys or -xpre/-xlink by the input's order), `long_run` (theta, the
  textbook and the model's half-lives, Gonzalo and Ng, computed in sima),
  `irf_bands` (the bootstrap's bands), `sweep` (robustness, one cached job a
  cell), `plot_rank_bootstrap`.
- **Extended, by the kind tag**: `forecast` (the VEC in levels through
  drvarma's forecaster, `drvec.to_levels_varma`: one forecaster),
  `impulse_response`, `variance_decomposition` and their plots (the levels;
  bands only from the bootstrap), `evaluate` (the yardstick for the VEC on
  drvec's origins: a veto when the purpose is to forecast, a caveat for a
  long-run claim), `plot_forecast`, `plot_residual_ccf`; `reorder` refuses on
  a VEC (another order is another fit); the VARMA-only tools say so.
- **Jobs** (`sima.jobs`): detached processes (`python -m sima.jobs run
  <folder>`) that survive the server and the client; at most cores - 1 slots,
  counted with drvec's workers; one folder per run (`sima_jobs/<id>/` next
  to the first file); a cache keyed by content (the files' bytes, the
  arguments, the engines' versions, the backend, the bootstrap engine, the
  platform tier, the seed); progress as "replication k of B, comparison
  r -> r + 1"; cancellation of the whole process tree; never a partial result
  as final; a ~20 s inline wait. Tools: `job_status`, `job_result`,
  `job_cancel`, `jobs`. The bootstraps run on drvec C when its binary is there
  (drvec's engine="auto"), with the engine in the result's provenance.
- **Provenance on every result**: each guion entry carries the versions of
  sima, drvarma, fue and drvec, the numerical backend, the platform tier and,
  for a job, its engine, seed, cache key and run folder; the HTML guion
  shows it.
- **The examples**: `flour_prices` continues into the rank (the bootstrap
  does not reject r = 0; the VEC's nodes follow on theory, written as such);
  `jenkins_alavi` gains the mixed case (B = 499); `lutkepohl_e1` is new
  (Lütkepohl's E1: r = 1, who corrects, two half-lives, the VARMA-VEC(2,1)'s
  ridge declared); `johansen_juselius` is new (the Danish money demand,
  public data via urca: the bootstrap does not reject r = 0 at n = 55 where
  the asymptotic trace test found one relation; on their theory the relation
  is theirs, LRM = 1.12 LRY - 5.16 IBO + 4.26 IDE); `martin_manjon_treadway`
  is new (U.S. interest rates, FRED, 1985-2008: Martín Manjón and Treadway
  (1997) taken further than the paper, with the rank by bootstrap on the whole
  homogeneous regime, who corrects by LR, the joint test of the conditional
  model and a control with the 10-year rate; MANUAL-vec §3.1). Each ships its job cache (`load_example` copies it), and on
  Linux x86_64 a rerun reproduces its files byte for byte
  (tests/test_example_caches.py; tools/build_example_caches.py builds them).
  The caches were rebuilt on drvec C 800a540 (#14: BUG-64's last-resort
  start, the I(1, r) check and the bootstrap block's new text): replications
  that failed to fit now converge, so a few p-values move in the third
  decimal (flour_prices r = 1: 0.784 to 0.786; lutkepohl_e1 r = 1: 0.345 to
  0.346, 499 usable of 499) and no verdict changes.
- **Dependencies**: `drvec>=0.1.0` (hard), `drvarma>=0.3.0`, `fue>=0.1.18`.
- The protocol and the rules in the server's instructions: N1c and the C
  nodes; no cointegration claim without a finished bootstrap; the yardstick's
  role by purpose; LR, not Wald; the order of a VEC is its normalisation.
- **The C engine's progress moves at every replication.** drvec C wrote the
  rank bootstrap's `.boot` through a 4 KB buffer, so a job's count jumped by
  ~160 replications and `job_status` added a note saying so; atsw-gui BUG-63
  flushes it line by line, and drvec-python bundles that C (csrc/ from
  atsw-gui abe6602). The note is gone.

## 0.1.1 — 2026-10-16

**The PyPI page and the install.** The Homepage pointed at
`github.com/davidesg/sima`, which does not exist; it is `sima-python`, with
Repository, Issues and Changelog beside it. The README's links were relative
and broke on PyPI; they are absolute now. Its protocol table was 0.1's first
one: it now has the raw entry (routes U and V), the canonical analysis, the
three identifications, the checking, the simplification, the structure,
`study_estimation` and the examples.

**The raw entry names its extra.** `pip install sima-tseries` does not bring
art, and `characterize` said "pip install art-tseries"; now it, an Excel table
without pandas, and `load_example` of an example that starts from the data
(lutkepohl_poskitt, tiao_box) say `pip install "sima-tseries[raw]"`, which the
README's Install section now shows (tests/test_raw_extra.py).

## 0.1.0 — 2026-10-15

### The worked examples of Tiao and Box and of the echelon form

Each of the three forms now has a worked example on its authors' own data,
as Jenkins and Alavi's had:
- `tiao_box`: Box and Jenkins' gas furnace, route V from the raw table. It
  reproduces the M(l) of their Table 12, the absence of feedback at AR(6)
  and the spurious feedback at AR(2) (Table 14), and their restricted AR(6)
  (5.7), with transfer weights close to their Table 13.
- `lutkepohl_poskitt`: the flour prices as rates of change, route V. SC and
  HQ choose (0, 0, 0), as their Table 1 does. Their restricted VAR(1) and
  MA(1) with five coefficients come out with their estimates and standard
  errors (Table 2).
- `load_example` loads a raw table too: the manifest's `raw` key gives the
  file, the frequency and the start, and the analysis goes on from
  `characterize`.
- `tools/sync_material.py` leaves out route V's specifications (`<data>_sima/`).
- `MANUAL-echelon.md`: Part 3 is now Lütkepohl and Poskitt's example. It
  corrects a sentence that gave (1, 1, 1) in log levels as "their own
  result": they work on the differences of the logs.

Tests: `tests/test_examples_route_v.py`.

### The echelon form on route U: the row factor

drvarma's echelon stage 4 (`docs/ECHELON_PLAN.md` §4) takes route U's models
into the echelon form:
- the seasonal and fixed-frequency factors of each `.pre` multiply its whole
  row (the row FACTOR);
- its regular ARMA is replaced by the row's free AR(n_i)/MA(n_i)
  (`Ladder(own="free")`).

What changes in sima:
- `identify_echelon` runs on route U. It searches each row filtered by its
  factor, in passes (drvarma `search_row_factors`): first with the
  univariate factors, then with those of the joint fit of each choice.
- `estimate(indices=)` fits the form on route U. When a row carries a
  factor, it reports THE ROW FACTOR'S CHECK: the LR against the same rows
  with the factor's restriction dropped (`Ladder.factor_test`), recorded in
  the guion.
- `cross="residual"` is refused with indices on either route.

On the examples:
- the flour prices (route U) give (1, 0, 0), which converges with white
  residuals;
- muskrat and mink give (3, 1);
- in the IPC the factor holds (p 0.16).

Tests: route U's echelon form on muskrat and mink (`tests/test_raw_entry.py`)
and on the IPC with its annual factors (`tests/test_echelon.py`).

### The third form: the echelon VARMA, `identify_echelon` and `estimate(indices=)`

Lütkepohl and Poskitt's (1996) echelon form on route V. Needs drvarma's
`Ladder(echelon=)` and `drvarma.echelon` (its stages 3a-3b).
- `identify_echelon(max_index=3, criterion="SC")` searches the Kronecker
  indices on the stationary vector: a long VAR, then least squares per
  candidate. It prints the criterion table and a menu, says that the order
  of the series is part of the form, and records the decision in the guion.
- `estimate(name, indices="2, 2")` writes each series' spec with its own
  AR(n_i)/MA(n_i) and fits the echelon form. It starts at the least-squares
  estimates. `structure`, `simplify`, `check_residuals`, `evaluate(indices=)`,
  `forecast` and `study_estimation` know the form: a fit key now carries the
  indices.
- Route U refused it then: its diagonal is the univariate model. The row
  factor (above) lifts that.
- `estimate`'s `start` defaults to the Ladder's own: zero for the VARMA, as
  before, and the least-squares estimates for the echelon form.

Tests: `tests/test_echelon.py` (a simulated (1, 0) system) and the gas
furnace in `tests/test_raw_entry.py`, where SC picks (2, 2), i.e. the
VARMA(2, 2), which from this start converges where from zero it stops on
the step size. Manual: `docs/MANUAL-echelon.md`.


**Hosking's Q on residuals subtracts the ARMA coefficients** (drvarma
BUG-0015). The estimation report (N3) uses `df = m²·s − k`, with k each
series' own ARMA coefficients plus the free cross ones. The pair's Q in the
cross identification (N2) uses `4·K − (k_i + k_j)`. It used `m²·s` and almost
never rejected. Needs drvarma with `Ladder.n_arma()`. The residual-ccf figure
keeps GraphMaker's `4(K − (p + q))`.

**`sima --help` and `--version` answer and exit** (drvarma BUG-0014). They
used to start the stdio server, so the command seemed to hang. Test:
`tests/test_cli_help.py`.

### The forecast figure is fuf's, drawn by pyfug

- `forecast_figure` draws each series with `pyfug.plot_forecast` (fufplot.c),
  from `forecast_data`. The grid of «all» puts those figures side by side.
  It used to be drawn here with pieces of `fue.plots` and
  `fue.report_forecast`.
- fuf's rule for what is drawn: λ ≥ 0 gives the annual change (a rate in %
  under a log, the series' units otherwise); λ < 0 gives the level. sima
  used to draw the level for every λ ≠ 0.
- pyfug is a dependency.

### Tiao and Box's structure and simplification: `structure`, `simplify`

- `estimate(..., zeros=)` holds coefficients at zero, by their printed names:
  - cross terms (`AR3[CO2<-GAS]`) on either route;
  - a series' own (`phi_CO2[B^5]`) on route V only, written into its spec as a
    fixed coefficient.

  Route U's diagonal is art's, and is refused. A fit already made with the
  same arguments is reused. `evaluate` takes `zeros` too.
- `simplify` (N4s): the coefficients with |t| < 1 (or `t=`) at zero, the model
  refitted, the LR against the full fit, AIC and BIC, and what fell below the
  threshold in the refit (another round). Tiao and Box (1981, §4).
- `structure` (N4t): for each ordered pair, the LR test that series j does not
  enter series i's equation. With up to 4 series it also tests every
  triangular ordering. When one stands, the system is a transfer network and
  sima OFFERS mtram with the same `.pre` files; it never hands back on its own.
  It warns that a low-order fit can show a spurious feedback.
- **Gas furnace:**
  - VAR(6): CO₂ → gas LR 6.0 with 6 d.f. (p 0.42), so gas → CO₂ stands;
  - VAR(2): the spurious feedback of their Table 14 (LR 32.2, p < 0.0001);
  - `simplify` drops 9 coefficients (LR 6.2, 9 d.f., p 0.72; AIC and BIC fall).
- **Muskrat–mink:** feedback both ways, a simultaneous system.

### Route V from raw data: `write_specs` — the vector first

- `write_specs` (N0v) writes each series' fue `.inp` with only its
  characterization (λ, d, D or harmonics, the mean when d = D = 0) and opens
  the session in route V (Tiao and Box).
- In route V:
  - `identify_matrices` reads the vector: method 1, the whole matrices and
    M(l). It does not pretend a method 2 (there are no univariate models), and
    proposes M(l)'s full VAR(p);
  - `estimate(p, q)` writes each series' spec with a free AR(p)/MA(q) of its
    own (`<SERIES>_v_p{p}q{q}.inp`), so the ladder is the full VARMA(p, q);
  - `evaluate` compares it with univariate models built by route U's builder,
    for the yardstick only.
- No `.pre` is written for the system. Its estimates are rows of the system.
- **Gas furnace** (Series J), from the raw table in levels:
  - M(l) is Tiao and Box's Table 12(b);
  - the exact VAR(6) has φ₁ 1.92 and φ₂ −1.19 for the input (their 1.93,
    −1.20), CO₂ receiving the gas at lag 3, and no feedback;
  - out of sample, the VAR(6) improves CO₂'s forecasts by 17–46 % at h ≥ 2
    but worsens the input's: the unrestricted model needs simplifying.

### Route U from raw data: `build_univariate`

- `build_univariate` (N0u) builds each series' model on its characterization:
  - the orders art's engine ranks first, with ties shown;
  - the mean when d = D = 0, starting at the series' mean (from 0, the mink's
    AR went to a unit root to carry the level), or a drift only if |t| ≥ 2;
  - a fue fit and a Ljung-Box check;
  - `<SERIES>_u.inp/.pre/.out`, every `.pre` marked "not reviewed in art".

  It then opens the ladder session on those files, the guion going on from the
  raw entry. The gate repeats the provenance, and the menu offers art for any
  series with a tie or a residual problem.

### The raw-data entry: `load_data` and `characterize`

- `load_data` (N0r): an Excel or CSV table of raw series in original levels,
  with an optional date column. Frequency and start are inferred from the
  dates or given. Missing values are refused, saying where. A numeric
  header-less CSV keeps its first row (the old sima dropped it).
- `characterize` (N0c): each series' λ, d (art's policy), seasonality and a
  preliminary outlier scan, with art's engine and in art's order. Each series
  keeps its own transformation: there is no joint consensus. `set=` records the
  analyst's changes ("mink: lam=0").
- `canonical_analysis` also reads the characterization's levels, before any
  model.
- The two routes, U (univariates first) and V (the vector first), are next
  (`docs/STUDY-raw-entry.md`). The `raw` extra declares art-tseries, pandas and
  openpyxl.

### Tiao and Box's tools: the stepwise M(l) and the canonical analysis

- `identify_matrices`, method 1: Tiao and Box's (1981) stepwise autoregression
  beside Jenkins and Alavi's S_k. It shows the indicator symbols of each
  partial autoregression matrix, M(l) with its chi-squared p-value, and the
  residual variances. The reading compares the last significant M(l) with S_k's
  cut-off, and option (d) offers M(l)'s order as the cross order when they
  differ.
- `canonical_analysis` (node N1b): Box and Tiao's (1977) canonical analysis of
  the transformed LEVELS. It gives the components from least to most
  predictable, their combinations and, for a VAR(1), the variance components.
  When two or more series are differenced and fewer components are near 1
  (√λ ≥ 0.90, on the scale of a root), it says the joint model may not need
  every difference and names drvec. It never changes a d. `run_gate` proposes
  it when two or more series are differenced.
- `examples/flour_prices` (`load_example("flour_prices")`): the flour prices of
  Tiao and Tsay (1989), from three univariate models to the yardstick, with the
  tutorial. Design and decisions: `docs/STUDY-tiao-box.md`.

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
