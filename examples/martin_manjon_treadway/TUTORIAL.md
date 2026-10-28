# Tutorial — Martín Manjón and Treadway (1997): the Fed controls only one of the two interest rates

*The step-by-step guide of the worked example, for the assistant that leads it.
The method is in `sima://doc/MANUAL-vec` (the study behind it, `sima://doc/STUDY-vec`) and the decisions in
`sima://doc/PLAN-vec` (§0). The data and the models: the example's README.*

## For the assistant: how to lead it

* **Guided lane**, ONE step at a time: present each report as always, and stop
  at ⏸. The analyst decides.
* After each report, add **"In the paper"**: what Martín Manjón and Treadway
  (1997) find at that step, on 1985–1995.
* The lessons: the bootstrap finds the paper's relation on the whole
  homogeneous regime (1985–2008), not on the paper's own sample; the variable
  that corrects is the Fed's target, not the market rates; and the joint LR
  reads the system as a conditional model, the target on the market rates.
  The last section, "Further than the paper", says what the paper could not
  test.
* The univariate models were built in art (AR(3), as in the paper), one per
  series.

---

## Step 1 · N1 — the gate

    run_gate("martin_manjon_treadway")

PASSED: every file is a fixed point. λ = 1, d = 1, no mean, AR(3) for the
three.

**In the paper (Table 2, 1985–95):** each rate is I(1) and ∇R is an AR(3)
without mean: a positive real factor and a complex pair, period 3–4 months.
The target's (1 − .78B)(1 + .32B + .25B²), σ = .17 %.

## Step 2 · N1b — the canonical analysis of the levels

    canonical_analysis("martin_manjon_treadway")

M(l) is significant up to l = 4, then again, alone, at l = 16 and l = 22. The
reading uses the last one, a VAR(22); the contiguous order is 4, and that is
the one prepare_vec takes by default (it offers 22). At the VAR(22) the three components are near 1
(√λ .94, .99, 1.00) and the reading is "no stationary combination". But look at
the least predictable component: R3 − .57·R0T − .53·R30, the relation the rank
will find in Step 5 (.575, .561). Its √λ = .939 is just above the 0.9
convention, at a VAR(22) inflated by isolated lags. The reading is not a test:
go on to N1c.

## Step 3 · N1c — the question, and the purpose

    prepare_vec("martin_manjon_treadway", purpose="long run", p=4)

Purpose: "long run" (the term structure's equilibrium). p = 4, the paper's
AR(3) in ∇ plus 1 (sima's own rule and the contiguous M(l) say the same); case
pre: no drift, as the univariate models have no mean.

## Step 4 · C1 — the rank, by parametric bootstrap

    rank_test("martin_manjon_treadway", B=499)          (cached)

* r = 0 → 1: LR 23.75 against the bootstrap's 95 % value 20.15, p 0.022;
* r = 1 → 2: LR 4.94 against 11.25, p 0.35.

**The bootstrap proposes r = 1: one relation, two common trends.** No
asymptotic table exists for case pre: the bootstrap is the only calibration.

**In the paper:** CI(1,1) for the trivariate, and no cointegration for
(target, 30-year). On their own 1985–95 sample the same test does not reject
r = 0 at p = 4 (LR 15.53 against 22.49, p 0.22; it does at p = 2, p 0.016):
the relation needs the doubled sample. On 1996–2008 alone, not either (p 0.15).

## Step 5 · C2 — the VEC, normalised on the 3-year rate

    estimate_vec("martin_manjon_treadway", r=1, normalise_on="R3")

    R3 = .575 R0T + .561 R30 − 0.89 %      (.043, .054, .23)

E[ec] is printed in fue's ×100 scale: −88.88 is −0.89 %. The 3-year rate is
an almost equal mix of the policy trend and the long one; the weights add up
to 1.14. Hosking's Q p 0.79; the multivariate JB rejects (the cuts of 2001 and
2008). alpha on R0T +0.119 (t 4.1); on R30 and R3, |t| < 1.

**In the paper:** the 3-year rate as a combination of the target and the
30-year rate, with weights of about .48 and .63 (the scanned table is hard to
read), and **μ = −.89 % for R3**: the same constant.

## Step 6 · C3 — who corrects, by LR

    test_restriction("martin_manjon_treadway", weakex="R0T")
    test_restriction("martin_manjon_treadway", alpha="[[1],[0],[0]]")

The target's weak exogeneity is rejected (LR 12.36, 1 df, p 0.0004); "only
the target corrects", alpha = Aψ with A = (1, 0, 0)′, is not (LR 1.70, 2 df,
p 0.43): **R30 and R3 are jointly weakly exogenous.** The Fed moves the target
towards what the curve has priced: in monthly data the market rates anticipate
it. Causality in the sense of prediction, not a structural claim.

⏸ The α test alone does not make the system conditional: the short run may
still feed the target back into the market rates. The joint test, both at
once:

    test_restriction("martin_manjon_treadway", alpha="[[1],[0],[0]]",
                     gamma="R30,R3 <- R0T")

