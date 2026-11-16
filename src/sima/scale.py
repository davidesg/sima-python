"""The rescaling factor in a system: what sima checks and how it presents.

Each fue file carries its own rescaling factor and its own lambda, and the
engines work in w = refactor * BoxCox(z). The rule is fue's (`fue.scale`), one
for the whole suite; this module applies it to a SYSTEM:

* `load_notes`: when the files are loaded, whether the optimiser can work on
  each series as it comes, and whether the files share a factor and a lambda;
* `cross`: the factor that takes a coefficient between two series from the
  engine's units to the units each series is presented in;
* `to_engine_b2`: the analyst's restriction on beta, given in those units,
  taken to the engine's.

The engines' own tables (drvec's .out) stay in the engine's units: they mirror
the C. What sima writes itself, and what the analyst imposes, are in the
series' units (BUG-0012).
"""

from __future__ import annotations

import numpy as np

from fue.scale import check_scale, display_cross, display_scale


def units_of_files(files):
    """{series name: (lambda, refactor)} read from the fue files."""
    import contextlib
    import io

    import fue
    out = {}
    for f in files:
        with contextlib.redirect_stdout(io.StringIO()):
            ts, model = fue.load(str(f))
        out[ts.name] = (float(model.boxlam), float(getattr(model, "refactor", 1.0) or 1.0))
    return out


def units_of_series(series):
    """{series name: (lambda, refactor)} from the session's series."""
    return {s.name: (float(s.model.boxlam),
                     float(getattr(s.model, "refactor", 1.0) or 1.0)) for s in series}


def mixed(units):
    """True when the series do not share one factor and one lambda."""
    return len(set(units.values())) > 1


def cross(units, out, inp):
    """Multiplier for a coefficient of series `inp` in the equation of `out`:
    engine's units -> the units each is presented in. 1 when they agree."""
    lo, fo = units[out]
    li, fi = units[inp]
    return display_cross(lo, fo, li, fi)


def what(units, out, inp):
    po = display_scale(*units[out]).percent
    pi = display_scale(*units[inp]).percent
    return ("an elasticity" if po and pi else
            f"per cent of {out} per unit of {inp}" if po else
            f"units of {out} per 1 % of {inp}" if pi else
            f"units of {out} per unit of {inp}")


def load_notes(series):
    """Lines for load_pre: the scale of each series and the mix of factors."""
    out = []
    for s in series:
        try:
            m = s.model
            c = check_scale(np.asarray(s.ts.data, float), float(m.boxlam),
                            int(m.d or 0), int(m.D or 0),
                            int(getattr(s.ts, "freq", 1) or 1),
                            float(getattr(m, "refactor", 1.0) or 1.0))
        except Exception:                                   # noqa: BLE001
            continue
        for _kind, text in c.problems:
            out.append(f"SCALE — {s.name}: {text}. Standard errors, the stopping "
                       "code and a test that finds \"no effect\" are not to be "
                       "trusted on this file as it is.")
    u = units_of_series(series)
    if mixed(u):
        out.append(
            "UNITS — the files do not share one rescaling factor or one lambda ("
            + ", ".join(f"{n}: lambda={l:g}, refactor={f:g}" for n, (l, f) in u.items())
            + "). The engines work in w = refactor*BoxCox(z), so a coefficient "
            "between two series carries the ratio of their factors, and standard "
            "errors lose precision. sima presents its own tables and takes your "
            "restrictions in each series' units; drvec's .out stays in the "
            "engine's. A common factor (100 with logs) avoids all of it.")
    return out


def to_engine_b2(units, order, r, value_by_row):
    """{row name: value in the series' units} -> {row name: engine value}.

    B2's entry for series i in the relation normalised on a Y1 series k is, in
    the engine, its value in the series' units divided by cross(k, i). A row
    restriction holds one value for every relation, so with r > 1 the Y1
    series must agree in their units; if they do not, it cannot be written and
    the caller is told.
    """
    y1 = list(order[len(order) - r:])
    out = {}
    for nm, v in value_by_row.items():
        ks = {round(cross(units, k, nm), 12) for k in y1}
        if len(ks) > 1:
            raise ValueError(
                f"the restriction on {nm} cannot be written: the series the relations "
                f"are normalised on ({', '.join(y1)}) do not share a rescaling factor, "
                "so one value in the series' units is a different engine value in "
                "each relation. Bring the files to a common factor.")
        out[nm] = float(v) / ks.pop()
    return out
