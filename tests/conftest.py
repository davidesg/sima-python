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
