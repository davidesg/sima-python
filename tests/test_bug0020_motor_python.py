"""BUG-0020: when drvarma computes on its pure-Python port, the tools say so
(the RuntimeWarning goes to the MCP server's stderr, which nobody sees), and
the provenance names the interpreter and why the engine did not load."""
import sys

import pytest

from sima import provenance


@pytest.fixture
def sin_motor(monkeypatch):
    monkeypatch.setitem(sys.modules, "drvarma._drvarma_engine", None)
    monkeypatch.delenv("DRVARMA_NO_ENGINE", raising=False)
    monkeypatch.setattr(provenance, "_BASE", None)
    yield
    provenance._BASE = None


def test_el_aviso_dice_el_porte_y_por_que(sin_motor):
    note = provenance.engine_notice()
    assert note.startswith("! ENGINE: drvarma")
    assert "pure-Python port" in note and "drvarma._drvarma_engine" in note
    assert "--python 3.13" in note


def test_pedido_con_la_variable_no_alarma(sin_motor, monkeypatch):
    monkeypatch.setenv("DRVARMA_NO_ENGINE", "1")
    note = provenance.engine_notice()
    assert "Asked for" in note and "slower" not in note


def test_la_procedencia_lleva_python_y_el_error(sin_motor):
    p = provenance.base()
    assert p["python"].startswith(("CPython", "PyPy")) and "bit" in p["python"]
    assert "drvarma._drvarma_engine" in p["drvarma_load_error"]
    assert "Python " + p["python"] in provenance.line(p)


def test_con_el_motor_no_hay_aviso(monkeypatch):
    pytest.importorskip("drvarma._drvarma_engine")
    pytest.importorskip("fue._fue_engine")
    monkeypatch.delenv("DRVARMA_NO_ENGINE", raising=False)
    monkeypatch.delenv("FUE_NO_ENGINE", raising=False)
    assert provenance.engine_notice() == ""
