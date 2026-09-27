"""sima — the assistant for simultaneous VARMA models, on drvarma's ladder.

The third rung of the ATSW ladder (art → mtram → sima). The engine is drvarma
(``drvarma.ladder``): it ships numbers and never argues. This package is the
assistant: the protocol, the evidence and the menu of decisions the model reads.
"""
try:
    from importlib.metadata import version as _v, PackageNotFoundError
    try:
        __version__ = _v("sima-tseries")
    except PackageNotFoundError:            # running from a source tree
        __version__ = "0.1.0.dev0"
except Exception:                           # pragma: no cover
    __version__ = "0.1.0.dev0"

__all__ = ["__version__"]
