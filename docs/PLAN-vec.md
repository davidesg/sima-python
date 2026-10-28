# sima 0.2.0 — the plan for cointegrated systems

This plan builds on `docs/STUDY-vec.md` (the study) and on the user's answers
of 2026-10-18 to its open questions. The study says *what* and *why*; this
plan says *in what order*, *where* and *how we know it is done*. Where the two
differ, the decisions below win.

## 0. The decisions this plan rests on

Taken by the user on 2026-10-17 and 2026-10-18. They are not reopened here.

1. **drvec's assistant is sima** (2026-10-13, unchanged). sima 0.2.0 manages
   drvarma, as now, and routes to drvec when the series are cointegrated. It
   runs the cointegration studies of STUDY-vec §3.
2. **The cointegration question is the analyst's.** sima offers it, with the
   evidence in view: the canonical analysis of the levels, each series' unit
   root, and theory. The analyst decides; in the autonomous lane sima sits in
   that chair and writes the reason down. It is offered whenever **two or
   more series have d = 1**. "With feedback" is dropped: feedback is tested
   inside the VEC (weak exogeneity), not assumed before it.
3. **No cointegration claim without the bootstrap.** The rank is decided by
   the parametric bootstrap. The asymptotic table is shown only as
   orientation and is never a verdict. A rank adopted on theory against the
   bootstrap is written in the guion as such. No tool reports a rank, a β or
   an equilibrium without a finished bootstrap behind it.
4. **The bootstrap must be affordable.** Hence two things:
   - a parallel, bit-identical bootstrap in drvec-python (§A2);
   - **sima can run the bootstraps with drvec C** (§B), because a job that
     takes about 12 hours in the port takes one or two in the C. The user had
     been running drvec C for the bootstraps all along.
5. **A VEC is a VARMA in levels** whose AR has reduced rank (Π = αβ′). It is
   forecast with the **VARMA system's forecasting code** (drvarma), with the
   VEC written in levels: one forecaster, not two (§A4).
6. **The yardstick rule.** sima's rule says a VARMA that does not forecast
   better than the univariates has no reason to exist.
   - For a VEC the comparison is always computed and reported.
   - It **vetoes** when the model's purpose is forecasting.
   - For a long-run claim (an equilibrium, who corrects) it is a **caveat,
     not a veto**: imposing cointegration often helps little at short
     horizons (Christoffersen and Diebold, 1998).
   - The purpose ("forecast" or "long run") is recorded at N1c.
7. **One session, one guion.** The VEC, the fallback VARMA in differences
   (r = 0) and their comparison with the univariates are one analysis, on the
   same files and the same window. Each fit carries a kind tag, VARMA or VEC,
   and the final-stage tools dispatch on it.
8. **The refused options stay refused.** drvec v1 refuses five groups:
   - `-warma`, `-mawarma` and `-specs`;
   - `-matest` and `-artest`;
   - the rank-test combinations;
   - `-m 2` and `-rankadm`;
   - the instruments and writers.

   sima never offers them.

The study's other recommendations are adopted as written:
- jobs run as detached subprocesses with an on-disk cache (Q3);
- the seed is optional (Q5);
- the half-lives and Gonzalo–Ng are computed in sima first (Q6);
- the best free fit is used in the restriction LRs (Q7);
- `export_tables` is deferred (Q8);
- full rank is not added to drvec (Q9);
- drvec is a hard dependency of sima (Q11);
- `study_estimation` for the VEC gets only the declaration and multistart (Q12);
- the tools are separate `*_vec` tools (Q13).

## A. drvec-python 0.1.0, before it is uploaded

drvec 0.1.0 is packaged but not on PyPI, and the release is joint. So
everything sima needs from the engine goes into 0.1.0 and costs no extra
release.

**The rule for this whole phase:** nothing here changes a number. The
golden suite stays byte-identical to drvec C 0.13 on Linux x86_64, and the
off-Linux tolerances stay as they are.

### A1. Accessors (STUDY-vec §4.2, items 1–6)

- Structured matrices on `FitResult`: α, B₂/β, Π, Γ, Θ, Σ, the residuals, and
  the stationary representation.
