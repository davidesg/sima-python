# sima — architecture and principles

The map above sima's documents: the principles it inherits from art and mtram,
the layers that carry them, and its two paths, route U (the ladder, Jenkins and
Alavi) and route V (the vector first, Tiao and Box). It states each thing once
and points to where it is argued and measured. Where the details live:

- `DESIGN.md`: the rungs, the seam between engine and assistant, the protocol;
- `DECISION_NODES.md`: node by node, with the declared autonomous defaults and
  the stops;
- `STUDY-raw-entry.md`: the two routes from raw data;
- `STUDY-tiao-box.md`, `DESIGN-jenkins-alavi.md`: the two schools;
- `MANUAL-*.md`: the methods (Jenkins and Alavi, the echelon form, the VEC).

The principles of the suite are argued in art (`art-python/docs/ARCHITECTURE.md`,
`ASSISTANT_LAYER_PROPOSAL.md`) and mtram (`drtran-python/docs/DECISION_NODES.md`,
`LADDER_AS_OPTIMISATION.md`). An evaluation of where sima stands, for people
rather than the assistant, is in `reviews/2026-11-20-sima-evaluation.md`.

## 1. The principles

They come down the ladder from art and mtram. They are named, not numbered:
"P1–P7" in sima's code and changelog are the steps of the guided lane's
homologation with art, not these.

**The file is the contract** (art's instructions; mtram's
`LADDER_AS_OPTIMISATION.md` §1–2).
- A `.pre` is an optimum, rerunnable: fue on it does not move the numbers.
  An `.inp` is a specification, and a `.pre` that is edited becomes an `.inp`.
- Only the program that estimated may write a `.pre`. sima never writes one
  for a system (rule 12).
- fue's format is the base of everything. Every engine reads it as fue
  writes it, Box-Cox included: refactor·y with λ = 1.

**The ladder: the univariate models first** (`DESIGN.md` §1; drvarma's
`docs/LADDER.md`; atsw-gui `engines/drvarma/docs/DESIGN-v5-ladder.md`).
- A system starts from each series' univariate model on its diagonal. The
  joint fit then re-estimates the own models together with the cross terms
  (`fixarma` is off): **the own structure is the univariate model's, and its
  values start at its optimum**.
- The gate makes two claims (`LADDER_AS_OPTIMISATION.md` §2.1):
  - the joint cast reproduces the univariate likelihoods (the crossing);
  - whether the files were optima (a file that moves is a specification).
- Starting values follow the same rule. A preliminary estimate adds only the
  relation (cross terms, covariances); it never replaces the own models
  (§4). The echelon form is the declared exception: its own terms come from
  its index table (§5).

**The univariate model is the yardstick** (rule 1; rule 9; `PLAN-vec.md`
decision 6).
- A VARMA is kept only if it forecasts better out of sample. When none does,
  the univariate models are the result: a finding.
- For a VEC whose purpose is the long run, the yardstick is a caveat, not a
  veto: imposing cointegration often helps little at short horizons
  (Christoffersen and Diebold).

**Engines ship numbers; the assistant argues** (`DESIGN.md` §2; art's
`ASSISTANT_LAYER_PROPOSAL.md` §5).
- Caveats travel as data, and there is no hard-wired recommendation.
- **The engines are homologated**: the port follows the C, and a fix starts
  in the C and both move together.
- What works is not touched: engine defaults pinned by the batteries stay.

**The decisions are the analyst's** (`DECISION_NODES.md`; art's
`ARCHITECTURE.md` §8).
- **The same computation in both lanes.** Guided and autonomous differ in who
  decides, never in what is computed: with the same choices they reach the
  same model (mtram).
- **In the guided lane the turn ends at the pause.**
- **The autonomous lane never makes a claim the data cannot make**
  (mtram).
- **Never decide nodes in batch.** art also measured "one series after
  another"; see §6 for where sima does not yet follow it.
- Every decision is recorded with its reason. sima keeps it as data: open,
  closed, adopted, set aside.

**Nothing partial is a result; a stop is not a decision.** These are listed
in `DECISION_NODES.md`:
- no rank without a finished bootstrap (rule 8), unless it is adopted on
  theory and written as such;
