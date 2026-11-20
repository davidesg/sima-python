# sima — an evaluation (20-nov-2026)

Where sima stands against its principles (`docs/ARCHITECTURE.md`), after the
homologation of its guided lane with art's (steps P1–P7, sima #26–#32) and
the first trial run on real data. It covers sima at `main` on drvarma main;
the changelog's 0.2.5 is unreleased, and `pyproject.toml` still says 0.2.4.

## 1. How it was evaluated

- **The trial run (rodaje), 19-nov-2026.** The US monetary VAR (IPI, IPC, WTI
  and a rate, monthly, 1990–2007), route U, with the univariate models guided
  in art. Four systems, one per rate (FF, GS1, GS2, GS3), in the guided lane
  in another conversation, with sima's telemetry on (34 calls).
- **Two measurements of the starting values** on the ladder: 59 fits (zero,
  preliminary, OLS; elf and Shea; routes U and V) and 54 fits
  (Hannan-Rissanen and shrinking, on models with MA).
- **The batteries:** the C engines (drvarma, drtran, drvec), the ports, and
  sima's suite (240 passed).
- **A review of the existing documents** of sima, art, mtram and drvarma (C
  and port), done before writing this one.

## 2. What is sound

- **Route U holds.** On the monetary VAR every system passed the gate
  exactly, and the identification read as the economics expects: the FF
  reacts to production, the market rates lead it. With the real optima, the
  order is VAR(1) in all four (VAR(2) against VAR(1): FF p 0.36, GS1 0.84,
  GS2 0.73, GS3 0.75).
- **The guided lane is now art's.** Every node has an envelope with options
  and their calls; the lane is the session's; decisions are recorded as data;
  `where`, `hand_over` and the decision-node map exist. The trial run walked
  it without the assistant improvising the path.
- **The engines are homologated, and the batteries show it.** The new start
  matches between the C and the port to 6 decimals, on both routes.
- **Defects were found where they showed, and fixed with repros** (§3).

## 3. What the trial run and its sequel found

Fixed:

| defect | where |
|---|---|
| the canonical analysis read the levels with harmonics and interventions inside: order 14 instead of 4 | sima BUG-0018 |
| `estimate`'s cache ignored `start`; a fit below its nested model was read as an optimum | sima BUG-0019 |
| from zero, exact ML stalled when the series' scales differ (the GS1 and GS3 VAR(2)): the cause is the scale of the cross terms, not the optimiser's penalty | drvarma BUG-0027 (open by design: the default stays zero); the `ols` start, C and port |
| the port seeded the own AR on route V and the C did not | drvarma #25, atsw-gui #200: neither does |
| with λ = 1 the C library transformed with refactor·(y − 1), fue with refactor·y: a fue `.pre` with d = 0 and a mean was not an optimum in the C ladder | atsw-gui lib/prewhiten BUG-0002 |
| the answers drifted into English | the instructions' language rule |

Open:

- **drvarma's deprecated `.inp` path** (C `transform.c`, port `transform.py`)
  still uses refactor·(y − 1) with λ = 1, and its documents call it the
  identity. After `-split`, the ladder now gives another μ with d = 0. It
  needs a report.
- **No reference case in the batteries has λ = 1, d = 0 and a mean.** That
  is why the library's defect went unseen.
- **drvec's C battery has 4 failures on `main`**, older than this work.

## 4. Route U — the risks that remain

