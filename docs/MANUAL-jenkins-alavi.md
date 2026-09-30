# sima user manual — Jenkins and Alavi's method

*A chapter of the sima user manual. Written 2026-09-30.*

This chapter explains the multivariate method of G. M. Jenkins and A. S. Alavi
(1981), shows how sima implements it tool by tool, and works through their own
example — the muskrat and mink skins of the Hudson's Bay Company — from the two
univariate models built in art to the forecasts. The example ships with sima: in a
conversation, `load_example("jenkins_alavi")` runs it node by node in real
time (3.3); in the repository, `examples/jenkins_alavi/run.py` runs it in one go.

Section numbers in brackets, [§3.4], are the paper's; equation numbers, (3.22),
too.

> G. M. Jenkins and A. S. Alavi (1981), "Some aspects of modelling and
> forecasting multivariate time series", *Journal of Time Series Analysis* 2,
> 1–47.

---

## Part 1 · The method

### 1.1 The model [§2]

A vector of m series, each transformed (Box-Cox) and differenced by its own
operator, w_it = ∇^{d_i} z_it^{(λ_i)}, follows a multivariate ARIMA

    φ(B) (w_t − c) = θ(B) a_t,        Σ = E[a_t a_t']

The diagonal operators φ_ii, θ_ii start with 1: they are, to begin with, the
univariate model of each series. The off-diagonal ones start with a power of
B: they carry what one series does to another, with a delay. The a_t are the
one-step forecast errors: serially random, correlated only at the same time,
through Σ. Σ stands for everything the model leaves out, and its off-diagonal
elements say how much the series' surprises move together.

Jenkins and Alavi build this model **from the univariate models up**. Each
series is modelled alone first, with the univariate tools (transformation,
differencing, ARMA). The multivariate step adds only what the univariate
models do not carry: the cross dynamics and the correlation of the errors.
That is the ATSW ladder: art → mtram → sima.

### 1.2 Identification: two methods, and both [§3.3–3.4]

**Method 1, not prewhitened.** On the stationary series w_t themselves:

* the correlation matrices **R_k**, with element r_ij(k) = corr(w_i,t, w_j,t−k).
  Their standard errors are Bartlett's (3.13), which grow with the
  autocorrelation of each series: two unrelated series with long cycles show
  large cross correlations by chance. A cut-off after lag q suggests an MA(q);
* the partial correlation matrices **S_k**: the last matrix of the AR(k)
  fitted by the multivariate Yule-Walker equations (3.11), standard error
  1/√n. A cut-off after lag p suggests an AR(p);
* the q-conditioned partial matrices **S_k(q)** of Alavi (1973): a cut-off
  after p suggests an ARMA(p, q). Their sampling behaviour is unstable [§4.1]:
  read the cut-off, not the size.

With many series, looking at every element becomes impossible ("the curse of
higher dimensionality"); the determinants |R_k|, |S_k|, |S_k(q)| have the same
cut-off properties and are a first guide.

**Method 2, prewhitened.** Each series is filtered by **its own** univariate
model, and the statistics are computed on the residuals α_t (3.20). If the
univariate models are right, the residuals follow a model

    α_t = u*(B) a_t                                                (3.21)

and the whole system is the univariate models times the residual model:

    w_t − c = u(B) u*(B) a_t                                       (3.22)

After prewhitening the residual model must be a moving average (3.26), so the
cross correlations R_k(α) are the statistic to read: their cut-off gives its
order and which links it has. This is Haugh's (1976) double prewhitening —
each series by its own model — not the single prewhitening of a transfer
function, which filters both series by the input's model and assumes the
influence runs one way.

**Use both.** If the two methods agree, estimate with more confidence. If they
do not, estimate both candidates and choose by what each explains of the
system and by parsimony. Their warning: after prewhitening a cross AR
structure reads as an MA of higher order (Table II), and can lead to
over-parameterisation.

### 1.3 Preliminary estimates [§3.2, §3.4]

The cross AR from the multivariate Yule-Walker equations (3.11) — "very good
approximations to the maximum likelihood estimates". The cross MA of the
residual model from the residual cross covariances: θ_ij,k ≈ −c_ij(k)/c_jj
(their −r_ji(k), with the variances kept). Both are starting values for the
estimation, and a second path to its optimum.

### 1.4 Estimation [§5.1]

Exact maximum likelihood. Parameters small against their standard errors are
then deleted: their (5.8) is "much simpler than the identified structure
(4.9)".

### 1.5 Checking [§5.2]

1. **Large residuals.** The a_it correlate at lag 0, so they cannot be judged
   one by one. Transform them to uncorrelated residuals a*_t = Q' a_t (Q the
   eigenvectors of Σ) and use limits ±2√λ. A large residual with a known cause
   is treated by intervention before anything else is read.
2. **Residual correlation matrices R_k(â)** and partial matrices: what is
   beyond the band is what the model does not carry.
3. **The portmanteau matrix** Q_ij = n Σ_k r_ij(k)². It "does not deserve the
   theoretical attention it has attracted": only the individual matrices give
   clues about how to change the model.

### 1.6 Forecasting [§6]

The covariance matrix of the l-step forecast errors,
V(l) = Σ_j ψ_j Σ ψ_j', gives the standard deviation of the forecast errors of
each series; for series in logs, 100 × it reads as a per cent (Table VII).
**Table VIII** compares it with the univariate models': where it is smaller,
the multivariate model could forecast better.

Two cautions of theirs. V(l) takes the parameters as known, so it measures the
uncertainty with uncertainty. And the real test is forecasting "from a range
of origins using data not used in fitting the model" — which, they write,
"cannot be carried out for the muskrat-mink series" because the forecast
errors are very large for both models and the series are short.

---

## Part 2 · How sima implements it

### 2.1 The starting point: art's univariate models

sima starts from one fue file per series: the `.pre` of the univariate model
built in art (an optimum). Each carries the series' whole univariate model —
Box-Cox, differencing, mean, ARMA factors — which sima keeps on the diagonal.
There is no raw-data entry: the univariate model is the seed of the system and
the yardstick it has to beat.

**The gate** (N1) checks that the diagonal system reproduces the univariate
models exactly: the sum of their log-likelihoods equals the joint one. If a
series is trimmed to the common window (a differenced series loses its first
observation), its model is re-estimated on the shorter sample.

### 2.2 The method step by step

| Jenkins and Alavi | sima tool | node |
|---|---|---|
| univariate models [§4.2] | art, then `load_pre` | N0 |
| — (the ladder's certification) | `run_gate` | N1 |
| method 2: R_k(α), the cross correlations of the prewhitened series | `identify_cross`, `identify_matrices`, `plot_identification(method=2)` | N2 |
| method 1: R_k (Bartlett), S_k, S_k(q), determinants | `identify_matrices`, `plot_identification(method=1)` | N2 |
| preliminary estimates (3.11), (3.12) | `estimate(start="preliminary")` | N3 |
| the residual model (3.22) | `estimate(..., cross="residual")` | N3 |
| exact ML estimation | `estimate` | N3 |
| checking [§5.2] | `check_residuals` | N4 |
| V(l), Table VIII [§6.2] | `forecast_uncertainty` | N5 |
| their §6.3 refit on part of the data | `forecast_uncertainty(estwin=)` | N5 |
| forecasting from a range of origins | `evaluate` | N5 |
| forecasts, impulse responses | `forecast`, `impulse_response`, `variance_decomposition` | N6 |

`estimate` options:

* `p`, `q`: the orders of the CROSS AR and MA; the diagonal is the univariate
  models';
* `links="A<-B, B<-A"`: the cross terms only on those pairs, the ones
  identification found;
* `cross="residual"`: the cross MA as a model for the univariate residuals,
  multiplied by each series' univariate MA — the form (3.22). The default,
  `"additive"`, adds the cross MA; the two are the same when the univariate
  models have no MA factors;
* `start="preliminary"`: the cross terms start at the preliminary estimates.
  Reaching the same optimum from zero and from them confirms it;
* `diagcov=True`: a diagonal Σ, when the errors do not correlate.

### 2.3 The figures

The figures copy the originals the school has used for decades — Treadway's
GraphMaker and drvus, and fue — rather than new designs. They are terse; the
numbers are in the report around them.

* **`plot_identification`**: for each pair of series, the **ccf** (R_k,
  two-sided, lag 0 included) above the **pccf** (the cross elements of S_k,
  two-sided; no lag 0), on the same lag axis and scale — as fue's acf over
  pacf. The panel is GraphMaker's CCF: bars, dotted ±2 standard-error bands, a
  dashed vertical at lag 0. The pair is titled **"A − B": A leads at k > 0**,
  the other at k < 0. Between the panels, for method 2, **Haugh's S\***:
  "S* ( d.f. ) = value". For method 1 the ccf band is Bartlett's and follows
  the lag, and there is no portmanteau (the series are not white). With three
  or more series each pccf comes from the VAR of all of them — it is given the
  other series — and `pairs="A-B, A-C"` draws only those chosen.
* **`check_residuals`** draws what drvus drew in its diagnosis (and their
  figure 7): fue's panel for each residual series — the residuals with ±2
  bands, the acf with its Q, the pacf — and the residual ccf of each pair, with
  Hosking's portmanteau labelled **P**, as GraphMaker did, "so as not to
  confuse it with Ljung-Box's Q".

**Degrees of freedom.** GraphMaker's P has 4(K − (p + q)) degrees of freedom
for a pair, p + q the largest AR plus the largest MA order of the model; the
acf's Q has K − npar. In annual data with long models the legacy numbers of
lags leave none. sima keeps **at least 2 lags beyond the parameters**: Q with
at least 2 degrees of freedom, a pair's P with at least 8. Even so, these
statistics have little power there: the individual bars against the band are
what to read.

### 2.4 The reports

Every tool that draws answers as art does, in four sections, and then the
figure:

1. **TABLE** — the numbers, as a block to be shown as it is;
2. **WHAT IT SHOWS** — per pair and side, the bars beyond the band, who leads,
   the cut-off, the isolated lags, the statistic and its p-value;
3. **CONCLUSIONS** — the method's reading;
4. **DECISION** — the alternatives, each with its call, and a pause (⏸).

In the guided lane the analyst decides at every pause; in the autonomous one
the assistant decides and writes why (`record_decision`). The tools never
decide. `export_guion` shows the path, node by node, with the evidence and the
decisions.

### 2.5 What sima does not do (yet)

* **Deleting single parameters.** Jenkins and Alavi deleted the small ones
  after estimation. sima restricts cross terms by pair (`links`), but cannot
  yet fix an individual own parameter of a series at zero inside the system.
* **The echelon form** (Kronecker indices) is phase 2, built on these
  statistics.

---

## Part 3 · The worked example: muskrat and mink

### 3.1 The data

Muskrat and mink skins traded annually by the Hudson's Bay Company (Jones
1914), 62 observations, in `examples/jenkins_alavi/data/mink_muskrat.csv`.
The mink is an important predator of the muskrat (Errington 1943).

**Dating.** Jenkins and Alavi date the series 1848–1909; Reinsel (1997) and
Mauricio (2006), where this file comes from, date the same 62 values
1850–1911. Every date below is **two years later** than the paper's: their
1906 is our 1908.

### 3.2 The univariate models, in art

Built in art's guided lane (`art/MUSKRAT_m03.pre`, `art/MINK_m02.pre`, with
their `.out`):

