"""BUG-0018: the canonical analysis reads the levels WITHOUT each model's
deterministic terms -- the seasonality always, the interventions by default
(interventions="keep" leaves them), never mu nor a trend -- and shows the
other reading for comparison. The case: the US monetary VAR (bugs/BUG-0018-repro).
"""
import glob
import json
import os
import warnings

import numpy as np
import pytest

import sima.mcp_server as M
from sima import levels as LV
from sima import session as S

_fn = lambda f: getattr(f, "fn", f)                      # noqa: E731
REPRO = os.path.join(os.path.dirname(__file__), "..", "bugs", "BUG-0018-repro")
FILES = [os.path.join(REPRO, f) for f in
         ("IPI_m07.pre", "IPC_m07.pre", "WTI_m03.pre", "FF_m03.pre")]


@pytest.fixture(scope="module")
def mon():
    warnings.simplefilter("ignore")
    _fn(M.load_pre)("b18", json.dumps(FILES))
    _fn(M.run_gate)("b18")
    return "b18"


def test_the_order_handed_to_prepare_vec_is_the_clean_one(mon):
    t = _fn(M.canonical_analysis)(mon)
    c = S.get(mon).canonical
    assert c.get("p_run", c["p"]) == 4 and c["interventions"] == "remove"
    assert "THE LEVELS READ (BUG-0018)" in t
    assert "IPC: 11 seasonal term(s), 2 intervention(s) (impulse, step)" in t
    # the other reading, before the decision (not after the pause)
    i = t.index("With the interventions INSIDE (for comparison)")
    assert i < t.index("## 4 · DECISION") and "order by M(l) 8 (here 4)" in t


def test_keep_leaves_the_interventions_and_compares_with_removing(mon):
    t = _fn(M.canonical_analysis)(mon, interventions="keep")
    c = S.get(mon).canonical
    assert c.get("p_run", c["p"]) == 8 and c["interventions"] == "keep"
    assert "its interventions KEPT" in t and "With the interventions REMOVED" in t
    assert "must be" in _fn(M.canonical_analysis)(mon, interventions="maybe")


def test_mu_is_never_removed(mon):
    ipc = S.get(mon).series[1]
    clean = LV.clean_levels(ipc)
    drift = float(np.mean(np.diff(clean)))
    assert ipc.model.estimate_mu and abs(drift - 0.2238) < 0.02   # IPC's mu, 0.223794


def test_a_model_without_deterministic_terms_reads_as_before(mon):
    ff = S.get(mon).series[3]
    assert not ff.model.interventions
    assert np.array_equal(LV.clean_levels(ff), np.asarray(ff.levels(), float))
    assert LV.describe(ff) == ""


def test_the_repro_says_fixed():
    import subprocess
    import sys
    r = subprocess.run([sys.executable, os.path.join(REPRO, "repro.py")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
