# The decision nodes of a simultaneous model

What the guided/autonomous split splits. A **node** is a point where the
evidence does not determine the answer: two analysts reading the same table
can reasonably differ. Everything else is procedure, and procedure does not
stop to ask. A **stop** is not a node either: there is nothing to weigh, only a
reason not to go on.

For each node: what leaves it undetermined, the evidence, what the guided lane
does, and the **declared default of the autonomous lane** — what the model does
when it sits in the analyst's chair. A default is stated so that it can be
disputed; the autonomous lane writes each decision down with
`record_decision(..., decided_by="LLM")`, and the answers put that call, filled
with the node and its evidence, where the guided lane's pause would be (P2).

The lane is the session's, declared once at the load (`lane=`). Undeclared, it
is guided, and every pause says so. `where(name)` tells where an analysis
stands (P3), and `hand_over(name)` closes it (P7).

The same school as mtram's `DECISION_NODES.md` (the transfer networks) and
art's guided lane, one rung up.

---

## N0 — The entry: the files, their ORDER, the purpose, the route

**Underdetermined by:** everything. No data answers these; they are what the
analyst arrives with.

- **The order of the series.** The order of the files in `load_pre` is the
  Cholesky order of the impulse responses and the variance decomposition, a
  VEC's normalisation (β on the last r) and the frame of the echelon form's A0.
  It is part of the model; `load_pre` restates it.
- **The purpose**, "forecast" or "long run". For a VEC it decides the role of
  the yardstick (C8: a veto or a caveat). It can come with the first question
  (`purpose=` at the load) or at N1c. For a VARMA it decides nothing: rule 1
  holds whatever the purpose (decision of 18-nov-2026).
- **With raw data, the route**: (U) the univariate models first, then the
  system (Jenkins and Alavi; the ladder), or (V) the vector first, the
  univariates only as the yardstick (Tiao and Box). Taken after `characterize`.

**Guided:** ask the three before loading; the order first.
**Autonomous:** the order the files come in, and say it is an assumption; the
purpose only if the analyst gave it (N1c records it otherwise, with its
reason); route U, the ladder, unless the analyst asked for V.

---

## N1 — The gate  · a STOP when it fails

`run_gate`: does the joint cast reproduce the univariate models? Not a node:
**a failed gate stops the analysis** (rule 2) — it is a defect of the engine or
of the files, and nothing estimated on top of it can be trusted.

What *is* a node here: **a file that moved.** A `.inp` (a specification, not an
optimum) is re-estimated at the load; its univariate model has not been
validated in art.
**Guided:** offer to go back to art first. **Autonomous:** go on, and write
down that the file moved and that its model is not validated here; the
hand-over lists it among the caveats.

## N1b — The canonical analysis · not a node

Box and Tiao's reading of the levels. A reading, not a test; sima never
changes a d. It feeds N1c.

---

## N1c — The cointegration question

**Underdetermined by:** the canonical count suggests, it does not decide.
Offered whenever two or more series have d = 1, whatever the count.

**Guided:** offer it with the purpose; the analyst may decline (then N2, the
VARMA in differences). The mixed case (I(0) and I(1)) is an option, never the
default.
**Autonomous:** test the rank whenever two or more series are I(1): the
question is cheap to ask and expensive to skip. Purpose: the one recorded at
N0; if none, "forecast" — the stricter rule — with the reason written.

## C1 — The rank  · a STOP without a finished bootstrap

**No rank is read without a finished bootstrap** (rule 8): a partial job is
never a result, and the asymptotic table is orientation. That is a stop, not a
node. The node is what the finished table leaves open:

- **a tie** (a p-value near the size, or a verdict that flips with p): estimate
  both ranks and compare; `sweep` reads the rank at the neighbouring orders;
- **all reject**: "at least M − 1" — a unit-root question, not a rank;
- **not I(1, r)**: no rank is read; reread the orders of integration.

**Guided:** show the table and the critical values; the analyst decides.
**Autonomous:** the bootstrap's rank. With n / (M p) small, run the sweep
first and argue p, not the rank. **A rank on theory is never the autonomous
default**: only when the analyst gave the theory, and then
`estimate_vec(theory=...)` writes it as such beside the bootstrap's numbers.
The autonomous lane never makes a claim the data cannot make.

## C2 — The roles (the normalisation)

**Underdetermined by:** β is identified up to a normalisation; which series
carry it (`normalise_on`) is a reading of the system, and in a VEC another order
is **another fit**, never a reorder (rule 11).
**Guided:** offer the normalisations that make sense of the canonical weights.
**Autonomous:** the file order (the last r), stated as the assumption it is.

## C3 — Restrictions on α, β and Γ