| series | model | art | Jenkins and Alavi |
|---|---|---|---|
| muskrat | ARIMA(6,1,1) on ln z | φ 0.65 −0.58 0.22 −0.31 −0.04 −0.32; θ 0.55; σ 28.1 % | φ 0.65 −0.60 0.23 −0.34 −0.06 −0.38; θ 0.54; σ 28.7 % |
| mink | AR(4) on ln z, with mean | φ 0.80 −0.21 0.00 −0.27; mean 10.82; σ 25.7 % | φ 0.82 −0.22 0.00 −0.28; mean 10.79; σ 26.1 % |

The muskrat needs a difference (its upward trend); the mink does not —
differenced, it needs an MA with θ close to 1, over-differencing. Factorised,
the mink's AR(4) has a 10.1-year cycle (damping 0.88) and a 2.9-year one; the
muskrat's AR(6) has cycles of 10.3, 4.2 and 2.6 years (damping 0.95, 0.84,
0.71). They report 10.2 and 2.9, and 10.3, 4.2 and 2.6: the ten-year cycle the
two species share.

### 3.3 Running it

**As a script**, the whole walkthrough, each report to `out/NN_<tool>.md` and
each figure to `out/figs/`:

    python3 examples/jenkins_alavi/run.py            # all of it
    python3 examples/jenkins_alavi/run.py --upto 6   # up to the identification

