import numpy as np
import pytest

from metrics import max_abs, rms
from paths import circle_arc, cross_track_error, nearest_index, s_curve, straight


def test_straight():
    p = straight(100.0, 0.1)
    assert p.s[-1] == pytest.approx(100.0, abs=0.1)
    assert np.allclose(p.y, 0.0) and np.allclose(p.yaw, 0.0) and np.allclose(p.kappa, 0.0)


def test_circle_curvature_and_length():
    R = 20.0
    p = circle_arc(R, np.pi / 2, 0.05)
    assert np.allclose(p.kappa, 1.0 / R, rtol=1e-3)
    assert p.s[-1] == pytest.approx(R * np.pi / 2, rel=1e-2)
    assert p.x[-1] == pytest.approx(R, rel=1e-2) and p.y[-1] == pytest.approx(R, rel=1e-2)


def test_s_curve_ends_parallel():
    p = s_curve(50.0)
    assert p.yaw[-1] == pytest.approx(0.0, abs=1e-2)
    assert p.kappa.max() == pytest.approx(1 / 50.0, rel=1e-2)
    assert p.kappa.min() == pytest.approx(-1 / 50.0, rel=1e-2)


def test_cte_sign_convention():
    p = straight()
    assert cross_track_error(p, 50.0, 1.0) == pytest.approx(1.0, abs=1e-2)
    assert cross_track_error(p, 50.0, -2.0) == pytest.approx(-2.0, abs=1e-2)
    assert nearest_index(p, 50.0, 3.0) == pytest.approx(500, abs=1)


def test_metrics():
    v = np.array([3.0, -4.0])
    assert rms(v) == pytest.approx(np.sqrt(12.5))
    assert max_abs(v) == pytest.approx(4.0)
