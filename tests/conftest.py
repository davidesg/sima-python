import json
import os

import pytest

DATA = os.path.join(os.path.dirname(__file__), "data")


def data(*names):
    return [os.path.join(DATA, n) for n in names]


TRIO = data("IPC_ES_m10.pre", "IPC_FR_msar.pre", "IPC_DE_mar3sar.pre")
EXT = data("IPC_ES_ext.pre", "IPC_FR_ext.pre", "IPC_DE_ext.pre")


@pytest.fixture
def trio_json():
    return json.dumps(TRIO)


@pytest.fixture
def ext_json():
    return json.dumps(EXT)


# The figures are drawn only where a test asks for them: since package B,
# every estimate in the guided lane draws its diagnosis' figures, and the suite
# estimates hundreds of times. The modules that test the figures themselves
# keep the default (shown in the guided lane).
_FIGURE_TESTS = {"test_figures", "test_jenkins_alavi_muskrat_mink", "test_check_residuals",
                 "test_vec"}
if "SIMA_FIGURES" not in os.environ:
    os.environ["SIMA_FIGURES"] = "0"
    _OURS = True
else:
    _OURS = False


@pytest.fixture(scope="module", autouse=True)
def _figures_by_module(request):
    if not (_OURS and request.module.__name__.rsplit(".", 1)[-1] in _FIGURE_TESTS):
        yield
        return
    mp = pytest.MonkeyPatch()
    mp.delenv("SIMA_FIGURES")
    yield
    mp.undo()