**In a conversation with sima**, in real time — the way to learn it. Ask the
assistant for the example, or call:

    examples()                       # what examples there are
    load_example("jenkins_alavi")    # the files, copied to ~/sima-examples/, loaded

and go on node by node from `run_gate("jenkins_alavi")`, deciding at every
pause. The assistant follows the tutorial, `sima://example/jenkins_alavi`:
after each report it adds what Jenkins and Alavi found at that step and where
this manual explains it. The tools answer exactly as in any analysis.

### 3.4 The walkthrough, with the paper's numbers

**N1 · Gate.** Passed (difference −1.1e-13). The common window starts in 1851:
the muskrat loses its first observation to the difference, and the mink's
model is re-estimated on 61 observations.

**N2 · Identification, method 2** (the univariate residuals):

| | sima | Jenkins and Alavi |
|---|---|---|
| r(0) | +0.38 | +0.42 ± 0.13 |
| MINK leads, k = +1 | −0.36 | negative at lag −1 |
| MUSKRAT leads, k = −1 | +0.35 | positive at lags 0 and 1 |
| Haugh S*(21) | 45.7, p = 0.001 | — |

More mink this year, fewer muskrat next year (predation); more muskrat, more
mink next year (food). The ccf cuts off after lag 1 on both sides: an **MA(1)
residual model** on both links — their (4.8). By side, S* = 14.9 (p = 0.14)
when the mink leads and 22.1 (p = 0.015) when the muskrat leads.

