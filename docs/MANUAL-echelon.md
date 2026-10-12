# sima user manual — the echelon form

*A chapter of the sima user manual. Written 2026-10-12.*

This chapter explains the third of sima's identification forms, the echelon
VARMA of Lütkepohl and Poskitt (1996). It shows how sima finds its Kronecker
indices and fits it, and works it through on Box and Jenkins' gas furnace,
the data of the Tiao and Box route. The other two forms are Jenkins and
Alavi's (`MANUAL-jenkins-alavi.md`) and Tiao and Box's (`STUDY-tiao-box.md`).

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

### 2.1 Route V only

The echelon form is fitted on route V's specifications (`write_specs`): each
series' file carries its transformation, and the system gives it a free
AR(n_i)/MA(n_i) of its own. On route U the diagonal is the univariate model,
whose degree (with seasonal factors, 13 and more) is not an echelon row's.
sima refuses the form there and says so.

### 2.2 `identify_echelon(max_index=3, criterion="SC")`

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

- **The echelon form on route U's models**, a seasonal univariate model as a
  row factor. That is drvarma's stage 4, still to be reviewed.
- **Choosing the order of the series.** The indices are those of the files'
  order. To try another order, open the data with the series in that order.

---

## Part 3 · The worked example: the gas furnace

### 3.1 The data and the route

Box and Jenkins' Series J: the input gas rate and the output CO2, 296
observations, in levels (d = 0, λ = 1 for the CO2). Route V, as in Tiao and
Box:

    load_data("gf", "gas_furnace.csv", freq=1, start="1000")
    characterize("gf", set="InputGasRate: d=0; CO2: lam=1, d=0")
    write_specs("gf"); run_gate("gf")

### 3.2 The indices

    identify_echelon("gf", max_index=6)

SC chooses **(2, 2)** (log|Σ̃| 12.27, SC 12.59) and HQ **(3, 2)**. The
long VAR has h = 6, Tiao and Box's order.

### 3.3 The fits

| model | parameters | logL | AIC | BIC | Hosking Q(8) p |
|---|---|---|---|---|---|
| echelon (2, 2) | 20 | −2649.24 | 5338.5 | 5412.3 | 0.09 |
| echelon (3, 2) | 24 | −2642.17 | 5332.3 | 5420.9 | 0.14 |
| VAR(6) (Tiao and Box) | 28 | −2638.76 | 5333.5 | 5436.9 | 0.25 |

(BIC with n = 296.)

- **(2, 2) has equal indices, so it is the VARMA(2, 2)**: the same optimum,
  −2649.24. From the least-squares start the optimiser converges on the
  gradient in 111 iterations. From zero it stops on the step size, and warns
  against trusting the standard errors.
- **The gas enters the CO2 equation** at lags 1 and 2, in the AR and the MA.
  The CO2 enters the gas equation more weakly (AR1, AR2 and MA2 with
  |t| ≈ 2.6–3.3).
- **BIC prefers (2, 2) and AIC the larger models.** The VAR(6) forecasts a
  little better. Over origins from observation 200, its 1–3 step RMSE ratios
  against the univariates are 0.61–0.76 for the CO2, against 0.62–0.78 for
  (2, 2), and 0.92–0.99 for the gas, against 0.98–1.08.

### 3.4 What the example says

The search points at a small identified model, and the analyst's comparison
does the rest: the LR, the information criteria, `evaluate`. On these data
the echelon form is a parsimonious rival to Tiao and Box's VAR(6), not a
replacement. It is the start that makes it fit cleanly.

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
