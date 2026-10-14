# Tutorial — the echelon form: Lütkepohl and Poskitt's flour prices

*The step-by-step guide of the worked example, for the assistant that leads it.
The method is in the manual `sima://doc/MANUAL-echelon`. The other two forms
are `sima://example/jenkins_alavi` and `sima://example/tiao_box`.*

## For the assistant: how to lead it

* **Guided lane**, as in a real analysis: ONE step at a time. Run the call,
  present the report as always (the table as it is, what it shows, the
  conclusions, the alternatives) and stop at ⏸. The analyst decides.
* After the report, and only then, add **"In the paper"**: what Lütkepohl and
  Poskitt (1996, §4.1, Tables 1 and 2) found at that step. Compare the
  numbers; say where they differ and why.
* **The scale.** sima works on 100 × the differences of the logs (per cent).
  Lütkepohl and Poskitt work on the differences of the logs. Their det Σ̃ ×
  10¹² is sima's |Σ̃|, so their log det plus 27.63 is sima's log|Σ̃|.
* The lesson of this example: the search gives a starting point, not a
  verdict. sima's SC and HQ choose (0, 0, 0), as theirs do. The LR against
  that choice, and the restricted models it leads to, are what decide.
* The session is the one `load_example` opened (by default `lutkepohl_poskitt`).

---

## Step 0 · N0r — the data (already loaded)

The flour price indices of Buffalo, Minneapolis and Kansas City, monthly,
August 1972 – November 1980 (100 months). They are Tiao and Tsay's (1989)
data, the same as in `flour_prices`.

**In the paper:** "Because the original series appear to be nonstationary, we
use rates of change (first differences of logarithms)."

## Step 1 · N0c — the transformation

    characterize("lutkepohl_poskitt")

art's engine proposes λ = 0 and d = 1 for the three cities: logs, and one
difference (ADF rejects a unit root only after it, KPSS never objects). No
seasonality (HAC F p 0.25, 0.23, 0.07). This is exactly their transformation.
If the analyst wants to fix it explicitly, as `run.py` does:

    characterize("lutkepohl_poskitt", set="Buffalo: lam=0, d=1; Minneapolis: lam=0, d=1; KansasCity: lam=0, d=1")

## Step 2 · N0v and N1 — route V, the gate

    write_specs("lutkepohl_poskitt"); run_gate("lutkepohl_poskitt")

Route V: the vector first. Each series gets a specification with only its
transformation, and no univariate model enters the system. The gate passes;
its diagonal is three random walks in the logs, not a yardstick.

**In the paper:** Lütkepohl and Poskitt build no univariate models. The
echelon form, like Tiao and Box's method, is specified on the vector.

## Step 3 · N2 — the Kronecker indices

    identify_echelon("lutkepohl_poskitt", max_index=6)

Look at:
* stage I: the long VAR has h = 1, by AIC;
* the table: log|S̃| 5.4205 for (0, 0, 0), 4.9739 for (1, 1, 1) with 18
  coefficients, and the larger ones;
* **SC and HQ choose (0, 0, 0)**, and HQ's second best is (1, 1, 1).

AIC is not printed, but the table gives it: log|S̃| + 2 dim / T, with T = 92
(the 99 differences less h + n_max = 7; the HQ and SC columns give the same
T). (0, 0, 0) gives 5.42 and (1, 1, 1) gives 4.97 + 36/92 = 5.37. **AIC
chooses (1, 1, 1).**

**In the paper (Table 1):** the full search with n_max = 6 chooses (1, 1, 1)
by AIC and (0, 0, 0) by HQ, with (1, 1, 1) second, the same as here. Their
other strategies give (2, 0, 0), (1, 0, 0) and (2, 2, 2). They go on with
(1, 1, 1) "because this is an intermediate value. Understating the
appropriate order may require modifications later, and overstating the order
may result in convergence problems in the next stage."

⏸ The analyst decides what to fit. The example fits both: the search's
choice, then theirs.

## Step 4 · N3 — the search's choice, (0, 0, 0)

    estimate("lutkepohl_poskitt", indices="0, 0, 0")

Three correlated random walks in the logs: 5 parameters (the covariance),
logL −687.91. Hosking's Q does not reject white residuals (p 0.72). Keep the
logL: the next fits are tested against it.

## Step 5 · N3 — their choice, (1, 1, 1)

    estimate("lutkepohl_poskitt", indices="1, 1, 1")

With equal indices the echelon form is the full VARMA(1, 1): 18 coefficients,
logL −659.17, log|Σ̃| 4.744. The echelon start was not admissible, so it
starts from zero and converges in 268 iterations. Most coefficients are small
against their s.e. Two own MA coefficients end at −1.000, and the MA matrix
has a pair of roots at modulus 0.999: nearly non-invertible. This is the
overfitting they warned of.

**In the paper (Table 2):** det Σ̃ = 1.127 × 10⁻¹⁰, which is 4.725 on sima's
scale (sima 4.744). "Clearly the unrestricted VARMA(1, 1) model contains a
substantial number of insignificant coefficients."

## Step 6 · N3 — the VAR(1), and its simplification

    estimate("lutkepohl_poskitt", 1, 0)
    simplify("lutkepohl_poskitt")

