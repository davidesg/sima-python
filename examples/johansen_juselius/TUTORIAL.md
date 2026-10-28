# Tutorial — Johansen and Juselius (1990): Danish money demand

*The step-by-step guide of the worked example, for the assistant that leads it.
The method is in `sima://doc/MANUAL-vec` (the study behind it, `sima://doc/STUDY-vec`) and the decisions in
`sima://doc/PLAN-vec` (§0). The data and the models: the example's README.*

## For the assistant: how to lead it

* **Guided lane**, ONE step at a time: present each report as always, and stop
  at ⏸. The analyst decides.
* After each report, add **"In the paper"**: what Johansen and Juselius (1990)
  find at that step.
* The lesson: at n = 55 the bootstrap and the asymptotic table part ways. The
  rank is the bootstrap's; a rank adopted on theory is written as such, and
  everything after it is conditional on it.
* The univariate models were built by sima's raw entry, NOT reviewed in art:
  say so, and offer art for any series the analyst doubts.

---

## Step 1 · N1 — the gate

    run_gate("johansen_juselius")

PASSED. Built by sima's raw entry: LRM with deterministic quarterly
seasonality (cos, sin, alter), the others without; d = 1 for all.

## Step 2 · N1b — the canonical analysis of the levels

    canonical_analysis("johansen_juselius")

M(l) on the levels: a VAR(2). Two components near 1 of four differenced series:
up to two stationary combinations are possible. The menu leads with N1c.

## Step 3 · N1c — the question, and the purpose

    prepare_vec("johansen_juselius", purpose="long run", p=2, case="2")

Purpose: "long run" (the money-demand relation). Case 2, the constant
restricted to the relation, is theirs.

## Step 4 · C1 — the rank, by parametric bootstrap

    rank_test("johansen_juselius", B=499)          (cached)

* r = 0 → 1: LR 25.91 against the bootstrap's 95 % value 29.78, p 0.12;
* r = 1 → 2: LR 21.22 against 23.53, p 0.10;
* r = 2 → 3: LR 4.07 against 14.07, p 0.70.

**No comparison is rejected at 5 %: the bootstrap proposes r = 0.** The
asymptotic column (orientation only) rejects r = 0 and r = 1 at 10 %. At
n = 55, with 25 to 43 parameters, the asymptotic critical values are too small:
the bootstrap's are larger at every step.

**In the paper:** Johansen and Juselius find r = 1 with the asymptotic trace
test (and discuss r = 2), at the edge of their tables. sima's exact-likelihood
test, calibrated by simulation, does not confirm it at 5 %.

**The report also says SMALL SAMPLE FOR THIS ORDER**: n / (M p) = 6.75, below
15, so the verdict can flip with p, and its first option is the sweep over p
(`sweep(p="1,2,3", B=499)`). Say so, and say that it is the right next step in
a real analysis. In this tutorial do not launch it unless the analyst asks:
its three rank jobs are not in the example's cache, and four series at B = 499
take hours. p = 2 is the paper's specification, and the lesson here is the
bootstrap against the asymptotic table at that p.

## Step 5 · C2 — r = 1 ON THEORY

    estimate_vec("johansen_juselius", r=1, normalise_on="LRM",
                 theory="Johansen and Juselius: one money-demand relation")

The rank is adopted on theory, against the bootstrap, and written in the guion
as such. Normalised on money (LRM, the Y1 block):

    LRM = 1.12 LRY − 5.16 IBO + 4.26 IDE  (+ a constant)

alpha on LRM −0.17 (t −2.3): money corrects; on income +0.14 (t 1.9).

**In the paper:** LRM = 1.03 LRY − 5.21 IBO + 4.22 IDE: the same relation, a
unit income elasticity and the two rates with opposite signs.

## Step 6 · C3 — weak exogeneity, by LR

    test_restriction("johansen_juselius", weakex="IBO")
    test_restriction("johansen_juselius", weakex="IDE")
    test_restriction("johansen_juselius", weakex="LRY")

The bond rate (LR 0.0003, p 0.99) and the deposit rate (LR 2.07, p 0.15) are
weakly exogenous; income only at the edge (LR 4.31, p 0.04). drvec's free
model and the adopted VEC agree (one LR each).

**In the paper:** income and the two rates are weakly exogenous; money is the
variable that adjusts.

## Step 7 · C5 — the long run

    long_run("johansen_juselius")

theta as above. The textbook half-life on money is 3.8 quarters; the model's,
the equilibrium error's own response, about 3. Gonzalo and Ng: three common
trends; the bond rate's variance is all permanent, money's 82 % permanent at
one quarter.

## Closing

    export_guion("johansen_juselius")

The path says, at C1, that the bootstrap did not find the relation, and at C2
that it was adopted on theory: both are findings.
