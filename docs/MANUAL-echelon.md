# sima user manual — the echelon form

*A chapter of the sima user manual. Written 2026-10-12.*

This chapter explains the third of sima's identification forms, the echelon
VARMA of Lütkepohl and Poskitt (1996). It shows how sima finds its Kronecker
indices and fits it. It works the form through on their own example, the
flour prices: in a conversation, `load_example("lutkepohl_poskitt")` runs it
node by node; in the repository, `examples/lutkepohl_poskitt/run.py` runs it
in one go. Then on Box and Jenkins' gas furnace, the data of Tiao and Box's
example. The other two forms are Jenkins and Alavi's
(`MANUAL-jenkins-alavi.md`) and Tiao and Box's (`STUDY-tiao-box.md`), each
with its worked example.

> H. Lütkepohl and D. S. Poskitt (1996), "Specification of echelon-form VARMA
> models", *Journal of Business & Economic Statistics* 14, 69–79.

---

## Part 1 · The method

### 1.1 Why another form

A VARMA(p, q) with the same orders for every series is not identified when
some series need less: the spare orders allow common factors, the likelihood
is flat along them, and the optimiser stops wherever its path ends. The
measured symptoms are an MA root on the invertibility wall and a fit whose
likelihood is below that of a model nested in it (drvarma
`docs/STUDY-echelon-rows.md`). The echelon form is the unique
parameterisation of a VARMA system: each series has its own degree, the
**Kronecker index** n_i, and a fixed table says which coefficients are free.

### 1.2 The form

    A_0 w_t + A_1 w_t-1 + ... = A_0 a_t + M_1 a_t-1 + ...

Row i has degree n_i. Its own AR and MA run to lag n_i. Its cross terms
follow Lütkepohl and Poskitt's table (their 2.3):

    n_ij = min(n_i + 1, n_j)  for j < i,     min(n_i, n_j)  for j >= i

- the cross AR on series j sits at the HIGH lags n_i − n_ij + 1 .. n_i;
- the cross MA at lags 1..n_i;
- A_0 is lower triangular, with a contemporaneous term AR0[i<-j] when j comes
  before i and n_j > n_i.

**The order of the series is part of the model**, because A_0 is triangular.
With equal indices nothing is restricted and A_0 = I: the echelon form is the
VARMA(n, n).

### 1.3 Why the univariate models do not give the indices

Every component of a system with indices n has a marginal ARMA(N, N), with
N = Σ n_i (the McMillan degree), unless roots cancel. So the univariate
orders measure N, not each n_i. drvarma's stage 0 tested it: the univariate
seed found the indices in 0–49 % of simulated systems
(`docs/STUDY-echelon-seed.md`).

### 1.4 Finding the indices [§3]

- **Stage I**: a long VAR(h), h by AIC. Its residuals stand for the
  innovations.
- **Stage II**: for each candidate n, least squares row by row on the echelon
  form, with the stage I residuals as the MA regressors and (w_t − ε̂_t) as
  A_0's. The criterion is log|Σ̃(n)| + c_T · dim(n) / T, with c_T = log T
  (SC) or 2 log log T (HQ).
- **Stage III**: exact maximum likelihood, from the stage II estimates.

---

## Part 2 · How sima implements it

### 2.1 Both routes, and the row factor

On route V (`write_specs`) each series' file carries its transformation, and
the system gives it a free AR(n_i)/MA(n_i) of its own.

On route U each series brings its univariate model, and two things change
(drvarma `docs/ECHELON_PLAN.md` §4).

- **The regular ARMA is replaced** by the row's free AR(n_i)/MA(n_i). The
  univariate orders are not the indices (§1.3).
- **The seasonal and fixed-frequency factors become the row's FACTOR.**
  They multiply the whole row, cross terms included:

      F_i(B) [A(B) w]_i = G_i(B) [M(B) a]_i

  The table keeps its meaning, because the echelon part of each row is
  still of degree n_i.

Putting the univariate model on the diagonal as it is does not work. Its
degree is the row's, so the table's high cross lags lose their meaning. On
muskrat and mink, the larger form (3, 1) ended below (2, 1).

A factor on a whole row is an a priori simplification. Lütkepohl and Poskitt
accept one only when it is checked, so `estimate` checks it.
**THE ROW FACTOR'S CHECK** is an LR against the same rows with every
position the factored product reaches free (own and cross). That fit starts
at the factored optimum, so the LR cannot be negative. When the factor is
rejected, compare the form with route U's VARMA(p, q), whose cross terms
are not filtered by the seasonal factors.

### 2.2 `identify_echelon(max_index=3, criterion="SC")`

On route U the search runs on each row filtered by its factor,
(F_i/G_i)(B) w. Unfiltered, it misses: on simulated quarterly systems it
found the indices in 0–6 % of the replications.

