"""05 kabul testleri. S-viraj R = 50 m, 10 m/s, 20 Hz algı."""
import numpy as np
import pytest

from loop import run
from metrics import max_abs, rms
from paths import s_curve
from perception_sim import LaneNoise

NOISE = LaneNoise()


@pytest.fixture(scope="module")
def path():
    return s_curve(50.0)


def _steer_rate_rms(res):
    return rms(np.diff(res.steer) / np.diff(res.t))


def test_stays_in_lane_with_tracker(path):
    res = run(path, 10.0, NOISE, p_drop=0.1, use_tracker=True, seed=0)
    assert max_abs(res.cte) < 0.5
    assert rms(res.cte) < 0.25


def test_tracker_smooths_steering(path):
    """Takip katmanının asıl işi: aynı veride direksiyon hızını en az yarıya indirmek."""
    with_t = run(path, 10.0, NOISE, p_drop=0.1, use_tracker=True, seed=0)
    without = run(path, 10.0, NOISE, p_drop=0.1, use_tracker=False, seed=0)
    assert _steer_rate_rms(with_t) < 0.5 * _steer_rate_rms(without)


def test_survives_heavy_dropout(path):
    res = run(path, 10.0, NOISE, p_drop=0.3, use_tracker=True, seed=1)
    assert max_abs(res.cte) < 0.75


def test_feedforward_helps_on_curve(path):
    ff = run(path, 10.0, NOISE, p_drop=0.1, use_feedforward=True, seed=2)
    no_ff = run(path, 10.0, NOISE, p_drop=0.1, use_feedforward=False, seed=2)
    assert rms(ff.cte) < rms(no_ff.cte)
