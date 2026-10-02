# Tiao and Box's tools with sima: flour prices in three cities

The worked example of `docs/STUDY-tiao-box.md` (served as
`sima://doc/STUDY-tiao-box`): Box and Tiao's (1977) canonical analysis and Tiao
and Box's (1981) stepwise autoregression on the data of Tiao and Tsay (1989),
from three univariate models to the yardstick.

| file | what it is |
|---|---|
| `data/flour_prices.csv` | monthly flour price indices, Buffalo, Minneapolis and Kansas City, August 1972 – November 1980 (100 months), transcribed from Tiao and Tsay (1989, *JRSS B* 51, Appendix B) and checked against the printed page |
| `art/<CITY>_m01.pre`, `.out` | the univariate models: ARIMA(0,1,1) on ln z, no mean — θ −0.135 (Buffalo), −0.251 (Minneapolis), −0.199 (Kansas City) |
| `run.py` | the walkthrough in one go, with sima's tools |
| `TUTORIAL.md`, `example.json` | the step-by-step tutorial the assistant follows, and the manifest (for `load_example`) |

**The univariate models** were built with art's engine in the autonomous lane
(2026-10-02): logs (Tiao and Tsay's transformation), no seasonality (art's HAC
test: p 0.25, 0.22, 0.07), d = 1, and the orders art ranks first. For Buffalo,
the random walk, AR(1) and MA(1) tie; MA(1) is taken for all three, so the
three cities share one form. Mean not significant (t ≈ 1). Residuals white
(Ljung-Box p > 0.76 at 6, 12 and 18 lags). An analyst may want to review them
in art's guided lane before trusting the rest.

**In real time, in a conversation with sima:** `load_example("flour_prices")`
copies these files to `~/sima-examples/flour_prices/`, loads the three models,
and the analysis goes on node by node; the assistant follows `TUTORIAL.md`
(`sima://example/flour_prices`).

**In one go:**

    python3 examples/flour_prices/run.py            # the whole walkthrough
    python3 examples/flour_prices/run.py --upto 4   # up to the identification

Reports go to `out/NN_<tool>.md`; the guion is written next to the `.pre` files.
