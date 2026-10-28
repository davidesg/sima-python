# Tutorial — Lütkepohl's E1: investment, income and consumption

*The step-by-step guide of the worked example, for the assistant that leads it.
The method is in `sima://doc/MANUAL-vec` (the study behind it, `sima://doc/STUDY-vec`) and
the decisions in `sima://doc/PLAN-vec` (§0).*

## For the assistant: how to lead it

* **Guided lane**, ONE step at a time: run the call, present the report as
  always (the table as it is, what it shows, the conclusions, the
  alternatives) and stop at ⏸. The analyst decides.
* After each report, add **"In the book"**: what Lütkepohl (2005, ch. 7)
  finds at that step.
* The lesson: the rank is the bootstrap's (B = 499); the VEC's long run is
  read with two half-lives that disagree; and an ill-defined fit is declared,
  never presented as an optimum.
* The session is the one `load_example` opened (by default `lutkepohl_e1`).

---

## Step 1 · N1 — the gate

    run_gate("lutkepohl_e1")

PASSED. The files are random walks with drift in logs (fue): the yardstick at
C8 is that.

## Step 2 · N1b — the canonical analysis of the levels

    canonical_analysis("lutkepohl_e1")

Two components near 1 of three differenced series: one stationary combination
is possible. The menu leads with N1c.

## Step 3 · N1c — the question, and the purpose

    prepare_vec("lutkepohl_e1", purpose="long run", p=2, case="2")

The purpose: "long run" (the consumption-income relation). p = 2 and case 2 (a
restricted constant, no drift in the relation) are the specification drvec's
oracle runs on E1.

## Step 4 · C1 — the rank, by parametric bootstrap

    rank_test("lutkepohl_e1", B=499)          (cached)

* r = 0 → 1: LR 58.65 against the bootstrap's 95 % value 22.59, p 0.002 (the
  floor, 1/(B+1)): rejected;
* r = 1 → 2: LR 6.02 against 13.22, p 0.35: not rejected.

**r-hat = 1.** The asymptotic table (orientation only) agrees here.

**In the book:** Lütkepohl finds one cointegration relation in this system
(Johansen's trace test, ch. 7–8).

## Step 5 · C2 — the VEC at r = 1

    estimate_vec("lutkepohl_e1", r=1)

beta normalised on consumption: cons = 0.03 invest + 0.93 income + a stationary
error (investment's coefficient not significant, t −0.6). alpha: income −0.23
and consumption −0.31 (both |t| > 4), investment +0.04 (t 0.25). The
normalisation's share is 50 %: well defined.

## Step 6 · C3 — who corrects, by LR

    test_restriction("lutkepohl_e1", weakex="invest")
    test_restriction("lutkepohl_e1", weakex="income")
    test_restriction("lutkepohl_e1", weakex="cons")

Investment is weakly exogenous (LR 0.06, p 0.80): it does not adjust to the
consumption-income equilibrium. Income (LR 22.1) and consumption (LR 47.2) do.

## Step 7 · C5 — the long run, and two half-lives

    long_run("lutkepohl_e1")

The textbook half-life on consumption, ln 0.5 / ln(1 − 0.31): about 1.9
quarters. The MODEL's — the equilibrium error's own response, short run
included — does not halve until about 52 quarters: the stationary form has a
root of modulus 0.99. The two disagree, and the second is the model's: the
relation is stationary but very persistent. Gonzalo and Ng: investment's
variance is almost all permanent at every horizon; consumption's is mostly
transitory at one quarter (15 % permanent) and permanent in the long run.

## Step 8 · C8 — the yardstick

    evaluate("lutkepohl_e1", estwin=72, horizon=8)

From 13 origins the VEC forecasts consumption and income better than the
random walks with drift at 2-8 quarters (ratios 0.56-0.95), investment
slightly worse. The purpose being the long run, the yardstick is reported as
a caveat; here it also speaks for the VEC.

## Step 9 · C2 again — an ill-defined fit

    prepare_vec("lutkepohl_e1", purpose="long run", p=2, q=1, case="2")
    estimate_vec("lutkepohl_e1", r=1, theory="r = 1 from the q = 0 bootstrap")

With an MA term every start of drvec's search stops on criterion 3 (the line
search finds no lower point), between logL 760.5 and 773.1: a flat ridge, not
a maximum. estimate_vec DECLARES it: "not a demonstrated maximum". The menu:
more starts (multistart), a lower q (step 5's model), or the declaration in
the guion. The point is never presented as an optimum.

## Closing

    export_guion("lutkepohl_e1")
