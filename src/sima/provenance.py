"""Who computed a result (PLAN-vec C1; STUDY-vec §3.13).

Every result sima reports carries its provenance: the engines' versions, the
numerical backend, the platform tier and, for a job, its engine, seed, cache
key and run folder. The guion stores it per entry, for every engine, not only
drvec: a number without the program that produced it cannot be reproduced.

The platform tier is the suite's convention: "exact" on Linux x86_64, where
drvec-python is byte-identical with drvec C (the oracle), "tolerance"
elsewhere, where the numbers agree to the declared tolerance and every
decision must still be the oracle's.
"""
from __future__ import annotations

import platform as _pf
import sys

_BASE = None


def _version(dist):
    try:
        from importlib.metadata import PackageNotFoundError, version
        try:
            return version(dist)
        except PackageNotFoundError:
            return None
    except Exception:                                        # noqa: BLE001
        return None


def platform_string():
    return f"{sys.platform} {_pf.machine()}"


# The glibc versions whose libm was measured to reproduce the examples' bytes
# (clean-install test of atsw 2.1.0, 2026-10-30): 2.35 to 2.41 agree; 2.28,
# 2.34 and musl differ. Outside this range the tier is "tolerance" until the
# same test in containers measures it (BUG-0009).
EXACT_GLIBC = ((2, 35), (2, 41))


def _glibc():
    """(major, minor) of the glibc, or None (musl, which libc_ver gives as
    ('', ''), or anything else)."""
    try:
        lib, ver = _pf.libc_ver()
        if lib != "glibc":
            return None
        return tuple(int(x) for x in ver.split(".")[:2])
    except Exception:                                        # noqa: BLE001
        return None


def platform_tier():
    """"exact" where an example's cache reproduces byte for byte: Linux
    x86_64 with a glibc in the measured range; "tolerance" elsewhere."""
    if sys.platform != "linux" or _pf.machine() not in ("x86_64", "AMD64"):
        return "tolerance"
    g = _glibc()
    lo, hi = EXACT_GLIBC
    return "exact" if g is not None and lo <= g <= hi else "tolerance"


def drvarma_backend():
    """drvarma's likelihood engine: "c" (compiled) or the Python fallback."""
    try:
        from drvarma._engine import engine_backend
        return engine_backend()
    except Exception:                                        # noqa: BLE001
        return "unknown"


def python_string():
    """The interpreter, with what decides whether a binary wheel exists for it
    (BUG-0020): version, implementation, bitness, free-threaded."""
    bits = "64-bit" if sys.maxsize > 2**32 else "32-bit"
    ft = ""
    try:
        if not sys._is_gil_enabled():                     # 3.13+ free-threaded
            ft = ", free-threaded"
    except AttributeError:
        pass
    return f"{_pf.python_implementation()} {sys.version.split()[0]} ({bits}{ft})"


def _load_error(module):
    try:
        import importlib
        return importlib.import_module(module).engine_load_error()
    except Exception:                                        # noqa: BLE001
        return None


def _backend(module):
    try:
        import importlib
        return importlib.import_module(module).engine_backend()
    except Exception:                                        # noqa: BLE001
        return "unknown"


def engine_notice():
    """A block for the tools' output when drvarma or fue computes on its
    pure-Python port, or "" (BUG-0020). Their own warning is a RuntimeWarning
    on stderr, which an MCP client shows to nobody; in the P08 five groups
    waited hours on the port without knowing it, and two left sima."""
    import os
    ports = [(eng, _load_error(f"{eng}._engine"))
             for eng in ("drvarma", "fue") if _backend(f"{eng}._engine") == "python"]
    if not ports:
        return ""
    asked = [e for e, _ in ports if os.environ.get(f"{e.upper()}_NO_ENGINE")]
    names = " and ".join(e for e, _ in ports)
    why = "; ".join(f"{e}: {err or 'the compiled engine is not installed'}" for e, err in ports)
    out = (f"! ENGINE: {names} compute{'s' if len(ports) == 1 else ''} on the "
           f"pure-Python port, not on the compiled engine ({python_string()}; {why}).")
    if len(asked) == len(ports):
        return out + " Asked for with the *_NO_ENGINE variable."
    return out + (
        " Same numbers, but 20-250 times slower: a VAR(1) of four series can take more "
        "than an hour and structure longer. Tell the analyst NOW, before any long "
        "fit. The usual cause is a Python without binary wheels (a new CPython, a "
        "free-threaded or a 32-bit build): reinstall the suite on a supported one, "
        "e.g. `uv tool install --python 3.13 --reinstall atsw`.")


def eigensolver():
    try:
        from drvec._gsl import backend
        return backend()
    except Exception:                                        # noqa: BLE001
        return "unknown"


def base():
    """The provenance every entry shares: versions, backend, platform."""
    global _BASE
    if _BASE is None:
        _BASE = {"sima": _version("sima-tseries"), "drvarma": _version("drvarma"),
                 "fue": _version("fue"), "drvec": _version("drvec"),
                 "backend": f"drvarma engine {drvarma_backend()}, eigensolver {eigensolver()}",
                 "platform": platform_string(), "tier": platform_tier(),
                 "python": python_string()}
        for eng in ("drvarma", "fue"):           # why an engine did not load (BUG-0020)
            err = _load_error(f"{eng}._engine")
            if err:
                _BASE[f"{eng}_load_error"] = err
    return dict(_BASE)


def of_drvec(prov):
    """A drvec Provenance as a plain dict, without what changes run to run
    (the wall time, the temporary folder, the argv's absolute paths): it goes
    into result files that must reproduce byte for byte."""
    if prov is None:
        return None
    extra = dict(getattr(prov, "extra", {}) or {})
    for k in ("elapsed", "folder", "argv"):
        extra.pop(k, None)
    return {"engine": prov.engine, "version": prov.version, "backend": prov.backend,
            "platform": prov.platform, "tier": prov.tier, "workers": prov.workers,
            "seed": prov.seed, "note": prov.note, "extra": extra}


def line(p):
    """One line for a report: what computed it."""
    if not p:
        return ""
    bits = [f"{k} {p[k]}" for k in ("sima", "drvarma", "fue", "drvec") if p.get(k)]
    out = "PROVENANCE: " + ", ".join(bits) + f"; {p.get('backend', '')}; " \
          f"{p.get('platform', '')} (tier {p.get('tier', '')})"
    if p.get("python"):
        out += f"; Python {p['python']}"
    if p.get("engine"):
        out += f"; bootstrap engine {p['engine']}"
    if "seed" in p:
        seed = p["seed"] if p["seed"] is not None else "987654321 (the C's default)"
        out += f"; seed {seed}"
    if p.get("key"):
        out += f"; cache key {p['key'][:16]}"
    if p.get("folder"):
        out += f"; run folder {p['folder']}"
    return out
