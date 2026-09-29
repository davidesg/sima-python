"""Jenkins and Alavi's (1981) two identifications in sima (identify_matrices)."""
import json
import os

import numpy as np

from sima import evidence, mcp_server as M

DATA = os.path.join(os.path.dirname(__file__), "data", "m6")
PAIR = [os.path.join(DATA, "M6_EI.pre"), os.path.join(DATA, "M6_EP.pre")]
SIG = np.array([[1.0, 0.3], [0.3, 1.0]])


def _fn(tool):
    return getattr(tool, "fn", tool)


def _sim(n, phi, theta, seed, sig=SIG):
    rng = np.random.default_rng(seed)
    a = (np.linalg.cholesky(sig) @ rng.standard_normal((2, n + 200))).T
    w = np.zeros((n + 200, 2))
    for t in range(2, n + 200):
        w[t] = (a[t] + sum(P @ w[t - 1 - i] for i, P in enumerate(phi))
                - sum(T @ a[t - 1 - i] for i, T in enumerate(theta)))
    return w[200:]


def test_a_cross_ma_on_the_residuals_is_read_by_method_2():
    """Residuals that are white except a cross MA(1): B leads A by one."""
    # innovations uncorrelated at lag 0: otherwise the cross MA also makes A
    # autocorrelated, which A's univariate model would have absorbed
    res = _sim(3000, [], [np.array([[0.0, -0.5], [0.0, 0.0]])], 1, np.eye(2))
    w = res                                            # univariate models: white noise
    _txt, facts = evidence.ja_identification(w, res, ["A", "B"], 6, 1, 1)
    assert facts["method2_q"] == 1 and facts["links"] == ["A<-B"]
    assert facts["diagonal_left"] == []


def test_a_cross_ar_is_read_by_method_1_off_diagonal():
    P = np.array([[0.5, 0.4], [0.0, 0.3]])
    w = _sim(3000, [P], [], 2)
    txt, facts = evidence.ja_identification(w, w, ["A", "B"], 6, 1, 1)
    assert facts["method1_p"] == 1 and facts["method1_links"] == ["A<-B"]
    assert "(b) from method 1: a cross AR of order 1" in txt


def test_the_tool_on_the_ladder():
    _fn(M.load_pre)("ja", json.dumps(PAIR))
    _fn(M.run_gate)("ja")
    txt = _fn(M.identify_matrices)("ja")
    for part in ("METHOD 2, prewhitened", "METHOD 1, not prewhitened", "S_k(1):",
                 "reading, off-diagonal", "Jenkins and Alavi: use both"):
        assert part in txt, part
    assert "identify_matrices" in _fn(M.export_guion)("ja", save=False)
