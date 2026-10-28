# Martín Manjón and Treadway's two interest-rate trends, with sima and drvec

R. Martín Manjón and A. B. Treadway (1997), "The Fed Controls Only One of the
Two Interest Rates in the U.S. Economy", Documento de Trabajo 9716, ICAE,
Universidad Complutense de Madrid. Their claim: U.S. interest rates share two
common stochastic trends, monetary policy (the Fed's target and the market
rates up to one or two years) and one the Fed does not control; the 3-year rate
combines the two, so (target, 30-year, 3-year) cointegrate with one relation
and no pair of them does. They found it on 1985–1995 by over-differencing and
reading the MA unit root by exact maximum likelihood.

This example takes their system to the whole homogeneous regime: monthly,
1/1985–9/2008, from the Fed's post-NOP procedure (it declares it controls the
Fed funds rate) to interest on reserves (10/2008) and the floor system. 285
observations, 284 in the VEC.

| series | what it is | FRED |
|---|---|---|
| `R0T` | the Fed funds target, monthly mean of the daily target | DFEDTAR |
| `R30` | the 30-year Treasury, constant maturity | GS30 |
| `R3` | the 3-year Treasury, constant maturity | GS3 |
| `R10` | the 10-year Treasury, constant maturity (the control) | GS10 |

Every rate y (in %) enters as 100·log(1 + y/100), as in the paper.
`data/tipos_1985_2008.csv` (SHA-256
8de12682d78406bc36dc6f14f7906a7a64c214534ac32ba699d27345cde5ac3c) also carries
the effective rate (`R0`, FEDFUNDS) and the 1- and 2-year rates (`R1Y`, `R2`:
GS1, GS2), downloaded from FRED on 2026-10-22. GS30 is not published from
2/2002 to 2/2006: FRED fills the gap with the Treasury's extrapolated value,
which is why the tutorial ends with the 10-year rate in its place.

| file | what it is |
|---|---|
| `art/<SERIES>_ar3.pre`, `.out` | the univariate models, built in art: λ = 1 (the series are already in log form), d = 1, no mean, AR(3) as in the paper's Table 2 |
| `art/sima_jobs/<id>/` | the cache of the tutorial's two rank tests (B = 499, drvec C 0.13, Linux x86_64) |
| `TUTORIAL.md`, `example.json` | the tutorial and the manifest |

The lesson against `johansen_juselius`: there the bootstrap does not find the
published relation at n = 55; here it finds the paper's, but only with the
doubled sample (on 1985–95 alone, 131 months, p = 4, it does not reject r = 0,
p 0.22).

**Taken further than the paper.** The paper read cointegration from the MA
unit root of the over-differenced series. Here the rank is tested by
parametric bootstrap on the exact likelihood, on the whole homogeneous regime;
who corrects is tested by LR (the target, not the market rates); and the joint
LR on α and the short run (p 0.45) reads the system as a conditional model,
the target on the market rates: mtram's next rung. The tutorial's last section
lists these, with the calibration on the 1- and 2-year rates and what happens
after 2008.
