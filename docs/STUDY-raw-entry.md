# Starting from raw data — a study

**Status: a study to be argued with, not a plan.** Written 2026-10-02.

The question: an analyst arrives with raw series and no univariate models, and
wants to go multivariate. Today sima sends them to art ("There is no raw-data
entry"). The old sima (drvarma's MCP server, still registered as `drvarma`)
did take raw data. This study asks what sima should do, and proposes two
routes that keep the file contract.

## 1. What the old sima did

`load_data` → `characterize_series` → `cross_correlation_matrices` /
`partial_autoregression_matrices` → `identify_varma_order` →
`confirm_and_estimate`, on `drvarma.Model`:

- **load_data**: Excel/CSV/JSON, the series in their original levels.
- **characterize_series**: per series, art's λ (`boxcox_selection`), d (unit-root
  tests, capped at 1), seasonality (HAC F-test) and a first (p, q). Then a joint
  **consensus**:
  - one λ for all (0 if every λ is near 0, otherwise the median);
  - **d = the maximum d**, every series differenced alike ("v1, no
    cointegration");
  - seasonal dummies for all if any series is seasonal.
- **identification**: CCM symbols, Tiao and Box's partial autoregression
  t-ratios, and a grid of exact-ML VARMA(p, q) ranked by BIC.
- **confirm_and_estimate**: the VARMA on the common transformation, with a
  free diagonal, and the multivariate `.inp` as its file.

What it lacked, and what sima was rebuilt to have:
- **one transformation for all.** A price in logs and a rate in levels got the
  same λ; a stationary series was differenced because another was not;
- **no yardstick.** Nothing said whether the VARMA beat the univariate models,
  because there were none;
- **the multivariate `.inp`**, deprecated since drvarma 5.0: the C ladder and the
  GUI read one fue file per series.

## 2. What sima has today that makes a raw entry cheap

- **The file contract carries a full VARMA.** `ladder.split`'s docstring: with a
  free regular AR(P)/MA(Q) in each series' `.inp` and cross orders p = P,
  q = Q, "the ladder is the old full VARMA(P,Q)". A series' file can hold only
  its transformation, its deterministic terms and a free AR placeholder. The
  ladder then estimates diagonal and cross terms jointly. **No engine change is
  needed for either route below.**
- **The gate already handles specifications.** It fits each file alone first,
  and says whether a file is an optimum or a specification (it moved).
- **art's engine is importable**: `boxcox_selection`, `unit_root_tests` /
  `recommended_d`, `detect_seasonality`, `suggest_orders` (option-B ranking,
  with the tie band and the domain card), and fue's `Model.fit` /
  `write_pre`. This is what the old `characterize_series` called, and what built
  the flour example's models by hand on 2026-10-02.
- **The Wisconsin tools on the vector**: method 1 of `identify_matrices` (R_k,
  S_k, S_k(q), the stepwise M(l)) and `canonical_analysis`.

## 3. The proposal: one entry, two routes

    load_data ── characterize ──┬── route U: build the univariate models ── load_pre ── (the ladder as today)
                                │
                                └── route V: the vector first ── identify on w_t ── estimate VAR/VARMA with a free diagonal
                                                                                     └── yardstick: the univariates built for N5

### 3.1 N0r — `load_data`

- Excel/CSV, one column per series, with frequency, start and names. The old
  tool's header sniffing is kept (BUG: a numeric header-less CSV lost its first
  row).
- The series are original levels, with one common calendar: aligned by
  construction, as the gate requires.

### 3.2 N0c — `characterize` (shared by both routes)

Per series, with art's engine and art's order:
1. λ (Box-Cox);
2. d (unit roots), D or seasonal harmonics (HAC F-test);
3. a preliminary outlier scan, reported but not acted on.

**No joint consensus.** Each series keeps its own λ and d: the ladder allows
it, and forcing them alike was the old sima's first fault. The report is a
table, one row per series, with art's evidence, and a menu: accept, change a
series' λ/d/D, or take a series to art.

