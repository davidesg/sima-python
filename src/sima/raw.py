"""The raw-data entry (docs/STUDY-raw-entry.md): an analyst with raw series and
no univariate models.

* `read_table`: an Excel or CSV table, one column per series, in original
  levels; an optional first column of dates (a year, or year-period).
* `characterize`: per series, with art's engine and in art's order, the
  transformation the two routes start from: lambda (Box-Cox), d (unit roots,
  art's policy: one step at a time), the seasonality (HAC F-test) and a
  preliminary outlier scan (reported, not acted on). Each series keeps its OWN
  lambda and d: there is no joint consensus (the old sima's first fault).
* `levels`: the transformed levels (Box-Cox and seasonal differences, no
  regular ones) that the canonical analysis reads.

Facts only; the reading and the menu are in evidence.py.
"""
from __future__ import annotations

import math
import os
import re

import numpy as np

DATE_HEADERS = {"date", "dates", "year", "years", "fecha", "periodo", "period", "time", "t"}
REFACTOR = 100.0                     # fue's rescaling of the transformed series


class RawError(ValueError):
    pass


# ── the table ──────────────────────────────────────────────────────────────

def _is_number(s):
    try:
        float(s)
        return True
    except (TypeError, ValueError):
        return False


def _parse_date(s, freq):
    """(year, period) from a date cell: 1850, 1850.0, '1972-08', '1972M08',
    '1972Q3', '1972:3', '1972-08-01'. None if not a date."""
    s = str(s).strip()
    if not s:
        return None
    m = re.fullmatch(r"(\d{4})(?:\.0+)?", s)
    if m:
        return int(m.group(1)), 1
    m = re.fullmatch(r"(\d{4})\s*[-/:MmQq]\s*(\d{1,2})(?:[-/]\d{1,2})?(?:[ T].*)?", s)
    if m:
        y, p = int(m.group(1)), int(m.group(2))
        if freq == 4 and "q" not in s.lower() and p > 4:     # a month in quarterly data
            p = (p - 1) // 3 + 1
        return y, p
    return None


def read_table(path):
    """(names, data n x m, first_dates or None) from an .xlsx/.xls or .csv.

    The first row is a header if any of its cells is not a number (a numeric
    header-less CSV keeps its first observation: the old sima's BUG). A first
    column is DATES if its header is a date word or its cells are not plain
    numbers in the series' sense; its first and second cells are returned so
    the caller can infer the start and check the frequency."""
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        raise RawError(f"no file {path}")
    low = path.lower()
    if low.endswith((".xlsx", ".xls")):
        import pandas as pd
        df = pd.read_excel(path, header=None, dtype=str)
        rows = df.fillna("").astype(str).values.tolist()
    else:
        import csv
        with open(path, newline="") as fh:
            sample = fh.read(4096)
            fh.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
            except csv.Error:
                dialect = csv.excel
            rows = [r for r in csv.reader(fh, dialect) if any(c.strip() for c in r)]
    if not rows:
        raise RawError("the table is empty")
    header = None
    if not all(_is_number(c) for c in rows[0] if c.strip()):
        header = [c.strip() for c in rows[0]]
        rows = rows[1:]
    ncol = max(len(r) for r in rows)
    rows = [list(r) + [""] * (ncol - len(r)) for r in rows]
    first = [r[0].strip() for r in rows]
    date_col = False
    if header and header[0].lower() in DATE_HEADERS:
        date_col = True
    elif not all(_is_number(c) for c in first):
        date_col = True
    names = (header or [f"S{j + 1}" for j in range(ncol)])
    cols = list(range(1, ncol)) if date_col else list(range(ncol))
    names = [names[j] if j < len(names) and names[j] else f"S{j + 1}" for j in cols]
    data = np.full((len(rows), len(cols)), np.nan)
    for i, r in enumerate(rows):
        for k, j in enumerate(cols):
            c = r[j].strip().replace(",", ".") if r[j].count(",") == 1 and "." not in r[j] else r[j].strip()
            if _is_number(c):
                data[i, k] = float(c)
    dates = first if date_col else None
    return names, data, dates


