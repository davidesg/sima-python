# sima — an evaluation (20-nov-2026)

Where sima stands against its principles (`docs/ARCHITECTURE.md`), after the
homologation of its guided lane with art's (P1–P7, sima #26–#32) and the first
trial run on real data. It covers sima at `main` (0.2.5, unreleased) on
drvarma 0.3.4.

## 1. How it was evaluated

- **The trial run (rodaje), 19-nov-2026.** The US monetary VAR (IPI, IPC,
  WTI and a rate, monthly, 1990–2007), route U, with the univariate models
  guided in art. Four systems, one per rate (FF, GS1, GS2, GS3), in the guided
  lane and in another conversation, with sima's local telemetry on (34
  calls).
- **Two measurements of the starting values** with the ladder:
  - 59 fits: zero, preliminary and OLS, with elf and Shea, on routes U and V;
  - 54 fits: Hannan-Rissanen and shrinking, on models with MA.
- **The reference batteries** of the C engines (drvarma, drtran, drvec) and
  of the ports, and sima's suite: 240 tests.

## 2. What is sound

- **Route U is structured, and it holds.** It inherits the ladder whole:
  - the analyst's univariate models;
  - the gate;
  - identification from the evidence, in one order;
  - the analyst's models as the yardstick.

  On the monetary VAR every system passed the gate exactly, the identification
  read as the economics expects (the FF reacts to production; the market
  rates lead it), and the order came out VAR(1) in all four. VAR(2) against
  VAR(1), once the optimum was the real one: FF p 0.36, GS1 0.84, GS2 0.73,
  GS3 0.75.
- **The guided lane is now art's.** It has:
  - the envelope at every node, with options and their calls;
  - the lane in the session;
  - decisions recorded as data;
  - `where`, `hand_over`, and the decision-node map.

  The trial run walked it without the assistant improvising the path.
- **The engines are homologated and say so.** The new start is the same in
  the C and the port, to 6 decimals on both routes. The batteries confirm
  that nothing else moved.
- **Failures are caught where they show.** The two bugs of the trial run
  were caught by the analyst and the telemetry, and fixed with repros:
  - the cache ignored the start, and a VAR(2) below its VAR(1) was read as
    an optimum (sima BUG-0019);
  - the cause underneath, the scale of the cross terms (drvarma BUG-0027).

## 3. What the trial run and its sequel exposed

Fixed:

| defect | where | fix |
|---|---|---|
| the canonical analysis read the levels with harmonics and interventions inside: order 14 instead of 4 | sima BUG-0018 | `sima.levels` |
| `estimate`'s cache ignored `start`; a fit below its nested model was read as an optimum | sima BUG-0019 | the paths and the guard |
| from zero, exact ML stalls when the series' scales differ (the GS1 and GS3 VAR(2)) | drvarma BUG-0027 | the `ols` start, C and port; default unchanged |
| the port seeded the own AR on route V and the C did not | drvarma #25, atsw-gui #200 | neither seeds the own models (P2) |
| with λ = 1 the C library used refactor·(y − 1), fue refactor·y: a fue `.pre` with d = 0 and a mean was not an optimum in the C ladder | atsw-gui lib/prewhiten BUG-0002 | fue's formula in the library and drtran's bands |
| the answers drifted from the user's language into English | instructions | the language rule strengthened |

Open:

- **drvarma BUG-0027 stays open by design.** The engine default is still the
  zero start (P4). sima avoids the stall with the `ols` start once drvarma
  ships it, and with the guard until then.
- **No reference case in the batteries had λ = 1, d = 0 and a mean**, which is
  why lib/prewhiten BUG-0002 went unseen. That gap in coverage is worth
  closing.
- **drvec's C battery has 4 failures on `main`** (reader round-trip 1 and 2,
  the chisq probe, BUG-40), older than this work.

## 4. Route U — remaining risks

1. **The base can be weak without anyone noticing.** From raw data,
   `build_univariate` writes light models, not reviewed in art: no
   interventions, Easter or formal tests. The files and the gate say so, but
   the system is built on them all the same.
