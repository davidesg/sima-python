"""sima's figures: presentation only, in the school's design.

Every number comes from the engine (drvarma: the ladder, its IRF/FEVD and its
bands); nothing is computed here that a table does not already say. The
design is the one the suite already reads:

* the IMPULSE RESPONSE is drawn as what it is, an ACF-like function of the
  lag: thick black impulses at h = 0..H, a zero line, the seasonal grid, only
  the left axis (fue's `_draw_acf_panel`). Its band is dashed, as the ACF's,
  but it follows h, since here it is a Monte-Carlo band per horizon.
* the VARIANCE DECOMPOSITION uses the same grid of panels and the same
  impulses, on a fixed 0-100 % axis: the row of a series reads the same in
  both figures.
* the residual CCFs are drvus' panels, reused from drvarma
  (`plots._draw_ccf_panel`), not redrawn.
* the forecast is each series in its level, with its 95 % band dashed.

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


def _impulse_panel(ax, h, vals, lo, hi, ylim, yticks, freq, title, zero=True):
    ax.vlines(h, 0.0, vals, colors="k", lw=3.0 if len(h) <= 30 else 2.2, zorder=3)
    if zero:
        ax.axhline(0.0, color="k", lw=1.4, zorder=2)
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
                           zero=False)
    sub = ("dashed: %d %% Monte-Carlo band, %d draws" % (round(100 * (1 - bands["alpha"])),
                                                         bands["ndraws_used"])
           if bands else "no band")
    fig.suptitle("Forecast-error variance decomposition, % by shock "
                 f"(Cholesky order: {', '.join(names)})\n{sub}", fontsize=10)
    fig.tight_layout()
    return fig


def residual_ccf_figure(L, nlags, freq=12):
    """drvus' two-sided CCF of every pair of residuals of the fitted model."""
    from drvarma.diagnostics import ccf, qccf
    from drvarma.plots import _draw_ccf_panel
    plt = _plt()
    a = np.asarray(L.result.residuals, float)
    n, m = a.shape
    names = [s.name for s in L.series]
    pairs = [(i, j) for i in range(m) for j in range(i + 1, m)]
    ncol = min(2, len(pairs))
    nrow = math.ceil(len(pairs) / ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(7.5 * ncol, 3.2 * nrow), squeeze=False)
    for k, (i, j) in enumerate(pairs):
        rho = ccf(a[:, i], a[:, j], nlags)
        Q, _df, _p = qccf(a[:, i], a[:, j], nlags)
        _draw_ccf_panel(axes[k // ncol, k % ncol], rho, nlags, n, freq,
                        f"{names[i]} , {names[j]}", "Q ( %d ) = %.1f" % (nlags, Q))
    for k in range(len(pairs), nrow * ncol):
        axes[k // ncol, k % ncol].set_visible(False)
    fig.suptitle("Residual cross-correlations of the fitted model "
                 "(lag k > 0: the second series leads)", fontsize=10)
    fig.tight_layout()
    return fig


def forecast_figure(L, fc, history=None):
    """Each series in its level: the recent history, the forecasts and the
    95 % band (dashed; asymmetric under a log model, so drawn as two lines)."""
    plt = _plt()
    k = len(fc)
    fig, axes = plt.subplots(k, 1, figsize=(8.5, 2.4 * k + 0.4), squeeze=False)
    for c, (d, s) in enumerate(zip(fc, [L.series[i] for i in L._act])):
        ax = axes[c, 0]
        n, f = s.nobs, s.freq
        hist = history or max(3 * f, 24)
        y = np.asarray(s.ts.data, float)[:n]
        t0 = max(0, n - hist)
        x_h = np.arange(t0 + 1, n + 1)
        H = len(d["level"])
        x_f = np.arange(n + 1, n + H + 1)
        ax.plot(x_h, y[t0:], color="k", lw=1.4)
        ax.plot(np.r_[n, x_f], np.r_[y[n - 1], d["level"]], color="k", lw=1.4, ls="-",
                marker="o", ms=3, markevery=list(range(1, H + 1)))
        ax.plot(x_f, d["low95"], color="k", lw=1.0, ls="--")
        ax.plot(x_f, d["high95"], color="k", lw=1.0, ls="--")
        ax.axvline(n + 0.5, color="0.5", lw=0.8)
        ticks = [x for x in np.r_[x_h, x_f] if (x - 1) % f == 0] if f > 1 else list(x_h[::5])
        ax.set_xticks(ticks)
        ax.set_xticklabels(["%d.%02d" % s.date_of(int(x)) if f > 1 else "%d" % s.date_of(int(x))[0]
                            for x in ticks], fontsize=8)
        ax.tick_params(axis="y", direction="out", labelsize=8)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        oy, op = d["origin"]
        ax.set_title(f"{d['series']}: forecasts from {oy}.{op:02d}, 95 % band dashed",
                     loc="left", fontsize=9)
    fig.tight_layout()
    return fig


def save(fig, path, dpi=130):
    plt = _plt()
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return path