- a fit on the MA wall is not an optimum;
- a fit below a model it nests is a failed search;
- a failed gate, a model that is not I(1, r), or a triangular or conditional
  system (which is mtram's) stops the path.

**What the numbers can be compared with** (`LADDER_AS_OPTIMISATION.md` §6):
- likelihoods are not comparable across different d;
- what is reproducible is a local optimum, not a global one;
- a test on an inadequate model is not a test (art's
  `AUTONOMOUS_PIPELINE.md` §4).

## 2. The layers

```
 the conversation (MCP)        tools · sima://protocol · sima://doc/...
 ┌──────────────────────────────────────────────────────────────────┐
 │ mcp_server · mcp_vec        the protocol, the tools, the instructions │
 │ lane (one wrapper on every tool): the lane · decisions · telemetry│
 │ envelope · evidence · vec · levels · status · figures · scale     │
 │ guion (the record) · session (the state) · jobs (bootstraps)      │
 └──────────────────────────────────────────────────────────────────┘
        numbers and caveats as data
 drvarma (the ladder; C ⇄ port) · drvec (C ⇄ port) · fue (the cast) · pyfug
```

`sima.lane` is the one place where the session's lane, the bookkeeping of
decisions and the opt-in telemetry act. A failure there never costs a tool
its answer.

## 3. The two routes

Both meet at the same session, the same nodes and the same yardstick. They
differ in what the system is built on. The two schools disagree, and sima
shows it rather than settling it (`STUDY-tiao-box.md` §3.1). Jenkins and
Alavi's own advice is to use both (`DESIGN-jenkins-alavi.md` §1).

| | route U — the ladder (Jenkins and Alavi) | route V — the vector first (Tiao and Box) |
|---|---|---|
| input | one `.pre` per series. The strong form uses the analyst's models from art; from raw data, `build_univariate` writes light ones, not reviewed in art | raw data → `characterize` → one `.inp` specification per series: λ, d, harmonics, mean, plus a free AR(p)/MA(q) per order (`STUDY-raw-entry.md` §3.4) |
| interventions | those of the `.pre` (decided in art, in the strong form) | none: `characterize` reports outliers, models none |
| the session's gate | certifies the univariate models | certifies the cast; the base specs are white noise (a random walk with d = 1) |
| the own dynamics | start at the univariate optimum, structure fixed, values re-estimated jointly | each fit first estimates every spec's own AR(p)/MA(q) by exact ML (its own gate), then everything jointly |
| identification | CCFs of the prewhitened residuals → matrices → echelon | the vector: R_k, S_k, Tiao and Box's M(l) → echelon |
| the LR of a fit | against the univariate models (for the plain VARMA; the echelon form's is against itself without cross terms) | against the same model without cross terms: m own AR(p)/MA(q) models |
| the yardstick (N5) | the analyst's models | the analyst's if given, else route U's builder; the evaluation says which (`_yardstick_text`) |
| files | `.pre` in; no file for the system | `.inp` specifications that never become `.pre`; no file for the system (`STUDY-raw-entry.md` §4) |

What route V gives up, it gives up knowingly, and it is where the analyst
carries more of the judgement: no validated base until N5, no interventions,
every coefficient free (simplification matters most here). What route U
risks is documented too: with an AR structure, the univariate models first
can lead towards the diagonal-AR representation and over-parameterisation
(`DESIGN-jenkins-alavi.md` §1).

## 4. Starting values

Exact ML from a poor start can stop far from the optimum. On the US monetary
VAR the zero start stopped the VAR(2) after two iterations, 50 points below
its VAR(1). The cause was the scale of the cross terms (drvarma BUG-0027).

| start | seeds | where |
|---|---|---|
| `zero` | nothing beyond the univariate models | C and port; **the engines' default** |
| `ols` | the original drvarma's `init_varma` in the ladder: the cross AR terms = +Φ_k from the least squares of the VAR(p) (Box and Jenkins); Q's covariances = the residuals' correlation × √(Q_ii Q_jj), with the gate's Q_ii (Q₁₁ = 1); the cross MA terms stay at zero | C (`-start ols`) and port, homologated |
| `preliminary` | Jenkins and Alavi's preliminary estimates of the cross terms | port only |
| `echelon` | Lütkepohl and Poskitt's stage II least squares: own, cross, A₀, Q | port only (the echelon form) |

- **What sima uses:** `ols` when the installed drvarma has it (drvarma >
  0.3.4), else the engine's zero.
- **The guard** (BUG-0019): a fit below a model it nests, or one that
  stalled, is retried once from `ols` (or `preliminary` with an older
  drvarma), and the report says so.
- **When the start fails:** if a start makes the system non-stationary, it
  falls back to zero and says so.

## 5. The branches

**The echelon form** (Lütkepohl and Poskitt; `MANUAL-echelon.md`) is the
third instrument of N2–N3 in either route, for an MA or a fit on the wall.
- Its Kronecker indices come from the data; A₀ is triangular, so the order of
  the series is part of the model.
- On route U its own AR(n_i)/MA(n_i) replaces each univariate model's
  regular ARMA. This is the declared departure from the ladder. The seasonal
  factors kept from the `.pre` multiply the whole row, and that is checked
  by LR.

**The VEC** (`MANUAL-vec.md`, `PLAN-vec.md`): with two or more I(1) series,
the cointegration question comes first (N1c). The rank comes from drvec's
bootstrap, then C2–C8.

## 6. Where sima departs from its inheritance, knowingly

- **`build_univariate` builds univariate models.** mtram's rule is that an
  assistant one rung up does not. sima says so in every file, the gate and
  the hand-over, and offers art for each series.
- **`characterize` and `build_univariate` decide every series in one call.**
  art measured "one series after another" as the safer practice. Not yet
  followed.
- **The lane is set per session, not per call as in art.** This is
  deliberate: per call is what let the pause into art's autonomous lane
  (art BUG-0181).
- **The echelon form** (§5).