**Underdetermined by:** each restriction is a hypothesis the analyst brings —
weak exogeneity, a known coefficient, no feedback. Tested by LR, never Wald
(rule 10).
**Guided:** offer the restrictions the estimates suggest (an α near zero; a β
near a round number), one at a time.
**Autonomous:** test only what the estimates point to, one at a time, each
with its record; keep a restriction only when the LR does not reject it.
**When weak exogeneity holds**, the conditional model is a transfer network:
offer mtram, naming output and inputs — never go there (a stop for sima, a
door for the analyst).

## C4 — Exogenous inputs

**Underdetermined by:** an input is a claim about the world. **Guided:** only
the inputs the analyst names. **Autonomous:** none unless the analyst named
them; the autonomous lane does not invent regressors.

## C5 — The long run · not a node

θ, the half-lives, Gonzalo and Ng: a reading of the adopted VEC.

## C6 — Responses and decomposition of a VEC

The **Cholesky order** is the node, as in N6. The bands come only from the
bootstrap (`irf_bands`, a job): no band is drawn from anything partial.

## C7 — Robustness · not a node

The sweep (p, case, subsamples): evidence for C1 and C8, not a decision.

## C8 — The yardstick for a VEC

Always computed and reported (rule 9). Purpose "forecast": a **veto**.
Purpose "long run": a **caveat**, beside the claim. Then `adopt` or
`abandon`, with `why=`.

---

## N2 — The identification: which cross structure

**Underdetermined by:** the CCFs and the matrices speak pair by pair and lag by
lag; several candidates read the same evidence. One order, always (P6):
`identify_cross` (route U: the residual CCFs, the quick reading) →
`identify_matrices` (Jenkins and Alavi's two methods, Tiao and Box's M(l);
route V starts here) → `identify_echelon` when an MA is in sight.

**Guided:** each report with its options; the analyst chooses the candidates.
**Autonomous:** candidates **from the evidence, not from a grid** — the
leads seen (the cross order), the contemporaneous correlation (the
covariance), and, when only some pairs showed anything, the restricted
candidate (`links`) beside the full one that tests it. Never prune a link to
improve a number (rule 6).

## N3 — The candidate, estimated

**Underdetermined by:** a tie — an LR p near 0.05, or two candidates that read
the same. **Both lanes:** estimate both and compare; a tie is not resolved on
paper.

## N4 — The in-sample evidence

`check_residuals`: large residuals (with dates: the entry to interventions,
which belong to art), the residual correlation matrices, the portmanteau.
**Guided:** the analyst reads them. **Autonomous:** a residual problem in one
series goes back to art for that series; one between series, back to N2.

## N4s — Simplification (Tiao and Box)

Coefficients with |t| < 1 at zero, refitted, tested by LR (and AIC, BIC).
**Autonomous:** adopt a round only when the LR does not reject it and both
criteria fall; several rounds, each recorded.

## N4t — Structure  · a STOP for sima when a triangular ordering stands

Is the system simultaneous? Each pair's cross terms at zero by LR, and every
triangular ordering. **One that stands is a transfer network**: offer mtram,
never go. A low-order fit can show a spurious feedback: say so.

## N4b — The MA wall

A fit that stopped on the MA invertibility wall is **ill-defined there**: it is
never presented as an optimum (both lanes). `study_estimation` gives the roots,
the second path (Shea), the restarts and the menu.
**Autonomous:** lower the MA order, or the echelon form; record why.

---

## N5 — The yardstick: keep the VARMA, or the univariates

**Rule 1:** a VARMA is kept only if it forecasts better than the univariate
models **out of sample**, same window. In-sample significance is necessary, not
sufficient. Whatever the purpose: the purpose relaxes the yardstick only for a
VEC (C8).

**Underdetermined by:** the pattern across series and horizons — a VARMA can
gain on one series at short horizons and lose elsewhere. Which cells matter is
the analysis' question.
**Guided:** the table and the options; the analyst adopts.
**Autonomous:** keep it only if it gains in most cells of the series the
analysis is about; otherwise the univariates — **a finding, stated plainly**.
Then `adopt(model=..., why=...)` or `abandon(...)`: the decision as data (P4).

## N6 — Use: forecast, responses, decomposition

The **Cholesky order** is an identifying assumption (rule 4). With a strong
contemporaneous correlation, `reorder` and compare before calling a response a
finding. The final-stage tools warn when they act on a model that is not the
adopted one.

---

## What is NOT a node

- **The horizon and the window** of `evaluate` and `forecast`: choices of
  presentation, set once and stated, not decisions about the model.
- **The number of bootstrap replications**: enough for the verdict to be
  stable; a parameter of the job, not of the model.
- **The figures**: they show; they do not decide.

## The stops, together

| where | the stop |
|---|---|
| N1 | the gate fails |
| C1 | no finished bootstrap: no rank, no β, no equilibrium |
| C1 | the model under H0 is not I(1, r) |
| C3 | weak exogeneity holds: the conditional model is mtram's |
| N4t | a triangular ordering stands: a transfer network, mtram's |
| N4b | a fit on the MA wall is not an optimum |
