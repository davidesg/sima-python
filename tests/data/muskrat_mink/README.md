# Muskrat and mink (Jenkins and Alavi 1981, §4.2, §5.4)

Skins traded by the Hudson's Bay Company, 1850–1911 (Jones 1914, as in
Reinsel 1997; Jenkins and Alavi used 1848–1909). Raw counts:
`atsw-gui/engines/drvec/datasets/mauricio/mink_muskrat.csv`.

The two `.pre` files are the univariate models Jenkins and Alavi report,
fitted by fue on this window (2026-09-29):

| series | model | fue | Jenkins and Alavi |
|---|---|---|---|
| muskrat | ARIMA(6,1,1) on ln | phi 0.65 −0.58 0.22 −0.31 −0.04 −0.32, theta 0.55 | 0.65 −0.60 0.23 −0.34 −0.06 −0.38, 0.54 |
| mink | AR(4) on ln, mean | phi 0.80 −0.21 0.00 −0.27, mean 10.82 | 0.82 −0.22 0.00 −0.28, 10.79 |

    fue.Model(muskrat, ar=[[0.1]*6], ma=[[0.3]], d=1, boxlam=0.0, refactor=1.0).fit()
    fue.Model(mink, ar=[[0.5, 0, 0, 0]], boxlam=0.0, refactor=1.0, estimate_mu=True).fit()
