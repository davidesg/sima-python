"""The LEVELS the canonical analysis reads, without the deterministic terms
(BUG-0018).

drvarma's ``Series.levels()`` gives each series' Box-Cox and seasonal
differences with its deterministic terms INSIDE: the harmonics, the steps,
the impulses of its univariate model. Box and Tiao's canonical analysis
measures predictability, and a harmonic is predictable by construction and a
step acts as a local unit root: both push lam towards 1 and lengthen the
order by M(l), which prepare_vec proposes as p. Method 1 of Jenkins and Alavi
reads ``Series.stationary()``, which removes them; the canonical analysis was
the one reading that did not.

How, without a new engine: ``stationary()`` is w = the differences of the
levels minus those of the deterministic terms (fue's cast, with the model's
own coefficients and time origin -- the gate's). So the differences of the
levels minus w, computed with the coefficients of the terms to KEEP set to
zero, are exactly the differences of the terms to remove; integrated, they
are those terms in levels (up to a constant, which the canonical analysis'
VAR absorbs). mu is never removed: the cast does not subtract it, and the
drift of the differences is the common growth the analysis has to see.

The groups: the deterministic SEASONALITY (cos, sin, alter, seasonal dummies,
Easter) is always removed; the INTERVENTIONS (impulses, steps, ramps, their
transfer functions, custom regressors) by default too, behind a switch; a
deterministic TREND is never removed (as mu).
"""
from __future__ import annotations

import numpy as np

SEASONAL = {"cos", "sin", "alter", "seasonal", "easter"}
KEPT_ALWAYS = {"trend"}


def _groups(series):
    """For each deterministic term: (its type, the slice of x that holds its
    coefficients), in fue's order (all omegas, then all deltas)."""
    itvs = series.model.interventions
    out, i = [], 0
    pos = [[] for _ in itvs]
    for k, itv in enumerate(itvs):
        for f in itv.omega_free:
            if f:
                pos[k].append(i)
                i += 1
    for k, itv in enumerate(itvs):
        for f in itv.delta_free:
            if f:
                pos[k].append(i)
                i += 1
    for k, itv in enumerate(itvs):
        out.append((itv.type, pos[k]))
    return out


def _removes(typ, interventions):
    if typ in KEPT_ALWAYS:
        return False
    if typ in SEASONAL:
        return True
    return interventions == "remove"


def describe(series, interventions="remove"):
    """What is removed from this series' levels, in words ("" when nothing)."""
    seas = sum(1 for t, _ in _groups(series) if t in SEASONAL)
    itv = [t for t, _ in _groups(series) if t not in SEASONAL | KEPT_ALWAYS]
    parts = []
    if seas:
        parts.append(f"{seas} seasonal term(s)")
    if itv:
        parts.append(f"{len(itv)} intervention(s) ({', '.join(itv)})"
                     + ("" if interventions == "remove" else ", KEPT"))
    return ", ".join(parts)


def clean_levels(series, interventions="remove"):
    """The levels with the deterministic terms removed (see the module)."""
    from fue.cast_us import cast_us_py
    L = np.asarray(series.levels(), float)
    groups = _groups(series)
    if not any(_removes(t, interventions) for t, _ in groups):
        return L
    x = np.array(series.x, float)
    for t, idx in groups:
        if not _removes(t, interventions):
            x[idx] = 0.0                       # kept in the levels: out of w's subtraction
    *_, w, ifault = cast_us_py(x, series.est_spec())
    if ifault:
        raise ValueError(f"{series.name}: the cast failed (ifault {ifault}) removing its "
                         "deterministic terms")
    w = np.asarray(w, float)
    d = int(series.model.d or 0)
    dl = L.copy()
    for _ in range(d):
        dl = dl[1:] - dl[:-1]
    n = min(len(dl), len(w))
    det = dl[-n:] - w[-n:]
    for _ in range(d):
        det = np.concatenate([[0.0], np.cumsum(det)])
    return L[-len(det):] - det
