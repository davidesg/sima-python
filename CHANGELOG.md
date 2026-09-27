# Changelog — sima-tseries

## 0.1.0 — unreleased

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