- The level IRF, FEVD and gain as arrays. They are today's private
  `report.level_irf_R`, `level_irf_fevd` and `compute_psi_weights`, made
  public.
- The IRF bootstrap as arrays, with a progress callback like `rank_test`'s.
- Diagnostics as numbers: Hosking Q (statistic, df, p) and JB.
- Forecasts as arrays: point, bands and dates.
- The restriction LRs with their degrees of freedom.

**Test:** every accessor equals the number printed in the `.out` it already
writes, on every golden case.

### A2. Parallel bootstrap, bit-identical

- The B samples are simulated **in sequence**, so the generator is consumed in
  the C's order. They are then **fit in a process pool**. The fits consume no
  random numbers (`rank.py`).
- The same scheme applies to `rank_test` and to `fit(irfboot=)`.
- `workers=1` is today's path.

**Tests:**
- `workers=1` and `workers=4` give byte-identical `.out` and `.boot` on every
  rank case in the suite;
- with the default seed, both stay byte-identical to the oracle.

### A3. `seed=`

- An optional `seed=` on `rank_test` and `fit(irfboot=)`. The default is the
  C's, so parity is untouched.
- sima offers it only as a "Monte Carlo check" of a rank at the edge of 5 %.

### A4. The VEC in levels, for drvarma's forecaster

Decision 5. Write the adopted VEC as a VARMA in levels, Φ(B) with
Φ(1) = −Π, plus Θ(B), Σ and the deterministic part. Then forecast it with
drvarma's forecasting code.

- **First, a check:** does drvarma's forecaster accept a non-stationary
  levels VARMA given its parameters, with no estimation?
  - If it does, A4 is a conversion function (`drvec.to_levels_varma`) and a
    test.
  - If it does not, the change goes into drvarma 0.3.0, which is also not
    released yet, as a forecasting entry point.
  - A second forecaster in sima is not the way out.
- **Test:** drvarma's forecasts of the converted model equal drvec's own
  `fit(forecast=H)`, both the points and the bands, on every golden case with
  a `.forecast`.
  - drvec's own forecaster stays, because it is the C's (`-f`) and is under
    byte identity.
  - If the two differ, the difference is understood and documented before
    sima uses either. The `bugs-con-repro` rule applies.

### A5. Docs and release notes

- README, CHANGELOG 0.1.0 and API docs for A1–A4.

## B. drvec C as the bootstrap engine

Decision 4. A job that takes about 12 hours in the port takes one or two
in the C. The C is the oracle, so the port is byte-identical to it on
Linux x86_64. Running the C is therefore not a second implementation: it is
the same model, run faster.

### B1. Where it lives: in drvec-python, not in sima

A module `drvec.c_engine`:
- finds the binary, in this order:
  1. `DRVEC_BIN`;
  2. `drvec` on the PATH;
  3. the ATSW install directory;
- checks its banner: the version must be the one the port mirrors (0.13
  today), otherwise it refuses with the reason;
- translates a `rank_test` or `fit(irfboot=)` call into the C's argv. This is
  the inverse of the port's `cli.py`, which already parses the same options;
- runs the binary in the job's folder;
- reads its `.out`, `.boot` and `.irfboot` back into the **same result
  objects** as the Python path.

It goes in drvec, not in sima, so that there is one translation of options
and one reader of the C's files, next to the port that defines them.

### B2. When it is used

- `engine="auto"`, the default: the C for the bootstraps when a matching
  binary is found, otherwise the parallel Python of A2.
- `engine="python"` and `engine="c"` force one or the other.
- Only the **bootstraps** (the rank test, the IRF bands and the sweep's rank
  cells) go to the C. The fit, the restrictions and everything sima reads
  as structure come from the port's objects, through the accessors.
- The engine used is part of the cache key and of the provenance in every
  result and in the guion.

### B3. Parity

**Tests:**
- on Linux x86_64, the C path and the Python path give byte-identical `.out`
  and `.boot` on the suite's rank cases and on one `irfboot` case;
- the C-path tests skip with a reason when no binary is found;
- CI builds drvec C 0.13 from atsw-gui at the oracle commit (drvec-python's
  `tests/data/oracle/SOURCE`).

**Off Linux** the C itself is a different platform. Its results carry that
platform's tier, like the port's.

