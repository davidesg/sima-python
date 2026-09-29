# Changelog — sima-tseries

## 0.1.0 — unreleased

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
