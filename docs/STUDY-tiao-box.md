# Tiao and Box in sima — a study

**Status: a study to be argued with, not a plan.** Written 2026-10-02 and
revised the same day against the papers, now in `drvarma_source/literature`.
It asks what the second of the school's "two basic works" of the multivariate
stochastic (MS) methodology adds to sima, now that the first, Jenkins and Alavi
(1981), is implemented (`DESIGN-jenkins-alavi.md`, phase 1, A–F;
`MANUAL-jenkins-alavi.md`). drvarma's `docs/ECHELON_SEEDED_DESIGN.md` §3.5 and
§5 already discuss the same papers from the echelon side; this study agrees
with it and does not repeat it.

## 0. The Wisconsin line

"Box and Tiao" here is a line of four papers. The first opens the question of
structure through linear combinations; the 1981 paper is the model-building
method; the two by Tiao and Tsay finish what it left open:

| paper | contribution | file |
|---|---|---|
| **Box and Tiao (1977)**, "A canonical analysis of multiple time series", *Biometrika* 64, 355–365 | the canonical transformation: components ordered from least to most predictable; near-white ones are **static relations** among the series, near-non-stationary ones the **common growth**; the hog data in levels | `Box-CanonicalAnalysisMultiple-1977.pdf` |
| **Tiao and Box (1981)**, "Modeling multiple time series with applications", *JASA* 76, 802–816 | iterative VARMA building on the whole vector: indicator symbols, the stepwise autoregression with M(l), conditional then exact likelihood, simplification, residual checking, feedback read from the fit | `Tiao-ModelingMultipleTimes-1981.pdf` |
| Tiao and Tsay (1983), "Multiple time series modeling and extended sample cross-correlations", *JBES* 1, 43–56 | the **extended** sample cross-correlation (ESCC) matrices: identification of the orders of a MIXED VARMA(p, q), which the 1981 paper declared still open; the U.S. hog data | `Tiao-MultipleTimeSeries-1983.pdf` |
| Tiao and Tsay (1989), "Model specification in multivariate time series", *JRSS B* 51, 157–213 (with discussion) | **scalar component models** (SCM): canonical correlations find linear combinations of low order, i.e. hidden simplifying structure; a χ² criterion table for the overall order; the flour-price data (printed in Appendix B) and the hog data | `Tiao-ModelSpecificationMultivariate-1989.pdf` |

One related work is not in the folder and is only pointed at: Box and Tiao
(1975), intervention analysis, which is art's.

Relloso (1997) cites the 1981 paper as *JASA* 75; it is 76(376).

## 1. Tiao and Box (1981), what it does

The Box–Jenkins cycle applied to the stationary vector **as a whole** (§4).

**Identification (§4.1).**
- Sample cross-correlation matrices as indicator symbols: + beyond 2n^{-1/2},
  − below −2n^{-1/2}, and . otherwise.
  - In their own words they are "a rather crude signal-to-noise ratio guide",
    not a test.
  - "Taken literally" they over-parameterise, because with autocorrelated
    series the variances are larger (p. 806).
  - They spot a low-order VMA: ρ(l) = 0 for l > q.
- **The stepwise autoregression.** Fit AR(l) by multivariate least squares for
  l = 1, 2, …. For each l, the table carries three things:
  - the indicator symbols of the last coefficient matrix 𝒫(l), at ±2 of its
    own standard errors;
  - the likelihood-ratio statistic
    M(l) = −(N − ½ − l·k) ln(|S(l)| / |S(l−1)|), asymptotically χ²(k²) under
    𝒫(l) = 0. Here S(l) is the residual sum of squares and cross-products
    matrix of the AR(l) (4.1), and N = n − p − 1 is the effective number of
    observations with a constant (4.2–4.3, Bartlett 1938);
  - the diagonal of the residual covariance matrix, i.e. how much each series
    gains as l grows.
- The residual cross-correlations after each AR(l) fit (Table 5), as symbols.
  For an ARMA they can mislead: Table 6 shows an ARMA(1,1) read as MA(2) after
  an AR(1) fit.