### B4. Distribution — needs a decision

drvec C is **not** in the ATSW packages today. `packaging/programas.sh`
records the analyst's decision of 2026-10-04: drvarma and drvec stay in the
tests and out of the package. So, today, only someone who builds it has it.

The options:
- (a) keep it so, and `DRVEC_BIN` points at a build;
- (b) add drvec to the ATSW packages in the joint release;
- (c) ship the binary inside the drvec wheel, which means a C build per
  platform in drvec-python's wheels.

**Recommendation:** (a) now, with (b) at the joint release. (c) duplicates
what the ATSW packages already do. This is the user's decision, because it
changes the 2026-10-04 one.

### B5. drvec C inside drvec-python's wheels (decided 2026-10-18)

sima's users install with pip and mostly have no ATSW, so the C must come with
the wheel. Otherwise the bootstraps that need it are 6–12x slower for most of
them. The C in the wheel is the oracle itself, so no new numerics are
written.

- **Vendor** drvec C's sources and the `lib/` pieces it links (fuedet,
  fuepre, diagmv, prewhiten, and whatever else) into drvec-python's `csrc/`.
  A test checks their sha256 against atsw-gui at the drvec 0.13 commit, as
  fue does for fuedet.
- **Build** the executable with cibuildwheel, with GSL static as in drvarma's
  wheels, for Linux x86_64 and aarch64, macOS arm64 and Windows. It ships as
  package data, `drvec/_bin/drvec[.exe]`.
- A **pure-Python wheel** remains the fallback, as in drvarma.
- **`c_engine`'s search order:** `DRVEC_BIN`, then the bundled binary, then
  the PATH or the ATSW install.
- **Tests:**
  - in CI, the wheel's binary gives the same bytes as the oracle on Linux
    x86_64;
  - the smoke test of each wheel runs one small bootstrap through the C path.
- It goes into **drvec 0.1.0**, so it costs no extra release.
- drvec in the ATSW packages (B4) remains a separate matter, for the GUI's
  users.

## C. sima 0.2.0

The tools are added; nothing that exists changes, except the menus and texts
of `canonical_analysis` and `run_gate` (STUDY-vec §4.1).

### C1. The session

- A kind tag (VARMA or VEC) on each fit.
- The purpose recorded at N1c (decision 6).
- The provenance fields on every result: engine versions, backend
  (python/c, compiled/fallback), platform tier, seed, cache key and run
  folder.

### C2. The job runner (STUDY-vec §5.3)

- `python -m sima.jobs run <folder>`, as a detached subprocess.
- At most `cores − 1` jobs at once, counted with the A2 workers.
- One folder per run.
- The content-keyed cache.
- Progress as "k of B, comparison r → r+1".
- Never a partial result as final.
- A ~20 s inline wait.
- Tools: `job_status`, `job_result`, `job_cancel`, `jobs`.

### C3. The node N1c

- After `canonical_analysis`, offered when ≥ 2 series have d = 1 (decision 2).
- Its outcomes:
  - **r = 0:** drvarma's VARMA in differences, in the same session;
  - **0 < r < M:** the C nodes;
  - **all comparisons reject:** "at least M − 1", sent to the unit-root
    evidence and the VARMA in levels;
  - **the mixed I(0)/I(1) case:** offered as an option, never as the default.
- The handover from mtram (a cycle plus I(1)) arrives here.

### C4. The tools (STUDY-vec §4.1)

- **New:**
  - `prepare_vec`;
  - `rank_test` (a job; decision 3: the only way to a rank);
  - `estimate_vec` (refuses without a finished `rank_test` for the same spec,
    unless the analyst adopts r on theory, which is written in the guion);
  - `test_restriction` (LR, df, p, and the best free fit known);
  - `add_exogenous`;
  - `long_run` (θ, both half-lives, Gonzalo–Ng, computed in sima);
  - `irf_bands` (a job);
  - `sweep` (a job);
  - `plot_rank_bootstrap`.
- **Extended, dispatching on the kind tag:**
  - `impulse_response` and `variance_decomposition`;
  - `forecast`, through drvarma (A4);
  - `evaluate`, the yardstick per decision 6;
  - the `plot_*` tools;
  - `reorder` (refuses on a VEC);
  - `canonical_analysis` (its menu calls `prepare_vec`).
