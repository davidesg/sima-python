# Tutorial — Jenkins and Alavi (1981): muskrat and mink

*The step-by-step guide of the worked example, for the assistant that leads
it. The explanation of every step is the manual, `sima://doc/MANUAL-jenkins-alavi`
(Part 1 the method, Part 2 sima, Part 3 this example).*

## For the assistant: how to lead it

* This is the **guided lane**, as in a real analysis: ONE step at a time. Run
  the call, present the tool's report exactly as always (the table as it is,
  what it shows, the conclusions, the alternatives, the figure) and stop at ⏸.
  The analyst decides; the tools do not change because this is a tutorial.
* After the report, and only then, add **"In the paper"**: what Jenkins and
  Alavi found at that step (below), and where the manual explains it. Compare
  the numbers; say where they differ and why.
* The analyst may take another road than the paper's. Follow them: the
  tutorial is a map, not a script. Come back to it when they want.
* Dates: Jenkins and Alavi date the series 1848–1909; these files, 1850–1911.
  **Every date here is two years later than the paper's** (their 1906 is our
  1908). Say it the first time a date comes up.
* The session is the one `load_example` opened (by default `jenkins_alavi`).

---

## Step 0 · The univariate models (already loaded)

`load_example("jenkins_alavi")` loaded art's two models:

* muskrat: ARIMA(6,1,1) on ln z — φ 0.65 −0.58 0.22 −0.31 −0.04 −0.32, θ 0.55,
  σ 28.1 %;
* mink: AR(4) on ln z with mean — φ 0.80 −0.21 0.00 −0.27, mean 10.82 (in logs),
  σ 25.7 %.

**In the paper** [§4.2]: muskrat φ 0.65 −0.60 0.23 −0.34 −0.06 −0.38, θ 0.54,
σ 28.7 %; mink φ 0.82 −0.22 0.00 −0.28, mean 10.79, σ 26.1 %. The muskrat's
operator has cycles of 10.3, 4.2 and 2.6 years, the mink's of 10.2 and 2.9:
the ten-year cycle both species share. The muskrat is differenced (its upward
trend); the mink is not — differenced, it needs an MA with θ near 1,
over-differencing. *Manual 3.2.*

## Step 1 · N1 — the gate

    run_gate("jenkins_alavi")

Look at: PASSED, the difference (about 1e-13), and the note that the mink is
re-estimated on 61 observations — the common window starts in 1851 because the
muskrat's difference costs it its first year.

**In the paper:** no gate; it is the ladder's certification that the system
starts exactly from the univariate models. *Manual 2.1.*

## Step 2 · N2 — method 2, prewhitened

    plot_identification("jenkins_alavi", method=2)

Look at: the ccf of the pair "MINK − MUSKRAT" (the mink leads at k > 0):
r(0) = +0.38; k = +1, −0.36 (more mink, fewer muskrat next year: predation);
k = −1, +0.35 (more muskrat, more mink next year: food); nothing else but an
isolated +0.27 at −5. S* = 45.7 (21 d.f., p = 0.001). The ccf cuts off after
lag 1 on both sides: an MA(1) residual model.

**In the paper** [§4.2, figure 5]: "positive correlations at lags 0 and 1 …
a negative correlation at lag −1" (their sign convention is the mirror of
sima's: they put the muskrat leading at k > 0); r(0) = 0.42 ± 0.13; the model
(4.8), a bivariate MA(1) for the residuals, preliminary estimates −0.49 and
+0.48. Consistent with Errington (1943): the mink is an important predator of
the muskrat. *Manual 1.2, 3.4.*

## Step 3 · N2 — method 1, not prewhitened

    plot_identification("jenkins_alavi", method=1)