- The **determinantal criterion** D(l, m) = 0 for l > p, m ≥ q (3.8–3.9): the
  multivariate corner method. They were still studying it, and it becomes the
  ESCC of 1983 and the canonical correlations of 1989.

**Estimation (§4.2).**
- Conditional likelihood in the preliminary stages, the exact likelihood
  (Hillmer and Tiao 1979) at the end. The conditional one "can be seriously
  inadequate" with small n or an MA root near the unit circle.

**Checking (§4.3).**
- Plots of the standardised residuals and their cross-correlation matrices as
  symbols.
- Hosking's and Li–McLeod's overall χ² "are not substitutes for more detailed
  study of the correlation structure".

**Simplification (§4, point 3; §5).** "Considerable simplification is almost
invariably possible after an initial model has been fitted":
- set to zero the coefficients "whose estimates were small compared to their
  standard errors" and re-estimate;
- **no formal rule** is given;
- in the gas furnace example the zeros also come from knowledge of the system
  (the delay).

So the software must allow "models … in which certain parameters are fixed or
constrained" (point 4).

**The examples, and what each one teaches:**
- **Simulated** (§3.1):
  - a VMA(1) with n = 250: Θ = [[.2, .3], [−.6, 1.1]], Σ = [[4, 1], [1, 1]];
  - a VAR(1) with n = 150 and the same matrix as Φ.

  For the VMA(1), a pure AR approach needs p ≈ 7 (Table 4, and the π weights
  in (4.4)): the partials alone mislead on an MA.
- **SCC** (stock index, car production, commodity prices; quarterly
  1952–1967):
  - AR(2) and ARMA(1,1) fitted, then restricted twice (Table 10);
  - the result is three near random walks with one leading indicator at lag 1;
  - only a small gain over the univariate model, (5.3) σ² .151 against .134:
    "it shows what is there and does not mislead".
- **Gas furnace** (Box–Jenkins Series J), without telling the method which
  series is the input:
  - M(l) = 1650, 665, 31.7, 22.5, 5.6, 12.9, 1.8, … points to AR(6);
  - 𝒫₁₂ is small at every lag, so there is **no feedback**: the system is a
    transfer function, with delay 3;
  - the restricted AR(6) reproduces the impulse weights of Box–Jenkins'
    transfer model (Table 13).
  - Table 14 is the warning: **at AR(1) or AR(2) the fit shows a spurious
    feedback**. The one-sided relation appears only at p = 3, once the input's
    own model (an AR(3)) is captured, and the delay appears at p = 4.
  - Also, temporal aggregation can create pseudo-feedback (Tiao and Wei 1976).
- **Muskrat–mink** (Table 15), on Chan and Wallis' polynomially detrended
  series:
  - M(1) = 111.7, M(2) = 4.8, so an AR(1);
  - they do "not wish to sanctify" it (lag-10 residual correlation, doubtful
    detrending);
  - the point is that the direct route gets there at once.

**The polemic (§4, §6).** "We see no alternative but to provide for direct
initial fitting of models of the form (3.1)". §6 then dismantles the routes that
start from the univariate models, Granger–Newbold and Wallis / Chan–Wallis:
- the residual model carries nonlinear constraints and is hard to identify;
- H(B) can have a higher degree than the univariate MAs;
- the diagonal-AR form needs pk(k − 1)² more parameters "merely to identify
  correctly a low order vector AR model";
- the degrees do not map one to one onto (p, q).

`ECHELON_SEEDED_DESIGN.md` §5 quotes it in full and reads where it leaves the
seed (it stands) and the a priori factorisation (only with its LR check).

**Last words (§6).** The eigen-analyses of Γ(0), Σ, Γ(0) − Σ (the predictable
part), and of the φ's and θ's, "useful in (a) detecting exact concurrent or
lagged linear relations between series" — "one of the most important and
challenging topics". That is Box and Tiao (1977), and Tiao and Tsay (1989).

## 2. Tiao and Tsay (1983) and (1989), in one paragraph each

**ESCC (1983).** The ESCC matrix ρ^(m)(j) is the lag-j cross-correlation
matrix of the series filtered by the j-th *iterated* AR(m) regression, which
removes the MA bias of plain least squares (3.14–3.17). For an ARMA(p, q):
- ρ^(m)(j) → 0 in a triangle with its vertex at (p, q) (3.31);
- read as symbols with the crude variance (n − m − j)^{-1};
- it is the vector extended ACF.

