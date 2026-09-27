# sima — simultaneous VARMA on the ATSW ladder

**sima** is the MCP assistant for systems of time series: VARMA models by exact
maximum likelihood, built on the univariate models of each series. The engine
is [drvarma](https://pypi.org/project/drvarma/), whose ladder mode takes
fue's univariate files as input. This package is the assistant: the protocol
the model walks, the evidence at each node, and the menu of decisions.

It is the third rung of the ATSW ladder:

    art (one series)  →  mtram (transfer networks)  →  sima (systems)

You arrive at sima with several univariate models (`.pre` files from art or
fue), or from mtram when its network identification found a **cycle**: two
series that feed each other, which no transfer network can hold. sima takes
the same files.

## Install

```sh
pip install sima-tseries
```

Register the server in your MCP client (the command is `sima`, stdio). The
binary wheels of drvarma carry the compiled likelihood the ladder needs. If
they are missing, drvarma warns and runs about 250 times slower.

## The protocol

| node | tool | what it answers |
|---|---|---|
| N0 | `load_pre` | the univariate models, the common window |
| N1 | `run_gate` | does the joint model reproduce the univariate ones? (it stops the analysis if not) |
| N2 | `identify_cross` | what the univariate models do NOT carry: residual cross-correlations |
| N3–N4 | `estimate` | a candidate: cross orders, covariance, LR against the univariates |
| N5 | `evaluate` | **the yardstick**: does it forecast better than the univariates? |
| N6 | `forecast`, `impulse_response`, `variance_decomposition` | use of the chosen model |
| — | `record_decision`, `export_guion` | the record of the analysis |
| — | `split_inp` | out of drvarma's deprecated multivariate `.inp` |

Two rules shape everything:

- **The univariate model is the yardstick.** A VARMA that does not forecast
  better than the univariate models out of sample has no reason to exist,
  however significant its cross terms are in sample.
- **Evidence and a menu, not a verdict.** The tools show the evidence and the
  options with their arguments for and against. The analyst decides in the
  guided lane, and the model decides, in writing, in the autonomous lane.

See [`docs/DESIGN.md`](docs/DESIGN.md) and the generated tool reference
[`docs/TOOLS.md`](docs/TOOLS.md).

## Licence

GPL-2.0-or-later. Authors: A.B. Treadway, J.A. Mauricio and D.E. Guerrero
(the engine); D.E. Guerrero (the assistant).