R30 and R3 weakly exogenous AND R0T absent from their equations at every lag
(Γ₁…Γ₃): LR 7.83, 8 df, p 0.45, not rejected (the Γ block alone: LR 6.81,
6 df, p 0.34). **The system reads as R0T | R30, R3: the target on I(1)
inputs, a transfer network whose gain is the long run and whose lags the
short run.** The report offers mtram, with the same three files and R0T as
the output; offer it, and do not go there yourself.

**In the paper:** in the bivariate (target, effective rate), a feedback from
the effective rate to the target (θ₁₂ = −.68); the trivariate's adjustment is
not tested.

## Step 7 · C5 — the long run

    long_run("martin_manjon_treadway")

θ as above. The textbook half-life on R3 is 18.9 months; the model's, the
equilibrium error's own response, 4 months after its peak: the short run
matters. Gonzalo and Ng: two permanent shocks and one transitory. The target's
forecast-error variance is 37 % permanent at one month and 97 % at twelve,
while R30's and R3's are permanent from the start: at short horizons the target
is the one that moves around the equilibrium.

## Step 8 · the control — the 10-year rate in place of the 30-year

    load_pre("mmt_r10", '["art/R0T_ar3.pre", "art/R10_ar3.pre", "art/R3_ar3.pre"]')
    run_gate("mmt_r10")
    prepare_vec("mmt_r10", purpose="long run", p=4)
    rank_test("mmt_r10", B=499)                          (cached)
    estimate_vec("mmt_r10", r=1, normalise_on="R3")
    test_restriction("mmt_r10", alpha="[[1],[0],[0]]")
    test_restriction("mmt_r10", alpha="[[1],[0],[0]]", gamma="R10,R3 <- R0T")

(the paths as `load_example` copied them.) The 30-year rate is not published
from 2/2002 to 2/2006 and FRED fills the gap; the 10-year rate is. The same
verdict: r = 0 rejected (LR 23.25 against 20.48, p 0.022), r = 1 not (p 0.46).
R3 = .477·R0T + .598·R10 − 0.48 % (.040, .046, .15); only the target corrects
(LR 0.24, 2 df, p 0.89), and the conditional model holds (LR 6.58, 8 df,
p 0.58). The 10-year rate is closer to the 3-year, so the long
trend weighs more and the constant is smaller. The structure is the same.

## Further than the paper

Martín Manjón and Treadway decided cointegration as the school does: they
over-differenced each series and read the MA unit root by exact maximum
likelihood. With sima and drvec the same question goes further:

* **The rank by parametric bootstrap.** The exact LR, calibrated by simulating
  the fitted model (Cavaliere, Rahbek and Taylor 2012): case pre has no
  asymptotic table, so this is a test the paper could not run. On their own
  sample (1985–95, p = 4) it confirms four of their five results: (target,
  effective rate) cointegrate, no pair with R3 or R30 does. The trivariate is
  the fifth, and it needs more data.
* **The doubled sample.** 1985–2008 is the whole regime the paper's argument
  is about (the post-NOP procedure up to interest on reserves). The trivariate
  relation is found on it (p 0.022), and on neither half alone (1985–95
  p 0.22, 1996–2008 p 0.15). μ = −0.89 % is the paper's constant. Across the
  halves the weight of R30 and μ are stable; the target's rises from .46 to .64.
* **Who corrects, by LR.** Not in the paper: the target corrects, the market
  rates are jointly weakly exogenous. The Fed follows the curve.
* **The conditional model.** The joint LR on α and the short-run block of Γ
  (Step 6) is not rejected: R0T | R30, R3, a reaction function in market rates,
  which is mtram's next rung.
* **The control.** The 10-year rate in place of the 30-year, whose 2002–2006
  gap FRED fills by extrapolation: the same structure (Step 8).
* **The market rates as the policy factor.** With GS1 or GS2 in place of the
  target, on 1985–2008, the rank is the same (one relation), but the roles turn
  round: the short market rate leads and the long ones adjust to it.
* **After 2008: the floor, QE and QT.** The next section.

## After 2008: the floor, QE and QT

*Results of a separate study with the same tools (drvec C 0.13, B = 499,
case pre); its data, FRED up to 9/2026, are not in this example. Tell the
analyst so, and present them as findings, not as steps to run.*

Since 10/2008 the Fed pays interest on reserves and since 12/2008 it runs a
floor system with a 0–0.25 band: the target sits at the floor and cannot
carry the policy factor. QE, Operation Twist and forward guidance were the
Fed's attempts to move the other trend, the long rates: the natural test of
the paper's title. The 2-year rate (GS2) takes the target's place, and the
calibration on 1985–2008 says it may: (GS2, GS30, GS10) gives the paper's
pattern there (r = 1, p 0.012; no pair cointegrates), with the roles turned
round, the short rate leading and the long ones adjusting.

