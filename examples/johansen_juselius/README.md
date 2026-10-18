# Johansen and Juselius's Danish money demand, with sima and drvec

The Danish data of Johansen and Juselius (1990), "Maximum likelihood
estimation and inference on cointegration — with applications to the demand
for money", *Oxford Bulletin of Economics and Statistics* 52, 169–210; also
Johansen (1995), *Likelihood-Based Inference in Cointegrated Vector
Autoregressive Models*, ch. 7. Quarterly, 1974Q1–1987Q3, 55 observations:

| series | what it is |
|---|---|
| `LRM` | log real money (M2) |
| `LRY` | log real income |
| `IBO` | the bond rate |
| `IDE` | the bank deposit rate |

`data/denmark.csv` is taken from the public repository davidesg/atsw-gui,
`engines/drvec/datasets/urca_denmark.csv` (R package urca's `denmark`; SHA-256
8af2d2844aff4fc1719eea651b44292fe0abec24c17c0ff42579a03289bb99c0, listed in
its `MANIFEST.md`), with the four series of the money-demand system and the
period written as `1974Q1`.

| file | what it is |
|---|---|
| `art/<SERIES>_u.pre`, `.out` | the univariate models, built by sima's raw entry (route U, art's engine, light: **not reviewed in art**): `LRM` with deterministic quarterly seasonality (cos, sin, alter), the others without; d = 1 for all; λ = 1 (the series are already logs or rates) |
| `art/sima_jobs/<id>/` | the cache of the tutorial's rank test (B = 499, drvec C 0.13, Linux x86_64) |
| `TUTORIAL.md`, `example.json` | the tutorial and the manifest |

Johansen and Juselius use centred seasonal dummies for every series; here the
seasonality is each series' own, as the raw entry's characterization found it
(art's HAC test), and deterministic, as drvec requires (a seasonal difference
is refused). With n = 55 the asymptotic table is least trustworthy: the
bootstrap matters most.
