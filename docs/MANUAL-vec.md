# sima user manual — cointegrated systems

*What sima does when two or more of the series are I(1): the question of
cointegration, the rank by parametric bootstrap, the VEC and what is read from
it. The engine is drvec (drvec-python, the port of drvec C, Mauricio's
VARMA-VEC by exact maximum likelihood). The study behind these choices is
`STUDY-vec.md`, and the decisions are in `PLAN-vec.md` §0. This manual is the
how-to: each node, its tool, what it answers and what it does not.*

The worked examples are listed in Part 3. Each one runs node by node with
`load_example(<name>)`, and its tutorial is `sima://example/<name>`.

## Part 1 · The method

### 1.1 The question

A univariate model of a series with d = 1 says that its level wanders without
an anchor. Two such series can share the wandering: some combination
β′Y of their levels is stationary, and the system corrects towards it. That is
cointegration, and the model that carries it is the vector error-correction
model, written by drvec in Johansen's notation:

    ∇Y_t = α (β′Y_{t-1} − E[W]) + Γ_1 ∇Y_{t-1} + … + Θ(L) A_t,   Π = αβ′ of rank r.

With r = 0 the univariate differences are right jointly, and the system is a
VARMA in differences (drvarma's ladder, N2). With 0 < r < M there are r
stationary relations and M − r common trends. The question belongs to the
analyst. sima asks it whenever two or more series have d = 1, and it never
changes a d on its own: the d is part of the `.pre`.

### 1.2 The rank, by parametric bootstrap

drvec tests the rank with the sequential likelihood ratio on the **exact**
likelihood: H0 rank r against r + 1, for r = 0, 1, … until one is not
rejected. This is a λ-max-type test, not Johansen's trace. It is calibrated
by a parametric bootstrap (Cavaliere, Rahbek and Taylor 2012). Each
replication simulates a sample from the model fitted under H0 and refits it
at r and r + 1 by the same route as the data. The percentiles of the B
statistics LR* are the critical values.

Why the bootstrap and not the tables: at the sample sizes of applied work the
asymptotic critical values are too small, and the sequential test
over-rejects with them. On Cavaliere, Rahbek and Taylor's design (q = 0,
case 2), drvec measured that the test of the true rank rejects 11 % against a
nominal 5 % at T = 50, and the bootstrap brings it to 4 %. sima shows the
asymptotic column only as orientation. There is no table at all for cases 3
and pre.

Before simulating, drvec checks that the model under H0 is I(1, r) (the
algorithm's step ii): every AR root of [∇Y2 ; W] outside the unit circle, and
∇Y2's long-run covariance non-singular. If the model fails the check, drvec
draws no sample from it and the comparison is reported as such. That is a
finding about the model, and a larger B does not change it.

### 1.3 The deterministic case

| case | E[∇Y2] | E[W] | what it means |
|---|---|---|---|
| `1` | 0 | 0 | no constant |
| `2` | 0 | free | a constant restricted to the relation: no drift |
| `3` | free | free | drifts |
| `pre` (default) | as the files say | free | each drift free, or zero where the series' `.pre` has no mean (case 3's mask) |

The default is `pre` because the univariate models have already decided
whether each series drifts, and the VEC should not contradict them silently.

### 1.4 What the school adds

The rules are the same as everywhere in sima (the server's instructions,
rules 8–13):

- **No cointegration claim without a finished bootstrap.** No rank, β or
  equilibrium is reported without one. The analyst may adopt r on THEORY, and
  `estimate_vec(theory=...)` writes it in the guion as such, beside the
  bootstrap's numbers.
- **LR, not Wald.** The `.out`'s Wald statistics depend on the
  normalisation and are not citable.
- **The order of the series is the normalisation** (β on the last r) and the
  Cholesky order. Another order is another fit, never a reorder.
- **The yardstick is always computed.** It is a veto when the purpose is to
  forecast, and a caveat beside a long-run claim.
- **A fit on a ridge is declared, never presented as an optimum.**

## Part 2 · How sima implements it