**N2 · Identification, method 1** (the stationary series ∇ln muskrat, ln
mink). Their Table IV is reproduced — R_k exactly, S_k within a few hundredths: r(0) = −0.33
(theirs −0.33); R_1 = [0.22 −0.64; 0.03 0.65] (theirs the same, with the cross
elements transposed: their r_ij(k) is corr(w_i,t, w_j,t+k)); S_1 = [0.01 −0.64;
0.28 0.74] (theirs [0.01 −0.60; 0.30 0.74]); S_2 = [−0.21 0.32; −0.01 −0.13]
(theirs [−0.21 0.30; −0.01 −0.13]). The ccf of these series
waves with their common ten-year cycle and does not cut off; the **pccf cuts
off after 2**: a **cross AR(2)** — their (4.10), (5.9). The Yule-Walker
preliminary estimates of the cross terms: −0.73 and +0.30 of the mink on the
muskrat, +0.23 of the muskrat on the mink.

**N3 · The two candidates**, estimated with the full covariance, from zero
and from the preliminary estimates (the same optimum both ways):

| | A · MA(1) residual model (3.22) | B · cross AR(2) |
|---|---|---|
| cross terms | MA1[MUSKRAT←MINK] 0.38 (0.19), MA1[MINK←MUSKRAT] −0.52 (0.12) | AR1[MUSKRAT←MINK] −0.54 (0.17), AR2 +0.40 (0.16); AR1[MINK←MUSKRAT] +0.46 (0.12), AR2 −0.09 (0.13) |
| log-likelihood | −561.26 (16 parameters) | −558.76 (18 parameters) |
| LR against the univariates | 36.2, 3 d.f. | 41.2, 5 d.f. |
| error correlation | 0.47 | 0.41 |
| AIC / BIC | 1154.5 / 1188.3 | 1153.5 / 1191.5 |
| the paper | (4.8): −0.49 and +0.48 at lag 1 | (5.9): −0.73, +0.41; +0.37, −0.24 |

(With the MA written a = α − θ α_{t−1}, A's 0.38 is a negative effect of a mink
shock on the muskrat, their −0.49.) The two are as close in sample as they were
for Jenkins and Alavi. In A the muskrat's own φ₁ and θ become small with large
standard errors (0.09 ± 0.70, −0.18 ± 0.76): the cross MA takes the role of
the muskrat's own MA — the kind of parameter they deleted in (5.8).