- **Not offered:** everything in decision 8, plus `rungs` and `export_tables`.

### C5. The server instructions and the docs

- The protocol gains N1c and the C nodes.
- The rules of STUDY-vec §3.13, with decisions 3 and 6 stated as rules.
- `docs/TOOLS.md` regenerated.
- A tutorial per worked example.

### C6. Worked examples, public data only

- **`flour_prices`**, the flagship: its tutorial now continues into the rank.
- **`jenkins_alavi`**, the mixed case: its bootstrap must be rerun with
  B ≥ 499, because the stored oracle run is B = 20.
- **Lütkepohl's E1**, with the ridge declared.
- **Johansen and Juselius's Danish data**, for restrictions and weak
  exogeneity.

Each example ships its job cache, so the tutorials return at once. On Linux
x86_64, rerunning the cache reproduces the same bytes, which is itself a test.

### C7. Tests

- the tools on the examples;
- the cache, cancellation and the "never partial" rule, with a small B;
- the dispatch on the kind tag;
- the refusals;
- an end-to-end guided and autonomous run on `flour_prices` with B small;
- CI on the three platforms, like the rest of the suite.

## D. Order, and how each step is closed

| step | where | closed when |
|---|---|---|
| A1–A3 | drvec-python | byte identity holds; workers=1 ≡ workers=4; the accessors equal the `.out` |
| A4 | drvec-python (+ drvarma 0.3.0 if needed) | drvarma's forecasts of the levels VARMA equal drvec's on every golden `.forecast` |
| B1–B3 | drvec-python | C ≡ Python bytes on Linux x86_64 on the rank cases; the skip works without a binary |
| B5 | drvec-python | wheels on 4 platforms carry the binary; the vendored sources pass the sha256 test; C ≡ oracle bytes on Linux x86_64 |
| C1–C2 | sima | runner tests pass; jobs survive the client |
| C3–C6 | sima | the examples run end to end in both lanes |
| C7 | sima | CI green on the three platforms |
| release | all | fue 0.1.18 → drvarma 0.3.0 → drvec 0.1.0 → sima 0.2.0 → ATSW release with the `drvec-v0.13` tag |

No tags and no uploads before the joint release.

A and B can run in parallel with C1–C2. The C tools need A1 and, for jobs, C2.

## E. Decided by the user (2026-10-18)

1. **The distribution of drvec C** (B4, B5): bundled in drvec-python's
   wheels (B5, which supersedes "DRVEC_BIN now" as the main route;
   `DRVEC_BIN` stays as an override); drvec also goes into
   the ATSW packages at the joint release, which amends the 2026-10-04
   decision recorded in atsw-gui `packaging/programas.sh`.
2. **The default engine for the bootstraps when the C is present:** the C
   (`engine="auto"`), with the engine written in every result. The port
   remains the reference for structure.

Why the C is worth it even with drvarma's compiled engine: the measurement in
drvec-python's TODO ("Option (b)") was made with the compiled likelihood, and
the port is still 6–12x slower. About half of an evaluation is drvec's cast in
pure Python, and about a quarter is drvarma's optimiser, also pure Python.

## F. Decided by the user on phase C's questions (2026-10-18)

1. **The yardstick's forecaster.** In 0.2.0 `evaluate` on a VEC keeps drvec's
   own rolling forecaster (it agrees with drvarma's to 1e-12). After 0.2.0 the
   rolling evaluation goes through `to_levels_varma` too (TODO).
2. **The cache key keeps the platform tier.** Off Linux x86_64 the tutorials'
   bootstraps run; caches per tier, built on CI, are the later route.
3. **Flour and the Danish data.** The bootstrap does not reject r = 0 where the
   published reading has r = 1. The tutorials say so and go on with r = 1
   adopted on theory, recorded as such: that is decision 2 of §0 at work.
4. **The tie rule is silent below B = 199**, where the result is already
   labelled an exploration.
5. **The default p in `prepare_vec`** is M(l) on the levels when
   `canonical_analysis` has run, and the AR rule otherwise (flour: 2, not 1).
