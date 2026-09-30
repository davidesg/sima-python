# Jenkins and Alavi (1981) with sima: muskrat and mink

The worked example of the manual chapter `docs/MANUAL-jenkins-alavi.md` (also
served by the MCP server as `sima://doc/MANUAL-jenkins-alavi`): Jenkins and
Alavi's multivariate method on their own data, from the two univariate models
built in art to the forecasts.

| file | what it is |
|---|---|
| `data/mink_muskrat.csv` | skins traded by the Hudson's Bay Company, 62 years (Jones 1914), dated 1850–1911 as in Reinsel (1997); Jenkins and Alavi date the same values 1848–1909 |
| `art/MUSKRAT_m03.pre`, `.out` | the muskrat's univariate model, built in art's guided lane: ARIMA(6,1,1) on ln z |
| `art/MINK_m02.pre`, `.out` | the mink's: AR(4) on ln z, with mean |
| `run.py` | the walkthrough, node by node, with sima's tools |

Run it from the repository (or with sima installed):

    python3 examples/jenkins_alavi/run.py            # the whole walkthrough
    python3 examples/jenkins_alavi/run.py --upto 6   # up to the identification

Each report goes to `out/NN_<tool>.md` and each figure to `out/figs/`; the
guion (the path, with the evidence and the decisions) is written next to the
`.pre` files. The evaluations take a minute or two.

What it reproduces, with the paper's numbers alongside, is in Part 3 of the
manual: the univariate models, both identifications (their Table IV and the
prewhitened ccf), both candidates (their (5.8) and (5.9)), the large residual
of 1906 (1908 here), their Table VIII on 48 observations (§6.3), and the
out-of-sample comparison they could not run.
