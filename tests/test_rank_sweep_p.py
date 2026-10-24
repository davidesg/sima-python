"""C1 at small n: the rank's verdict is conditional on p, and rank_test offers
the sweep over p, which runs before any VEC (TODO, shakedown of 0.2.0, Martín
Manjón and Treadway on 2016-2020 and 2022-2026, n about 50)."""
import json
import os
import shutil

import pytest

from sima import vec
from sima import mcp_server as M

EX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")
FLOUR = [os.path.join(EX, "flour_prices", "art", f"{c}_m01.pre")
         for c in ("BUFFALO", "MINNEAPOLIS", "KANSASCITY")]


def _fn(f):
    return getattr(f, "fn", f)


def _res(nobs, p, lr0=25.09, cv0=21.3, pv0=0.026):
    """A finished rank test shaped like the job's result: (R0T, R30, R3),
    2022-2026, p = 2 (the shakedown's first row)."""
    comp = lambda h, lr, cv, pv: {"h0": h, "lr": lr, "B": 499, "ok": 499, "simfail": 0,
                                  "fitfail": 0, "cv": [cv - 3, cv, cv + 6], "pvalue": pv,
                                  "asym_cv": None, "asym_verdict": ""}
    return {"tool": "rank_test", "names": ["R0T", "R30", "R3"], "M": 3, "nobs": nobs,
            "p": p, "q": 0, "case": "pre", "nodrift": [], "B": 499, "multistart": 0,
            "ranks": [{"r": r, "logL": -100.0 + r, "npar": 20 + r} for r in range(3)],
            "comparisons": [comp(0, lr0, cv0, pv0), comp(1, 4.1, 12.0, 0.6)]}


def test_small_n_makes_the_verdict_conditional_on_p():
    t, r_hat = vec.rank_report(_res(50, 2), "x")
    assert r_hat == 1
    assert "SMALL SAMPLE FOR THIS ORDER: n / (M p) = 8.3" in t
    # the sweep comes first among the alternatives, at the neighbouring orders
    assert '**A)** the rank at p = 1, 2, 3' in t
    assert 'sweep(name="x", p="1,2,3", B=499)' in t


def test_a_long_sample_is_not_warned():
    t, _r = vec.rank_report(_res(285, 4), "x")                     # 1985-2008: 23.8
    assert "SMALL SAMPLE" not in t and "sweep(" not in t
    t, _r = vec.rank_report(_res(130, 4), "x")                     # 1985-1995: 10.8
    assert 'sweep(name="x", p="3,4,5", B=499)' in t


def test_the_rank_cell_reads_each_comparison():
    assert vec.rank_cell_text(_res(50, 2)) == (
        "r-hat 1 (B = 499); r=0: LR 25.09, 95% 21.30, p 0.026; "
        "r=1: LR 4.10, 95% 12.00, p 0.600")


@pytest.fixture(scope="module")
def flour(tmp_path_factory):
    d = tmp_path_factory.mktemp("flour_sweep")
    old = os.environ.get("SIMA_JOBS_HOME")
    os.environ["SIMA_JOBS_HOME"] = str(d / "home")
    files = []
    for f in FLOUR:
        shutil.copy(f, d)
        files.append(str(d / os.path.basename(f)))
    _fn(M.load_pre)("rsw", json.dumps(files))
    _fn(M.run_gate)("rsw")
    _fn(M.prepare_vec)("rsw", purpose="long run", p=1)
    yield "rsw"
    if old is None:
        os.environ.pop("SIMA_JOBS_HOME", None)
    else:
        os.environ["SIMA_JOBS_HOME"] = old


def test_the_sweep_reads_the_rank_before_any_vec(flour):
    t = _fn(M.sweep)(flour, p="1,2")
    assert "the sweep reads the RANK only: give B" in t
    t = _fn(M.sweep)(flour, p="1,2", B=19, wait=900)
    assert "Sweep of the rank over the order (C1), before any VEC" in t, t
    assert "p=1 case pre RANK" in t and "p=2 case pre RANK" in t
    assert t.count("r-hat") == 2 and "r=0: LR" in t
    e = M._sess.get(flour).guion.entries[-1]
    assert e.node == "C1" and e.tool == "sweep"
