"""sima's figures: presentation only, in the school's design.

Every number comes from the engine (drvarma: the ladder, its IRF/FEVD and its
bands); nothing is computed here that a table does not already say. The
design is the one the suite already reads:

* the IMPULSE RESPONSE is drawn as what it is, an ACF-like function of the
  lag: thick black impulses at h = 0..H, a zero line, the seasonal grid, only
  the left axis (fue's `_draw_acf_panel`). Its band is dashed, as the ACF's,
  but it follows h, since here it is a Monte-Carlo band per horizon.
* the VARIANCE DECOMPOSITION uses the same grid of panels and the same
  impulses, on a fixed 0-100 % axis with the horizontal axis at 0: the row of
  a series reads the same in both figures. Its band is shaded as well as
  dashed (approved 2026-09-29): a share lives in 0-100, and the shaded area
  shows at a glance how much of that range the estimate leaves open.
* the CCFs are GraphMaker's panel (Treadway's; the same as drvus' ccf and
  drtran's), reused from drvarma (`plots._draw_ccf_panel`), not redrawn; so is Jenkins and Alavi's
  identification, per pair R_k over S_k, both two-sided: the CCF over its
  partial, as fue's ACF over PACF.
* the forecast follows FUF and art (fufplot.c, fue.report_forecast): per
  series, the annual rate of change (or the level) with its band, and the
  ERR panel of the last residuals under their dates.

Matplotlib is imported inside each function.
"""
from __future__ import annotations

import math

import numpy as np


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _spines(ax):
    """Only the left axis, as the ACF panels (fue `_tj_spines(('left',))`)."""
    for sp in ("top", "right", "bottom"):
        ax.spines[sp].set_visible(False)
    ax.spines["left"].set_linewidth(1.2)


def _nice(v):
    """A tidy symmetric limit: 1, 2 or 5 times a power of ten, at least v."""
    if not v > 0:
        return 1.0
    e = 10.0 ** math.floor(math.log10(v))
    for f in (1.0, 2.0, 2.5, 5.0, 10.0):
        if f * e >= v * 1.0001:
            return f * e
    return 10.0 * e


def _seasonal_grid(ax, H, freq, x0):
    if freq > 1:
        grid = [freq * k for k in range(1, 4) if freq * k <= H]
    else:
        gap = max(1, round(H / 3))
        grid = [gap * k for k in range(1, 4) if gap * k <= H]
    for xv in grid:
        ax.axvline(xv, color="0.5", lw=0.8, zorder=1)
    ax.set_xticks([x0] + grid)
    ax.tick_params(axis="x", length=0, labelsize=8)
    return grid


def _impulse_panel(ax, h, vals, lo, hi, ylim, yticks, freq, title, zero=True,
                   shade=False):
    ax.vlines(h, 0.0, vals, colors="k", lw=3.0 if len(h) <= 30 else 2.2, zorder=3)
    if zero:
        ax.axhline(0.0, color="k", lw=1.4, zorder=2)
    if shade and lo is not None and hi is not None:
        ax.fill_between(h, lo, hi, color="0.85", lw=0, zorder=1)
    if lo is not None and hi is not None:
        ax.plot(h, lo, color="k", lw=1.0, ls="--", zorder=2)
        ax.plot(h, hi, color="k", lw=1.0, ls="--", zorder=2)
    _seasonal_grid(ax, int(h[-1]), freq, int(h[0]))
    ax.set_xlim(h[0] - 0.5, h[-1] + 0.5)
    ax.set_ylim(*ylim)
    ax.set_yticks(yticks)
    ax.yaxis.set_tick_params(direction="out", labelsize=8)
    _spines(ax)
    ax.set_title(title, loc="left", fontsize=9, pad=2)


