# Changelog — sima-tseries

## 0.1.0 — unreleased

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
