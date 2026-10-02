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