**The samples.** 12/2008–2/2020 (n 135: the floor, QE1–3, the Twist, the
lift-off, QT1); 12/2008–11/2015 (84, the floor alone); 12/2015–2/2020 (51,
lift-off and QT1); 3/2022–9/2026 (55, the hikes, QT2, the cuts);
12/2015–9/2026 (130, the pandemic floor as interventions). The univariate
models come from art, with the interventions its node finds, ω in percentage
points: GS10 8/2011 (dated guidance, the S&P downgrade) −0.61 (.16); GS30
8/2011 and 9/2011 (the Twist) −0.60, −0.44 (.14); GS2 6/2019 (the turn to
cuts) −0.31 (.09); 3/2020, the cut to zero, on R0T, GS2 and GS3. The AR orders
fall on the floor (the long rates AR(1), GS2 AR(2)): before 2008 the Fed's
gradualism gave the changes their autocorrelation.

**The rank** (r = 0 → 1: LR, the bootstrap's 95 % value, p):

| system | sample | n | p | r = 0 → 1 | r̂ |
|---|---|---|---|---|---|
| (GS2, GS30, GS10) | 2008–2020 | 134 | 4 | 7.92 (22.27) .758 | 0 |
| (GS2, GS10) / (GS2, GS30) | 2008–2020 | 134 | 4 | p .386 / .286 | 0 |
| (GS2, GS30, GS10) | 2008–2015 | 83 | 4 | 19.54 (22.90) .116 | 0 |
| (GS2, GS30, GS10) | 2016–2020 | 50 | 2 / 3 / 4 | **30.85 (22.82) .004** / 16.10 (26.49) .348 / 21.28 (27.36) .230 | 1 / 0 / 0 |
| (R0T, R30, R3) | 2022–2026 | 54 | 2 / 3 / 4 | **25.09 (23.55) .026** / 9.77 (24.69) .850 / 20.70 (27.97) .232 | 1 / 0 / 0 |
| (R0T, R30, R3) | 2015–2026 | 129 | 4 | 16.12 (22.80) .202 | 0 |
| (GS2, GS30, GS10) | 2015–2026 | 129 | 4 | 5.34 (22.01) .868 | 0 |

Power: the LR grows roughly with n, so 1985–2008's 23.2 (n 284) would be
about 11 at n 134, below the 95 % value; a non-rejection here says "not
detected", not "absent". And at n ≈ 50 the verdict depends on p: only p = 2
rejects r = 0 (as on 1985–95), which is why rank_test, at small n, offers the
sweep over p first.

**The VECs with r = 1** (on theory where the bootstrap says r = 0):

| system, sample | p | weights | μ | who corrects (LR) |
|---|---|---|---|---|
| GS10 on GS2, GS30, 2008–2020 | 4 | .056 (.215), .405 (.442) | +1.14 % (1.88) | not identified: a flat likelihood |
| GS10 on GS2, GS30, 2008–2015 | 4 | 1.212 (.124), 1.333 (.184) | −3.24 % (.79) | GS30 (p .016); GS2 exogenous (p .49) |
| GS10 on GS2, GS30, 2016–2020 | 2 | .310 (.015), .922 (.042) | −0.81 % (.10) | GS2 (LR 10.56, p .001) |
| R3 on R0T, R30, 2022–2026 | 2 | .433 (.050), .415 (.108) | +0.22 % (.52) | R0T (LR 13.22, p .0003) |

(The calibration on 1985–2008, for the GS10 rows: GS2 .243, GS30 .821,
μ −0.44 %.)

**QT2 on the long rates.** A step at each QT2 date, one at a time, on the
univariate GS10 and GS30: only the start leaves a mark (+0.47 pp on GS10,
t 2.8, 6/2022 or 9/2022), and it cannot be told apart from the 75 bp hikes of
6/2022 and 9/2022. The slowdowns (6/2024, 4/2025) and the end (12/2025) leave
nothing. QE bought duration (the Twist, about 30 % of its purchases at 20–30
years) and its steps are clear; QT lets short residual maturities run off and
reaches the term premium only through the Treasury's issuance.

**The reading.**

* **The floor breaks the structure as one regime.** With the floor in the
  sample nothing is found with any p or system; the floor alone gives a
  different relation (the long rate loads heavily on GS2, the lift-off date),
  and mixing it with the active-rate stretches erases both.
* **Outside the floor the structure is compatible with the old one, not
  proved.** 2016–2020 has nearly the calibration's weights, with GS2
  correcting; 2022–2026 has the paper's relation, R3 an almost equal mean of
  R0T and R30, and the target correcting again, at any p. But with n ≈ 50 the
  rank rejects r = 0 only at p = 2.
* **Caveats.** The weak-exogeneity LRs are asymptotic χ² (drvec has no
  bootstrap of them), less reliable at n ≈ 50–135; GS1 and GS2 are censored at
  zero on the floor; the parametric bootstrap is homoscedastic and does not
  see the variance changes between stretches.

## Closing

    export_guion("martin_manjon_treadway")

The path says, at N1b, that the canonical reading at a VAR(22) saw no
stationary combination, and at C1 that the bootstrap found one: both are
findings, and the second is the test.