**N4 · Checking.** Both candidates are clean: no residual correlation beyond
the band (A: one, of 1.2 expected by chance), no significant portmanteau. The
largest residual is **1908** — the muskrat −3.6 to −4.0 s.d., the mink −2 —
their **1906** (−3.9 and −1.9); the others, 1870, 1885 and 1899, are their
1868, 1883 and 1897. They did not intervene ("it would be interesting to know
what caused" it), and neither does the example.

**N5 · Table VIII, on all the data** (per cent standard deviation of the
forecast errors, univariate → model):

| lead | muskrat, B | mink, B | muskrat, A | mink, A |
|---|---|---|---|---|
| 1 | 28.8 → 25.5 | 26.2 → 23.2 | 28.8 → 29.3 | 26.2 → 21.6 |
| 2 | 43.0 → 37.2 | 33.6 → 32.4 | 43.0 → 44.9 | 33.6 → 33.0 |
| 3 | 46.3 → 42.0 | 35.4 → 35.4 | 46.3 → 49.5 | 35.4 → 36.8 |

B lowers the uncertainty of both series at every lead; A only the mink's at
short leads. Jenkins and Alavi forecast with the AR structure, B.

**N5 · Their experiment [§6.3].** They refitted the univariate models and the
AR structure on 48 observations (their 1848–1895, our 1850–1897) and compared
V(l) — their Table VIII. `forecast_uncertainty(estwin=48)`:

| lead | muskrat, univariate: sima / theirs | muskrat, bivariate: sima / theirs | mink, univariate: sima / theirs | mink, bivariate: sima / theirs |
|---|---|---|---|---|
| 1 | 25.7 / 25.6 | 18.2 / 19.2 | 26.2 / 25.9 | 22.0 / 24.2 |
| 2 | 38.7 / 38.6 | 28.3 / 32.7 | 31.6 / 31.8 | 28.4 / 31.2 |
| 3 | 41.1 / 40.8 | 35.5 / 41.9 | 32.5 / 32.9 | 29.5 / 34.1 |

The univariate refits agree with theirs (6.10), (6.11) to a few hundredths
(muskrat φ 0.72 −0.68 0.34 −0.42 0.14 −0.39, θ 0.59; theirs 0.73 −0.71 0.36
−0.46 0.15 −0.45, 0.60), and so do the cross terms of B with their (6.12):
−0.71 and +0.51 of the mink on the muskrat (theirs −0.75, +0.36), +0.54 and
−0.47 of the muskrat on the mink (+0.36, −0.51). sima's bivariate V(l) is
smaller than theirs because sima keeps the full univariate operators on the
diagonal, where their (6.12) was simplified.

**N5 · What they could not run: the forecasts from every origin.**
`evaluate` estimates on the same 48 observations, holds the parameters fixed
and forecasts from each of the 14 origins 1898–1911. The ratio is the model's
RMSE over the univariate models' (below 1, the model gains):

| | h = 1 | h = 2 | h = 3 |
|---|---|---|---|
| muskrat, B | 1.016 | 1.026 | 1.035 |
| mink, B | 1.383 | 1.422 | 1.324 |
| muskrat, A | 1.054 | 1.007 | 0.983 |
| mink, A | 1.082 | 0.988 | 0.996 |

B, the model that lowers V(l) by a quarter in sample, forecasts worse in every
cell; A ties with the univariate models.

### 3.5 What the example says

* sima reproduces Jenkins and Alavi's analysis from the univariate models up:
  their univariate models, both identifications (Table IV, the prewhitened
  ccf), both candidates (5.8) and (5.9), the large residual of 1906, and their
  Table VIII.
* The predator–prey interaction is real: both methods find it at lag 1, and
  both candidates improve the likelihood by far (LR 36 and 41).
* In sample the system promises better forecasts (Table VIII). Out of sample,
  with 48 years to estimate 16–18 parameters, it does not deliver them. That
  is sima's rule 1 at work: **the univariate models are the yardstick**, and a
  model whose cross terms do not forecast better is a finding, not a model to
  forecast with. B remains the structural description — their Lotka–Volterra
  reading (5.10): the muskrat's growth falls with last year's mink, and the
  mink rises with last year's muskrat.
* Jenkins and Alavi foresaw it: the demonstration "cannot be carried out" with
  errors this large and series this short. sima can run it, and it says why
  they were right to be cautious.

---

## References

* Errington, P. L. (1943). An analysis of mink predation upon muskrats in
  North-Central United States. *Research Bulletin, Iowa Agricultural
  Experiment Station* 320, 799–924.
* Haugh, L. D. (1976). Checking the independence of two covariance-stationary
  time series: a univariate residual cross-correlation approach. *JASA* 71,
  378–385.
* Jenkins, G. M. and Alavi, A. S. (1981). Some aspects of modelling and
  forecasting multivariate time series. *JTSA* 2, 1–47.
* Jones, J. W. (1914). *Fur-farming in Canada*. Commission of Conservation,
  Ottawa.
* Mauricio, J. A. (2006). Exact maximum likelihood estimation of partially
  nonstationary vector ARMA models. *CSDA* 50, 3644–3662.
* Reinsel, G. C. (1997). *Elements of Multivariate Time Series Analysis*, 2nd
  ed. Springer.