def irf_figure(L, horizon, bands=None, freq=12):
    """The orthogonalised IRF of the fitted ladder, m x m: row = response,
    column = shock (in the Cholesky order of the series). `bands` is
    `Ladder.irf_fevd_bands` or None."""
    from drvarma.irf import oirf
    plt = _plt()
    r = L.result
    names = [s.name for s in L.series]
    m = len(names)
    O = oirf(r.phi, r.theta, r.sigma, horizon)             # (H+1, m, m)
    h = np.arange(horizon + 1)
    fig, axes = plt.subplots(m, m, figsize=(2.9 * m + 0.6, 2.1 * m + 0.6), squeeze=False)
    for i in range(m):
        row = [np.abs(O[:, i, :])]
        if bands:
            row += [np.abs(bands["oirf_lo"][:, i, :]), np.abs(bands["oirf_hi"][:, i, :])]
        c = _nice(max(float(np.max(x)) for x in row))
        for j in range(m):
            lo = bands["oirf_lo"][:, i, j] if bands else None
            hi = bands["oirf_hi"][:, i, j] if bands else None
            _impulse_panel(axes[i, j], h, O[:, i, j], lo, hi, (-c, c),
                           [-c, -c / 2, 0.0, c / 2, c], freq, f"{names[i]} <- {names[j]}")
    sub = ("dashed: %d %% Monte-Carlo band, %d draws" % (round(100 * (1 - bands["alpha"])),
                                                         bands["ndraws_used"])
           if bands else "no band")
    fig.suptitle(f"Orthogonalised impulse responses (Cholesky order: {', '.join(names)})\n{sub}",
                 fontsize=10)
    fig.tight_layout()
    return fig


def fevd_figure(L, horizon, bands=None, freq=12):
    """The variance decomposition in the IRF's grid: panel (i, j) is the % of
    the h-step forecast-error variance of i due to the shock of j."""
    from drvarma.irf import fevd
    plt = _plt()
    r = L.result
    names = [s.name for s in L.series]
    m = len(names)
    F = fevd(r.phi, r.theta, r.sigma, horizon)             # (H, m, m), %
    h = np.arange(1, horizon + 1)
    fig, axes = plt.subplots(m, m, figsize=(2.9 * m + 0.6, 2.1 * m + 0.6), squeeze=False)
    for i in range(m):
        for j in range(m):
            lo = bands["fevd_lo_h"][:, i, j] if bands else None
            hi = bands["fevd_hi_h"][:, i, j] if bands else None
            _impulse_panel(axes[i, j], h, F[:, i, j], lo, hi, (0.0, 100.0),
                           [0, 25, 50, 75, 100], freq, f"{names[i]} <- {names[j]}  (%)",
                           zero=True, shade=True)
    sub = ("shaded, between the dashed lines: %d %% Monte-Carlo band, %d draws" % (round(100 * (1 - bands["alpha"])),
                                                         bands["ndraws_used"])
           if bands else "no band")
    fig.suptitle("Forecast-error variance decomposition, % by shock "
                 f"(Cholesky order: {', '.join(names)})\n{sub}", fontsize=10)
    fig.tight_layout()
    return fig


MIN_DF_LAGS = 2    # lags left beyond the parameters, at least


def q_lags(K, npar, n):
    """The lags of a residual portmanteau: the legacy K (fug's acf rule,
    GraphMaker's ccf lags), moved up when it leaves fewer than MIN_DF_LAGS lags
    beyond the parameters — in annual data with long models the legacy K
    leaves none, and a statistic without degrees of freedom has no meaning.
    Two lags left: Q with 2 d.f., a pair's P with 4 x 2 = 8. Never beyond n - 2."""
    return int(min(max(K, npar + MIN_DF_LAGS), n - 2))


def residual_npq(L):
    """GraphMaker's p + q for the P of a residual pair: the largest AR order
    plus the largest MA order of the fitted model (the expanded operators,
    own and cross)."""
    r = L.result
    return int(np.shape(r.phi)[0] if np.size(r.phi) else 0) + \
        int(np.shape(r.theta)[0] if np.size(r.theta) else 0)


def _p_label(Q, K, npq):
    """GraphMaker's label: P ( 4 (K - (p + q)) ) = value. With K <= p + q no
    degree of freedom is left, and the label says so instead of a number."""
    df = 4 * (K - npq)
    return "P ( %d ) = %.1f" % (df, Q) if df > 0 else "P = %.1f  (K \u2264 p + q)" % Q


