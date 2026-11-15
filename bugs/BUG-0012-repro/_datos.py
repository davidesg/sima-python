"""Synthetic data for the scale bugs (BUG-0011, 0012, 0013). No real series."""
import warnings

import numpy as np

import fue
from fue.forecast import _boxcox

warnings.filterwarnings("ignore")
N = 200


def transfer(seed=11):
    """Two stationary AR(1) in logs; Y answers X with one lag."""
    rng = np.random.default_rng(seed)
    e, x = np.zeros(N), np.zeros(N)
    for t in range(1, N):
        x[t] = 0.6 * x[t - 1] + rng.normal(0, 0.01)
    for t in range(1, N):
        e[t] = 0.5 * e[t - 1] + 0.4 * x[t - 1] + rng.normal(0, 0.005)
    return e, x


def coint(seed=8):
    """Two I(1) logs with log Y - log X stationary: beta = (1, -1)."""
    rng = np.random.default_rng(seed)
    c = np.cumsum(rng.normal(0, 0.01, N))
    u = np.zeros(N)
    for t in range(1, N):
        u[t] = 0.7 * u[t - 1] + rng.normal(0, 0.004)
    return c + u + np.log(1.2), c


def pre(path, y, lam, factor, d, name):
    """Fit an AR(1) (with a mean when d = 0) by fue and write its .pre."""
    ts = fue.TimeSeries(list(map(float, y)), freq=12, start=(2000, 1), name=name)
    w = np.array([_boxcox(float(v), lam, factor) for v in y])
    for _ in range(d):
        w = np.diff(w)
    m = fue.Model(ts, d=d, D=0, boxlam=lam, ar=[[0.1]], ar_free=[[True]],
                  mu=float(w.mean()) if d == 0 else 0.0, estimate_mu=(d == 0),
                  refactor=float(factor))
    m.fit()
    m.write_pre(path)
    return path
