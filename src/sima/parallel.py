"""Independent exact-ML fits in parallel (observation i of the trial run,
25-nov-2026): `structure` on four series and a VAR(1) refits the model some
twenty times, one after another, ~12 minutes on one core of four.

The fits are independent, so each goes to a PROCESS of its own: the engine is
C behind cffi, and nothing says its state is safe to share between threads. A
worker is a fresh interpreter (`python -m sima.parallel`), the same on every
platform, that takes its share of the fits (round robin) and runs them one
after another; the Ladder of a fit is built here, from plain arguments, so that it
imports drvarma and this module and nothing of the MCP server; and it comes
back whole (a fitted Ladder pickles), so the session caches it as if fitted at
home.

A worker's standard output is closed: the stdio MCP server talks to its
client on that pipe, and a word from the engine there would break it.

``SIMA_WORKERS`` sets the number of processes (default: cores - 1).
"""
from __future__ import annotations

import os


def build_ladder(files, p, q, diagcov, estwin=None, links=None, start=None,
                 cross="additive", zeros=None, lik="elf", echelon=None, own="spec",
                 own_zeros=None, route="u"):
    """start None: the Ladder's default (ols with q = 0, else zero). own
    "free": the echelon rows' own part replaces each univariate model's
    regular ARMA (route U); `own_zeros` holds some of its lags at zero
    (BUG-0003). route "v": the engine's route V (own_zeros are then the free
    AR(p)/MA(q)'s lags held at zero)."""
    from drvarma.ladder import Ladder
    if echelon:
        p = q = 0                       # the indices give the orders
    if route == "v":
        return Ladder(list(files), p, q, diagcov=diagcov, estwin=estwin,
                      links=links or None, start=start, cross=cross,
                      zeros=list(zeros) if zeros else None, lik=lik,
                      echelon=tuple(echelon) if echelon else None,
                      own_zeros=own_zeros or None, route="v")
    return Ladder(list(files), p, q, diagcov=diagcov, estwin=estwin,
                  links=links or None, start=start, cross=cross,
                  zeros=list(zeros) if zeros else None, lik=lik,
                  echelon=tuple(echelon) if echelon else None,
                  own=own if echelon else "spec",
                  own_zeros=own_zeros if (echelon and own == "free") else None)


def workers(n):
    """How many processes for `n` fits: SIMA_WORKERS, or cores - 1."""
    try:
        w = int(os.environ.get("SIMA_WORKERS", "") or 0)
    except ValueError:
        w = 0
    if w <= 0:
        w = max(1, (os.cpu_count() or 2) - 1)
    return max(1, min(w, n))


def _fit(spec):
    args, kw = spec
    L = build_ladder(*args, **kw)
    L.fit()
    return L


def job_structure_fits(job, folder):
    """The job behind `structure` (BUG-0021): its restricted fits, in
    parallel, in a detached process that outlives the MCP server and its
    client. The fitted Ladders go to fits.pkl; result.json holds the logL of
    each, for the record. A fit that fails fails the job (not cached)."""
    import pickle
    from . import jobs
    with open(job["extra_files"][0], "rb") as fh:       # written by structure
        specs = pickle.load(fh)
    tk = jobs.Ticks(folder, len(specs), "restricted fits")
    w = workers(len(specs))
    out = []
    for k in range(0, len(specs), w):            # a wave per round: the progress
        out += fit_many(specs[k:k + w], w)
        for _ in specs[k:k + w]:
            tk()
    bad = [L for L in out if isinstance(L, Exception)]
    if bad:                      # a failed job is not cached: the same call runs again
        raise RuntimeError(f"a restricted fit failed: {bad[0]}")
    fits = out
    tmp = os.path.join(folder, "fits.pkl.part")
    with open(tmp, "wb") as fh:
        pickle.dump(fits, fh)
    os.replace(tmp, os.path.join(folder, "fits.pkl"))
    return {"tool": "structure_fits", "n": len(specs), "workers": w,
            "logL": [float(L.result.logL) for L in fits], "files": ["fits.pkl"]}


def _run_one(specs, tmp):
    """Some fits in a fresh interpreter (`python -m sima.parallel IN OUT`), one
    after another (the interpreter's start, ~1 s, is paid once): no
    main module to import again, as multiprocessing's spawn does (a script
    without its `if __name__ == "__main__"` guard ran itself in every
    worker), and nothing on the parent's stdout."""
    import pickle
    import subprocess
    import sys
    import uuid
    base = os.path.join(tmp, uuid.uuid4().hex)
    fin, fout = base + ".in", base + ".out"
    with open(fin, "wb") as fh:
        pickle.dump(list(specs), fh)
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(p for p in sys.path if p)
    # one thread per worker: the BLAS of each would take every core
    for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        env.setdefault(v, "1")
    r = subprocess.run([sys.executable, "-m", "sima.parallel", fin, fout],
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                       stderr=subprocess.PIPE, env=env)
    if r.returncode != 0 or not os.path.exists(fout):
        tail = r.stderr.decode(errors="replace").strip().splitlines()[-1:] or ["no message"]
        return [RuntimeError(f"the worker failed: {tail[0]}")] * len(specs)
    with open(fout, "rb") as fh:
        return pickle.load(fh)


def fit_many(specs, n_workers=None):
    """Fit each `(args, kwargs)` of build_ladder; the fitted Ladders in the
    same order, an exception in the place of a fit that failed. One fit, or
    one worker: here, in this process."""
    specs = list(specs)
    w = n_workers or workers(len(specs))
    if len(specs) <= 1 or w <= 1:
        out = []
        for sp in specs:
            try:
                out.append(_fit(sp))
            except Exception as e:                           # noqa: BLE001
                out.append(e)
        return out
    import tempfile
    from concurrent.futures import ThreadPoolExecutor
    chunks = [list(range(k, len(specs), w)) for k in range(w)]      # round robin
    out = [None] * len(specs)
    with tempfile.TemporaryDirectory(prefix="sima_fits_") as tmp, \
            ThreadPoolExecutor(max_workers=w) as ex:
        res = ex.map(lambda ix: _run_one([specs[i] for i in ix], tmp), chunks)
        for ix, rs in zip(chunks, res):
            for i, r in zip(ix, rs):
                out[i] = r
    return out


def _main(argv):
    import pickle
    import warnings
    warnings.simplefilter("ignore")
    fin, fout = argv
    with open(fin, "rb") as fh:
        specs = pickle.load(fh)
    res = []
    for spec in specs:
        try:
            res.append(_fit(spec))
        except Exception as e:                               # noqa: BLE001
            res.append(RuntimeError(f"{type(e).__name__}: {e}"))
    tmp = fout + ".part"
    with open(tmp, "wb") as fh:
        pickle.dump(res, fh)
    os.replace(tmp, fout)


if __name__ == "__main__":
    import sys
    _main(sys.argv[1:])