def infer_start(dates, freq):
    """(year, period) of the first row from the date column, or None."""
    if not dates:
        return None
    return _parse_date(dates[0], freq)


def check_table(names, data):
    """Refusals and notes: missing values (where), too short, non-positive."""
    n, m = data.shape
    if m < 2:
        raise RawError(f"{m} series: a system needs two or more (one series is art's).")
    bad = [(names[j], i + 1) for j in range(m) for i in range(n) if not np.isfinite(data[i, j])]
    if bad:
        where = ", ".join(f"{nm} row {r}" for nm, r in bad[:6]) + (" ..." if len(bad) > 6 else "")
        raise RawError(f"missing or non-numeric values: {where}. sima needs one common, "
                       "complete calendar; fill or trim the table first.")
    if n < 30:
        raise RawError(f"{n} observations: too few for a system.")
    return [names[j] for j in range(m) if np.min(data[:, j]) <= 0]


# ── the characterization ───────────────────────────────────────────────────

def _ts(y, name, freq, start):
    import fue
    return fue.TimeSeries(list(map(float, y)), freq=freq, start=start, name=name)


def characterize_one(y, name, freq, start):
    """The facts of one series, in art's order: lambda -> d -> seasonality ->
    preliminary outliers. Returns a dict."""
    try:
        import art
    except ImportError as e:              # pragma: no cover
        raise RawError(f"art is not installed ({e}): the raw entry uses art's engine "
                       "(pip install art-tseries).") from e
    ts = _ts(y, name, freq, start)
    out = {"name": name, "n": len(y)}
    # lambda
    if np.min(y) <= 0:
        out.update(lam=1.0, lam_why="non-positive values: logs impossible", lam_ambiguous=False,
                   corr_raw=None, corr_log=None)
    else:
        b = art.describe_boxcox(ts).data
        out.update(lam=float(b["recommended_lambda"]),
                   corr_raw=float(b["corr_raw_signed"]), corr_log=float(b["corr_log_signed"]),
                   lam_ambiguous=bool(b.get("ambiguous", False)),
                   lam_why="mean-sd correlation")
    lam = out["lam"]
    # d
    u = art.describe_unit_root(ts, lam=lam, max_d=2).data
    out["d"] = int(u["recommended_d_policy"])
    out["d_tests"] = int(u["recommended_d"])
    out["unit_root"] = [(r["d"], r["adf_pvalue"], r["kpss_pvalue"], r["verdict"])
                        for r in u["results"]]
    # seasonality
    out["seasonal"] = None
    out["D"] = 0
    out["harmonics"] = False
    if freq > 1:
        s = art.detect_seasonality(ts, d=out["d"], lam=lam)
        out["seasonal"] = (bool(s.seasonal_detected), float(s.f_stat), float(s.p_value))
        out["harmonics"] = bool(s.seasonal_detected)
    # preliminary outliers (reported only)
    try:
        p = art.describe_prelim_scan(ts, d=out["d"], D=out["D"], lam=lam).data
        out["outliers"] = [(o.get("date"), float(o["z"])) for o in p.get("outliers", [])]
        out["q"] = (float(p["q_stat"]), int(p["q_lag"]), float(p["q_pvalue"])) \
            if p.get("q_stat") is not None else None
    except Exception as e:                # noqa: BLE001
        out["outliers"], out["q"] = [], None
        out["scan_error"] = str(e)
    return out


def characterize(names, data, freq, start):
    return [characterize_one(data[:, j], names[j], freq, start) for j in range(len(names))]


_SET = re.compile(r"\s*(lam|lambda|d|D|harmonics)\s*=\s*([-\w.]+)\s*")


