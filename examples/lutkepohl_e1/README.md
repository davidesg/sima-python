# Lütkepohl's E1: a cointegrated system with sima and drvec

West German fixed investment, disposable income and consumption expenditures,
billions of DM, quarterly, seasonally adjusted, 1960Q1–1982Q4 (92
observations): data set E1 of Lütkepohl (2005), *New Introduction to Multiple
Time Series Analysis*, Springer; source Deutsche Bundesbank. Distributed with
JMulTi and tracked in the public repository davidesg/atsw-gui,
`engines/drvec/datasets/lutkepohl/e1.dat` (SHA-256
c4fdef149249cea596657c42713ce2f41df160d23c29ed1b9b59e2ff10fc0d97, listed in
its `MANIFEST.md`).

| file | what it is |
|---|---|
| `art/e1invest.pre`, `art/e1income.pre`, `art/e1cons.pre` | one fue model per series: a random walk with drift in logs (λ = 0, d = 1, the mean free), estimated by fue; copied byte for byte from drvec-python's `tests/data/fixtures/` (their provenance in its `e1-inp/SOURCE`) |
| `art/sima_jobs/<id>/` | the cache of the tutorial's rank test (B = 499, drvec C 0.13 on Linux x86_64): `load_example` copies it, and the rank returns at once |
| `TUTORIAL.md`, `example.json` | the step-by-step tutorial the assistant follows, and the manifest |

The univariate files are random walks with drift, not art's models: on the
`.pre` route drvec reads each file's series, calendar, Box-Cox, rescaling,
deterministic terms and mean flag, not its ARMA, and the yardstick at C8 is
then the random walk with drift. An analyst who wants a stronger yardstick
builds each series in art first.

**In real time:** `load_example("lutkepohl_e1")`, then the tutorial
(`sima://example/lutkepohl_e1`). The cache was built with
`tools/build_example_caches.py`.
