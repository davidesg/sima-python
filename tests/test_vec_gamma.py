"""C3, no feedback in the short run: test_restriction(gamma=...) on drvec's
-gzero (TODO, shakedown of 0.2.0, Martín Manjón and Treadway 1997: the
conditional model R0T | (R30, R3)). In two series the joint restriction
weakex + gamma IS -xsys (add_exogenous(series=...)): the same model."""
import json
import os
import shutil

import pytest

from sima import vec
from sima import mcp_server as M

EX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")
MM = [os.path.join(EX, "jenkins_alavi", "art", f) for f in ("MUSKRAT_m03.pre", "MINK_m02.pre")]

pytest.importorskip("drvec")
import drvec.params as _dp                                      # noqa: E402
if "gzero" not in _dp.Spec.__dataclass_fields__:
    pytest.skip("drvec without -gzero", allow_module_level=True)


def _fn(f):
    return getattr(f, "fn", f)


def test_parse_gamma():
    order = ["R0T", "R30", "R3"]
    assert vec.parse_gamma("R30,R3 <- R0T", order) == (("R30", "R0T"), ("R3", "R0T"))
    assert vec.parse_gamma("R30 <- R0T; R3 <- R0T, R30", order) == (
        ("R30", "R0T"), ("R3", "R0T"), ("R3", "R30"))
    with pytest.raises(ValueError, match="own short run"):
        vec.parse_gamma("R3 <- R3", order)
    with pytest.raises(ValueError, match="no series R10"):
        vec.parse_gamma("R10 <- R0T", order)
    with pytest.raises(ValueError, match="EQUATIONS <- REGRESSORS"):
        vec.parse_gamma("R30 R0T", order)
    assert vec.restriction_kw({"gamma": (("R30", "R0T"), ("R3", "R0T"))}, order, 1) == {
        "gzero": [(2, 1), (3, 1)]}


def test_conditional_roles():
    order = ["R0T", "R30", "R3"]
    gam = (("R30", "R0T"), ("R3", "R0T"))
    A = [[1.0], [0.0], [0.0]]                          # alpha rows of R30 and R3 zero
    assert vec.conditional_roles({"gamma": gam, "alpha": A}, order) == (["R0T"], ["R30", "R3"])
    assert vec.conditional_roles({"gamma": gam}, order) is None          # alpha free
    assert vec.conditional_roles({"gamma": gam[:1], "alpha": A}, order) is None
    assert vec.conditional_roles({"gamma": gam, "weakex": "R30"}, order) is None


@pytest.fixture(scope="module")
def mm(tmp_path_factory):
    d = tmp_path_factory.mktemp("mmgamma")
    old = os.environ.get("SIMA_JOBS_HOME")
    os.environ["SIMA_JOBS_HOME"] = str(d / "home")
    files = []
    for f in MM:
        shutil.copy(f, d)
        files.append(str(d / os.path.basename(f)))
    _fn(M.load_pre)("vg", json.dumps(files))
    _fn(M.run_gate)("vg")
    _fn(M.prepare_vec)("vg", purpose="long run", p=3, case="2", mixed=True)
    t = _fn(M.estimate_vec)("vg", r=1, theory="the test's: a VEC to restrict")
    assert "ADOPTED ON THEORY" in t, t
    yield "vg"
    if old is None:
        os.environ.pop("SIMA_JOBS_HOME", None)
    else:
        os.environ["SIMA_JOBS_HOME"] = old


def test_gamma_alone(mm):
    t = _fn(M.test_restriction)(mm, gamma="MINK <- MUSKRAT")
    assert "no feedback: MINK <- MUSKRAT held at 0 for k = 1..2" in t
    assert "drvec's LR (gzero)" in t and "df 2" in t
    assert "conditional model's joint test" in t


def test_the_joint_restriction_is_xsys_and_offers_mtram(mm):
    j = _fn(M.test_restriction)(mm, weakex="MUSKRAT", gamma="MUSKRAT <- MINK")
    assert "drvec's LR (gzero+alpha)" in j and "df 3" in j
    x = _fn(M.add_exogenous)(mm, series="MUSKRAT")
    s = M._sess.get(mm)
    fits = [vf for vf in s.vec_fits.values() if vf.restriction]
    gz = [vf.fit.loglik for vf in fits if vf.restriction.get("gamma") and vf.restriction.get("weakex")]
    xs = [vf.fit.loglik for vf in fits if vf.restriction.get("xsys")]
    assert gz and xs and abs(gz[0] - xs[0]) < 1e-6
    if "REJECTED" in j:
        assert "does not say which part fails" in j and "it adjusts" not in j
    if "not rejected" in j:
        assert "CONDITIONAL model's" in j and "**C)** the conditional model in mtram" in j
        assert "output MINK, inputs MUSKRAT" in j
    assert "-xsys" in x


def test_gamma_refusals(mm):
    assert "does not combine with fixb2" in _fn(M.test_restriction)(
        mm, gamma="MINK <- MUSKRAT", fixb2row="MUSKRAT=0")
    assert "own short run" in _fn(M.test_restriction)(mm, gamma="MINK <- MINK")


def test_a_conditional_model_that_holds_offers_mtram():
    """The shakedown's numbers (Martín Manjón and Treadway, 1985-2008): R0T |
    (R30, R3), LR 7.83, 8 df, p .45 -> the roles and mtram, with the files."""
    from types import SimpleNamespace as NS
    order = ["R0T", "R30", "R3"]
    base = NS(fit=NS(loglik=-3496.1350553), r=1, p=4, q=0, case="pre", order=order,
              files=[f"/x/{n}_ar3.pre" for n in order])
    rl = NS(kind="gzero+alpha", ll_free=-3496.1350553, ll_restricted=-3500.0503243,
            lr=7.8305379, df=8, pvalue=0.4501965)
    restr = {"gamma": (("R30", "R0T"), ("R3", "R0T")), "alpha": [[1.0], [0.0], [0.0]],
             "_call": 'alpha=..., gamma="R30,R3 <- R0T"'}
    t, f = vec.restriction_report(base, NS(restriction_lr=rl), restr, "mmt", "joint")
    assert f["df"] == 8 and abs(f["p"] - 0.4502) < 1e-3
    assert "R0T | R30, R3" in t and "mtram's ground" in t
    assert "**C)** the conditional model in mtram: output R0T, inputs R30, R3" in t
    assert "R0T_ar3.pre, R30_ar3.pre, R3_ar3.pre" in t
