"""Sessions: a name, the fue files, and what the engine has estimated on them."""
from __future__ import annotations

from dataclasses import dataclass, field

from .guion import Guion


@dataclass
class Session:
    name: str
    files: list
    series: list                       # drvarma.ladder.LadderSeries, loaded once
    guion: Guion
    gate: dict = None                  # the result of the diagonal gate
    diagonal: object = None            # Ladder fitted with p = q = 0, diagcov
    fits: dict = field(default_factory=dict)       # (p, q, diagcov) -> fitted Ladder
    current: tuple = None              # the key of the last estimated model
    evaluations: dict = field(default_factory=dict)  # (p, q, diagcov, estwin, H) -> summary


_SESSIONS: dict = {}


def open_session(name, files):
    from drvarma.ladder import load, check_alignment
    series = load(files)
    check_alignment(series)
    s = Session(name, list(files), series, Guion(name, list(files)))
    _SESSIONS[name] = s
    return s


def get(name):
    if name not in _SESSIONS:
        raise KeyError(f"no session '{name}': start it with load_pre")
    return _SESSIONS[name]


def names():
    return sorted(_SESSIONS)
