"""01 kabul testleri. Başlangıçta kırmızıdır."""
import numpy as np
import pytest

from bicycle import VehicleParams, simulate, step, wrap_angle

P = VehicleParams()


def test_wrap_angle():
    assert abs(wrap_angle(3 * np.pi)) == pytest.approx(np.pi)
    assert wrap_angle(-0.5) == pytest.approx(-0.5)
    assert -np.pi <= wrap_angle(7.0) <= np.pi


@pytest.mark.parametrize("method", ["euler", "rk4"])
def test_straight_line(method):
    """Direksiyon 0, sabit hız: 10 s'de 100 m düz gider, y ve yaw 0 kalır."""
    n, dt = 1000, 0.01
    traj = simulate(np.array([0.0, 0.0, 0.0, 10.0]), np.zeros(n), np.zeros(n), dt, P, method)
    assert traj.shape == (n + 1, 4)
    assert traj[-1, 0] == pytest.approx(100.0, rel=1e-6)
    assert abs(traj[-1, 1]) < 1e-9
    assert abs(traj[-1, 2]) < 1e-9


def _radius_error(method, dt):
    steer = np.deg2rad(10.0)
    v = 5.0
    R = P.wheelbase / np.tan(steer)
    T = 2 * np.pi * R / v                       # bir tam tur
    n = int(round(T / dt))
    traj = simulate(np.array([0.0, 0.0, 0.0, v]), np.zeros(n), np.full(n, steer), dt, P, method)
    center = np.array([0.0, R])                 # sola dönüş, merkez +y'de
    r = np.linalg.norm(traj[:, :2] - center, axis=1)
    return np.max(np.abs(r - R)) / R


def test_circle_radius_rk4():
    """Sabit direksiyonda yörünge R = L / tan(delta) çemberi; RK4 ile %1 içinde."""
    assert _radius_error("rk4", 0.01) < 0.01


def test_rk4_more_accurate_than_euler():
    assert _radius_error("rk4", 0.05) < _radius_error("euler", 0.05)


def test_steer_saturation():
    s0 = np.array([0.0, 0.0, 0.0, 5.0])
    a = step(s0, 0.0, np.deg2rad(80.0), 0.01, P)
    b = step(s0, 0.0, P.max_steer, 0.01, P)
    np.testing.assert_allclose(a, b)


def test_unknown_method_raises():
    with pytest.raises(ValueError):
        step(np.zeros(4), 0.0, 0.0, 0.01, P, method="verlet")
