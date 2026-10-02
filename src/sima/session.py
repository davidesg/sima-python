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
    fits: dict = field(default_factory=dict)       # (p, q, diagcov, links) -> fitted Ladder
    current: tuple = None              # the key of the last estimated model
    evaluations: dict = field(default_factory=dict)  # (p, q, diagcov, estwin, H) -> summary
    route: str = "U"                   # "U": univariate models on the diagonal; "V": the vector first
    v: dict = None                     # route V: {"dir", "raw"} (docs/STUDY-raw-entry.md)


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


# --------------------------------------------------------------------------- #
#  The raw-data entry (docs/STUDY-raw-entry.md)                               #
# --------------------------------------------------------------------------- #

@dataclass
class RawSession:
    """Raw series with no univariate models yet: the table, its calendar and
    the characterization per series. A route (U or V) turns it into files and
    a ladder session of the same name."""
    name: str
    path: str
    names: list
    data: object                       # numpy array, n x m, original levels
    freq: int
    start: tuple
    guion: Guion
    chars: list = None                 # characterize(): one dict per series


_RAW: dict = {}


def open_raw(name, path, names, data, freq, start):
    s = RawSession(name, path, list(names), data, int(freq), tuple(start),
                   Guion(name, [path]))
    _RAW[name] = s
    return s


def get_raw(name):
    if name not in _RAW:
        raise KeyError(f"no raw data '{name}': load it with load_data")
    return _RAW[name]


def has_raw(name):
    return name in _RAW
