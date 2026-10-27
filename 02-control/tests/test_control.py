"""02 kabul testleri. Eşikleri gevşetmek yerine kontrolcüyü ayarla."""
import numpy as np
import pytest

from closed_loop import run_closed_loop
from controllers import PID, SPEED_PID_GAINS
from metrics import max_abs, rms
from paths import s_curve, straight


def test_pid_speed():
    """v' = a modelinde, ivme ±3 m/s² sınırlı, 0 → 10 m/s: 5 s içinde %2 bandına gir, aşma < %10.

    Kazançlar controllers.SPEED_PID_GAINS = (kp, ki, kd); seçim senin.
    """
    pid = PID(*SPEED_PID_GAINS, out_min=-3.0, out_max=3.0)
    v, dt, hist = 0.0, 0.01, []
    for _ in range(int(10 / dt)):
        v += pid.update(10.0 - v, dt) * dt
        hist.append(v)
    hist = np.array(hist)
    assert hist.max() < 11.0
    assert np.all(np.abs(hist[int(5 / dt):] - 10.0) < 0.2)


@pytest.mark.parametrize("ctrl", ["pure_pursuit", "stanley"])
def test_offset_recovery_straight(ctrl):
    """Düz yolda 1 m sol ofset, 10 m/s: 10 s sonra |CTE| < 0.05 m, aşma < 0.3 m."""
    res = run_closed_loop(straight(200.0), ctrl, v_ref=10.0, y0_offset=1.0, T=12.0)
    after = res.t >= 10.0
    assert max_abs(res.cte[after]) < 0.05
    assert res.cte.min() > -0.3


@pytest.mark.parametrize("ctrl", ["pure_pursuit", "stanley"])
def test_s_curve_tracking(ctrl):
    """S-viraj, R = 50 m, 10 m/s: RMS CTE < 0.1 m, maks |CTE| < 0.25 m."""
    res = run_closed_loop(s_curve(50.0), ctrl, v_ref=10.0)
    assert rms(res.cte) < 0.1
    assert max_abs(res.cte) < 0.25


def test_steer_within_limits():
    from bicycle import VehicleParams
    res = run_closed_loop(s_curve(50.0), "stanley", v_ref=10.0)
    assert max_abs(res.steer) <= VehicleParams().max_steer + 1e-9