The nodes in order, with the call each one takes. Every tool returns its
evidence and a menu. The analyst decides in the guided lane, and the model
decides in writing in the autonomous lane.

### 2.1 N1b `canonical_analysis(name, p=0)` — a reading, not a test

Box and Tiao's (1977) canonical analysis of the levels orders the series'
combinations from least to most predictable. Fewer near-non-stationary
components than differenced series point to cointegration. `p = 0` takes the
VAR order from Tiao and Box's stepwise M(l) and names the lags that are
significant alone. The menu leads to N1c. Nothing is decided here.

### 2.2 N1c and C0 `prepare_vec(name, purpose, p=0, q=0, case="pre", nodrift="", mixed=False)`

`prepare_vec` asks the question and records the PURPOSE, "forecast" or "long
run", which decides how C8 reads the yardstick. It then runs the checks
before the rank:

- d ≥ 2 or D > 0;
- drvec's refusals;
- a moved file;
- the window (drvec lines the files up on the intersection of their dates).

It also proposes p. **p = 0** takes Tiao and Box's M(l) on the levels **up to
its first run of two non-significant lags**. A lag significant alone after a
silence is reported and offered, never taken: on Martín Manjón and Treadway's
rates the last significant M(l) gave p = 15, and the contiguous order gives 4.
The mixed case, with I(0) and I(1) series together, is an option (`mixed=True`),
never the default. Declining the question goes to N2.

### 2.3 C1 `rank_test(name, B=499)` — the rank (a job)

