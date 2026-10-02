# Tutorial — Tiao and Box's tools: flour prices in three cities

*The step-by-step guide of the worked example, for the assistant that leads it.
The method is in the study `sima://doc/STUDY-tiao-box` (§1 Tiao and Box 1981,
§2 Tiao and Tsay, §2.bis Box and Tiao 1977); the J&A identification it sits
beside is `sima://doc/MANUAL-jenkins-alavi`.*

## For the assistant: how to lead it

* **Guided lane**, as in a real analysis: ONE step at a time. Run the call,
  present the report as always (the table as it is, what it shows, the
  conclusions, the alternatives) and stop at ⏸. The analyst decides.
* After the report, and only then, add **"In the papers"**: what Tiao and Tsay
  (1989) — and Box and Tiao (1977), Tiao and Box (1981) — say at that step.
  Compare the numbers; say where they differ and why.
* The lesson of this example: the three univariate models difference every
  series, and the Wisconsin tools say that the system lives in the LEVELS. sima
  reads that and points to drvec; it does not change a d. Do not oversell it:
  the canonical analysis is a reading, not a test.
* The session is the one `load_example` opened (by default `flour_prices`).

---

## Step 0 · The univariate models (already loaded)

Three ARIMA(0,1,1) on ln z, no mean: θ −0.135 (Buffalo), −0.251 (Minneapolis),
−0.199 (Kansas City); residual s.d. 4.8, 5.0, 5.2 %. Each city alone is close
to a random walk (θ < 0: a small overshoot, the forecast weights alternate).

**In the papers:** Tiao and Tsay model the logs jointly from the start, with no
univariate step (the Wisconsin school's position, Tiao and Box 1981 §4, §6).
Their Fig. 1: "the price movements are closely parallel".

## Step 1 · N1 — the gate

    run_gate("flour_prices")

PASSED; every file a fixed point. It ends by proposing `canonical_analysis`:
three series are differenced.

## Step 2 · N1b — the canonical analysis of the levels

    canonical_analysis("flour_prices")

Look at:
* the stepwise table on the LEVELS: M(1) = 462, M(2) = 31: a VAR(2) in levels;
* three components, λ = 0.76, 0.85, 0.94 (√λ = 0.87, 0.92, 0.97):
  - the most predictable is ≈ Buffalo + Kansas City (+ a little Minneapolis):
    **the common trend** of flour prices;
  - the least predictable is a **contrast between markets** (Buffalo − Minneapolis,
    with Kansas City), root ≈ 0.87;
* 3 series differenced, 2 components near 1: there may be ONE stationary
  combination of the levels. The menu names drvec (Johansen's test).

**In the papers:** Tiao and Tsay (1989, §6.1) find an ARMA(1,1) in levels with
three scalar components. One is a contrast between markets that follows an
AR(1) with φ = 0.88, "nearly non-stationary": "the difference between markets
is not very stable". The other two are "clearly non-stationary", one being "the
overall trend movement". The contrast's root of 0.88 is the 0.87 here (λ =
0.76 = 0.87²). Two non-stationary components and one nearly so is what this
reading says. Whether the contrast is stationary is exactly the question a test
must settle, which is drvec's. The threshold matters: with it on λ instead of
√λ, only one component would count as near 1.

Decision to propose: go on in sima with the univariates' differences, as
Jenkins and Alavi would, knowing the caveat. Record it.

## Step 3 · N2 — the residual cross-correlations

    identify_cross("flour_prices")

The innovations correlate at 0.96 (Buffalo–Minneapolis), 0.85, 0.88: the three
markets receive the same shocks. No lagged cross correlation beyond chance.

**In the papers:** Box and Tiao (1977, §5.1) warn that λ near 1 also comes from
a nearly singular innovation covariance. With correlations of 0.96, that caveat
is live here, and one more reason to leave the decision to a test.

## Step 4 · N2 — the two identifications, with Tiao and Box's M(l)

    identify_matrices("flour_prices")

Look at method 1:
* R_k(w) cuts off after lag 1, which points to an MA(1) of the differences;
* S_k (Jenkins and Alavi) never cuts off: the same pattern lag after lag;
* Tiao and Box's stepwise table: only M(1) is significant (38.0, 9 d.f.), so a
  VAR(1).
* Method 2 shows nothing cross beyond lag 0.

The disagreement is the lesson. A system with a stable combination of its
levels, once every series is differenced, has an MA that does not invert
(Box and Tiao 1977, §4.4). Its partials do not cut off (Tiao and Box 1981,
Table 4, the VMA case). M(l), a test with m² d.f., is the one to follow on the
order.

## Step 5 · N3 — the VAR(1) M(l) asks for

    estimate("flour_prices", p=1, q=0)

logL −671.34 with 14 parameters. The cross AR terms Buffalo←Minneapolis (0.35),
Minneapolis←Buffalo (0.29) and Kansas City←Buffalo (0.63) are significant. The
LR against the univariates is large (459, 9 d.f.), but most of it is the
covariance: the diagonal system with full covariance alone gives 431.

## Step 5b · N4 — its checking

    check_residuals("flour_prices")

The residual matrices are clean (none beyond the band; about 5 expected by
chance). The uncorrelated transformed residuals a* = Q'â tell more. The largest,
1974.05 at 4.7 s.d., is on a*_3, which loads Minneapolis +0.71 against Buffalo
−0.71. That is the contrast between markets again, the component the canonical
analysis found least persistent and Tiao and Tsay "not very stable". 1973–74
is the grain price shock. An intervention would belong in art, on each city's
model; the example leaves it as a caveat.

## Step 6 · N5 — the yardstick

    evaluate("flour_prices", 1, 0, 72, horizon=6)

RMSE ratios 0.93–1.01: no gain worth a model. The significant cross terms in
sample do not forecast better out of sample.

**Closing reading.** In the differences, the joint model adds little: the
univariates with a full covariance carry the forecasts. What ties the three
markets lives in the levels, which is the canonical analysis's message and
Tiao and Tsay's model. The next step is a test of the stationary combination,
drvec's. That is where this example ends, and it is the honest answer of the
ladder to these data.