When two or more series come out with d ≥ 1, it already offers
`canonical_analysis` on the levels. It is the place where differencing is
cheapest to question, before anything is built on it.

### 3.3 Route U — the univariate seed (Jenkins and Alavi, the ladder)

`build_univariate(name)`, for each series:
1. take the orders art ranks first (`suggest_orders`), with the tie and the
   domain card shown when there is one;
2. estimate with fue, and check the residuals (Ljung-Box, the large ones);
3. write `<SERIES>_sima.pre` and `.out` next to the data.

Then `load_pre` with those files, and the protocol as today.

This is **art's autonomous lane in miniature**, and it says so:
- every `.pre` carries a provenance line, "built by sima's raw entry, not
  reviewed in art";
- the guion records it at the node;
- the gate's report repeats it.

It does not do what art's protocol does after the orders: over-parameterisation,
Easter, formal tests, MEG reformulation, interventions. The menu at the end of
the node says so, and offers each series to art's guided lane.

### 3.4 Route V — the vector first (Tiao and Box)

**The current `.inp` is enough.** Route V's files are ordinary fue `.inp`
specifications, one per series, carrying:
- λ, d, and D or the seasonal harmonics;
- the deterministic terms, if any;
- the mean, if it applies;
- once the order is chosen, a regular AR(p), and an MA(q) for a VARMA, with
  starting values 0 and every coefficient free.

No new format and no engine change: it is what `ladder.split(ar=, ma=)`
already writes.

**Why the diagonal has to be in the file.** The ladder's cross orders build
only the OFF-diagonal terms (`_pairs` requires i ≠ j); each series' own
dynamics always come from its file. So an `.inp` with only λ, d and
deterministic terms, estimated with p = 6, would be a VAR(6) with a zero
diagonal, which is not Tiao and Box's model. With the diagonal AR(P)/MA(Q) in
the files and cross orders p = P, q = Q, the ladder IS the full VARMA(P, Q).

1. **Specifications.** `write_specs(name)` writes `<SERIES>.inp` per series with
   the transformation and the deterministic terms only: the order is not known
   yet.
2. **Identification on the vector.** `identify_matrices`, method 1 (R_k, S_k,
   M(l), S_k(q)), and canonical_analysis on the levels. Method 2 has no
   residuals to read, because there are no univariate models; the tool says so
   instead of pretending.
3. **Estimation.** Once identification gives (P, Q), sima rewrites each `.inp`
   with the free AR(P)/MA(Q). An `.inp` is a specification, so rewriting it is
   legitimate. Then `estimate(name, P, Q)` as always: the full VARMA, Tiao and
   Box's model, by exact ML. C from the Tiao–Box study, the simplification by
   coefficient, is what makes it readable; this is the route where C matters
   most.

**Route V writes no `.pre` for the system.** Its diagonal is estimated jointly
with the cross terms: each series' coefficients are its ROW of the system, not
its univariate optimum. Written as one `.pre` per series, they would break the
`.pre` invariant (fue, rerunning that `.pre` alone, would move the numbers).
The system's files are and stay `.inp`. The joint result needs its own record
(§4, decision 4).
3. **The yardstick.** N5 needs univariate models to compare with. Route V builds
   them with route U's builder, **for N5 only**; they never enter the system.
   The evaluation's text says where they came from.

What the gate means here: the specs are white-noise univariates (a random walk
for d = 1). The gate still certifies the cast. It says nothing about the
univariates, and the report says so.

### 3.5 The first question, extended

When the input is raw data:

> "You have no univariate models. Two schools:
> (U) build them first and model the system on top of them (Jenkins and Alavi;
> the ladder), or
> (V) model the vector directly, the univariate models only as the yardstick
> (Tiao and Box).
> Either way, every series keeps its own transformation."

Then the usual guided/autonomous question.

## 4. Files: no multivariate `.inp`