On the hog data (5 series, 82 annual observations, from Quenouille):
- it identifies an ARMA(1,1), then restricted by zeros and estimated by exact
  ML;
- the largest residuals are treated as outliers (the first two observations
  are dropped);
- the joint model cuts the residual variances by 28–65 % against the
  univariates;
- and: **hog prices need a difference alone, and none jointly**. "Taking
  differences to transform a nonstationary component series into a stationary
  one is not necessary when considering several series jointly. In fact, it
  will lead to unnecessary complexity in the model."

**SCM (1989).** A scalar component is a linear combination v'z_t that follows
a low-order ARMA:
- canonical correlations between the stacked present and the past find them;
- a χ² **criterion table** crit(m, j) gives the overall order;
- a search path gives k components of minimal orders, and so a parsimonious
  and identifiable model, with "exchangeable" representations recognised.

The flour-price example (three cities, monthly 1972–1980, data in Appendix B):
- an ARMA(1,1) whose transformed components separate a common trend from
  local spreads;
- the trend is the non-stationarity of all three series: the ancestor of a
  cointegration reading.

drvarma's echelon note (§3.5) records why Lütkepohl and Poskitt prefer echelon
forms: inference with a data-dependent transformation is problematic, and this
package's output is t-ratios and bands. The SCM belongs to phase 2's
comparison, not here.

## 2.bis Box and Tiao (1977), the canonical analysis

**The idea.** Take a VAR(p), z_t = ẑ_{t−1}(1) + a_t, so that Γ₀(z) = Γ₀(ẑ) + Σ:
the variance is the predictable part plus the innovations. The predictability
of a combination u_t = m′z_t is

    λ = m′Γ₀(ẑ)m / m′Γ₀(z)m                                          (2.2)

so the combinations come from the eigen-analysis of Γ₀(z)⁻¹Γ₀(ẑ), with
λ₁ ≤ … ≤ λ_k in [0, 1]. For the VAR(1), Γ₀(ẑ) = φΓ₀φ′, and the matrix is
Q = Γ₀⁻¹φΓ₀φ′ (3.2). The k canonical components y_t = Mz_t are:
- ordered from least to most predictable;
- contemporaneously independent, in both their predictable parts and their
  innovations (2.5).

**The two ends:**
- **λ ≈ 0, white components.** If k₁ roots are zero, y₁t = b₁t:
  - k₁ "static" relations among the original variables,
    Σ m_ji z_it = constant + white noise (2.9);
  - relations that "remain stable over time".
- **λ → 1, near non-stationary components.** For the VAR(1), k₂ of the λ_j
  tend to 1 *if and only if* k₂ eigenvalues of φ approach the unit circle
  (Appendix). These components are "composite indicators of the overall
  dynamic growth".

  In general (3.6) the vector splits into three parts: white noise, stationary,
  and near non-stationary. Each part's predictable part depends only on the
  parts before it.
- **The variance components** (3.4, 3.8). Scaled so that every component has
  unit variance, the j-th row of the transformed φ sums to λ_j. The table of
  proportional contributions (their Table 4.3) says what each component owes
  to each component's past, and what (1 − λ_j) it owes to its own shock.

**The hog data** (Quenouille's 5 series, 82 years, logged and coded; series 2
and 5 shifted one year). VAR(1) **in levels**, λ = 0.023, 0.142, 0.506, 0.690,
0.887:
- **Two near-white components.** Within their plane, Box and Tiao look for
  combinations "scientifically meaningful" and find two stable laws:
  - farm return over expenditure, H_P·H_S / (R_P·R_S)^0.75·W^0.50 ≈ constant
    (4.6);
  - hog supply against the price ratio, H_S·R_P / H_P ≈ constant (4.8).
- **The most predictable component** is ≈ farm wages + 0.67·hog supply: a
  random walk with drift, the system's growth (4.2–4.3).

