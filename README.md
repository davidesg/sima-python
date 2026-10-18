# sima — simultaneous VARMA on the ATSW ladder

**sima** is the MCP assistant for systems of time series: VARMA models by exact
maximum likelihood, built on the univariate models of each series, and, when
the series are cointegrated, the VARMA-VEC in levels. The engines are
[drvarma](https://pypi.org/project/drvarma/), whose ladder mode takes fue's
univariate files as input, and [drvec](https://pypi.org/project/drvec/), the
port of drvec C (Mauricio's VARMA-VEC by exact maximum likelihood), which takes
the same files. This package is the assistant: the protocol the model walks,
the evidence at each node, and the menu of decisions.

It is the third rung of the ATSW ladder:

    art (one series)  →  mtram (transfer networks)  →  sima (systems)

You arrive at sima with several univariate models (`.pre` files from art or
fue), or from mtram when its network identification found a **cycle**: two
series that feed each other, which no transfer network can hold. sima takes
the same files.

## Install

```sh
pip install sima-tseries            # from univariate models (.pre / .inp files); brings drvec
pip install "sima-tseries[raw]"     # also from raw data: adds art-tseries, pandas, openpyxl
```

The raw entry (`load_data`, `characterize`, `build_univariate`, `write_specs`)
uses art's engine, so it needs the `raw` extra; so do the worked examples that
start from the data (`lutkepohl_poskitt`, `tiao_box`).

Register the server in your MCP client (the command is `sima`, stdio). The
binary wheels of drvarma carry the compiled likelihood the ladder needs. If
they are missing, drvarma warns and runs about 250 times slower. drvec's
wheels carry drvec C 0.13, which runs the long bootstraps (the rank test, the
IRF bands) 6-12 times faster than the port; the engine used is written in
every result.

## The protocol

| node | tool | what it answers |
|---|---|---|
| N0r–N0c | `load_data`, `characterize` | raw data: the table, and each series' λ, d and seasonality (art's engine) |
| N0u / N0v | `build_univariate` / `write_specs` | route U (the univariate models first) or route V (the vector first) |
| N0 | `load_pre` | the univariate models, the common window |
| N1 | `run_gate` | does the joint model reproduce the univariate ones? (it stops the analysis if not) |
| N1b | `canonical_analysis` | Box and Tiao's canonical analysis of the levels |
| N1c / C0 | `prepare_vec` | the cointegration question (two or more series with d = 1), the model's purpose, the VEC's specification and its checks |
| C1 | `rank_test` | the cointegration rank, by **parametric bootstrap** (a job) |
| C2 | `estimate_vec` | the adopted VEC: the roles (normalisation), α, β, Π |
| C3–C4 | `test_restriction`, `add_exogenous` | restrictions on α and β by LR (who corrects); exogenous inputs |
| C5 | `long_run` | θ, two half-lives, Gonzalo and Ng's permanent and transitory shocks |
| C6–C7 | `irf_bands`, `sweep` | the level responses' bootstrap bands; robustness (jobs) |
| C8 | `evaluate` | the yardstick for the VEC: a veto to forecast, a caveat for a long-run claim |
| — | `job_status`, `job_result`, `job_cancel`, `jobs` | the long jobs: detached, cached by content, they outlive the conversation |
| N2 | `identify_cross`, `identify_matrices`, `identify_echelon` | the cross dynamics: residual CCFs, Jenkins and Alavi's matrices, the Kronecker indices of the echelon form |
| N3–N4 | `estimate`, `check_residuals`, `simplify`, `structure` | a candidate and its LR, the checking, Tiao and Box's simplification, is it really simultaneous? |
| N4b | `study_estimation` | a fit on the MA invertibility wall |
| N5 | `evaluate`, `forecast_uncertainty` | **the yardstick**: does it forecast better than the univariates? |
| N6 | `forecast`, `impulse_response`, `variance_decomposition`, `reorder` | use of the chosen model (on a VEC: the levels; `reorder` refuses) |
| — | `plot_*` | the figures |
| — | `examples`, `load_example` | the worked examples |
| — | `record_decision`, `export_guion` | the record of the analysis |
| — | `split_inp` | out of drvarma's deprecated multivariate `.inp` |

The rules that shape everything:

- **The univariate model is the yardstick.** A VARMA that does not forecast
  better than the univariate models out of sample has no reason to exist,
  however significant its cross terms are in sample. For a VEC the comparison
  is always made and reported: a veto when the model is to forecast, a caveat
  beside a long-run claim (the purpose is recorded at N1c).
- **No cointegration claim without a finished bootstrap.** The rank is the
  parametric bootstrap's; the asymptotic table is orientation only. A rank
  adopted on theory is written in the guion as such.
- **Evidence and a menu, not a verdict.** The tools show the evidence and the
  options with their arguments for and against. The analyst decides in the
  guided lane, and the model decides, in writing, in the autonomous lane.

See [`docs/DESIGN.md`](https://github.com/davidesg/sima-python/blob/main/docs/DESIGN.md) and the generated tool reference
[`docs/TOOLS.md`](https://github.com/davidesg/sima-python/blob/main/docs/TOOLS.md).

## User manual

* [Jenkins and Alavi's method](https://github.com/davidesg/sima-python/blob/main/docs/MANUAL-jenkins-alavi.md): the method of
  Jenkins and Alavi (1981), how sima implements it tool by tool, and their
  muskrat-mink example worked through from art's univariate models — runnable
  in [`examples/jenkins_alavi/`](https://github.com/davidesg/sima-python/tree/main/examples/jenkins_alavi/).
* [Tiao and Box's method](https://github.com/davidesg/sima-python/blob/main/docs/STUDY-tiao-box.md): the vector first, Tiao
  and Box (1981) and Box and Tiao (1977): the stepwise M(l), the canonical
  analysis of the levels, the structure and the simplification. Their gas
  furnace is runnable in [`examples/tiao_box/`](https://github.com/davidesg/sima-python/tree/main/examples/tiao_box/), and the
  flour prices in [`examples/flour_prices/`](https://github.com/davidesg/sima-python/tree/main/examples/flour_prices/).
* [Cointegrated systems](https://github.com/davidesg/sima-python/blob/main/docs/STUDY-vec.md): the
  cointegration question at N1c, the rank by parametric bootstrap, the VEC
  and its long run (the plan: [`docs/PLAN-vec.md`](https://github.com/davidesg/sima-python/blob/main/docs/PLAN-vec.md)).
  Worked in [`examples/flour_prices/`](https://github.com/davidesg/sima-python/tree/main/examples/flour_prices/) (the flagship: where
  the ladder's analysis leads into the rank), [`examples/jenkins_alavi/`](https://github.com/davidesg/sima-python/tree/main/examples/jenkins_alavi/)
  (the mixed case) and [`examples/lutkepohl_e1/`](https://github.com/davidesg/sima-python/tree/main/examples/lutkepohl_e1/) (Lütkepohl's
  E1: one relation, who corrects, an ill-defined fit declared) and
  [`examples/johansen_juselius/`](https://github.com/davidesg/sima-python/tree/main/examples/johansen_juselius/) (the Danish money
  demand: the bootstrap against the asymptotic table at n = 55). Each ships its
  bootstraps' cache, so the tutorial's jobs return at once.
* [The echelon form](https://github.com/davidesg/sima-python/blob/main/docs/MANUAL-echelon.md): Lütkepohl and Poskitt's (1996)
  identified VARMA: the Kronecker indices from the data (`identify_echelon`),
  the fit (`estimate(indices=...)`), and their flour prices worked through,
  runnable in [`examples/lutkepohl_poskitt/`](https://github.com/davidesg/sima-python/tree/main/examples/lutkepohl_poskitt/).

Each worked example runs node by node in a conversation with
`load_example(<name>)` (`examples` lists them).

## Licence

GPL-2.0-or-later. Authors: A.B. Treadway, J.A. Mauricio and D.E. Guerrero
(the engine); D.E. Guerrero (the assistant).
