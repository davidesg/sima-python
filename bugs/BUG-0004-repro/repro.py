"""BUG-0004: on route V, evaluate (N5) measures the candidate against univariate
models built silently by route U's light builder, and the analyst cannot give
it their own. In the lutkepohl_poskitt example the builder picks, inside art's
tie, an MA(1) for Minneapolis and Kansas City; the analyst's art models are
AR(1). Against the light yardstick Lutkepohl and Poskitt's restricted VAR(1)
gains at h = 1 in Minneapolis (ratio 0.941, RMSE 7.035 vs 7.478); against the
art AR(1) (route U, same window) the univariate RMSE is 7.046: no gain. The
report does not say which models the yardstick is, and there is no way to pass
others.

    PYTHONPATH=src python3 bugs/BUG-0004-repro/repro.py   # exits 1 while open
"""
import inspect, os, re, shutil, sys, tempfile
from sima import mcp_server as M
fn = lambda t: getattr(t, "fn", t)
HERE = os.path.dirname(os.path.abspath(__file__))
tmp = tempfile.mkdtemp()
csv = shutil.copy(os.path.join(HERE, "flour_prices.csv"), tmp)
N = "bug4"
fn(M.load_data)(N, csv)
fn(M.characterize)(N, set="Buffalo: lam=0, d=1; Minneapolis: lam=0, d=1; "
                          "KansasCity: lam=0, d=1")
fn(M.write_specs)(N)
fn(M.run_gate)(N)
Z = ("phi_KansasCity[B^1], AR1[Buffalo<-KansasCity], "
     "AR1[Minneapolis<-KansasCity], AR1[KansasCity<-Buffalo]")
fn(M.estimate)(N, 1, 0, zeros=Z)
out = fn(M.evaluate)(N, 1, 0, estwin=72, horizon=6, zeros=Z)
print(next(l for l in out.splitlines() if re.match(r"\s*Minneapolis\s+1\s", l)))
can_pass = any(k in inspect.signature(fn(M.evaluate)).parameters
               for k in ("yardstick", "univariates"))
names_models = bool(re.search(r"Minneapolis[^\n]*(MA|AR)\s*\(?1", out))
print("evaluate takes the analyst's univariates:", can_pass)
print("the report names the yardstick's models:", names_models)
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(0 if (can_pass and names_models) else 1)