Look at: the ccf of the stationary series waves with the common cycle (its
band, Bartlett's, follows the lag) and does not cut off; the pccf does: −0.64
at +1 and +0.32 at +2 (the mink on the muskrat's growth), +0.28 at −1. A cross
AR(2). Both readings are present: the report offers both candidates.

**In the paper** [Table IV], reproduced (R_k exactly, S_k within a few hundredths): r(0) = −0.33;
the lag-1 cross correlation −0.64; S_1 −0.60 and S_2 +0.30 of the mink on the
muskrat (sima −0.64, +0.32), S_1 +0.30 of the muskrat on the mink (sima +0.28),
the own elements 0.01 and 0.74 exactly. Their R_k is printed transposed: their
r_ij(k) is corr(w_i,t, w_j,t+k). "A model with maximum order p = 2 or 3": their
(4.10). They estimated both structures. *Manual 1.2, 3.4.*

If the analyst wants the matrices themselves (S_k(q), determinants, the
+ − . table): `identify_matrices("jenkins_alavi")`.

## Step 4 · N3 — the two candidates

    estimate("jenkins_alavi", 0, 1, links="MUSKRAT<-MINK, MINK<-MUSKRAT",
             cross="residual", start="preliminary")
    estimate("jenkins_alavi", 2, 0, links="MUSKRAT<-MINK, MINK<-MUSKRAT",
             start="preliminary")

Look at: A (the MA(1) residual model, form (3.22)): MA1[MUSKRAT←MINK] 0.38,
MA1[MINK←MUSKRAT] −0.52, log-likelihood −561.26 (16 parameters), LR 36.2 on
3 d.f.; the muskrat's own φ₁ and θ become small with large standard errors.
B (the cross AR(2)): −0.54 and +0.40 of the mink on the muskrat, +0.46 and
−0.09 of the muskrat on the mink, −558.76 (18 parameters), LR 41.2 on 5 d.f.
AIC prefers B by 1, BIC A by 3: as close as in the paper. Starting at the
preliminary estimates, both converge; from zero they reach the same optimum
(worth showing if the analyst asks whether it is one).

**In the paper** [§5.4]: (5.8), from method 2, with the small parameters
deleted; (5.9), from method 1: 0.73B − 0.41B² of the mink on the muskrat and
−0.37B + 0.24B² of the muskrat on the mink (in sima's convention −0.73, +0.41;
+0.37, −0.24). "Both provide adequate representations"; the choice is by the
"structural" description: a discrete Lotka–Volterra (5.10). *Manual 1.3–1.4,
3.4.*

## Step 5 · N4 — the checking

    check_residuals("jenkins_alavi")        (after each estimate)

Look at: no residual correlation beyond the band; the largest transformed
residual 1908 — the muskrat −3.6 to −4.0 s.d., the mink −2; others 1870, 1885,
1899. The panels show the muskrat's fall in 1908.

**In the paper** [§5.4]: their 1906 (= our 1908): muskrat −3.9, mink −1.9;
and 1868, 1883, 1897, 1860 (= 1870, 1885, 1899, 1862). "It would be
interesting to know what caused the number of muskrat skins traded in 1906 to
fall so drastically." They did not intervene. *Manual 1.5, 3.4.*

## Step 6 · N5 — Table VIII

    forecast_uncertainty("jenkins_alavi", horizon=3)            (with B current)
    forecast_uncertainty("jenkins_alavi", horizon=3, estwin=48)

Look at: on all the data B lowers the uncertainty of both series at every
lead (muskrat 28.8 → 25.5 at lead 1). Refitted on 48 observations (to 1897),
the univariate V(l) is theirs: 25.7 38.7 41.1 and 26.2 31.6 32.5.

**In the paper** [§6.3, Table VIII, models (6.10)–(6.12)]: univariate 25.6
38.6 40.8 and 25.9 31.8 32.9; bivariate 19.2 32.7 41.9 and 24.2 31.2 34.1
(sima's is lower: it keeps the full univariate operators on the diagonal).
"The benefits from using the bivariate model are greater for the muskrat."
*Manual 1.6, 3.4.*

## Step 7 · N5 — what they could not run

    evaluate("jenkins_alavi", 2, 0, 48, horizon=3, links="MUSKRAT<-MINK, MINK<-MUSKRAT")
    evaluate("jenkins_alavi", 0, 1, 48, horizon=3, links="MUSKRAT<-MINK, MINK<-MUSKRAT",
             cross="residual")

Look at: estimated on 48 years and forecast from each of the 14 origins
1898–1911, B loses in every cell (the mink by 32 to 42 %); A ties. The system
that lowers V(l) by a quarter in sample does not forecast better.

**In the paper** [§6.2]: the demonstration from a range of origins "cannot be
carried out for the muskrat-mink series" — the forecast errors are very large
for both models. sima runs it and says why they were cautious. The rule of
sima: the univariate models are the yardstick; B stays as the structural
description. *Manual 3.5.*

## Closing

    export_guion("jenkins_alavi")

The path, node by node, with the evidence and the analyst's decisions. Offer
the manual for the method, and `examples/jenkins_alavi/run.py` in the
repository for the whole walkthrough in one go.
