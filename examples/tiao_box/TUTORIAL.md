# Tutorial — Tiao and Box: the gas furnace

*The step-by-step guide of the worked example, for the assistant that leads it.
The method is in the study `sima://doc/STUDY-tiao-box` (§1, Tiao and Box
1981). The other two forms are `sima://example/jenkins_alavi` and
`sima://example/lutkepohl_poskitt`; Tiao and Box's tools on data in levels
that need a difference are `sima://example/flour_prices`.*

## For the assistant: how to lead it

* **Guided lane**, as in a real analysis: ONE step at a time. Run the call,
  present the report as always (the table as it is, what it shows, the
  conclusions, the alternatives) and stop at ⏸. The analyst decides.
* After the report, and only then, add **"In the paper"**: what Tiao and Box
  (1981, §5.2, Tables 12–14) found at that step. Compare the numbers; say
  where they differ and why.
* **The scale.** sima's variances are in the data's units squared × 10⁴
  (Tiao and Box's .0359 is sima's 359). Their series are centred (gas rate
  + .057, CO2 − 53.5); sima estimates the means.
* The lesson of this example: the vector first, without telling the method
  which series is the input. The identification finds the one-sided
  relation, the delay and the input's own model by itself, but only at the
  right order: at AR(2) it finds a feedback that is not there.
* The session is the one `load_example` opened (by default `tiao_box`).

---

## Step 0 · N0r — the data (already loaded)

Box and Jenkins' Series J: the input gas rate and the output CO2 of a gas
furnace, 296 pairs at 9-second intervals. The table has no dates, so sima
counts the observations as years from 1000: an index, nothing more.

**In the paper:** "This set of data was employed in Box and Jenkins (1970) to
illustrate a procedure of identification, fitting, and checking of a transfer
function model … We shall analyze the data using the present approach where
no distinction is made between an input and output variable and the fact that
no feedback could occur in the system is not used."

## Step 1 · N0c — the transformation

    characterize("tiao_box")

d = 0 for both. ADF rejects a unit root in levels (p 0.01 and 0.02); KPSS
objects at 5 %, so art calls it ambiguous and stays at d = 0. For the CO2,
art's engine proposes logs by its domain rule ("a quantity goes to logs"),
although the mean-sd correlation is +0.06 in levels: there is nothing to
correct. Tiao and Box, like Box and Jenkins, work in levels:

    characterize("tiao_box", set="InputGasRate: lam=1, d=0; CO2: lam=1, d=0")

## Step 2 · N0v and N1 — route V, the gate

    write_specs("tiao_box"); run_gate("tiao_box")

Route V: each series gets a specification with only its transformation and
its mean. No univariate model enters the system. The gate passes; its
diagonal is white noise around the means, not a yardstick.

## Step 3 · N2 — Tiao and Box's stepwise M(l)

    identify_matrices("tiao_box", nlags=11)

Method 2 does not apply on route V: there are no univariate models to
prewhiten with. Look at method 1 and the stepwise table:
* M(l) = 1649.7, 665.1, 31.7, 22.5, 5.6, 12.8, 1.8, 8.0, …: significant up
  to **l = 6**, with l = 5 not significant on the way;
* the diagonal of Σ̃ settles after lag 3 for the gas (1022, 369, 358, 356)
  and more slowly for the CO2 (3464, 690, 632, 588, 579, 566).

**In the paper (Table 12):** M(l) = 1650, 665, 31.7, 22.5, 5.6, 12.9, 1.8,
8.0, 3.5, 0, 2.0. "The M(l) statistic … suggests that an AR(6) model might be
appropriate." The values agree to the first decimal up to l = 8.

⏸ The analyst decides the order. The example fits the VAR(6).

## Step 4 · N3 — the full VAR(6)

    estimate("tiao_box", 6, 0)

logL −2638.76, 28 parameters. The
residuals are white (Hosking Q(8) p 0.25). The gas's first own coefficient is
1.92 (s.e. .057).

**In the paper (5.6):** 1.93 (.06) for the same coefficient.

## Step 5 · N4t — the structure: is there feedback?

    structure("tiao_box")

Each series dropped from the other's equation, refitted, and tested by LR:
* CO2 → InputGasRate: LR 6.01, df 6, p 0.42. **The CO2 does not enter the
  gas equation.**
* InputGasRate → CO2: LR 205, df 6. The gas enters the CO2 equation.
* The triangular ordering InputGasRate → CO2 stands: **a transfer function**.
  sima offers the network to mtram (drtran), the rung where the input is
  declared. It does not hand it over on its own.

**In the paper:** "φ̂₁₂(l) are small compared with their standard errors over
all lags, confirming (as in this case is known from the physical nature of the
apparatus generating the data) that there is a unidirectional relationship …
involving no feedback. Also, φ̂₂₁(l) is small for l = 1, 2 … implying a delay
of 3 periods."

## Step 6 · N3–N4t — the warning of their Table 14

    estimate("tiao_box", 2, 0); structure("tiao_box")

