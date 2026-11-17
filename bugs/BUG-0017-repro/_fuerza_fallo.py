"""pytest plugin for the repro: a drvarma version no cache was built with, so
the tutorial's rank test misses its cache (the situation of 2026-11-16)."""
from sima import provenance

_real = provenance._version
provenance._version = lambda k: "0.0.0" if k == "drvarma" else _real(k)