**The argument against differencing everything** (§4.4). Individually one
would difference four of the five series. But if the dynamics come from a few
near non-stationary components and stable relations hold among the series,
"differencing all the original series could lead to complications". Their
example (4.9): z₁ a random walk, z₂ = βz₁ + a₂. In levels it is a VAR(1);
differenced, w₂ = βa₁ + a₂ − a₂(t−1) carries a non-invertible MA, and "cannot
be put into the autoregressive form". This is the over-differencing that
drvec's documents call the Plosser–Schwert / Hillmer–Tiao signature.

**What it does not settle** (§5):
- λ ≈ 1 also arises when Σ is nearly singular, and how to tell the two cases
  apart was "currently being investigated";
- an exactly singular Γ₀ (identities in the data) needs a principal-component
  analysis first;
- there is no test. Λ is a descriptive reading, and its formal successors
  are Johansen's reduced-rank tests (drvec) and the SCM χ² of 1989.

**Checked.** Table 4.2 is reproducible without the data: from the printed
μ̂, C₀ and C₁ (p. 359), φ̂ = C₁C₀⁻¹ and Q in (3.2) give λ = 0.0232, 0.142,
0.5061, 0.690, 0.8868, against the published 0.0232, 0.1421, 0.5061, 0.6901,
0.8868. The eigenvalues of φ̂ are 0.92, 0.84, 0.52 and a complex pair of
modulus 0.28. (Either orientation of C₁ gives the same λ.)

## 3. What this means for sima

**3.1 The two schools disagree, and sima should show it, not settle it.**
Tiao and Box start from the vector; Jenkins and Alavi from the univariate
models, and then also from the vector, and their conclusion is to use both
(§3.4). sima sits on the ladder: its input is the `.pre` files, and its
yardstick is the univariates. Tiao and Box's §6 is the strongest argument
against making that the ONLY route. sima already has J&A's method 1 on the
vector; what Tiao and Box add is method 1 **carried through**:
- a test (M(l)) where J&A have a guide (S_k);
- a mixed-order tool (ESCC) beside Alavi's S_k(q);
- a reduction step (zeros by coefficient);
- a structural reading (feedback or not).

**3.2 Two warnings sima should carry from these papers:**
- *Feedback read from a low-order fit can be spurious* (gas furnace, Table 14),
  and so can feedback from aggregated data. Any structural verdict needs the
  order adequate first.
- *Differencing each series by its own d is not innocent jointly* (hog data;
  flour). The ladder takes each series' d from its univariate model, which is
  J&A's assumption (§3.3). When two or more series are I(1) and their levels
  may share a component, the joint model may need fewer differences: that is
  drvec's ground (cointegration), and sima should name it and hand over, not
  absorb it. Box and Tiao (1977, §4.4) is the original argument and the
  original tool (§2.bis).

## 4. Proposed work

Engine facts in drvarma (Python first, then C and GUI), the reading in sima.
No new figure designs: Tiao and Box's displays are tables of symbols; the
GraphMaker/drvus panels already plot R_k and S_k.

**A. The stepwise autoregression table.** In `drvarma.identification_mv`, add
`stepwise_ar(x, L)`. For l = 1..L it returns:
- 𝒫(l) and its t-ratios, which moves the old server's `_tiaobox_tratios` into
  the engine;
- M(l) with exactly (4.3) and its p-value;
- diag Σ̂(l) and |Σ̂(l)|;
- optionally, the residual cross-correlation symbols after each fit
  (Table 5).

`identify_matrices` shows it under method 1, next to S_k. This settles the J&A
design's open decision 2: **both** — S_k as the pattern, with its figure, and
M(l) as the test, in the table. With the 1981 paper's own warning: on an MA
the partials need a high p (Table 4).

**B. The structural reading: is the system simultaneous?** After a fit, for
each ordered pair (i ← j):
- the LR test that j's coefficients in i's equation are all zero;
- the triangular orderings the data do not reject;
- the gas furnace warning in the text: the verdict is only as good as the
  order.

If a triangular ordering stands, sima says the system is a transfer network
and offers the hand-back to mtram with the same `.pre` files. Today the seam
works one way only (mtram hands over on a cycle) and nothing checks the cycle.
Their §3.1 also names the general case, lower **block** triangular: a DAG of
simultaneous blocks (the echelon note §5.1).