At AR(2) the picture changes: CO2 → InputGasRate gives LR 32.2 with df 2,
and **no triangular ordering stands**. The fit reports a feedback that the
furnace does not have.

**In the paper (Table 14):** "If only AR(1) or AR(2) were considered, one
might be led to believe mistakenly that there was a feedback relationship
between these two series." The one-sided relation appears at p = 3, once the
input's own model (an AR(3)) is captured. The order of the fit comes before
any reading of its structure.

## Step 7 · N3 — simplification

    estimate("tiao_box", 6, 0); simplify("tiao_box")

`simplify` (|t| < 1) holds 9 coefficients at zero: LR 6.21, df 9, p 0.72;
AIC and BIC fall. Four of the nine are the CO2's lags 3 to 6 in the gas
equation, and two are the gas's first two lags in the CO2 equation: the
structure and the delay of Step 5, found coefficient by coefficient. After the refit, four
more have |t| < 1.

**In the paper:** "Considerable simplification is almost invariably possible
after an initial model has been fitted." In this example their zeros also
come from what is known about the system.

## Step 8 · N3 — their restricted AR(6)

    estimate("tiao_box", 6, 0, zeros="phi_InputGasRate[B^4], phi_InputGasRate[B^5], phi_InputGasRate[B^6], AR1[InputGasRate<-CO2], AR2[InputGasRate<-CO2], AR3[InputGasRate<-CO2], AR4[InputGasRate<-CO2], AR5[InputGasRate<-CO2], AR6[InputGasRate<-CO2], AR1[CO2<-InputGasRate], AR2[CO2<-InputGasRate], phi_CO2[B^5], phi_CO2[B^6]")

Their zeros: the gas's own AR(3), no CO2 in the gas equation, a delay of
three periods, and the CO2's own AR(4). 15 parameters, logL −2647.48. Against
the full VAR(6): LR 17.4, df 13, and the data do not object.

| | Tiao and Box (5.7) | sima |
|---|---|---|
| the gas's own AR(3) | 1.98 (.06), −1.38 (.10), .35 (.06) | 1.968 (.054), −1.364, .339 |
| Box and Jenkins' input model (5.4a) | 1.97, −1.37, .34 | |
| the CO2's own φ₂₂(1), φ₂₂(2), φ₂₂(3) | 1.53, −.58, −.14 | 1.530, −.594, −.128 |
| the delay, φ₂₁(3) | −.53 | −.534 |
| Var(a₁), Var(a₂) | .0359, .0561 | .0351, .0554 |
| correlation of a₁ and a₂ | "negligible" | −.06 |

The model's transfer weights, v_j = φ₂₁(j) + Σ_l φ₂₂(l) v_{j−l}, are
arithmetic on the printed coefficients:

| v₃ … v₁₂ | |
|---|---|
| Box and Jenkins' transfer model (5.4b) | −.53 −.67 −.89 −.51 −.29 −.17 −.09 −.05 −.03 −.02 |
| Tiao and Box's AR(6) (Table 13) | −.53 −.70 −.77 −.48 −.26 −.09 −.01 .01 .00 −.01 |
| sima's restricted AR(6) | −.53 −.68 −.80 −.52 −.30 −.12 −.04 −.01 −.02 −.03 |

**In the paper:** at first sight the AR(6)'s dynamic model "appears markedly
different" from Box and Jenkins'. The reason is that in the AR form "the
denominators of the dynamic model and of the noise model are constrained to
be identical". The impulse weights show that "the models are in fact very
similar".

⏸ The analyst chooses the model to check. The example takes their restricted
AR(6).

## Step 9 · N4 — its checking

    check_residuals("tiao_box")

One residual correlation beyond the band (about 1.2 expected by chance), the
gas with itself at lag 4, and nothing in the portmanteau matrix. The largest
transformed residual is observation 1264, at 6.2 s.d.: a large shock in an
engineering record, worth asking about before reading the rest.

**In the paper:** "Examination of the pattern of the cross-correlations of
the residuals suggests that the model is adequate."

## Step 10 · N5 — the yardstick

    evaluate("tiao_box", 6, 0, 200, horizon=3, zeros="<the same 13 zeros>")

Route V builds univariate models now, with route U's quick builder, only as the
yardstick. The CO2 gains a quarter to nearly 40 % of its RMSE: ratios 0.76,
0.64 and 0.61 at one, two and three steps. The gas gains too (0.82–0.92),
but its equation has no CO2 in it. That gain is its own AR(3), Box and
Jenkins' model, against the ARMA(1, 1) the quick builder gave it. An analyst
would review that model in art.

**Closing reading.** Tiao and Box's method, given two series and no roles,
finds what Box and Jenkins were told:
- the gas drives the CO2, with a delay of three periods;
- the gas follows an AR(3);
- the transfer weights match.

The system is a transfer function, so mtram is the natural next rung. On
these data the echelon form's search gives (2, 2) by SC and (3, 2) by HQ
(`sima://doc/MANUAL-echelon`, Part 4): a smaller rival to the VAR(6).
