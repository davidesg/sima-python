"""The impulse responses as they are read in a paper: CUMULATED to the level
of a differenced series, and SCALED to a shock of a stated size.

drvarma gives the orthogonalised responses of the STATIONARY series (the
transformed, differenced w) and their Monte-Carlo band. A monetary VAR in
differences is read in levels — "a rise of 25 basis points lowers prices by
x % after a year" — so the analyst cumulated the monthly responses by hand,
and the band was lost on the way (the trial run of 25-nov-2026). Here:

* `cumulative`: the running sum over h of each response, which is the
  response of the LEVEL of a series with d = 1 (of w, so of 100*log z for a
  series in logs with the usual factor). Its band is not the sum of the
  monthly bands: it is taken from the same draws, each cumulated, as the
  drvarma band is taken from them uncumulated. The draws are drvarma's,
  repeated here (Ladder.irf_fevd_bands keeps only the percentiles): N(x_hat,
  cov) through the ladder's cast, the same seed, the same rejections.
* `scale`: the shock to one series rescaled so that ITS OWN response at
  h = 0 is the stated size, in the table's units. A constant factor on the
  point and on the band (the band is the one-s.d. shock's, scaled), the usual
  practice; the factor is reported.
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


def draws_cumulative_bands(L, horizon, ndraws=800, alpha=0.05, seed=0):
    """The Monte-Carlo band of the CUMULATED orthogonalised responses: drvarma's
    draws (Ladder.irf_fevd_bands), each cumulated over h before the
    percentiles. Returns {"lo", "hi", "ndraws_used", "ndraws_rejected", "alpha"}."""
    from drvarma.irf import oirf, _stable, _bands_from_draws
    r = L.result
    if r is None or r.cov is None or not np.all(np.isfinite(r.cov)):
        raise ValueError("the fit carries no usable covariance of the estimates; no bands")
    cov = 0.5 * (r.cov + r.cov.T)
    ev, V = np.linalg.eigh(cov)
    Lc = V @ np.diag(np.sqrt(np.clip(ev, 0.0, None)))
    rng = np.random.default_rng(seed)
    od, rejected = [], 0
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
            except Exception:                                # noqa: BLE001
                rejected += 1; continue
            if not np.all(np.isfinite(o)):
                rejected += 1; continue
            od.append(np.cumsum(o, axis=0))
    finally:
        L.cast(r.x)                                          # the state back at x_hat
    if len(od) < 20:
        raise ValueError(f"only {len(od)} of {ndraws} draws were admissible; no band")
    lo, hi = _bands_from_draws(np.stack(od), alpha)
    return {"lo": lo, "hi": hi, "ndraws_used": len(od), "ndraws_rejected": rejected,
            "alpha": alpha}


def responses(L, horizon, bands=None, cumulative=False, scale=None, ndraws=800):
    """(O, lo, hi, info): the responses to read, point and band, after the
    cumulation and the scaling asked for. `bands` is drvarma's band dict (or
    None: no band). `scale` is parse_scale's (j, size) or None."""
    from drvarma.irf import oirf
    r = L.result
    O = oirf(r.phi, r.theta, r.sigma, horizon)
    lo = hi = None
    info = {"cumulative": bool(cumulative), "factor": None, "band_note": None}
    if cumulative:
        O = np.cumsum(O, axis=0)
        if bands is not None:
            cb = draws_cumulative_bands(L, horizon, ndraws=ndraws, alpha=bands["alpha"])
            lo, hi = cb["lo"], cb["hi"]
            info["band_note"] = cb
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
