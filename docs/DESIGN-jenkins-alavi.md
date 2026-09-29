# Jenkins and Alavi (1981) from the ladder — design, phase 1

**Status: a design to be argued with, not a plan yet.** Written 2026-09-29.
Phase 1 of the road to the echelon VARMA: the identification, estimation and
checking framework of the school's multivariate stochastic (MS) model, built on
what the ladder already is. Phase 2, the echelon form (Kronecker indices), is
drvarma's `docs/ECHELON_SEEDED_DESIGN.md` and Gómez (2019); it will rest on the
statistics of this phase.

Reference: G. M. Jenkins and A. S. Alavi (1981), "Some aspects of modelling and
forecasting multivariate time series", *Journal of Time Series Analysis* 2,
1–47 (in `drvarma_source/literature`). Section numbers in brackets are the
paper's. It is the school's base: Relloso (1997, ICAE 9720) calls it and Tiao and
Box (1981) "the two basic works" of the MS methodology, and Muñoz Polo (2001,
Treadway's thesis) writes that her research "did not need multivariate methods
more complex than those set out by Alavi and Jenkins".

---

## 1. The vision of Jenkins and Alavi

**The model** [§2]. A vector of series, each transformed (Box-Cox) and
differenced by its own operator, w_it = ∇^{d_i} z_it^{(λ_i)}, follows a
multivariate ARIMA

    φ(B)(w_t − c) = θ(B) a_t,       Σ = E[a_t a_t']

where the DIAGONAL operators φ_ii, θ_ii lead with 1 and the OFF-DIAGONAL ones
with a power of B. The a_t are the one-step forecast errors: serially random,
correlated only at the same time (Σ), which stands for everything left out of
the model. Seasonality is best confined to the diagonal — **multiplicative
diagonals** [§2.3]: what happens this month in series i is unlikely to depend on
series j twelve months ago.

**Identification: two methods, and both** [§3.3–3.4].

* *Method 1, no prewhitening*, on the stationary series w_t:
  - correlation matrices R_k, compared with Bartlett's standard errors (3.13),
    which grow with the autocorrelation of each series — a cut-off after q
    suggests MA(q);
  - partial correlation matrices S_k: the last matrix of the AR(k) fitted by
    the multivariate Yule-Walker equations (3.11), standard error 1/√n — a
    cut-off after p suggests AR(p);
  - q-conditioned partial correlation matrices S_k(q) (Alavi 1973): the last
    matrix of (3.14) solved from lag q + 1 on — a cut-off after p suggests
    ARMA(p, q);
  - with many series (they worked with up to 8), the determinants |R_k|,
    |S_k|, |S_k(q)| first, as scalar guides with the same cut-off properties
    ("the curse of higher dimensionality").
* *Method 2, with prewhitening*: the same statistics on the residuals a_it of
  UNIVARIATE models fitted to each series separately. The cross correlations
  are then free of the autocorrelation that distorts them (the argument of
  transfer-function prewhitening, §3.4) and compare with 1/√n. A model u*(B) is
  identified for the residual vector, a_t = u*(B) α_t, and combined with the
  univariate ones, u(B) diagonal:

      w_t − c = u(B) · u*(B) · α_t                                    (3.22)

**When each method misleads** [§3.4, "Some general conclusions"]. For a
multivariate MA the univariate orders are ≤ q, so the diagonal is identified
right by the univariate models and the prewhitened cross correlations give the
off-diagonal MA — prewhitening helps. With an AR structure it does not: every
multivariate ARIMA can be written with a DIAGONAL AR equal to |φ(B)| in every
equation and an MA of higher order (3.26–3.28), so fitting the univariates
first leads towards that representation — a mis-specified AR structure and
over-parameterisation (their Series 2: prewhitening led to a wrong
identification). Their conclusion: use both; if they agree, estimate with more
confidence; if they reveal different AR structures, choose by (i) how far each
illuminates the system and (ii) parsimony. And since it is wise to proceed
gradually, **the univariate models are fitted first**, which makes both
identifications cheap.

**Preliminary estimates** [§3.2]. AR: the Yule-Walker estimates (3.11), close to
the ML ones. MA from the prewhitened residuals, assuming ρ₁₂ small and
σ₁ ≈ σ₂: unit diagonal and θ_ij,k ≈ −r_ji(k). When nothing better is at hand,
the univariate models for the diagonal and small off-diagonal values.

**Estimation** [§5.1]. Exact likelihood recommended. Near the invertibility
boundary it is "not wise to describe the likelihood function by its maximum in
any case", and the standard errors lose their meaning — the stance the ladder
and sima already take on the MA wall.

**Checking** [§5.2]. (1) Plot the residuals with ±2σ; large ones distort
structure, estimates, correlations and forecasts, and are treated by
intervention analysis. Since the a_it correlate at lag 0, also plot the
UNCORRELATED transformed residuals a*_t = Q'a_t (Q the eigenvectors of Σ̂,
limits ±2√λ_i). (2) Residual correlation and partial correlation matrices, as
in identification; a portmanteau matrix Q_ij = n Σ_k r_ij(k)² exists, but "it is
usually only the individual matrices which can provide clues". (3) Elaboration:
add parameters where suspected, without creating factors that cancel.

**Forecasting** [§6]. V(l) = Σ + ψ₁Σψ₁' + … ; the per cent standard deviations
of the forecast errors at lead times 1, 2, 3 compared with the univariate
models' (their Table VIII); and "a large number of forecast origins would be
needed to demonstrate the forecasting superiority" of a multivariate model.

## 2. The ladder is already Jenkins and Alavi's path

| Jenkins and Alavi | the ladder / sima today |
|---|---|
| univariate models first, each series with its λ and d [§3.3, §3.4 end] | the `.pre` files from art/fue; nothing about them re-implemented |
| multiplicative diagonals: seasonality on the diagonal [§2.3] | each series keeps its whole univariate model on the diagonal |
| u(B), the diagonal of univariate models | the diagonal system, certified by the GATE (it reproduces the univariates) |
| prewhitened residuals a_it | the residuals of the diagonal system (N2 reads their CCFs) |
| method 2: R_k of the residuals | pairwise CCFs only; no matrix view |
| method 1: R_k, S_k, S_k(q) of w_t | nothing in sima (the old sima had R_k and Tiao-Box t-ratios) |
| the residual model combined: w − c = u(B)u*(B)α (3.22) | cross terms ADDED to the diagonal operators (cross AR up to p, cross MA up to q, `links`) |
| preliminary estimates | cross terms start at 0 |
| exact likelihood; distrust the maximum near the boundary | exact ML (elf/Shea); the MA wall reported; `study_estimation` |
| residual matrices, uncorrelated residuals, Q_ij, elaboration | Hosking Q; residual CCF figure |
| V(l) against the univariates; many origins | `evaluate`: fixed-parameter forecasts from every origin (more than they had) |

So both of their methods start FROM the ladder: method 2 on the residuals of
the diagonal system, method 1 on the w_t of the same `.pre` files, with the λ
and d the univariate analysis decided (which is exactly their assumption,
§3.3). What is missing is the identification statistics as matrices, the second
method, the residual-model form of the combination, the preliminary estimates,
and part of the checking.

**One difference worth stating.** In (3.22) the cross structure enters through
the residual model, MULTIPLIED by the univariate operators:

    φ_d(B)(w_t − c) = θ_d(B) · U*(B) · α_t,      U*(B) = I − U₁B − … − U_qB^q

so the MA of equation i is θ_ii(B) times row i of U*(B). The ladder instead
adds a cross MA polynomial −Σ e_ij,k B^k. The two coincide when the univariate
models have no MA factors (their butter–margarine model (5.11) is of this kind:
random walks and AR(1)s). When they have them — an airline, (1 − θB)(1 − ΘB¹²) —
they differ: in (3.22) a cross effect at lag k is filtered by the univariate MA
of the receiving series, seasonal factor included; in the ladder it acts at lag
k only. And since prewhitened residuals of well-identified univariate models
must have an MA structure (3.26), the residual model u*(B) is an MA: the cross
AR of the ladder belongs to method 1's alternative, not to (3.22).

## 3. Proposed work, phase 1

Engine facts in drvarma (C where the C is the oracle, Python), the reading in
sima, as always.

**A. Identification statistics** (drvarma, a module `identification_mv`):
- `corr_matrices(x, K)`: R_k, with Bartlett's standard errors (3.13) or 1/√n
  when the input is prewhitened; the symbol table + − . as in Tiao-Box.
  (The old sima's `_ccm_values` moves here.)
- `partial_corr_matrices(x, K)`: S_k by the multivariate Yule-Walker equations
  (3.11), standard error 1/√n.
- `q_partial_corr_matrices(x, K, q)`: S_k(q), solving (3.14)–(3.15).
- `det_series(...)`: |R_k|, |S_k|, |S_k(q)| for k = 1..K.
- The old sima's Tiao-Box OLS t-ratios stay available as a second reading of
  S_k (Tiao and Box 1981, the other basic work).

**B. N2 in sima becomes Jenkins and Alavi's identification.**
- N2a, method 2 (prewhitened): R_k of the diagonal residuals, as matrices and
  pairwise (the current CCFs), with the directed pairs and lags that show
  (today's `links` proposal). Suggests the MA order q of the residual model and
  its non-zero elements.
- N2b, method 1 (not prewhitened): R_k, S_k, S_k(q) of the w_t, and the
  determinants when m ≥ 3. Suggests p (and q).
- N2c, the comparison, as a menu: agreement → the candidate with more
  confidence; disagreement → both candidates, with their criteria
  (understanding of the system, parsimony), and the warning of (3.26) whenever
  the evidence points to a cross AR structure read after prewhitening.

**C. The residual-model form in the ladder** (C and Python):
`Ladder(..., cross="additive" | "residual")`. `residual` builds the MA as
θ_d(B)·U*(B) (3.22); `additive` is today's. The cast is the only change; the
likelihood, the gate and the rest do not see the difference. Measure on the
cases where the univariates have MA factors (the ES/FR CPIs, m6) whether the
two forms differ in logL, parsimony and forecasts.

**D. Preliminary estimates for the cross terms**: from the prewhitened R_k (the
MA of the residual model; θ_ij,k ≈ −r_ji(k)·σ_i/σ_j in general, to be checked by
simulation) and from Yule-Walker (the AR). An option to start the ladder there
instead of at zero (`start="zero" | "preliminary"`), which may also settle some
of the path differences seen on m6.

**E. Checking as they do**:
- the residual correlation matrices R_k(â) (and S_k(q, â));
- the uncorrelated transformed residuals a*_t = Q'â_t with ±2√λ_i, for the
  large residuals and their dates (the entry to interventions);
- the portmanteau matrix Q_ij beside Hosking's overall Q.

**F. Forecasting**: next to `evaluate`, the table of per cent standard
deviations of the forecast errors at lead times 1..s from V(l), multivariate
against univariate (their Table VIII). Cheap: the ψ weights and Σ are there.

## 4. Validation

- **Their own data.** Muskrat and mink (Jones 1914; Hudson's Bay Company, 62
  years). The raw skin counts are in the monorepo, tracked:
  `atsw-gui/engines/drvec/datasets/mauricio/mink_muskrat.csv` (1850–1911, as
  in Reinsel 1997; theirs is 1848–1909). drvec's `tests/fixtures/mmpre.*.pre`
  are placeholders (random walks, λ = 1), not these univariate models: the
  univariate models are built first in art, as an analyst would, which also
  exercises the whole chain art → ladder → sima. What they publish to check against: the
  univariate models (an ARIMA(6,1,1) for ∇ln muskrat, an AR(4) for ln mink),
  the prewhitened r(0) = 0.42 ± 0.13, Table IV (R_k and S_k, k ≤ 6), and the
  two final models (5.8) and (5.9) with |Σ̂| = 0.00331 and 0.00378. Their
  estimates use a back-forecasting likelihood, so numbers will differ
  slightly; the structures and the ranking should not.
- **A second look at the same data**: Chan and Wallis (1978), "Multiple time
  series modelling: another look at the mink–muskrat interaction", *Applied
  Statistics* 27, 168–175 (in `drvec/literature`), who revisit Jenkins (1975)
  — a second reference for the structures and the univariate models.
- **Their simulated series** (4.1)–(4.3): simulate with our generator and
  check that the statistics show the patterns they describe (MA(2) cut-off;
  AR(2) cut-off in S_k, and the mis-identification after prewhitening; the
  ARMA(2,1) in S_k(1)).
- **The school's cases**: the ES/FR CPIs, m6, and the thesis series, where
  the residual form (C) and the preliminary estimates (D) are measured.

## 5. Open decisions

1. The residual form (C): in the C as well (the C stays the oracle), or first
   in Python and measured?
2. S_k: Jenkins and Alavi's Yule-Walker with 1/√n as the main reading, the
   Tiao-Box OLS t-ratios as a second one — or the other way round?
3. The order of work proposed: A → B → E → D → C → F (statistics first, since
   everything reads them; the residual form last, once there is evidence to
   measure it with).
