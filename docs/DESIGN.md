# sima — design

## 1. Where sima sits

The ATSW ladder is a chain of assistants over a chain of engines:

| assistant | engine | model |
|---|---|---|
| art | fue | one series: ARIMA with interventions |
| mtram | drtran | a transfer network: a DAG, a triangular VARMA |
| **sima** | **drvarma (ladder mode)** | a system: a general VARMA |
| **sima** | **drvec** (the port of drvec C) | a cointegrated system: the VARMA-VEC in levels |

The contract between rungs is the **file**: a `.pre` is the optimum of a
univariate model, rerunnable (fue's file contract). sima's input is one of those
per series: the univariate model of each series is the seed of the system and
the yardstick it must beat. From raw data (`load_data`, `characterize`) sima
first builds those files, by route U (the univariate models first) or V (the
vector first), and goes on from them (`docs/STUDY-raw-entry.md`).

With two or more series differenced once, the cointegration question comes
before any VARMA in differences (N1c, `prepare_vec`): the rank by parametric
bootstrap, and the VEC on drvec when there is one. One session holds both
kinds of fit; the method is in `docs/MANUAL-vec.md`.

**Where drtran ends.** mtram casts a network as a triangular VARMA. When its
identification finds a cycle, the system is simultaneous and mtram has nothing
more to do. The hand-over is the same list of `.pre` files, loaded here with
`load_pre`.

## 2. The seam: engine and assistant

Everything the model reads belongs to the assistant, and the engine ships
numbers and never argues (`art-python/docs/ASSISTANT_LAYER_PROPOSAL.md`).

- **Engines (drvarma, drvec):**
  - `drvarma.ladder`, which covers the gate, fitting, the LR, forecasts and
    recursive evaluation, and returns its caveats as data: the gate's
    per-series `move` and `trimmed`, `termcode`;
  - `diagnostics.ccf`/`qccf`/`hosking_q`;
  - `irf.oirf`/`fevd`;
  - drvec's `rank_test` (the sequential exact LR and its bootstrap, on drvec
    C) and `fit` (the VEC, its restrictions and LRs), and drvarma's
    `forecast_given` for the VEC written in levels.
- **Assistant (this package):**
  - `evidence.py` turns those numbers into evidence and a menu;
  - `mcp_server.py` holds the protocol, the tools and the instructions;
  - `vec.py` and `mcp_vec.py` hold the VEC's nodes (N1c, C0–C8);
  - `jobs.py` runs the long ones (bootstraps, sweeps) as detached, cached
    jobs;
  - `guion.py` keeps the record;
  - `session.py` keeps the state.

**No hard-wired recommendation.** art's `Description.recommendation` is the one
thing the proposal says not to copy: two judges at once (a heuristic and the
model), able to contradict each other. sima's decision nodes return options
with arguments for and against, never a verdict.

## 3. The protocol

- **N0 `load_pre`:** fue's parser, alignment by date (BUG-2), the series table.
- **N1 `run_gate`:** each series alone on the common window, then the
  diagonal system evaluated at those optima. The identity is exact, and if it
  fails the analysis stops. It also says whether each file is an optimum, a
  specification, or an optimum on another sample.
- **N1c–C8 (the VEC):** the cointegration question and the purpose, the rank
  by parametric bootstrap, the VEC, its restrictions by LR, the long run, the
  level responses, robustness and the yardstick (`docs/MANUAL-vec.md`).
- **N2 `identify_cross`:** the CCFs of the residuals of the diagonal system,
  which are each series' innovations and so prewhitened by construction. It
  separates:
  - contemporaneous correlation, which points to a full covariance;
  - short lead-lag correlation (lags ≤ 3), which points to cross orders;
  - isolated long or seasonal correlations, which point back to art: they are
    better read as something a univariate model misses than as a VAR with
    many lags.
- **N3/N4 `estimate`:** the candidate, the LR against the univariates (in
  sample: necessary, not sufficient), the residual portmanteau, and how the
  optimiser stopped.
- **N5 `evaluate`:** the yardstick. The candidate and the diagonal system on
  the same estimation window, parameters fixed, forecasts from every origin,
  and the RMSE/MAPE ratio by series and horizon.
- **N6:**
  - `forecast`: every series in its level, with its own model;
  - `impulse_response` and `variance_decomposition`: Cholesky in the order of
    the files, named as an identifying assumption.

## 4. Speed

The ladder evaluates the exact likelihood thousands of times per fit, with the
compiled `elf` of drvarma's wheels. On three monthly series of 263
observations, the whole path N0–N6 with a 48-origin evaluation takes about
10 s.

## 5. Tests

Three kinds (`tests/`):
- the server (tools registered, docstrings, instructions);
- the protocol on real data, with the engine's pinned numbers;
- **what it says** in the delicate cases:
  - a failed gate stops the analysis;
  - no evidence offers staying univariate;
  - menus, not verdicts;
  - the Cholesky order named an assumption;
  - a yardstick loss called a finding.

The last kind is the discipline the proposal asks for (§5.3).