The old sima's "inp for raw data" comes back as **one fue file per series**:
- route U writes `.pre` (optima of the univariate models);
- route V writes `.inp` (specifications: λ, d, deterministic terms and, once
  identified, free AR(P)/MA(Q)). They never become `.pre`: their estimates are
  rows of the system, not univariate optima (§3.4). Its only `.pre` are the
  yardstick's univariates.

The multivariate `.inp` stays deprecated: the C ladder (drvarma v5) and the GUI
read lists of fue files, and reviving it would split the contract.

What does not exist on either route is **a file for the joint model itself**,
which today lives in the session and the guion. Route U and the `.pre` route
already have this gap. Route V makes it more pressing: there, the per-series
files hold no estimates at all. It is noted in §7, not solved here.

## 5. What it costs

| piece | where | size |
|---|---|---|
| `load_data` (raw, with header sniffing) | sima | small; the old tool's code |
| `characterize` (λ, d, D, outlier scan per series; table and menu) | sima, art's engine | medium |
| `build_univariate` (orders, fue fit, residual check, `.pre` with provenance) | sima, art's engine and fue | medium |
| `write_specs` (fue `.inp` per series: λ, d, deterministic terms; free AR(P)/MA(Q) once identified) | sima; `ladder.split`'s writer, factored out | small |
| rewriting the specs with the identified (P, Q) and reloading before `estimate` | sima | small |
| method 2 without univariates; the route in the gate, N5 and the guion texts | sima | small |
| instructions: the raw entry and the two schools | sima | small |

No change in drvarma's engine. art-python becomes a dependency of sima's raw
entry only, imported lazily as the old server did.

## 6. Validation

- **Flour prices, route U.** From `data/flour_prices.csv` alone, the builder
  must reach the example's three ARIMA(0,1,1) (or tell why not). It must also
  flag Buffalo's tie (random walk, AR(1), MA(1)).
- **Muskrat–mink, route U.** From `data/mink_muskrat.csv`, compare what the
  builder reaches with art's guided models (MUSKRAT ARIMA(6,1,1), MINK AR(4)).
  The distance between them is the honest measure of what "not reviewed in art"
  means, and it goes in the manual.
- **Gas furnace, route V.** The vector first, as Tiao and Box did:
  - M(l) points to AR(6) (already tested in drvarma);
  - the exact-ML VAR(6) with a free diagonal should be close to their LS
    estimates (5.6);
  - later, B's structural test finds no feedback.
- **Flour prices, route V.** VAR(2) in levels (d = 0 per series), against the
  differenced route U. Tiao and Tsay's ARMA(1,1) in levels is the reference.

## 7. Decisions

1. **Both routes**, with the school asked at the entry, or route U only for now?
2. **Route U's depth**: the light builder proposed (orders, fit, residual check,
   provenance), or more of art's autonomous protocol (over-parameterisation,
   formal tests) inside sima? The proposal is light: the rest belongs to art,
   and the menu sends there.
3. **Route V's yardstick**: the univariates built by route U's builder for N5,
   as proposed?
4. **The joint model's file** (§4): leave it for later, or study it now? The C
   ladder and the GUI will need it, and route V more than route U: its
   per-series files are specifications with no estimates.
5. **Order of work**: `load_data` + `characterize` → route U (it reuses
   everything and gives the flour and muskrat–mink checks) → route V (with the
   gas furnace, and C of the Tiao–Box study right after).

**Decided (2026-10-02, the study's recommendations accepted):**
1. Both routes, U and V. With raw data, the school is asked at the entry, then
   guided or autonomous.
2. Route U's builder is the light one (orders, fit, residual check,
   provenance); the rest of art's protocol stays in art, and the menu sends
   there.
3. Route V's yardstick: the univariates built by route U's builder, for N5 only.
4. The joint model's file: deferred, to be studied before the C ladder and the
   GUI need it. Route V's reports say that the system's estimates live in the
   session and the guion.
5. Order of work: `load_data` + `characterize` → route U (flour and
   muskrat–mink checks) → route V (gas furnace), with C of the Tiao–Box study
   right after.