def apply_overrides(chars, text):
    """'MINK: lam=0, d=0; MUSKRAT: d=1, harmonics=no' -> the analyst's changes
    on top of the engine's proposal. Returns the list of changes made."""
    if not text or not text.strip():
        return []
    by = {c["name"]: c for c in chars}
    changes = []
    for part in text.split(";"):
        if not part.strip():
            continue
        nm, sep, rest = part.partition(":")
        nm = nm.strip()
        if not sep or nm not in by:
            raise RawError(f"'{part.strip()}': write SERIES: key=value, ...; the series are "
                           f"{', '.join(by)}.")
        c = by[nm]
        for item in rest.split(","):
            if not item.strip():
                continue
            m = _SET.fullmatch(item)
            if not m:
                raise RawError(f"'{item.strip()}': keys are lam, d, D, harmonics.")
            k, v = m.group(1), m.group(2)
            if k in ("lam", "lambda"):
                lam = float(v)
                if lam not in (0.0, 1.0):
                    raise RawError("lambda is 0 (logs) or 1 (levels), as in art.")
                if lam == 0.0 and c.get("lam_why", "").startswith("non-positive"):
                    raise RawError(f"{nm} has non-positive values: logs are impossible.")
                c["lam"] = lam
            elif k in ("d", "D"):
                iv = int(v)
                if not 0 <= iv <= 2:
                    raise RawError(f"{k} = {iv}: 0, 1 or 2.")
                c[k] = iv
                if k == "D" and iv:
                    c["harmonics"] = False
            else:
                c["harmonics"] = v.lower() in ("1", "yes", "true", "si", "sí")
                if c["harmonics"]:
                    c["D"] = 0
            changes.append(f"{nm}: {k} = {v}")
        c["changed"] = True
    return changes


def boxcox(y, lam):
    y = np.asarray(y, float)
    if lam == 0.0:
        return REFACTOR * np.log(y)
    if lam == 1.0:
        return REFACTOR * y
    return REFACTOR * (y ** lam - 1.0) / lam


def levels(data, chars, freq):
    """The transformed levels, n' x m: each series' Box-Cox and seasonal
    differences, no regular ones, aligned at the end."""
    cols = []
    for j, c in enumerate(chars):
        y = boxcox(data[:, j], c["lam"])
        for _ in range(int(c.get("D", 0))):
            y = y[freq:] - y[:-freq]
        cols.append(y)
    n = min(len(v) for v in cols)
    return np.column_stack([v[-n:] for v in cols])


def date_label(start, freq, k):
    """The label of observation k (0-based)."""
    y0, p0 = start
    if freq <= 1:
        return str(y0 + k)
    t = (p0 - 1) + k
    return f"{y0 + t // freq}.{t % freq + 1:02d}"


def window(start, freq, n):
    return f"{date_label(start, freq, 0)} - {date_label(start, freq, n - 1)}"


def _fmt_p(p):
    return "—" if p is None or (isinstance(p, float) and math.isnan(p)) else f"{p:.3f}"


# ── the fue specification (both routes) ────────────────────────────────────

PROVENANCE = "* Built by sima's raw entry (route U), not reviewed in art"


def _operator(title, order, lag_only=0):
    """An .inp operator block: `order` coefficients at 0, free; with
    `lag_only` = k, only lag k is free (art's sparse AR[k]/MA[k])."""
    if order <= 0:
        return [f"** {title}:", "0"]
    rows = []
    for k in range(1, order + 1):
        rows.append(f"0.000000  {0 if lag_only and k != lag_only else 1}")
    return [f"** {title}:", f"1 {order}", "**"] + rows


