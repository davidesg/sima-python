# sima — architecture and principles

What sima is built on, in one place: the principles it inherits and keeps, the
layers that carry them, and the two paths through a system — route U (the
ladder, Jenkins and Alavi) and route V (the vector first, Tiao and Box) — with
the two branches that hang off them (the echelon form, the VEC). The decision
nodes, one by one, are in `DECISION_NODES.md`; the design of each piece in
`DESIGN.md` and the studies; this document is the map above them. An
evaluation of where sima stands against it is in
`reviews/2026-11-20-sima-evaluation.md`.

## 1. Where sima sits

The ATSW suite is a ladder of assistants over a ladder of engines:

| rung | assistant | engine | model |
|---|---|---|---|
| 1 | art | fue | one series: ARIMA with interventions |
| 2 | mtram | drtran | a transfer network: a DAG, a triangular VARMA |
| 3 | **sima** | **drvarma** (ladder mode) | a system: a general VARMA |
| 3 | **sima** | **drvec** | a cointegrated system: the VARMA-VEC in levels |

Every engine is a C program with a Python port, and the two are homologated.
The rungs talk through **files**: the `.pre` of fue.

## 2. The principles

These are not sima's choices. They come down the ladder from art and mtram,
and sima keeps them. Where sima departs from one, it says so (route V, §5).

**P1 — The fue format is the base of everything.**
- A `.pre` is the optimum of a univariate model, rerunnable: run fue on it and
  the numbers do not move. An `.inp` is a specification, with values that are
  only seeds; a `.pre` that is edited becomes an `.inp` again.
- Every engine reads the format as fue writes it, transformation included.
  The Box-Cox is fue's, refactor·y with λ = 1, not the textbook
  refactor·(y − 1) (lib/prewhiten BUG-0002, fixed on 20-nov-2026).

**P2 — The ladder: the univariate models first.**
- A system starts from the univariate model of each series, kept on its
  diagonal. What the system adds is only the RELATION between the series: the
  cross dynamics and the innovation covariances.