**C. Simplification by coefficient.**
- `simplify(name, t=…)` lists the cross coefficients with small |t|, proposes
  the restricted model, fits it, and reports the LR against the full one and
  the parameters saved, as a menu.
- It needs zeros per coefficient in the ladder: extend `links` from pairs to
  `"A<-B:ar1,ma2"`. `Ladder._masks` already carries per-parameter masks, so
  only the grammar and the C's `-links` follow.
- J&A's caution stays in the reading: do not create factors that cancel.

**D. ESCC for mixed orders** (Tiao and Tsay 1983). `escc(x, M, J)` gives the
table of symbol matrices, with the triangle's vertex as the suggestion. Under
method 1, beside Alavi's S_k(q): two answers to the same question, (p, q) of a
mixed model. Where they agree, more confidence; where they disagree, both
candidates.

**E. The canonical analysis (Box and Tiao 1977), in two places.** Engine:
`drvarma.identification_mv.canonical(x, p)`. It returns:
- λ₁ ≤ … ≤ λ_k;
- the eigenvectors in the original units;
- the variance-component table (3.8);
- the components as series.

Pure linear algebra on a least-squares VAR(p): its p comes from A's stepwise
table. Two readings in sima:
- **E1, before the ladder, on the transformed levels** (each series' λ, no
  differencing). When ≥ 2 series have d ≥ 1, count the components with λ near
  1 against the number of differenced series:
  - fewer means there are stationary combinations of the levels: the joint
    model may need fewer differences than the univariates. sima says so, shows
    the combinations, and names drvec, where Johansen's test is the formal
    decision;
  - λ near 0 points to static relations (or accounting identities, or a
    near-singular Σ: §5's caveat, said in the text).

  A reading, not a test, and **sima does not change any d**: the d belongs to
  the `.pre`, and changing it is a decision for drvec or art.
- **E2, after a fit, on w_t** (Tiao and Box 1981, §6: the eigen-analysis of
  Γ(0), Σ and Γ(0) − Σ of the fitted model). Which combinations of the series
  the system predicts, and how well: the multivariate gain read as structure,
  beside `forecast_uncertainty`'s Table VIII. Optional, after E1.

No new figure: the canonical components are series, and they go in the
existing series panel (their Fig. 1(b)).

The SCM procedure (1989) is a reference for phase 2's echelon/SCM comparison,
not work here.

## 5. Validation

- **Gas furnace** (Box–Jenkins Series J, public). Reproduce:
  - Table 12(b), M(l) = 1650, 665, 31.7, 22.5, 5.6, 12.9, 1.8, 8.0, 3.5, 0, 2.0.
    Least squares is deterministic, so the match should be close (A);
  - Table 14's spurious feedback at p ≤ 2 and its disappearance at p ≥ 3 (B);
  - the restricted AR(6) (C).

  It is also a cross-rung test: mtram must fit the same transfer function.
- **Their simulated models** (§3.1), with our generator. Check:
  - the VMA(1) cuts off in R_k after lag 1, and its partials and M(l) persist
    to p ≈ 7 (Table 4);
  - the VAR(1) cuts off in M(l) after 1 (Table 3);
  - ESCC finds (1,1) on a VARMA(1,1) (D; 1983, Table 6).
- **Flour prices** (1989, Appendix B: the data are printed, so they can be
  transcribed and checked). The ESCC and the stepwise table on the logs, and
  the joint-differencing warning (E): three I(1) series with one common trend.
- **Muskrat–mink**: the stepwise table on our w_t next to J&A's Table IV and
  Tiao–Box's Table 15. The three treatments of the same data (J&A's
  differencing; Chan–Wallis' detrending, which T&B used; the ladder's `.pre`)
  are a lesson in themselves.
- **Hog data, canonical analysis** (E): already checked from the printed
  moments (§2.bis). The test pins λ, the eigenvectors of Table 4.2 and the
  variance components of Table 4.3 to C₀ and C₁ as printed. The raw series
  (Quenouille 1957) would also give Tiao and Tsay's (1983) ESCC on the same
  data.