def write_inp(path, name, y, freq, start, lam, d, D=0, harmonics=False, mean=False,
              p=0, q=0, P=0, Q=0, sparse_ar=0, sparse_ma=0, comment=""):
    """One fue .inp: the transformation (lambda, d, D), the seasonal harmonics
    as free deterministic terms, an optional free mean, and free ARMA
    operators at 0. The same layout as drvarma's ladder.split; existing files
    are overwritten only by the caller's choice (the caller checks)."""
    s = int(freq)
    year, sub = start
    specs = []
    if harmonics and s > 1:
        for k in range(1, (s + 1) // 2):
            specs += [f"cos {k}", f"sin {k}"]
        if s % 2 == 0:
            specs.append("alter")
    nd = len(specs)
    L = ["************************************************",
         "* Input file for program FUE                   *",
         "************************************************"]
    if comment:
        L.append(comment)
    L += ["", "** Frequency of time series: either 1(A), 4(Q) or 12(M):", f" {s}",
          "** Number of observations and starting date of time series:",
          f" {len(y)}  {sub if s > 1 else 1} {year} {name}",
          "** Number of deterministic variables (including seasonal components):", f"{nd}"]
    if nd:
        L += ["**"] + specs + ["**", " ".join(["0"] * nd)]
        for _k in range(nd):
            L += ["**", "0.000000  1"]
        L += ["**", " ".join(["0"] * nd)]
    pr = max(p, sparse_ar)
    qr = max(q, sparse_ma)
    L += _operator("Number and orders of regular AR operators", pr, sparse_ar)
    L += _operator("Number and orders of annual AR operators", P)
    L += _operator("Number and orders of regular MA operators", qr, sparse_ma)
    L += _operator("Number and orders of anual MA operators", Q)
    L += ["** Number and frequencies of regular AR(2) operators with fixed frequency:", "0",
          "** Number and frequencies of regular MA(2) operators with fixed frequency:", "0",
          "** Mean parameter (mu):", f"{_mean0(y, lam, d, D, s):.6f} 1" if mean else "0",
          "** Box-Cox lambda, regular differences and complete annual differences:",
          f" {float(lam):g}  {int(d)}  {int(D)}",
          "** Individual factors of the annual difference (starting at freq 0.0):",
          " ".join(["0"] * (s // 2 + 1)) if s > 1 else " 0",
          "** ACF/PACF bands (0 Automatic) and reescaling factor:", f" 0 {REFACTOR:g}",
          "** Time series (stochastic and non-standard deterministic variables):"]
    L += [f"{v:.15g}" for v in y]
    with open(path, "w") as fh:
        fh.write("\n".join(L) + "\n")
    return path


def _mean0(y, lam, d, D, s):
    """The mean's starting value: the sample mean of the stationary series.
    Starting at 0 on a series in levels (the mink, ~1080 in 100 ln) let the
    optimiser push the AR to a unit root to carry the level instead."""
    w = boxcox(y, lam)
    for _ in range(int(D)):
        w = w[s:] - w[:-s]
    for _ in range(int(d)):
        w = np.diff(w)
    return float(np.mean(w))


# ── route U: the univariate seed ───────────────────────────────────────────

def _resid(model):
    r = model.residuals
    return np.asarray(getattr(r, "data", r), float)


def _fit(path):
    import fue
    ts, model = fue.load(path)
    model.fit()
    return model


def build_one(y, c, freq, start, out_dir, top_n=5):
    """Route U for one series: art's first-ranked orders on the characterized
    transformation, fitted with fue (the mean kept when d = D = 0, a drift
    kept only if |t| >= 2), the residuals checked, and the .pre/.out written
    with the provenance line. Returns a dict of facts."""
    import art
    from fue.diagnostics import ljung_box
    name = c["name"]
    ts = _ts(y, name, freq, start)
    D = int(c.get("D", 0))
    specs = art.suggest_orders(ts, d=c["d"], D=D, lam=c["lam"], top_n=top_n)
    if not specs:
        raise RawError(f"{name}: art's identification returned no candidate")
    sp = specs[0]
    tied = [x.label() for x in specs if getattr(x, "tied", False)]
    order = dict(p=int(sp.p if not sp.sparse_ar_lag else 0),
                 q=int(sp.q if not sp.sparse_ma_lag else 0),
                 P=int(sp.P), Q=int(sp.Q), sparse_ar=int(sp.sparse_ar_lag),
                 sparse_ma=int(sp.sparse_ma_lag))
    base = os.path.join(out_dir, f"{name}_u")
    stationary = c["d"] == 0 and D == 0
    common = dict(name=name, y=y, freq=freq, start=start, lam=c["lam"], d=c["d"], D=D,
                  harmonics=c.get("harmonics", False), comment=PROVENANCE, **order)
    write_inp(base + ".inp", mean=True, **common)
    model = _fit(base + ".inp")
    mean_note = "mean estimated (d = D = 0)" if stationary else ""
    if not stationary:
        par = np.asarray(model.params, float)
        se = np.asarray(model.std_errors, float)
        t = par[-1] / se[-1] if se[-1] > 0 else 0.0
        if abs(t) < 2.0:
            write_inp(base + ".inp", mean=False, **common)
            model = _fit(base + ".inp")
            mean_note = f"no drift (|t| = {abs(t):.2f} < 2)"
        else:
            mean_note = f"drift kept (t = {t:.2f})"
    model.write_pre(base + ".pre")
    model.write_out(base + ".out", inp_name=os.path.basename(base) + ".inp",
                    out_name=os.path.basename(base) + ".out")
    with open(base + ".pre") as fh:
        lines = fh.read().split("\n")
    if PROVENANCE not in lines:
        lines.insert(4, PROVENANCE)
        with open(base + ".pre", "w") as fh:
            fh.write("\n".join(lines))
    r = _resid(model)
    npar = len(np.asarray(model.params, float))
    lags = [k for k in ((6, 12) if freq == 1 else (freq, 2 * freq)) if k > npar]
    lb = ljung_box(r, lags=lags, df_correction=npar) if lags else None
    z = (r - r.mean()) / r.std()
    big = int(np.argmax(np.abs(z)))
    return {"name": name, "label": sp.label(), "order": order, "tied": tied,
            "candidates": [x.label() for x in specs[:3]],
            "pre": base + ".pre", "mean": mean_note,
            "params": [float(v) for v in np.asarray(model.params, float)],
            "sigma": float(np.std(r)),
            "lb": None if lb is None else list(zip(lb["lags"], lb["statistic"], lb["pvalue"])),
            "max_z": (date_label(start, freq, len(y) - len(r) + big), float(z[big]))}


def build_univariate(names, data, chars, freq, start, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    return [build_one(data[:, j], chars[j], freq, start, out_dir)
            for j in range(len(names))]


# ── route V: the vector first ──────────────────────────────────────────────

V_PROVENANCE = "* Route V (the vector first, Tiao and Box): a specification of sima's raw entry"


def v_path(out_dir, name, p=None, q=None):
    tail = "" if p is None else f"_p{int(p)}q{int(q)}"
    return os.path.join(out_dir, f"{name}_v{tail}.inp")


def write_v(out_dir, names, data, chars, freq, start, p=0, q=0, base=False):
    """Route V's specifications: each series' transformation, its harmonics,
    its mean when d = D = 0 and, unless `base`, a free regular AR(p)/MA(q) —
    with cross orders p, q the ladder is the full VARMA(p, q). Returns paths."""
    os.makedirs(out_dir, exist_ok=True)
    out = []
    for j, nm in enumerate(names):
        c = chars[j]
        path = v_path(out_dir, nm, None if base else p, None if base else q)
        write_inp(path, nm, data[:, j], freq, start, c["lam"], c["d"], c.get("D", 0),
                  harmonics=c.get("harmonics", False),
                  mean=(c["d"] == 0 and c.get("D", 0) == 0),
                  p=0 if base else int(p), q=0 if base else int(q), comment=V_PROVENANCE)
        out.append(path)
    return out
