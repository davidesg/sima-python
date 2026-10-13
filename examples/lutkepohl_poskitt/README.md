# The echelon form with sima: Lütkepohl and Poskitt's flour prices

The worked example of `docs/MANUAL-echelon.md` (served as
`sima://doc/MANUAL-echelon`): the specification of an echelon-form VARMA by
Lütkepohl and Poskitt (1996, §4.1), on their data, from the raw table to the
yardstick.

| file | what it is |
|---|---|
| `data/flour_prices.csv` | monthly flour price indices, Buffalo, Minneapolis and Kansas City, August 1972 – November 1980 (100 months), transcribed from Tiao and Tsay (1989, *JRSS B* 51, Appendix B); the same file as `flour_prices` |
| `run.py` | the walkthrough in one go, with sima's tools |
| `TUTORIAL.md`, `example.json` | the step-by-step tutorial the assistant follows, and the manifest (for `load_example`) |

**Route V.** Lütkepohl and Poskitt build no univariate models: the rates of
change (first differences of the logs) are modelled as a vector from the
start. So the example starts from the raw table, and the univariate models
appear only at the end, as the yardstick.

**What it reproduces** (their Tables 1 and 2):
- the index search: SC and HQ choose (0, 0, 0), with (1, 1, 1) second; AIC
  chooses (1, 1, 1);
- the unrestricted (1, 1, 1): log|Σ̃| 4.744 against their 4.725;
- the restricted VAR(1) and MA(1) with five coefficients: the same estimates
  and standard errors to the second decimal, log|Σ̃| 5.000 and 5.027 against
  4.985 and 5.004.

**In real time, in a conversation with sima:** `load_example("lutkepohl_poskitt")`
copies these files to `~/sima-examples/lutkepohl_poskitt/` and loads the
table; the analysis goes on node by node from `characterize`, and the
assistant follows `TUTORIAL.md` (`sima://example/lutkepohl_poskitt`).

**In one go:**

    python3 examples/lutkepohl_poskitt/run.py            # the whole walkthrough
    python3 examples/lutkepohl_poskitt/run.py --upto 5   # up to the index search

Reports go to `out/NN_<tool>.md`; the specifications and the guion are written
to `data/flour_prices_sima/`.

> H. Lütkepohl and D. S. Poskitt (1996), "Specification of echelon-form VARMA
> models", *Journal of Business & Economic Statistics* 14, 69–79.