- **SCC data**: not printed (Coen, Gomme and Kendall 1969). Only if it turns up.

## 6. Order and decisions

Proposed order: **A → E1 → B → C → D**, with E2 optional.
- A is cheap and settles the J&A design's open decision 2, and the gas furnace
  checks it exactly.
- E1 is cheap too: linear algebra on A's VAR. It is checked already against
  Box and Tiao's own numbers. It answers the ladder's most exposed assumption,
  one d per series.
- B answers a question the ladder already has, at the mtram seam, and the gas
  furnace tests it.
- C needs the ladder's grammar extended.
- D is the most new code.

Decisions (2026-10-02, the study's recommendations accepted):
1. **Scope:** A, E1, B and C now, in that order of work (A → E1 → B → C); D
   (ESCC) later; SCM only as a phase-2 reference.
2. **Simplification threshold** (C): |t| < 1 proposes the restricted model, the
   LR against the full one checks it; always a menu.
3. **Structure** (B): sima reports a triangular ordering that is not rejected and
   OFFERS the hand-back to mtram; it does not hand back on its own. The gas
   furnace warning goes with it.
4. **The canonical analysis** (E1): a reading on the levels that points to drvec
   and never changes a d. Near 1 starts at **√λ ≥ 0.90**, on the scale of a
   root: for an AR(1) component λ = φ² (Box and Tiao's x₅: λ 0.8868, φ 0.94),
   so that 0.90 is art's convention for an MA root, and the threshold on λ
   itself would have asked for a root of 0.95. Calibrate later.
5. **Data and example:** the gas furnace and the hog moments are drvarma test
   data (`tests/data/tiao_box/`, `tests/test_tiao_box.py`). The worked example is
   the **flour prices** (`examples/flour_prices`, `load_example("flour_prices")`):
   it shows A and E1 together, which the gas furnace cannot (both series are
   stationary). Its univariate models were built with art's engine; the hog data
   are not available.

## 7. Done (2026-10-02)

- **A** — `drvarma.identification_mv.stepwise_ar` / `stepwise_order`:
  - reproduces the gas furnace's M(l) (Table 12(b)) to the printed digit for
    l = 1..8, with Tiao and Box's conventions found by trying them: common sample
    t = L+1..n and N = n − L − 1. The last three come out 3.7, 1.0, 4.0 against
    3.5, 0, 2.0, all non-significant;
  - reproduces the residual covariance matrices (Σ̂ = S(l)/(n − L)) and the
    indicator symbols of every fit in Table 14, the spurious feedback at p ≤ 2
    included;
  - shown under method 1 in `identify_matrices`, with the reading against
    S_k's cut-off, and option (d) when they differ.
- **E1** — `drvarma.identification_mv.canonical` / `canonical_from_moments`, and
  `LadderSeries.levels()`:
  - reproduces Box and Tiao's Table 4.2 (eigenvalues and eigenvectors) and
    Table 4.3 (variance components) from the printed moments. Their C₁ is
    E(z_{t−1} z_t′), so φ = C₁′C₀⁻¹: the eigenvalues do not tell the
    orientation, the eigenvectors do;
  - sima's `canonical_analysis` (node N1b), which `run_gate` proposes when two
    or more series are differenced.
- **The flour example**:
  - the canonical analysis finds the common trend and a contrast between
    markets with root 0.87 (Tiao and Tsay's φ = 0.88);
  - on the differences, S_k never cuts off while M(l) says VAR(1);
  - the VAR(1) does not beat the univariates out of sample.

  The structure is in the levels: drvec.
- **B** — `structure` (sima) on `Ladder(zeros=)` (drvarma):
  - the pair tests and the triangular orderings, with mtram offered, never
    taken;
  - gas furnace VAR(6): the ordering gas → CO₂ stands (CO₂ → gas p 0.42);
  - gas furnace VAR(2): the spurious feedback of Table 14 (p < 0.0001);
  - muskrat–mink: feedback both ways.
- **C** — `simplify` and `estimate(zeros=)`: cross zeros on both routes, own
  zeros on route V (in the spec file). On the gas furnace VAR(6), 9
  coefficients go (LR p 0.72, AIC and BIC fall), and a second round is
  offered.
