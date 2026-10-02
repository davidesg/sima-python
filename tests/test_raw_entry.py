"""The raw-data entry (docs/STUDY-raw-entry.md): load_data and characterize."""
import os

import numpy as np
import pytest

from sima import mcp_server as M
from sima import raw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLOUR = os.path.join(ROOT, "examples", "flour_prices", "data", "flour_prices.csv")
MM = os.path.join(ROOT, "examples", "jenkins_alavi", "data", "mink_muskrat.csv")


def _fn(tool):
    return getattr(tool, "fn", tool)


# ── the table ────────────────────────────────────────────────────────────────

def test_dates_and_frequency_are_read():
    names, data, dates = raw.read_table(FLOUR)
    assert names == ["Buffalo", "Minneapolis", "KansasCity"] and data.shape == (100, 3)
    assert raw.infer_start(dates, 12) == (1972, 8)
    t = _fn(M.load_data)("r_fl", FLOUR)
    assert "monthly, 1972.08 - 1980.11" in t
    t = _fn(M.load_data)("r_mm", MM)
    assert "annual, 1850 - 1911" in t


def test_a_numeric_csv_without_header_keeps_its_first_row(tmp_path):
    """The old sima's BUG: the first row was dropped as a header."""
    p = tmp_path / "x.csv"
    rng = np.random.default_rng(1)
    x = 10 + rng.random((40, 2))
    np.savetxt(p, x, delimiter=",")
    names, data, dates = raw.read_table(str(p))
    assert dates is None and data.shape == (40, 2) and data[0, 0] == pytest.approx(x[0, 0])
    assert "Say the frequency" in _fn(M.load_data)("r_x", str(p))
    assert "Say the first date" in _fn(M.load_data)("r_x", str(p), freq=4)
    assert "quarterly" in _fn(M.load_data)("r_x", str(p), freq=4, start="2000Q1")


def test_missing_values_are_refused_with_where(tmp_path):
    p = tmp_path / "m.csv"
    rows = ["date,A,B"] + [f"{2000 + i},{1 + i},{2 + i}" for i in range(40)]
    rows[5] = "2004,,6"
    p.write_text("\n".join(rows))
    t = _fn(M.load_data)("r_m", str(p))
    assert "Cannot load" in t and "A row 5" in t


# ── the characterization ─────────────────────────────────────────────────────

def test_flour_characterization():
    _fn(M.load_data)("r_fl2", FLOUR)
    t = _fn(M.characterize)("r_fl2")
    for h in ("## 1 · TABLE", "## 2 · WHAT IT SHOWS", "## 3 · CONCLUSIONS",
              "## 4 · DECISION", "⏸"):
        assert h in t
    ch = M._sess.get_raw("r_fl2").chars
    assert [(c["lam"], c["d"], c["harmonics"]) for c in ch] == [(0.0, 1, False)] * 3
    assert "3 series are differenced" in t and 'canonical_analysis(name="r_fl2")' in t


def test_each_series_keeps_its_own_and_the_analyst_can_change_it():
    """Mink and muskrat: different d (0 and 1), no consensus. The engine
    proposes levels for the mink (opposite signs: the domain decides); the
    analyst sets logs, as Jenkins and Alavi."""
    _fn(M.load_data)("r_mm2", MM)
    t = _fn(M.characterize)("r_mm2")
    ch = {c["name"]: c for c in M._sess.get_raw("r_mm2").chars}
    assert ch["mink"]["d"] == 0 and ch["muskrat"]["d"] == 1 and ch["muskrat"]["lam"] == 0.0
    assert "they differ here" in t
    t = _fn(M.characterize)("r_mm2", set="mink: lam=0")
    assert ch["mink"]["lam"] == 0.0
    assert "Changed by the analyst: mink: lam = 0" in t
    assert "the series are mink, muskrat" in _fn(M.characterize)("r_mm2", set="otter: d=1")
    assert "lambda is 0" in _fn(M.characterize)("r_mm2", set="mink: lam=0.5")
    g = M._sess.get_raw("r_mm2").guion.entries
    assert [e.node for e in g] == ["N0r", "N0c", "N0c"]


def test_canonical_analysis_on_raw_levels_is_the_ladders():
    """The same lambdas as from the .pre files (test_tiao_box), before any
    model; the menu speaks of characterize, not of the .pre."""
    _fn(M.load_data)("r_fl3", FLOUR)
    assert "Characterize the series first" in _fn(M.canonical_analysis)("r_fl3")
    _fn(M.characterize)("r_fl3")
    c = _fn(M.canonical_analysis)("r_fl3")
    assert "1  0.758    0.870" in c and "3  0.943    0.971" in c
    assert 'characterize(name="r_fl3", set="SERIES: d=0")' in c
    assert "it is the analyst's, in characterize" in c
