"""BUG-0006: rank_test does not say that a comparison's model under H0 is not
I(1, r). drvec (C 0.13, 800a540; Cavaliere, Rahbek and Taylor 2012, Algorithm
1 step ii) checks the fitted H0 model before simulating and, when it is not
I(1, r), draws no sample and says so in Bootstrap.i1r. sima does not read the
field: the comparison comes out as "fewer than 10 replications ok, no critical
value" with a row of NaN, which reads as a failed bootstrap ("rerun with a
larger B") and not as what it is, a finding about the model.

The check is forced here (drvec's own test does the same,
tests/test_rank.py::test_a_model_that_is_not_i1r_is_said_and_not_simulated):
the H0 model at r = 1 of Lütkepohl's E1 is declared not I(1, 1).

    PYTHONPATH=src python3 bugs/BUG-0006-repro/repro.py   # exits 1 while open
"""
import os, sys, tempfile
from drvec import rank
from sima import vec

HERE = os.path.dirname(os.path.abspath(__file__))
real = rank.i1r_check
rank.i1r_check = lambda spec, data, x: ((True, 1.2345, 3.0e-9) if spec.r == 1
                                        else real(spec, data, x))
files = [os.path.join(HERE, f"e1{s}.pre") for s in ("invest", "income", "cons")]
job = {"args": {"p": 2, "q": 0, "case": "2", "nodrift": [], "B": 19, "multistart": 0,
                "names": ["invest", "income", "cons"]},
       "files": files, "engine": ["python"], "workers": 1, "seed": 987654321}
res = vec.job_rank_test(job, tempfile.mkdtemp())
text, r_hat = vec.rank_report(res, "e1")
c1 = next(c for c in res["comparisons"] if c["h0"] == 1)
print(f"comparison r = 1 -> 2: B {c1['B']}, ok {c1['ok']}, cv {c1['cv']}")
says_i1r = "I(1, 1)" in text
blames_b = "fewer than 10 replications" in text
print("the report says the H0 model is not I(1, 1):", says_i1r)
print("the report blames the replications:", blames_b)
print([l for l in text.splitlines() if "r-hat" in l][0][:160])
sys.exit(1 if (blames_b or not says_i1r) else 0)