The univariate factors are not the rows' factors when a series' marginal
mixes the others'. So the search runs in passes (drvarma
`search_row_factors`):
1. the first pass uses the univariate factors;
2. each next pass fits the previous choice by exact ML, which estimates
   the factors jointly, and searches again with those;
3. the passes stop when the choice repeats, and the report lists them.

On drvarma's simulated systems (`docs/STUDY-echelon-rowfactor.md`):
- one search with the univariate factors found (2, 1) in 28 % of the
  replications;
- the passes found it in 88 %, and the indices in 84–100 % in 16 of the
  18 cells.

It prints the criterion table, every candidate with its dimension,
log|Σ̃|, HQ and SC, and gives the choice with a menu:
- (a) fit it;
- (b) compare it with the VARMA(p, q) of `identify_matrices`;
- (c) the other criterion's choice, when it differs.

What drvarma measured (`docs/STUDY-echelon-search.md`), and sima does:
- **SC is the default**; HQ overfits.
- **Each candidate gets one round of Hannan and Kavalieris' (1984)
  correction**: its residuals recomputed from its own stage II model, and
  stage II again. Without it the search does not improve with the sample.
- **Every candidate is fitted** while there are at most 256 (1.3 s for three
  series and max_index 3). Beyond that, Hannan and Kavalieris' two steps.
- **The result**: the true indices in 80–97 % of the simulated generic
  systems on average, more with more data. Weak cross dynamics are missed:
  the search underfits, and `check_residuals` then shows what is left.

### 2.3 `estimate(name, indices="2, 1")`

It writes each series' spec with its own AR(n_i)/MA(n_i), fits the Ladder
with `echelon=n`, and reports as any fit does: the parameters (AR0 terms
included), the LR against the system without cross terms, the residuals.

Exact ML starts at the stage II estimates, A_0 included. That is the form's
default, and what makes large systems work. On a five-dimensional simulated
system, 20 % of the fits from zero ended below the true parameters, and none
from this start. MA roots that least squares leaves outside the unit circle
are pulled inside first, and the report says so.

`links` and `zeros` restrict the form further. `simplify`, `structure`,
`check_residuals`, `evaluate`, `forecast` and `study_estimation` work on it
as on any fit.

### 2.4 What sima does not do (yet)

- **Choosing the order of the series.** The indices are those of the files'
  order. To try another order, open the data with the series in that order.

---

## Part 3 · The worked example: Lütkepohl and Poskitt's flour prices

### 3.1 The data and the route

The flour price indices of Buffalo, Minneapolis and Kansas City, monthly,
1972–1980 (Tiao and Tsay 1989). Lütkepohl and Poskitt (§4.1) use "rates of
change (first differences of logarithms)" and build no univariate models:
route V.

    load_example("lutkepohl_poskitt")          # the table, loaded
    characterize(...); write_specs(...); run_gate(...)

### 3.2 The indices

`identify_echelon(max_index=6)`: SC and HQ choose **(0, 0, 0)**, with
(1, 1, 1) second; AIC, from the same table, chooses (1, 1, 1). Their Table 1
gives the same for the full search: HQ (0, 0, 0), AIC (1, 1, 1). They go on
with (1, 1, 1), "an intermediate value".

### 3.3 The fits

| model | parameters | logL | log\|Σ̃\| | theirs (Table 2) |
|---|---|---|---|---|
| (0, 0, 0) | 5 | −687.91 | | |
| (1, 1, 1), the VARMA(1, 1) | 23 | −659.17 | 4.744 | 4.725 |
| restricted VAR(1), 5 coefficients | 10 | −669.13 | 5.000 | 4.985 |
| restricted MA(1), 5 coefficients | 10 | −670.47 | 5.027 | 5.004 |