- **The gate** certifies the start: the joint cast (fue's) reproduces the
  univariate models exactly, or nothing is built on it.
- This is a commitment of the suite (art → mtram → sima), not an option of a
  route. Even the starting values follow it: the own models are never seeded;
  only the relation is preestimated (§6).

**P3 — The univariate model is the yardstick.**
- A VARMA is kept only if it forecasts better than the univariate models out
  of sample (rule 1). In-sample significance is necessary, not sufficient.
  When no system wins, the univariate models are the result, and that is a
  finding.
- The VEC is the one exception. With the purpose "long run" the yardstick is a
  caveat, because the equilibrium has its own test, the rank by bootstrap.
  For a VARMA the purpose decides nothing.

**P4 — Engines ship numbers; the assistant argues.**
- The engines compute and return their caveats as data. The assistant turns
  them into evidence and options.
- There is no hard-wired recommendation: two judges (a heuristic and the
  model) would contradict each other.
- **The engines are homologated.** The port does not depart from the C, not
  even to fix it: a fix starts in the C and both move together.
- **What works is not touched.** A latent defect in a tested engine is bounded
  and reported; the defaults that the reference batteries pin do not change.

**P5 — The decisions are the analyst's.**
- **Guided lane:** the analyst decides every node.
- **Autonomous lane:** the model sits in the analyst's chair. It walks the
  same nodes and writes down each decision with its reason.
- Each node answers with an envelope: table, what it shows, conclusions, and
  options with their exact calls. It ends in the pause, or in the filled-in
  `record_decision` call in the autonomous lane.
- The guion records every decision as data: open, closed (with which option),
  adopted, or set aside.

**P6 — Nothing partial is a result, and a stop is not a decision.**
- No rank, β or equilibrium is reported without a finished bootstrap.
- A fit on the MA wall is not an optimum.
- A fit below a model it nests is a failed search, not an estimate.
- Some points are stops, with nothing to weigh: a failed gate; no finished
  bootstrap; a system that is triangular or conditional, which is mtram's
  (offered, never taken). They are listed in `DECISION_NODES.md`.

## 3. The layers

```
 the conversation (MCP: Claude Code, Desktop, ...)
   │  tools, resources (sima://protocol, sima://doc/...)
 ┌─┴──────────────────────────────────────────────────────────────┐
 │ sima.mcp_server / mcp_vec   the protocol: nodes, tools, instructions │
 │ sima.lane (one wrapper on every tool)                          │
 │   ├ the lane      guided pause / autonomous record call         │
 │   ├ decisions     pending → closed / adopted / dead-end         │
 │   └ telemetry     opt-in, local (SIMA_TELEMETRY)                │
 │ sima.envelope · evidence · vec · levels · status · figures      │
 │ sima.guion (the record) · session (the state) · jobs (bootstraps)│
 └─┬──────────────────────────────────────────────────────────────┘
   │  numbers and caveats as data
 ┌─┴───────────────────────┐  ┌──────────────────────────┐
 │ drvarma (ladder) ⇄ C     │  │ drvec ⇄ C                 │
 │ fue (the cast, the format)│  │ pyfug (the figures, CCF)  │
 └─────────────────────────┘  └──────────────────────────┘
```

The wrapper in `sima.lane` is the one place where the session's lane, the
bookkeeping of decisions and the telemetry act. The tools that build the
envelopes do not know about any of them, and a failure there never costs a
tool its answer.

## 4. Route U — the ladder (Jenkins and Alavi)

The structured path. It is the ladder of art and mtram, one rung up, and it
inherits their discipline: a validated base, a gate, identification from the
evidence, a yardstick the analyst already trusts.

| node | tool | what happens |
|---|---|---|
| N0 | `load_pre` | the `.pre` files (from art: the analyst's reviewed univariate models); the lane, the purpose, the ORDER of the series (the Cholesky order) |
| N1 | `run_gate` | the joint cast reproduces each univariate model, or STOP |
| N1b | `canonical_analysis` | Box and Tiao on the levels, without the models' deterministic terms (BUG-0018): does the system need every difference? |
| N1c | `prepare_vec` → `rank_test` | with two or more I(1) series: the cointegration question (§8) |
| N2 | `identify_cross` → `identify_matrices` → `identify_echelon` | the residual CCFs pair by pair (what the univariate models do not carry), then the matrices, then the echelon form if an MA is in sight |
| N3 | `estimate`, `lag_order` | candidates from the evidence; the own models stay the `.pre`'s; the order by LR |
| N4 | `check_residuals`, `simplify`, `structure`, `study_estimation` | in-sample evidence; a triangular system is mtram's; the MA wall |
| N5 | `evaluate` → `adopt` / `abandon` | the yardstick: the analyst's univariate models |
| N6 | `impulse_response`, `variance_decomposition`, `forecast` | the use, on the adopted model |
| N7 | `hand_over` → `export_guion` | the result, its yardstick, the caveats |

**From raw data**, route U first builds the univariate models with
`build_univariate`: art's autonomous lane in miniature. The models are light
and not reviewed in art, and every file, the gate and the hand-over say so.
The strong form of route U is the one that starts from the analyst's art
models.

## 5. Route V — the vector first (Tiao and Box)

For raw data, when the analyst wants the system without univariate models
first. **It is the less structured path, and the more dangerous one**,
because it gives up most of what makes route U safe:

| | route U | route V |
|---|---|---|
| the base | the analyst's univariate models, reviewed in art | specifications: only each series' transformation (λ, d, harmonics, mean) |
| the gate | certifies the univariate models | certifies only the cast; the diagonal it checks is white noise (a random walk with d = 1) |
| interventions | in the `.pre`, decided in art | none: `characterize` scans for outliers and reports them, but does not model them |
| the own dynamics | fixed: the univariate optimum | estimated jointly with the cross terms, all m²(p + q) coefficients |
| identification | CCFs of prewhitened residuals, then matrices | the vector only: R_k, S_k and Tiao and Box's M(l), by least squares |
| the LR of a fit | against the univariate models | against the same model without cross terms (one AR(p)/MA(q) per series): a lower bar |
| the yardstick (N5) | the analyst's models | built by route U's builder (light, not reviewed) unless the analyst provides them (BUG-0004) |
| the files | `.pre` in, `.pre` everywhere | `.inp` specifications that never become `.pre`; the joint result lives only in the session and the guion |

The ladder still applies where it can. Route V passes the gate, the diagonal
fit estimates each specification's own model by exact ML before any cross term
(§6), and N5 still judges by the univariate models. But the first time a
route V system meets a validated univariate model is at the end, at N5.

## 6. Starting values

Exact ML from a poor start can stop far from the optimum. On the US monetary
VAR, from zero, the VAR(2) stopped after two iterations, 50 points below its
VAR(1) (drvarma BUG-0027). The cause was the scale of the cross terms, not the
optimiser's penalty. The rule, the same in the C (`-start ols`) and the port
(`start="ols"`):

- **The own models are never seeded.** On route U they are the `.pre`'s; on
  route V the diagonal fit has estimated them (P2).
- **The relation is preestimated:**
  - the cross AR terms are +Φ_k from the least squares of the VAR(p) (the Box
    and Jenkins convention, the MA included: θ = −coefficient);
  - Q's covariances are the residuals' correlation in the ladder's
    normalisation, q_ij = r_ij √(Q_ii Q_jj), with Q₁₁ = 1 (Mauricio 1995) and
    the gate's Q_ii.
- **The engine default stays zero** (P4). sima uses `ols` when the installed
  drvarma has it, else `preliminary` (Jenkins and Alavi's).
- **The guard** (BUG-0019): a fit below a model it nests, or one that stalled,
  is retried from the preliminary estimates, and the report says so.
- **The echelon form** keeps its own start: the least squares of Lütkepohl and
  Poskitt's stage II.

Measured and not adopted: a multivariate Hannan-Rissanen start. It adds
nothing where the starts agree, and on Jenkins and Alavi's VARMA(2,1) it lands
on a worse local maximum, certified.

## 7. The echelon branch (Lütkepohl and Poskitt)

The echelon form is not a third route. It is the third instrument of N2 and
N3 in either route, for when an MA is in sight or a VARMA(p, q) is ill-defined
on the MA wall.

- **`identify_echelon`** gives the Kronecker indices from the data: a long VAR,
  then least squares per candidate, chosen by SC with HQ beside it.
- **`estimate(indices=...)`** fits the echelon VARMA by exact ML from the stage
  II least squares. A₀ is lower triangular, so **the order of the series is
  part of the model**.
- **On route U**, the own AR(n_i)/MA(n_i) replaces each univariate model's
  regular ARMA. What is kept from the `.pre` — the transformation, the
  deterministic terms, the seasonal factors — multiplies the whole row, and
  that row factor is checked by LR (`factor_test`).

## 8. The cointegration branch (the VEC)

With two or more I(1) series, the cointegration question comes before any
VARMA in differences (N1c). It is offered whatever the canonical count, and it
is the analyst's to take.

- The rank comes from drvec's parametric bootstrap, a detached job; nothing
  partial is read.
- Then the VEC's own nodes: C2 the roles, C3 the restrictions by LR (never
  Wald), C4 the exogenous inputs, C5 the long run, C6 the responses in levels
  with bootstrap bands, C7 the sweep, C8 the yardstick by purpose.
- One session and one guion hold both kinds of fit. `docs/MANUAL-vec.md` has
  the method.

## 9. Where it lives

| piece | file |
|---|---|
| the protocol, the instructions, the tools | `src/sima/mcp_server.py`, `src/sima/mcp_vec.py` |
| the envelope, the lane, the decisions, the telemetry | `envelope.py`, `lane.py`, `decisions.py`, `telemetry.py` |
| evidence and menus | `evidence.py`, `vec.py` |
| the levels without deterministic terms | `levels.py` |
| `where`, `hand_over` | `status.py` |
| the record, the state, the jobs | `guion.py`, `session.py`, `jobs.py` |
| the decision nodes | `docs/DECISION_NODES.md` |
| the raw entry, the two routes | `docs/STUDY-raw-entry.md` |
| the engines | drvarma (`drvarma.ladder`), drvec, fue; their C in atsw-gui `engines/` |
