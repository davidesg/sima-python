"""Without the `raw` extra, the raw entry says how to install it (0.1.1)."""
import sys

from sima import mcp_server as M
from sima.raw import RAW_EXTRA

fn = lambda t: getattr(t, "fn", t)


def test_the_message_names_the_extra():
    assert 'pip install "sima-tseries[raw]"' in RAW_EXTRA


def test_without_art_load_example_and_characterize_say_so(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "art", None)        # import art -> ImportError
    import importlib.util
    real = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, "find_spec",
                        lambda n, *a, **k: None if n == "art" else real(n, *a, **k))
    out = fn(M.load_example)("lutkepohl_poskitt", session="noart", dest=str(tmp_path))
    assert RAW_EXTRA in out
    assert RAW_EXTRA in fn(M.characterize)("noart")


def test_an_example_from_univariate_models_does_not_ask_for_it(tmp_path):
    out = fn(M.load_example)("jenkins_alavi", session="ja_extra", dest=str(tmp_path))
    assert RAW_EXTRA not in out
