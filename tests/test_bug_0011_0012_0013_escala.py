"""BUG-0011, 0012 and 0013: the scale of the files in a system. Each repro is
a self-contained case on synthetic series and returns 0 when the defect is
gone."""
import importlib.util
import json
import pathlib
import sys

import numpy as np
import pytest

BUGS = pathlib.Path(__file__).resolve().parents[1] / "bugs"


@pytest.mark.parametrize("n", ["0011", "0012", "0013"])
def test_the_repro_exits_zero(n):
    d = BUGS / f"BUG-{n}-repro"
    sys.path.insert(0, str(d))
    try:
        spec = importlib.util.spec_from_file_location(f"repro_{n}", d / "repro.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert mod.main() == 0
    finally:
        sys.path.remove(str(d))
        sys.modules.pop("_datos", None)


def _files(tmp_path, fy, fx):
    sys.path.insert(0, str(BUGS / "BUG-0012-repro"))
    try:
        from _datos import coint, pre
        y, x = coint()
        return [pre(str(tmp_path / f"Y{fy:g}.pre"), 100 * np.exp(y), 0.0, fy, 1, "Y"),
                pre(str(tmp_path / f"X{fx:g}.pre"), 100 * np.exp(x), 0.0, fx, 1, "X")]
    finally:
        sys.path.remove(str(BUGS / "BUG-0012-repro"))
        sys.modules.pop("_datos", None)


def test_load_pre_says_nothing_at_the_norm_and_speaks_otherwise(tmp_path):
    import sima.mcp_server as S
    assert "SCALE" not in S.load_pre("a", json.dumps(_files(tmp_path, 100.0, 100.0)))
    mixto = S.load_pre("b", json.dumps(_files(tmp_path, 100.0, 1.0)))
    assert "UNITS" in mixto and "do not share one rescaling factor" in mixto
    assert "SCALE — X" in mixto            # logs at factor 1: 0.01, under the band


def test_the_restriction_is_taken_in_the_series_units():
    from sima import scale
    from sima.vec import restriction_kw
    u = {"Y": (0.0, 100.0), "X": (0.0, 1.0)}
    kw = restriction_kw({"fixb2": -1.0}, ["Y", "X"], 1, u)
    assert "fixb2" not in kw and kw["fixb2row"] == {1: pytest.approx(-0.01)}
    same = {"Y": (0.0, 100.0), "X": (0.0, 100.0)}
    assert restriction_kw({"fixb2": -1.0}, ["Y", "X"], 1, same) == {"fixb2": -1.0}
    assert scale.cross(u, "Y", "X") == pytest.approx(0.01)
    assert scale.what(u, "Y", "X") == "an elasticity"