1. **Methodological, and documented** (`DESIGN-jenkins-alavi.md` §1).
   With an AR structure, fitting the univariate models first can lead towards
   the diagonal-AR representation, with misidentification and
   over-parameterisation (Jenkins and Alavi's Series 2). The matrices and the
   echelon form are the instruments against it.
2. **The base.**
   - The strong form uses the analyst's art models.
   - From raw data, `build_univariate` writes light models: no interventions,
     Easter or formal tests. The files, the gate and the hand-over say so.
   - `characterize` and `build_univariate` decide every series in one call,
     against art's measured "one series after another".
3. **Scale.** `load_pre` already warns per series (the dispersion band) and
   about mixed factors or λ (BUG-0011–0013). It does not warn about series
   with the same factor and very different magnitudes. The monetary VAR is the
   case: IPC in %, the rate in basis points. The `ols` start and the guard
   handle it; a warning is pending, together with the units of rates in art.
   Both are the analyst's decisions.
4. **Several maxima with MA.** On Jenkins and Alavi's VARMA(2,1) each start
   ends at a different maximum, each certified: preliminary 15.95, ols 15.56,
   Hannan-Rissanen 13.89. The guard does not see it, because none is below a
   nested model. Within the frame "reproducible, locally optimal"
   (`LADDER_AS_OPTIMISATION.md` §6), estimating from two starts when q > 0
   would make it visible.
5. **The echelon form** replaces the univariate model's regular ARMA on route
   U (`ARCHITECTURE.md` §5). That is declared, and the row factor is tested.

## 5. Route V — the less structured path

What route V gives up is already documented (`STUDY-raw-entry.md` §3.4 and
§4, `STUDY-tiao-box.md` §3.2, `ARCHITECTURE.md` §3):
- **No validated base until N5.** The session's gate certifies the cast on
  white-noise specs and "says nothing about the univariates". Each fit does
  estimate every spec's own AR(p)/MA(q) by exact ML first, and checks it with
  its gate.
- **No interventions.** `characterize` reports outliers and models none. A
  level shift or an outlier ends up in the system's dynamics.
- **Every coefficient is free.** That makes simplification essential: on the
  gas furnace the VAR(6) loses 4–16 % on the gas through 12 useless cross
  coefficients (`STUDY-raw-entry.md` §7).
- **Spurious feedback at a low order**, and **each series' own d is not
  innocent jointly** (`STUDY-tiao-box.md` §3.2).
- **The yardstick.** If the analyst gives no models, it is route U's light
  builder. The evaluation already says so at N5 (`_yardstick_text`). The
  hand-over does not.
- **Starting values.** The least-squares cross terms on the diagonal's own
  models can make the start non-stationary (the gas furnace VARMA(2,1)). It
  falls back to zero and says so.
- **A misleading caveat.** `hand_over` calls a route V spec "a specification
  (.inp), re-estimated at the load; its univariate model was not validated in
  art". But a spec has no univariate model at all.

On the analyst's view (20-nov), route V is the less structured path and a
dangerous one. The suite's recorded decision is to show the two schools, not
settle them (`STUDY-tiao-box.md` §3.1; `STUDY-raw-entry.md` decision 1, a
neutral question). The autonomous lane already defaults to route U
(`DECISION_NODES.md` N0).

## 6. Recommendations, in order

1. **The analyst's decision.** Should the route question stop being neutral,
   with route U the default and route V an explicit choice named as the less
   structured path? This changes a recorded decision, so it is David's.
   Independently of that answer:
   - `hand_over` should list route V's caveats (no interventions, the
     yardstick's origin, every coefficient free);
   - its wrong caveat about the specs should be corrected;
   - `DECISION_NODES.md` should have route V's own stops and caveats.
2. **Interventions on route V.** Carry `characterize`'s outliers into the
   caveats at least, or into the specifications when the analyst accepts
   them.
3. **Two starts when q > 0** (`ols` and `preliminary`), keeping the better
   and saying so when they differ.
4. **The cross-series magnitude warning at the load**, and the units of rates
   in art. Both are the analyst's.
5. **Shrink a non-stationary start** before falling back to zero. Measured:
   ×0.5 is enough on the cases seen. A change in the C and the port.
6. **Coverage:** a reference case with λ = 1, d = 0 and a mean in the C
   batteries. A report for the `.inp` path's Box-Cox (C and port).
7. **The documents of drvarma** (C and port) have no architecture of the
   ladder. Its starts, its homologation matrix and several stale pages
   (`-m`, Shea in pure Python, the wheels) are listed in the review of
   20-nov.
8. **The release:** drvarma 0.3.5 (the `ols` start), sima's caches rebuilt,
   sima 0.2.5, then atsw.
9. **A file for the joint model**, on both routes (`STUDY-raw-entry.md` §4).

## 7. In one paragraph

Route U is the ladder, and what the trial run found there was in the edges
(the start, the cache, a library formula): fixed, homologated, covered. Its
remaining risks are known, one methodological and documented, the others
operational. Route V is the other school, legitimate and documented. In it the
analyst carries more of the judgement, and whether sima should present it as
the exception is the analyst's decision.
