"""P5 and P6 — the first question leads to a path, and N2 has one order.

P5: the purpose ("forecast" or "long run") can be given with the first
question, at the load; N0 records it, with the lane and the ORDER of the
series, and N1c (prepare_vec) inherits it instead of asking again. load_pre
says what the order fixes. P6: N2 in one order -- identify_cross (route U) ->
identify_matrices -> identify_echelon when an MA is in sight; the canonical
analysis points to the first of them on its route.
"""
import json
import os
import shutil
import warnings

import pytest

import sima.mcp_server as M
from sima import session as S

from test_vec import FLOUR

_fn = lambda f: getattr(f, "fn", f)                      # noqa: E731


@pytest.fixture(scope="module")
def flour(tmp_path_factory):
    warnings.simplefilter("ignore")
    d = tmp_path_factory.mktemp("flour_fq")
    files = []
    for f in FLOUR:
        shutil.copy(f, d)
        files.append(str(d / os.path.basename(f)))
    return files


def test_n0_records_purpose_lane_and_order_and_says_what_the_order_fixes(flour):
    out = _fn(M.load_pre)("fq_n0", json.dumps(flour), lane="guided", purpose="long-run")
    s = S.get("fq_n0")
    assert s.purpose == "long run"
    n0 = [e for e in s.guion.entries if e.node == "N0"][-1]
    assert n0.args["purpose"] == "long run" and n0.args["lane"] == "guided"
    assert n0.args["order"] == M._names(s)
    assert "THE ORDER of the series" in out and " → ".join(M._names(s)) in out
    assert "Cholesky" in out and "normalisation" in out and "A0" in out
    assert "Purpose: long run (recorded at N0; N1c inherits it)." in out


def test_n1c_inherits_the_purpose_and_does_not_ask_again(flour):
    _fn(M.load_pre)("fq_in", json.dumps(flour), purpose="forecast")
    _fn(M.run_gate)("fq_in")
    t = _fn(M.prepare_vec)("fq_in")                       # no purpose: inherited
    assert "needs the model's PURPOSE" not in t
    n1c = [e for e in S.get("fq_in").guion.entries if e.node == "N1c"][-1]
    assert n1c.args["purpose"] == "forecast"


def test_without_a_purpose_n1c_still_asks(flour):
    _fn(M.load_pre)("fq_no", json.dumps(flour))
    _fn(M.run_gate)("fq_no")
    assert "needs the model's PURPOSE" in _fn(M.prepare_vec)("fq_no")


def test_an_unknown_purpose_is_refused(flour):
    out = _fn(M.load_pre)("fq_bad", json.dumps(flour), purpose="structure")
    assert '"forecast" or "long run"' in out and "fq_bad" not in S._SESSIONS


def test_canonical_points_to_the_first_identification_of_its_route(flour):
    _fn(M.load_pre)("fq_can", json.dumps(flour))
    _fn(M.run_gate)("fq_can")
    t = _fn(M.canonical_analysis)("fq_can")
    assert 'identify_cross(name="fq_can")' in t            # route U opens with the CCFs
    assert 'identify_matrices(name="fq_can")' not in t.split("go on with")[1].split("\n")[1]
