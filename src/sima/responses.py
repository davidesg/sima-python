"""The impulse responses as they are read in a paper: on each series' LEVEL,
with the PERMANENT EFFECT, and to a shock of a stated size.

drvarma gives the orthogonalised responses psi_h of the STATIONARY series (the
transformed, differenced w). They are an impulse response: ONE shock at h = 0,
and the response of the rates (for 100 log of a price index, the monthly
inflation). Being stationary, they die out: psi_h -> 0.

`levels`: the response of each series' LEVEL to that same single shock. The
level is the sum of its differences, so its response is psi_h with the
series' own differences undone: summed once for d = 1, twice for d = 2, and
at lag s for a seasonal difference; a series with d = D = 0 is left as it is.
Numerically, for d = 1, it is also the STEP response of the differences
(V_h = sum v_j, a shock repeated every period), but the question is another:
one shock, the level measured. Its band is taken from the same Monte-Carlo
draws, each transformed, never by summing the monthly bands.

The PERMANENT EFFECT: for a series with d = 1 and no seasonal difference the
level response converges, to Psi(1) P (row of the series) with
Psi(1) = Phi(1)^-1 Theta(1) and P the Cholesky factor of Sigma: a shock to an
I(1) series moves its level for good. With d = 0 the level response dies out
(the effect is 0); with d = 2 or a seasonal difference it does not converge,
and there is no permanent effect to report.

`scale`: the shock to one series rescaled so that ITS OWN response at h = 0 is
the stated size, in the table's units. A constant factor on the point and on
the band (the band is the one-s.d. shock's, scaled), the usual practice; the
factor is reported.

The draws repeat drvarma's (Ladder.irf_fevd_bands keeps only the
percentiles): N(x_hat, cov) through the ladder's cast, the same seed, the same
rejections. When drvarma gives the draws, this goes.
"""
from __future__ import annotations

import numpy as np


def parse_scale(text, names):
    """"FF=25" -> (index of FF, 25.0); "" -> None. Raises ValueError."""
    t = (text or "").strip()
    if not t:
        return None
    if "=" not in t:
        raise ValueError(f'scale must be "SERIES=size", e.g. "{names[-1]}=25"')
    nm, v = (x.strip() for x in t.split("=", 1))
    if nm not in names:
        raise ValueError(f"scale names {nm!r}, not one of the series: {', '.join(names)}")
    return names.index(nm), float(v)


def differences(L):
    """[(d, D, s)] of each series, from its univariate model."""
    out = []
    for s in L.series:
        m = s.model
        out.append((int(getattr(m, "d", 0) or 0), int(getattr(m, "D", 0) or 0),
                    int(getattr(s.ts, "freq", 1) or 1)))
    return out


def undo(x, d, D, s):
    """The response of the level from that of the differenced series, along
    axis 0 (h = 0, 1, ...; nothing before h = 0): (1 - B)^-d (1 - B^s)^-D."""
    y = np.array(x, float, copy=True)
    for _ in range(d):
        y = np.cumsum(y, axis=0)
    for _ in range(D):
        for h in range(s, y.shape[0]):
            y[h] = y[h] + y[h - s]
    return y


def to_levels(O, diffs):
    """Each RESPONSE series (axis 1) back to its level, by its own differences."""
    out = np.array(O, float, copy=True)
    for i, (d, D, s) in enumerate(diffs):
        out[:, i, :] = undo(O[:, i, :], d, D, s)
    return out


def permanent(phi, theta, sigma, diffs):
    """The permanent effect on each level, (m, m): Psi(1) P on the rows with
    d = 1 and D = 0; 0 on the rows with d = D = 0; NaN where the level response
    does not converge (d = 2, or a seasonal difference)."""
    phi = np.asarray(phi, float)
    theta = np.asarray(theta, float)
    m = np.asarray(sigma).shape[0]
    A = np.eye(m) - (phi.sum(axis=0) if phi.size else 0.0)
    B = np.eye(m) - (theta.sum(axis=0) if theta.size else 0.0)
    P = np.linalg.cholesky(np.asarray(sigma, float))
    lr = np.linalg.solve(A, B) @ P
    out = np.full((m, m), np.nan)
    for i, (d, D, _s) in enumerate(diffs):
        if D == 0 and d == 1:
            out[i] = lr[i]
        elif D == 0 and d == 0:
            out[i] = 0.0
    return out