2. **Scale.** Series in very different units (a rate in basis points beside
   prices in %) make the cross terms of a natural size of 0.01 or 100 for an
   optimiser that assumes 1. The `ols` start and the guard handle it, but the
   load says nothing; a warning there is pending the analyst's decision, along
   with the units of the rates in art.
3. **Several maxima with MA.** On Jenkins and Alavi's VARMA(2,1) each start
   lands on a different maximum: preliminary 15.95, ols 15.56, Hannan-Rissanen
   13.89, all certified. The guard does not see it, because none is below a
   nested model. Estimating from two starts when q > 0 would see it.
4. **The echelon form replaces each univariate model's regular ARMA** on
   route U. That is a departure from P2 that the method needs. The row factor
   is checked by LR, but the analyst should know the univariate optimum is
   gone from those rows.

## 5. Route V — the less structured path, and dangerous

Route V gives up most of what makes route U safe (`ARCHITECTURE.md` §5):

1. **No validated base.** The specifications carry only each series'
   transformation. The gate certifies the cast and nothing else, so the first
   validated univariate model the system meets is the yardstick at N5.
2. **No interventions.** `characterize` reports outliers and acts on none. A
   level shift or an outlier ends up in the system's dynamics, and nothing
   downstream separates it.
3. **Every coefficient is free.** All m²(p + q) coefficients are estimated
   together, the own included. Identification reads the whole matrices by
   least squares (M(l)). The simplification by coefficient is what makes the
   result readable, and it is optional.
4. **A lower bar in sample.** Each fit's LR is against the same model without
   cross terms, not against univariate models: a system can look significant
   against white-noise rows.
5. **A weaker yardstick.** Unless the analyst brings models, N5 compares with
   univariate models built by route U's builder: light, not reviewed. Rule 1
   is only as strong as its yardstick.
6. **Starting values.** The least-squares cross terms on top of the diagonal's
   own models can make the start non-stationary (the gas furnace VARMA(2,1)).
   It falls back to zero and says so; the shrink that would avoid it is
   pending.
7. **Nothing reusable.** The specifications never become `.pre`, and the joint
   model lives only in the session and the guion (`STUDY-raw-entry.md` §4).
8. **Thinner decision nodes.** `DECISION_NODES.md` is written mostly from
   route U; route V's specific stops and caveats are not listed as such.

None of this makes route V wrong: it is Tiao and Box's method, and the
literature's. It makes it a path where the analyst carries more of the
judgement, and the assistant should say so plainly, at the entry and at the
end.

## 6. Recommendations, in order

1. **Make route V's risk visible.**
   - **At the route question:** route U is the default; route V is an
     explicit choice, named as the less structured path.
   - **At N5:** if the yardstick was built by sima, say so as a caveat, and
     offer art's guided lane for the analyst's own models.
   - **In `hand_over`:** list route V's caveats — no interventions, a yardstick
     not reviewed, nothing reusable.
   - **In `DECISION_NODES.md`:** route V's own stops and caveats.
2. **Interventions on route V.** Carry `characterize`'s outliers into the
   caveats, at least, or into the specifications when the analyst accepts
   them.
3. **Two starts when q > 0** (`ols` and `preliminary`), keeping the better,
   and saying so when they differ: it catches several maxima.
4. **The scale warning at the load**, and a decision on the units of rates in
   art (% or basis points). Both are the analyst's.
5. **Shrink a non-stationary start** before falling back to zero. It is
   measured: ×0.5 is enough on the cases seen. It is a change in the C and the
   port.
6. **Coverage:** a reference case with λ = 1, d = 0 and a mean in the C
   batteries.
7. **The release:** drvarma 0.3.5 (the `ols` start), sima's caches rebuilt,
   sima 0.2.5, then atsw. Until then, the trial-run environment carries what
   will be published, except the `ols` start.
8. **A file for the joint model** (route V first): open since the raw-entry
   study.

## 7. In one paragraph

Route U is the ladder, and it is sound: what the trial run found there was in
the edges — the start, the cache, a library formula — and is fixed, homologated
and covered. Route V is a different kind of path. It is legitimate, and it is
where the analyst's judgement has to replace the structure the ladder gives,
so sima should present it that way: as the exception, with its caveats
carried to the end.