(log|Σ̃| on sima's scale, 100 × the differences of the logs; theirs converted.)

- **The (1, 1, 1) overfits**: most of its 18 coefficients are small, and a
  pair of MA roots sits at modulus 0.999.
- **Their restricted models come out with their estimates and standard
  errors** to the second decimal. Each equation depends on the lagged
  changes of Buffalo and Minneapolis only.
- **The search's (0, 0, 0) underfits**: against the restricted VAR(1), LR
  37.6 with 5 df, though Hosking's Q does not reject its residuals.
- **Out of sample** the restricted VAR(1) gains little over the univariates
  (RMSE ratios 0.94–1.03).

### 3.4 What the example says

The search gives a starting point, not a verdict. On these data both criteria
underfit, as theirs do. The fits, the LR between them and the restrictions
lead to a small identified model: five coefficients, against the 14
parameters of Tiao and Tsay's scalar-component model. The tutorial,
`sima://example/lutkepohl_poskitt`, follows it step by step.

---

## Part 4 · On Tiao and Box's data: the gas furnace

### 4.1 The data and the route

Box and Jenkins' Series J: the input gas rate and the output CO2, 296
observations, in levels (d = 0, λ = 1 for the CO2). Route V, as in Tiao and
Box:

    load_data("gf", "gas_furnace.csv", freq=1, start="1000")
    characterize("gf", set="InputGasRate: d=0; CO2: lam=1, d=0")
    write_specs("gf"); run_gate("gf")

### 4.2 The indices

    identify_echelon("gf", max_index=6)

SC chooses **(2, 2)** (log|Σ̃| 12.27, SC 12.59) and HQ **(3, 2)**. The
long VAR has h = 6, Tiao and Box's order.

### 4.3 The fits

| model | parameters | logL | AIC | BIC | Hosking Q(8) p |
|---|---|---|---|---|---|
| echelon (2, 2) | 20 | −2649.24 | 5338.5 | 5412.3 | 0.09 |
| echelon (3, 2) | 24 | −2642.17 | 5332.3 | 5420.9 | 0.14 |
| VAR(6) (Tiao and Box) | 28 | −2638.76 | 5333.5 | 5436.9 | 0.25 |

(BIC with n = 296.)

- **(2, 2) has equal indices, so it is the VARMA(2, 2)**: the same optimum,
  −2649.24. From the least-squares start the optimiser converges on the
  gradient in 111 iterations (with other numpy and scipy versions it may stop
  at the same optimum because the last step found no lower point). From
  zero it stops on the step size, and warns against trusting the standard
  errors.
- **The gas enters the CO2 equation** at lags 1 and 2, in the AR and the MA.
  The CO2 enters the gas equation more weakly (AR1, AR2 and MA2 with
  |t| ≈ 2.6–3.3).
- **BIC prefers (2, 2) and AIC the larger models.** The VAR(6) forecasts a
  little better. Over origins from observation 200, its 1–3 step RMSE ratios
  against the univariates are 0.61–0.76 for the CO2, against 0.62–0.78 for
  (2, 2), and 0.92–0.99 for the gas, against 0.98–1.08.

### 4.4 What the example says

The search points at a small identified model, and the analyst's comparison
does the rest: the LR, the information criteria, `evaluate`. On these data
the echelon form is a parsimonious rival to Tiao and Box's VAR(6), not a
replacement. It is the start that makes it fit cleanly.

---

## Part 5 · Route U: the flour prices and the IPC

### 5.1 The flour prices (Tiao and Box's tools)

The `flour_prices` example brings three univariate models: an MA(1) on the
differenced logs for each city.

    load_example("flour_prices"); run_gate(...); identify_echelon(...)

The search on the differences chooses **(1, 0, 0)**, with both criteria.
That is the choice of Poskitt's procedure by HQ in Lütkepohl and Poskitt's
Table 1, on the same differences. Route V on the same data, their own
analysis, is Part 3.

The fit, `estimate(indices="1, 0, 0")`:
- **converges** (termcode 1) with white residuals (Hosking p 0.99);
- **11 parameters, logL −670.78**, against 14 and −671.34 for route U's
  VAR(1);
- **the own MA(1) of the univariate models is replaced** by each row's free
  AR(n_i)/MA(n_i): Buffalo gets an ARMA(1, 1), and Minneapolis and Kansas
  City none, linked to Buffalo through A_0.

### 5.2 The IPC: a seasonal factor on the row

Three monthly price indices (`tests/data/IPC_*_ext.pre`):
- Germany: AR(3) × annual AR(1);
- Spain: AR(1);
- France: annual AR(1).

The annual factors of Germany and France become their rows' factors, and
the search runs on each row filtered by them.

SC chooses **(0, 1, 1)** and HQ (0, 3, 1). SC's fit stops on the MA wall
and its residuals are not white: the search underfits here, which
`check_residuals` shows.

THE ROW FACTOR'S CHECK on that fit gives LR 3.63, df 2, p 0.16. The annual
factors hold on the whole rows. On (1, 1, 1) the check gives p 0.04, a
marginal rejection.

---

## References

- E. J. Hannan and L. Kavalieris (1984), "Multivariate linear time series
  models", *Advances in Applied Probability* 16, 492–561.
- H. Lütkepohl and D. S. Poskitt (1996), "Specification of echelon-form VARMA
  models", *Journal of Business & Economic Statistics* 14, 69–79.
- G. C. Tiao and G. E. P. Box (1981), "Modeling multiple time series with
  applications", *Journal of the American Statistical Association* 76,
  802–816.
- drvarma: `docs/ECHELON_PLAN.md`, `docs/STUDY-echelon-form.md`,
  `docs/STUDY-echelon-search.md`.