def _draws(L, horizon, diffs, ndraws, alpha, seed=0):
    """The band of the level responses and of the permanent effect, from
    drvarma's draws, each transformed."""
    from drvarma.irf import oirf, _stable, _bands_from_draws
    r = L.result
    if r is None or r.cov is None or not np.all(np.isfinite(r.cov)):
        raise ValueError("the fit carries no usable covariance of the estimates; no bands")
    cov = 0.5 * (r.cov + r.cov.T)
    ev, V = np.linalg.eigh(cov)
    Lc = V @ np.diag(np.sqrt(np.clip(ev, 0.0, None)))
    rng = np.random.default_rng(seed)
    od, pd, rejected = [], [], 0
    try:
        for _ in range(int(ndraws)):
            vec = r.x + Lc @ rng.standard_normal(r.x.size)
            try:
                _mu, phi, theta, qq, _w, ifa = L.cast(vec)
                if ifa:
                    rejected += 1; continue
                sig = r.sigma2 * np.asarray(qq, float)
                np.linalg.cholesky(sig)
                if phi.shape[0] and not _stable(phi):
                    rejected += 1; continue
                if theta.shape[0] and not _stable(-np.asarray(theta, float)):
                    rejected += 1; continue
                o = oirf(phi, theta, sig, horizon)
                pe = permanent(phi, theta, sig, diffs)
            except Exception:                                # noqa: BLE001
                rejected += 1; continue
            if not np.all(np.isfinite(o)):
                rejected += 1; continue
            od.append(to_levels(o, diffs))
            pd.append(pe)
    finally:
        L.cast(r.x)                                          # the state back at x_hat
    if len(od) < 20:
        raise ValueError(f"only {len(od)} of {ndraws} draws were admissible; no band")
    lo, hi = _bands_from_draws(np.stack(od), alpha)
    plo, phi_ = _bands_from_draws(np.stack(pd), alpha)
    return {"lo": lo, "hi": hi, "perm_lo": plo, "perm_hi": phi_,
            "ndraws_used": len(od), "ndraws_rejected": rejected, "alpha": alpha}


def responses(L, horizon, bands=None, levels=False, scale=None, ndraws=800):
    """(O, lo, hi, info): the responses to read, point and band, on the levels
    when asked, and scaled. `bands` is drvarma's band dict (or None: no band);
    `scale` is parse_scale's (j, size) or None. With `levels`, info carries the
    permanent effect ("permanent", and its band "perm_lo"/"perm_hi")."""
    from drvarma.irf import oirf
    r = L.result
    O = oirf(r.phi, r.theta, r.sigma, horizon)
    lo = hi = None
    diffs = differences(L)
    info = {"levels": bool(levels), "diffs": diffs, "factor": None, "band_note": None,
            "permanent": None, "perm_lo": None, "perm_hi": None}
    if levels:
        O = to_levels(O, diffs)
        info["permanent"] = permanent(r.phi, r.theta, r.sigma, diffs)
        if bands is not None:
            cb = _draws(L, horizon, diffs, ndraws, bands["alpha"])
            lo, hi = cb["lo"], cb["hi"]
            info.update(band_note=cb, perm_lo=cb["perm_lo"], perm_hi=cb["perm_hi"])
    elif bands is not None:
        lo, hi = bands["oirf_lo"], bands["oirf_hi"]
    if scale is not None:
        j, size = scale
        base = O[0, j, j]
        if not base:
            raise ValueError("the shocked series' own response at h = 0 is zero: cannot scale")
        c = size / base
        O = O.copy()
        O[:, :, j] *= c
        if lo is not None:
            lo, hi = lo.copy(), hi.copy()
            a, b = lo[:, :, j] * c, hi[:, :, j] * c
            lo[:, :, j], hi[:, :, j] = np.minimum(a, b), np.maximum(a, b)
        for k in ("permanent", "perm_lo", "perm_hi"):
            if info[k] is not None:
                info[k] = info[k].copy()
                info[k][:, j] *= c
        if info["perm_lo"] is not None:
            a, b = info["perm_lo"][:, j].copy(), info["perm_hi"][:, j].copy()
            info["perm_lo"][:, j], info["perm_hi"][:, j] = np.minimum(a, b), np.maximum(a, b)
        info["factor"] = (j, size, float(base), float(c))
    return O, lo, hi, info


def units_line(L, names):
    """What the numbers are in, per series: w = refactor * BoxCox(z)."""
    out = []
    for s, nm in zip(L.series, names):
        lam = float(s.model.boxlam)
        f = float(getattr(s.model, "refactor", 1.0) or 1.0)
        if lam == 0 and f == 100:
            u = "per cent (100 log)"
        elif lam == 1 and f == 100:
            u = "100 x its units (a rate in %: basis points)"
        elif lam == 1 and f == 1:
            u = "its own units"
        else:
            u = f"w = {f:g} x BoxCox(z, {lam:g})"
        out.append(f"{nm}: {u}")
    return "Units: " + "; ".join(out) + "."