def residual_ccf_figure(L, nlags, freq=12):
    """The two-sided CCF of every pair of residuals of the fitted model, in
    GraphMaker's panel: titled "A - B" with A leading at k > 0, Hosking's P
    below."""
    from drvarma.diagnostics import ccf, qccf
    from drvarma.plots import _draw_ccf_panel
    plt = _plt()
    a = np.asarray(L.result.residuals, float)
    n, m = a.shape
    names = [s.name for s in L.series]
    pairs = [(i, j) for i in range(m) for j in range(i + 1, m)]
    npq = residual_npq(L)
    ncol = min(2, len(pairs))
    nrow = math.ceil(len(pairs) / ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(7.5 * ncol, 3.2 * nrow), squeeze=False)
    for k, (i, j) in enumerate(pairs):
        rho = ccf(a[:, i], a[:, j], nlags)          # k > 0: series j leads
        Q, _df, _p = qccf(a[:, i], a[:, j], nlags)
        _draw_ccf_panel(axes[k // ncol, k % ncol], rho, nlags, n, freq,
                        f"{names[j]} - {names[i]}", _p_label(Q, nlags, npq))
    for k in range(len(pairs), nrow * ncol):
        axes[k // ncol, k % ncol].set_visible(False)
    # terse, as GraphMaker: the pair above, P below; the rest is in the text
    fig.tight_layout()
    return fig


def identification_figure(x, names, K, method, freq=1, pairs=None, Kp=None):
    """Jenkins and Alavi's (1981) identification, pair by pair, in GraphMaker's
    CCF panel (the one drtran reads): for each pair of series the correlation
    function R_k ("ccf", two-sided, lag 0 included) ABOVE the partial one
    ("pccf", the cross elements of S_k, two-sided; no lag 0) — fue's ACF over PACF: the same lag
    axis and the same scale, so a lag is read down the column. The pairs go
    side by side, two per row. Terse, as the originals: the pair once above,
    "ccf" / "pccf" centred under it, the statistic between; what they mean goes in
    the tool's text.

    method 2: x are the univariate residuals (prewhitened), band 2/sqrt(n) on
    both panels and, between them (where fue puts its Q), Haugh's S* as
    GraphMaker writes its P: "S* ( d.f. ) = value", nothing more. method 1: x are the stationary
    series w_t, not white, so the CCF band is Bartlett's (3.13) for unrelated
    series, lag by lag (the dotted line follows it); the partial keeps
    2/sqrt(n); nothing under the panels (no valid portmanteau on series that
    are not white; the band that follows the lag says it is Bartlett's).
    With more than two series S_k comes from the VAR of ALL of them:
    the partial panel of a pair is conditional on the other series too.
    `Kp` caps the partial's order (the VAR behind S_K has m^2 K coefficients)."""
    from drvarma import identification_mv as im
    from drvarma.plots import _ccf_scale, _draw_ccf_panel
    plt = _plt()
    x = np.asarray(x, float)
    n, m = x.shape
    Kp = min(K, Kp or K)
    pairs = pairs or [(i, j) for i in range(m) for j in range(i + 1, m)]
    R, seR = im.corr_matrices(x, K, prewhitened=(method == 2))
    S, seS = im.partial_corr_matrices(x, Kp)
    r0 = np.corrcoef(x.T)
    band_p = np.full(2 * K + 1, 2.0 * seS)
    ncol = min(2, len(pairs))
    nblk = math.ceil(len(pairs) / ncol)
    fig, axes = plt.subplots(2 * nblk, ncol, figsize=(8.5 * ncol, 6.2 * nblk), squeeze=False)
    for k, (i, j) in enumerate(pairs):
        top, bot = axes[2 * (k // ncol), k % ncol], axes[2 * (k // ncol) + 1, k % ncol]
        rho = im.two_sided(R, i, j, r0[i, j])
        band = 2.0 * im.two_sided(seR, i, j, 1.0 / np.sqrt(n))
        s = np.zeros(2 * K + 1)
        s[K - Kp:K + Kp + 1] = im.two_sided(S, i, j, 0.0)
        c = _ccf_scale(max(np.abs(rho).max(), np.abs(s).max(), band.max(), band_p.max()))
        # under each panel only the statistic, as GraphMaker's P: Haugh's S*
        # between the two for method 2; nothing for method 1 (no valid one on
        # series that are not white) nor under S_k. The rest goes in the text.
        lab = ""
        if method == 2:
            S_, df_, _p = im.haugh(x[:, i], x[:, j], K)["all"]
            lab = "S* ( %d ) = %.1f" % (df_, S_)
        # the pair once, centred above, as GraphMaker; "ccf" / "pccf" centred
        # under it, as drvus titles its "acf" / "pacf"
        _draw_ccf_panel(top, rho, K, n, freq, "", lab, band=band, cmax=c)
        _draw_ccf_panel(bot, s, K, n, freq, "", "", band=band_p, cmax=c)
        top.set_title(f"{names[j]} - {names[i]}", fontsize=11, pad=24)
        top.text(0.5, 1.02, "ccf", transform=top.transAxes, ha="center",
                 va="bottom", fontsize=13, fontweight="bold")      # bold, as fue's acf
        bot.set_title("pccf", fontsize=13, fontweight="bold")
    for k in range(len(pairs), nblk * ncol):
        axes[2 * (k // ncol), k % ncol].set_visible(False)
        axes[2 * (k // ncol) + 1, k % ncol].set_visible(False)
    fig.suptitle("Method 2 (prewhitened)" if method == 2 else "Method 1 (not prewhitened)",
                 fontsize=11)
    fig.tight_layout()
    return fig


def residual_panels(L):
    """fue's diagnosis panel for every residual series of the fitted model —
    what drvus drew per series (A1.eps) and art shows in its diagnosis: the
    standardised residuals with their +-2 bands, the acf with its Q, the pacf
    under it (pyfug's `plot_combined`, the same call as art's
    `figura_residuos`). The residuals go in fractions (pyfug labels x100 %),
    dated from the first residual, with fug C's lags; the Q discounts the
    series' own ARMA parameters. [] when pyfug is not installed."""
    try:
        from fue.diagnostics import default_lags, free_arma_count
        from pyfug.core import Tseries
        from pyfug.graphics import plot_combined
    except ImportError:
        return []
    a = np.asarray(L.result.residuals, float)
    n = a.shape[0]
    figs = []
    for col, k in enumerate(L._act):
        sr = L.series[k]
        rf = float(getattr(sr.model, "refactor", None) or 1.0)
        y0, p0 = sr.date_of(sr.nobs - n + 1)
        ser = Tseries(name=f"A.{sr.name}", freq=sr.freq, nobs=n, begyear=int(y0),
                      begtime=int(p0), data=np.ascontiguousarray(a[:, col] / rf))
        npar = free_arma_count(sr.model)
        figs.append((sr.name, plot_combined(ser, npar=npar,
                                            nlags=q_lags(default_lags(n, sr.freq), npar, n),
                                            title=ser.name)))
    return figs


def forecast_figure(L, fc, only=None):
    """The forecasts in the format of FUF (atsw-gui fuf/src/fufplot.c) and art
    (fue.report_forecast), one cell per series, each with its two panels:

    * top: with a log (lambda = 0), the ANNUAL RATE OF CHANGE (%),
      100 (ln y_t - ln y_t-s), of the last L observations and the L forecasts,
      one line with dots (larger where observed) and the +-1 sigma band dashed
      ("LRC anual (%)"); with another lambda, the LEVEL with a +-2 sigma band;
    * bottom, ERR: the residuals of those L observations as impulses (x100),
      under their dates, with the zero line and +-2 sigma dashed; the panel
      ends at the forecast origin.

    The numbers are the ladder's: ystar and sd_annual from Ladder.forecast,
    the residuals and each series' sigma from the fit. `only`: the name of one
    series, for a figure of its own (as FUF draws one page per series).
    """
    from matplotlib.gridspec import GridSpecFromSubplotSpec
    from fue.plots import _tj_spines
    from fue.report_forecast import _prevcmax, _year_ticks
    plt = _plt()
    r = L.result
    series = [L.series[i] for i in L._act]
    cols = list(range(len(fc)))
    if only is not None:
        cols = [c for c, d in enumerate(fc) if d["series"] == only]
        if not cols:
            raise ValueError(f"no series named {only!r}")
    k = len(cols)
    ncol = min(3, k)
    nrow = math.ceil(k / ncol)
    fig = plt.figure(figsize=(4.8 * ncol, 5.6 * nrow))
    outer = fig.add_gridspec(nrow, ncol, wspace=0.28, hspace=0.30)
    a_all = np.asarray(r.residuals, float)
    for cell, c in enumerate(cols):
        d, s = fc[c], series[c]
        g = GridSpecFromSubplotSpec(2, 1, subplot_spec=outer[cell // ncol, cell % ncol],
                                    height_ratios=[2.2, 1], hspace=0.22)
        ax_top, ax_bot = fig.add_subplot(g[0]), fig.add_subplot(g[1])
        n, f, H = s.nobs, s.freq, len(d["level"])
        lam, ref = s.model.boxlam, s.model.refactor
        sc = (100.0 if lam == 0.0 else 1.0) / ref
        ys = np.asarray(d["ystar"], float)
        if lam == 0.0:
            hist = np.array([sc * (ys[n - H + i] - ys[n - H + i - f]) for i in range(H)])
            fore = np.array([sc * (ys[n + i] - ys[n + i - f]) for i in range(H)])
            band = sc * np.asarray(d["sd_annual"], float)
            up, lo = fore + band, fore - band
            title = "LRC anual (%)"
        else:
            hist = np.asarray(s.ts.data, float)[n - H:n]
            fore = np.asarray(d["level"], float)
            sd = np.asarray(d["sd"], float)
            up = np.array([L._inv(s, ys[n + i] + 2.0 * sd[i]) for i in range(H)])
            lo = np.array([L._inv(s, ys[n + i] - 2.0 * sd[i]) for i in range(H)])
            title = "LEVEL"
        xt, xl = _year_ticks(s.ts, n, H, f)
        xlim = (-0.5, 2 * H - 0.5)

        _tj_spines(ax_top, ("left", "bottom"))
        x_all = np.arange(2 * H)
        ax_top.plot(x_all, np.r_[hist, fore], color="k", lw=1.2, marker="o", ms=3.5, zorder=3)
        ax_top.plot(np.arange(H), hist, "ko", ms=5.5, zorder=4)
        ax_top.plot(np.arange(H, 2 * H), up, "k--", lw=1.2, zorder=2)
        ax_top.plot(np.arange(H, 2 * H), lo, "k--", lw=1.2, zorder=2)
        ax_top.axvline(H - 0.5, color="0.55", lw=0.9, zorder=1)
        if lam == 0.0:
            ax_top.axhline(0, color="k", lw=0.7, zorder=1)
        ax_top.set_xlim(*xlim)
        ax_top.set_xticks(xt)
        ax_top.set_xticklabels(xl, fontsize=8)
        ax_top.tick_params(direction="out", labelsize=8)
        ax_top.set_axisbelow(True)
        ax_top.grid(axis="x", color="0.75", lw=0.5, zorder=0)
        oy, op = d["origin"]
        ax_top.set_title(f"{d['series']}   {title}   (origin {oy}.{op:02d})",
                         loc="left", fontsize=9, fontweight="bold", pad=4)

        a = a_all[:, c]
        m_err = min(H, len(a))
        err = sc * a[-m_err:]
        sig = sc * math.sqrt(float(r.sigma[c, c]))
        cmax = _prevcmax(err, sig)
        x_end = m_err - 0.5
        _tj_spines(ax_bot, ("left", "bottom"))
        ax_bot.vlines(np.arange(m_err), 0, err, colors="k", lw=1.6, zorder=3)
        ax_bot.hlines(2 * sig, -0.5, x_end, colors="k", lw=1.0, ls="--", zorder=2)
        ax_bot.hlines(-2 * sig, -0.5, x_end, colors="k", lw=1.0, ls="--", zorder=2)
        ax_bot.hlines(0, -0.5, x_end, colors="k", lw=1.2, zorder=2)
        ax_bot.set_ylim(-(cmax + 0.1 * sig), cmax + 0.1 * sig)
        yt = np.arange(0, cmax + 0.05 * sig, 2 * sig)
        ax_bot.set_yticks(np.concatenate([-yt[1:][::-1], yt]))
        from matplotlib.ticker import FormatStrFormatter
        ax_bot.yaxis.set_major_formatter(FormatStrFormatter("%.1f"))
        ax_bot.set_xlim(*xlim)
        ht = [p for p in xt if p < m_err]
        ax_bot.set_xticks(ht)
        ax_bot.set_xticklabels(xl[:len(ht)], fontsize=8)
        ax_bot.tick_params(direction="out", labelsize=8)
        ax_bot.set_axisbelow(True)
        ax_bot.grid(axis="x", color="0.75", lw=0.5, zorder=0)
        ax_bot.spines["bottom"].set_bounds(-0.5, x_end)
        ax_bot.set_title("ERR", loc="left", fontsize=9, fontweight="bold", pad=4)
    return fig


def save(fig, path, dpi=130):
    plt = _plt()
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return path