`rank_test` runs the sequential exact LR and its bootstrap on drvec C (the
binary in drvec's wheel), as a detached job (§2.9). The report shows:

- the table of each comparison: LR, the bootstrap's 90/95/99 % values, the
  p-value with its Monte Carlo error, and the usable replications out of B;
- the asymptotic column, for orientation;
- a **proposed r̂**: the first comparison not rejected at 5 %, read from the
  critical values, not from the p-value.

The outcomes:

- **r = 0:** the differences are right. Back to N2, in the same session.
- **0 < r < M:** the VEC, C2 onwards.
- **Every comparison rejects:** "at least M − 1". The last step is a
  unit-root question (the canonical analysis, art's table per series).
- **A tie** (a p-value within two Monte Carlo errors of 5 %, at B ≥ 199):
  estimate both ranks and compare them, or rerun with another seed.
- **Not I(1, r):** no rank is read. Reread the integration orders, or try
  another specification.

B below 199 is an exploration, not a verdict. **At small n the rank is
conditional on p.** When n / (M p) is below 15 the report says so, and its
first option is `sweep(name, p="p-1,p,p+1", B=...)`, the rank at the
neighbouring orders (one cached rank job per order). The LR need not be
monotone in p. `plot_rank_bootstrap(name)` draws each comparison's LR*
against the observed LR.

### 2.4 C2 `estimate_vec(name, r, normalise_on="", theory="", multistart=0)`

`estimate_vec` fits the adopted VEC. It refuses without a finished rank test
for the same specification, unless `theory=` says why r is adopted. The
report gives:

- **the roles**: β is normalised on the last r series in drvec's order, or on
  `normalise_on`. The rest are the ∇Y2 block.
- **drvec's `.out` blocks verbatim**: the search table (every start and where
  it stopped: the spread is the diagnostic), α, β, the short run and the
  residuals.
- **the canonical weights beside β.**
- **how the optimiser stopped.** A search that ends on a ridge is said to be
  "not a demonstrated maximum".

### 2.5 C3 `test_restriction(name, weakex="", alpha="", fixb2="", fixb2row="", gamma="", adopt=False)`

`test_restriction` tests restrictions by LR, against the best free fit known
and against drvec's own free fit (both are shown).

- **`weakex="X"`**: weak exogeneity, α = 0 in X's equation. X does not
  correct.
- **`alpha="[[1],[0],[0]]"`**: α = Aψ, for example only the first series
  corrects.
- **`fixb2`, `fixb2row`**: restrictions on β.
- **`gamma="X1,X2 <- Y"`**: **no feedback in the short run**, Γ_k[X][Y] = 0
  at every lag (drvec's `-gzero`).

With `weakex`/`alpha` on the same inputs, `gamma` gives the **conditional
model's** joint test (Johansen 1992): the inputs are weakly exogenous and
receive no feedback. When it holds, the report names the output and the
inputs and offers **mtram** with the same files: the system is a transfer
network, Y on I(1) inputs. sima never goes there on its own. In two series,
weakex + gamma is `add_exogenous(series=...)` (drvec's `-xsys`), the same
model, checked.

### 2.6 C4 `add_exogenous(name, series="", inputs="", links="")`

`add_exogenous` adds exogenous inputs, dispatched by their order of
integration: an I(1) series of the system as exogenous (`-xsys`), or I(0)
inputs with their transfer links (`-xpre`/`-xlink`).

### 2.7 C5 `long_run(name)` · C6 `impulse_response`, `variance_decomposition`, `irf_bands`

- **`long_run`** gives:
  - θ;
  - two half-lives: the textbook one, from α′β alone, and the model's, from
    the equilibrium error's own response;
  - Gonzalo and Ng's permanent and transitory shocks.
- **The responses and the FEVD** are of the LEVELS. Their bands come only
  from the bootstrap: `irf_bands(name, N=499)`, a job.

### 2.8 C7 `sweep(name, p="", case="", estwin="", B=0)` · C8 `evaluate(name)`

- **The sweep** is robustness, one cached job per cell:
  - p, the case and subsamples (`estwin`);
  - and, before any VEC, the rank over p (§2.3).
- **The yardstick**: `evaluate` compares the VEC's forecasts with the
  univariate models' on drvec's origins. It is a veto when the purpose is to
  forecast, and a caveat beside a long-run claim. A VEC is forecast by
  drvarma's forecaster, the VEC written in levels (`drvec.to_levels_varma`):
  one forecaster for every system.

### 2.9 The jobs

`rank_test`, `irf_bands` and `sweep` run as detached processes that survive
the conversation:

- they use at most cores − 1 slots;
- each run has its own folder, `sima_jobs/<id>/`, next to the first file;
- results are **cached by content**: the files' bytes, the arguments, the
  engine and the platform tier.

A job tool waits about 20 s and then returns the job id. Follow it with
`job_status`, `job_result`, `job_cancel` and `jobs`. Nothing partial is ever
a result.

The examples ship their caches, so their tutorials' bootstraps return at
once. The key holds the engine and the tier: on other platforms the jobs run
again (Linux x86_64 is drvec C's reference platform).

## Part 3 · The worked examples

| example | data | what it shows |
|---|---|---|
| `flour_prices` | Tiao and Box's flour prices, three cities | the flagship: the ladder's analysis leads into the rank; the bootstrap does not reject r = 0, and the VEC's nodes follow on theory, written as such |
| `jenkins_alavi` | Jenkins and Alavi's muskrat and mink | the mixed case (`mixed=True`): an I(0) and an I(1) series |
| `lutkepohl_e1` | Lütkepohl's E1 (investment, income, consumption) | r = 1 by bootstrap, who corrects, the two half-lives, and a VARMA-VEC(2,1) on a ridge, declared |
| `johansen_juselius` | the Danish money demand | the bootstrap against the asymptotic table at n = 55: r = 0 where the trace test found one; their relation on theory; small n, the rank conditional on p |
| `martin_manjon_treadway` | U.S. interest rates, FRED, 1985–2008 | Martín Manjón and Treadway (1997) taken further: §3.1 |

### 3.1 Martín Manjón and Treadway: further than the paper

Martín Manjón and Treadway (1997) claim that U.S. interest rates share two common
stochastic trends: monetary policy (the Fed's target and the market rates up
to one or two years) and one the Fed does not control. The 3-year rate
combines the two, so (target R0T, 30-year R30, 3-year R3) cointegrate with
one relation, and no pair of them does. They decided it as the school does,
over-differencing each series and reading the MA unit root by exact maximum
likelihood, on 1985–1995. The example (`sima://example/martin_manjon_treadway`)
takes the same three AR(3) models, built in art, to the whole homogeneous
regime, 1/1985–9/2008 (the post-NOP procedure up to interest on reserves),
and walks the nodes of Part 2:

| node | result | in the paper |
|---|---|---|
| C1, B = 499, p = 4, case pre | r = 0 rejected (LR 23.75 against 20.15, p 0.022), r = 1 not (p 0.35) | CI(1,1), from the MA unit root |
| C1 on 1985–95 alone | r = 0 not rejected (p 0.22; at p = 2, p 0.016) | the paper's sample |
| C2, normalised on R3 | R3 = .575 R0T + .561 R30 − 0.89 % (.043, .054, .23) | weights ≈ .48, .63; μ = −.89 % |
| C3, weak exogeneity | R0T corrects (LR 12.36, p 0.0004); R30 and R3 jointly weakly exogenous (LR 1.70, 2 df, p 0.43) | not tested |
| C3, α and Γ jointly | no feedback R30, R3 ← R0T with α = (1, 0, 0)′: LR 7.83, 8 df, p 0.45 | not tested |
| control, R10 for R30 | the same rank (p 0.022, 0.46), R3 = .477 R0T + .598 R10 − 0.48 %, the joint test p 0.58 | — |

What the drvec bootstrap and the LRs add to the paper:

* **A test for the rank where there was a reading.** Case pre has no
  asymptotic table; the bootstrap is its calibration (§1.2). With it the
  paper's relation needs the doubled sample: neither 1985–95 nor 1996–2008
  alone rejects r = 0 at p = 4. The constant is the paper's.
* **Who corrects.** The target, not the market rates: in monthly data the
  curve anticipates the Fed, and the Fed closes the gap. Causality in the
  sense of prediction, not a structural claim.
* **The conditional model** (§2.5, Johansen 1992). The joint LR on α and the
  short-run block of Γ does not reject R0T | R30, R3: a reaction function in
  market rates, a transfer network on I(1) inputs. sima offers mtram with the
  same files; it does not go there itself.
* **The control** with the 10-year rate, whose series has no gap (FRED fills
  GS30's 2002–2006 gap by extrapolation): the same structure.

A separate study, whose data are not in the example, also ran the calibration
with the 1- and 2-year rates in the target's place (the same rank on
1985–2008, but the short rate leads and the long ones adjust), and the samples
after 2008: on the floor system no rank is found with any p; outside it the
weights are the old ones, but with about 50 months the rank does not prove
it. Its results, with the QE and QT interventions, are in the tutorial's
last section, "After 2008: the floor, QE and QT".

## References

- Box, G. E. P. and G. C. Tiao (1977), "A canonical analysis of multiple time
  series", *Biometrika* 64, 355–365.
- Cavaliere, G., A. Rahbek and A. M. R. Taylor (2012), "Bootstrap determination
  of the co-integration rank in vector autoregressive models", *Econometrica*
  80, 1721–1740.
- Gonzalo, J. and S. Ng (2001), "A systematic framework for analyzing the
  dynamic effects of permanent and transitory shocks", *Journal of Economic
  Dynamics and Control* 25, 1527–1546.
- Johansen, S. (1992), "Cointegration in partial systems and the efficiency of
  single-equation analysis", *Journal of Econometrics* 52, 389–402.
- Johansen, S. and K. Juselius (1990), "Maximum likelihood estimation and
  inference on cointegration — with applications to the demand for money",
  *Oxford Bulletin of Economics and Statistics* 52, 169–210.
- Lütkepohl, H. (2005), *New Introduction to Multiple Time Series Analysis*,
  Springer.
- Martín Manjón, R. and A. B. Treadway (1997), "The Fed controls only one of
  the two interest rates in the U.S. economy", Documento de Trabajo 9716,
  ICAE, Universidad Complutense de Madrid.
- Tiao, G. C. and G. E. P. Box (1981), "Modeling multiple time series with
  applications", *Journal of the American Statistical Association* 76,
  802–816.