The VAR(1) is the (1, 1, 1) form with the MA part at zero: 9 coefficients,
logL −667.68. `simplify` (|t| < 1) holds Kansas City's three lags at zero:
LR 1.71, df 3, p 0.63; AIC and BIC fall. A second pass would drop Kansas
City ← Buffalo as well.

**In the paper:** "In several steps, we have restricted some of them to 0 and
finally obtained the restricted VAR(1) and MA(1) models."

## Step 7 · N3 — their restricted VAR(1) and MA(1)

    estimate("lutkepohl_poskitt", 1, 0, zeros="phi_KansasCity[B^1], AR1[Buffalo<-KansasCity], AR1[Minneapolis<-KansasCity], AR1[KansasCity<-Buffalo]")
    estimate("lutkepohl_poskitt", 0, 1, zeros="theta_KansasCity[B^1], MA1[Buffalo<-KansasCity], MA1[Minneapolis<-KansasCity], MA1[KansasCity<-Buffalo]")

Five coefficients each. sima against Table 2:

| | coefficients (s.e.) | log\|Σ̃\| |
|---|---|---|
| VAR(1), theirs | −.88 (.18), 1.02 (.19) / −.44 (.18), .62 (.19) / .25 (.10) | 4.985 |
| VAR(1), sima | −.871 (.178), 1.024 (.187) / −.438 (.179), .633 (.191) / .253 (.101) | 5.000 |
| MA(1), theirs | −.90 (.20), 1.06 (.20) / −.45 (.20), .67 (.21) / .28 (.10) | 5.004 |
| MA(1), sima | .865 (.192), −1.043 (.202) / .461 (.205), −.686 (.218) / −.289 (.103) | 5.027 |

The rows are Buffalo, Minneapolis and Kansas City; the columns, the lags of
Buffalo and Minneapolis. Each equation depends on those two only. sima's MA
is Box and Jenkins', (I − Θ B) a_t, and theirs is (I + M₁ B) u_t: every MA
coefficient has the opposite sign, and the same size.

Against the search's (0, 0, 0): the VAR(1) gives LR = 2 (−669.13 + 687.91) =
37.6 with 5 df. **The search's choice underfits**, although Hosking's Q did
not see it. The LR on five specific coefficients is a sharper test than a
portmanteau on 24 lags.

**In the paper:** "Note that both models are valid echelon forms with
Kronecker indices (1, 1, 1) in which certain of the freely varying
parameters are 0." Their portmanteau statistics (P12, P20) "do not give any
reason for concern", and the determinants show "a slight preference for the
VAR(1)". sima's logLs agree: −669.13 against −670.47.

⏸ The analyst chooses the model to check. The example takes the restricted
VAR(1).

## Step 8 · N4 — its checking

    check_residuals("lutkepohl_poskitt")

The residual matrices are clean (none beyond the band; about 5 expected by
chance), and the portmanteau matrix shows nothing. The largest transformed
residual, 1974.05 at 4.7 s.d., is on a*₃, which loads Minneapolis +0.71
against Buffalo −0.71. That is the contrast between markets of the
`flour_prices` example, in the 1973–74 grain price shock.

## Step 9 · N5 — the yardstick

    evaluate("lutkepohl_poskitt", 1, 0, 72, horizon=6, zeros="phi_KansasCity[B^1], AR1[Buffalo<-KansasCity], AR1[Minneapolis<-KansasCity], AR1[KansasCity<-Buffalo]")

The yardstick is univariate models built by route U's builder on the same
transformation, and the report names them: a random walk for Buffalo and an
MA(1) for Minneapolis and Kansas City, the first of a tie in art's ranking.
The restricted VAR(1) gains little: RMSE ratios 1.03, 0.94 and 1.00 at one
step, about 1.00 at six. The ratios depend on the yardstick: with the
analyst's models from art as the yardstick (`yardstick=` with their `.pre`,
an AR(1) for Minneapolis and Kansas City) Minneapolis's 0.94 becomes 1.00.

**In the paper:** they leave the comparison to Grubb (1992), who favoured a
VAR(1) for the undifferenced data, and in whose comparison "the MA(1) model
for the first differences did quite well".

**Closing reading.** The echelon form leads straight to a small identified
model: five coefficients, against Tiao and Tsay's 14 parameters. The
dynamics it finds are significant in sample (LR 37.6) and small out of
sample. The levels hold what ties the markets (`flour_prices`), and testing
that is drvec's ground.

**An aside: the bound of the search.** `flour_prices` runs the same search
on the same differences, from three univariate MA(1) models, with the
default `max_index=3`. There SC and HQ choose (1, 0, 0), which is Poskitt's
procedure's choice by HQ in their Table 1. The route is not what changes it:
the univariate ARMA plays no part in the search, and route V with
`max_index=3` gives the same (1, 0, 0). The bound sets the common sample
(T 95 with 3, T 92 with 6), and on these data that flips the choice
(`sima://doc/MANUAL-echelon`, §5.1).

**A second aside: the analyst's models and the 1973 shock.** With the univariate models built in art (a random walk and two AR(1)), and then with the December 1973 – January 1974 step that art finds in all three cities, the cross dynamics of their restricted models stops being significant (LR 5.1, df 3, p 0.16). Whether that shock is an anomaly or the transmission itself is a position, not a result (`sima://doc/MANUAL-echelon`, §5.3). The steps above are theirs.
