# Tiao and Box with sima: the gas furnace

The worked example of `docs/STUDY-tiao-box.md` (served as
`sima://doc/STUDY-tiao-box`): Tiao and Box's (1981, §5.2) building of a
vector model on their own example, from the raw table to the yardstick.

| file | what it is |
|---|---|
| `data/gas_furnace.csv` | Box and Jenkins' Series J: input gas rate and output CO2, 296 pairs at 9-second intervals, from <https://openmv.net/info/gas-furnace> (md5 4950b8ad0b048c453257747ea6e04078) |
| `run.py` | the walkthrough in one go, with sima's tools |
| `TUTORIAL.md`, `example.json` | the step-by-step tutorial the assistant follows, and the manifest (for `load_example`) |

**Route V.** Tiao and Box fit the vector directly, "where no distinction is
made between an input and output variable". So the example starts from the
raw table, and univariate models appear only at the end, as the yardstick.

**What it reproduces:**
- M(l) of their Table 12 (1650, 665, 31.7, 22.5, 5.6, 12.9, …);
- no feedback and a delay of three periods;
- the spurious feedback of their Table 14 at AR(2);
- their restricted AR(6) (5.7): the input's AR(3) at 1.97, −1.36, .34, as
  Box and Jenkins; the delay coefficient −.53; the variances .0351 and .0554
  against .0359 and .0561;
- transfer weights close to their Table 13.

**In real time, in a conversation with sima:** `load_example("tiao_box")`
copies these files to `~/sima-examples/tiao_box/` and loads the table; the
analysis goes on node by node from `characterize`, and the assistant follows
`TUTORIAL.md` (`sima://example/tiao_box`).

**In one go:**

    python3 examples/tiao_box/run.py            # the whole walkthrough
    python3 examples/tiao_box/run.py --upto 7   # up to the structure of the VAR(6)

Reports go to `out/NN_<tool>.md`; the specifications and the guion are written
to `data/gas_furnace_sima/`.

> G. C. Tiao and G. E. P. Box (1981), "Modeling multiple time series with
> applications", *Journal of the American Statistical Association* 76,
> 802–816.
