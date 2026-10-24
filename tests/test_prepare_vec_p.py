"""prepare_vec's default p from M(l): the contiguous order, not a lag
significant alone after a silence (TODO, shakedown of 0.2.0, Martín Manjón and
Treadway 1985-1995: (R0T, R0) gave p = 15 with nothing significant from 5 to
14). Tiao and Box's single gap stays: the gas furnace keeps its AR(6)."""
import json
import os
import shutil

import numpy as np
import pandas as pd

from conftest import DATA

from drvarma.identification_mv import stepwise_ar, stepwise_order
from sima import mcp_server as M
from sima.evidence import contiguous_order

EX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")
FLOUR = [os.path.join(EX, "flour_prices", "art", f"{c}_m01.pre")
         for c in ("BUFFALO", "MINNEAPOLIS", "KANSASCITY")]

# the M(l) p-values of the shakedown, levels 1985-01 to 1995-12, L = 22
R0T_R0 = [0.0, 0.0, 0.373, 0.015, 0.113, 0.086, 0.474, 0.301, 0.148, 0.052, 0.706,
          0.12, 0.313, 0.907, 0.034, 0.119, 0.915, 0.551, 0.446, 0.513, 0.606, 0.771]
R0T_R30 = [0.0, 0.0, 0.026, 0.004, 0.871, 0.615, 0.041, 0.052, 0.489, 0.345, 0.193,
           0.837, 0.374, 0.67, 0.326, 0.49, 0.612, 0.66, 0.059, 0.847, 0.576, 0.624]


def _fn(f):
    return getattr(f, "fn", f)


def test_an_isolated_lag_is_not_the_order():
    sw = {"pvalue": np.array(R0T_R0)}
    assert stepwise_order(sw)[0] == 15            # Tiao and Box's reading
    assert contiguous_order(sw) == (4, [15])      # one gap (3) kept, 5-6 stop it
    sw = {"pvalue": np.array(R0T_R30)}
    assert stepwise_order(sw)[0] == 7
    assert contiguous_order(sw) == (4, [7])


def test_the_gas_furnace_keeps_its_single_gap():
    x = pd.read_csv(os.path.join(DATA, "gas_furnace.csv")).values.astype(float)
    sw = stepwise_ar(x, 12)
    assert stepwise_order(sw) == (6, [5])
    assert contiguous_order(sw) == (6, [])


def test_nothing_significant_is_order_zero():
    assert contiguous_order({"pvalue": np.array([0.3, 0.6, 0.01])}) == (0, [3])


def test_prepare_vec_takes_the_contiguous_order(tmp_path):
    files = []
    for f in FLOUR:
        shutil.copy(f, tmp_path)
        files.append(str(tmp_path / os.path.basename(f)))
    _fn(M.load_pre)("pvp", json.dumps(files))
    _fn(M.run_gate)("pvp")
    s = M._sess.get("pvp")
    s.canonical = {"p": 15, "p_tb": 15, "p_run": 4, "isolated": [15]}
    t = _fn(M.prepare_vec)("pvp", purpose="long run")
    assert s.vec_spec["p"] == 4
    assert "the last significant M(l) is 15" in t and "p=15" in t
    # a session whose facts predate p_run keeps Tiao and Box's reading
    s.canonical = {"p": 2, "p_tb": 2}
    _fn(M.prepare_vec)("pvp", purpose="long run")
    assert s.vec_spec["p"] == 2
    # the analyst's p is the analyst's
    s.canonical = {"p": 15, "p_tb": 15, "p_run": 4, "isolated": [15]}
    _fn(M.prepare_vec)("pvp", purpose="long run", p=15)
    assert s.vec_spec["p"] == 15
