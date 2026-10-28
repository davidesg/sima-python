"""BUG-0006: a comparison whose model under H0 is not I(1, r) (drvec draws no
sample from it, Cavaliere, Rahbek and Taylor 2012) is said as such, not as a
failed bootstrap."""
import types

import pytest

from sima import vec

pytest.importorskip("drvec")


def _res(i1r):
    comps = [{"h0": 0, "lr": 58.65, "B": 499, "ok": 499, "simfail": 0, "fitfail": 0,
              "cv": [19.8, 22.6, 30.1], "pvalue": 0.002, "asym_cv": [20.0, 22.0, 26.0],
              "asym_verdict": "reject H0 at 1%", "i1r": None},
             {"h0": 1, "lr": 6.02, "B": 0, "ok": 0, "simfail": 0, "fitfail": 0,
              "cv": None, "pvalue": None, "asym_cv": [13.0, 15.7, 20.0],
              "asym_verdict": "H0 not rejected", "i1r": i1r}]
    return {"tool": "rank_test", "names": ["invest", "income", "cons"], "M": 3, "nobs": 91,
            "p": 2, "q": 0, "case": "2", "nodrift": [], "B": 499, "multistart": 0,
            "ranks": [{"r": r, "logL": 700.0 + r, "npar": 14 + 4 * r, "ma_boundary": False}
                      for r in range(3)],
            "comparisons": comps}


@pytest.mark.parametrize("i1r, says", [((0.9999, 1.0), "on or inside the unit circle"),
                                       ((1.4, 3.0e-9), "long-run covariance is singular")])
def test_the_report_says_not_i1r(i1r, says):
    text, r_hat = vec.rank_report(_res(list(i1r)), "e1")
    assert r_hat is None
    assert "the model under H0 is not I(1, 1): not simulated" in text
    assert says in text and "a larger B does not change it" in text
    assert "fewer than 10 replications" not in text
    assert "nan" not in text.split("```")[1].split("r=1")[1].splitlines()[0]
    assert 'estimate_vec(name="e1", r=1, theory="...")' in text
    assert "rerun with a larger B" not in text


def test_without_i1r_the_old_reading_stays():
    text, r_hat = vec.rank_report(_res(None), "e1")
    assert r_hat is None and "fewer than 10 replications ok" in text


def test_the_job_keeps_drvecs_field(monkeypatch, tmp_path):
    import drvec
    b0 = types.SimpleNamespace(h0=0, lr=58.65, reps=[], nok=0, cv=None, pvalue=None, i1r=None)
    b1 = types.SimpleNamespace(h0=1, lr=6.02, reps=[], nok=0, cv=None, pvalue=None,
                               i1r=(1.2345, 3.0e-9))
    rt = types.SimpleNamespace(bootstraps=[b0, b1], names=["a", "b", "c"], nobs=91,
                               ll=[1.0, 2.0, 3.0], npar=[1, 2, 3], boundary=[0, 0, 0],
                               drift_how="", provenance=None,
                               critical_values=lambda h: None, verdict=lambda h: "",
                               out_text=lambda base: "", boot_text=lambda v: "")
    monkeypatch.setattr(drvec, "rank_test", lambda *a, **k: rt)
    import sima.provenance
    monkeypatch.setattr(sima.provenance, "of_drvec", lambda p: {})
    job = {"args": {"p": 2, "q": 0, "case": "2", "nodrift": [], "B": 19, "multistart": 0,
                    "names": ["a", "b", "c"]},
           "files": ["a.pre", "b.pre", "c.pre"], "engine": ["python"], "workers": 1,
           "seed": 1}
    res = vec.job_rank_test(job, str(tmp_path))
    assert [c["i1r"] for c in res["comparisons"]] == [None, [1.2345, 3.0e-9]]
