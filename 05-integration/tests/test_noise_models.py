"""Sentetik algının ilişkili gürültü ve kümeli kayıp modelleri."""
import numpy as np
import pytest

from paths import straight
from perception_sim import LaneNoise, NoiseMemory, measure_lane

PATH = straight(50.0)
STATE = np.array([10.0, 0.0, 0.0, 10.0])        # yolun tam üstünde: ölçüm = saf gürültü


def _draw(noise, p_drop, n=20000, seed=0, memory=True):
    rng = np.random.default_rng(seed)
    mem = NoiseMemory() if memory else None
    return [measure_lane(STATE, PATH, rng, noise, p_drop, mem) for _ in range(n)]


def test_defaults_reproduce_independent_model():
    """rho = 0 ve burst_len = None iken memory vermek sonucu değiştirmez (eski davranış)."""
    a = _draw(LaneNoise(), 0.1, n=500, memory=True)
    b = _draw(LaneNoise(), 0.1, n=500, memory=False)
    assert all((x is None and y is None) or np.array_equal(x, y) for x, y in zip(a, b))


def test_ar1_keeps_sigma_and_sets_lag1():
    z = np.array(_draw(LaneNoise(rho=0.7), 0.0))[:, 0]
    assert np.std(z) == pytest.approx(0.3, rel=0.05)
    r = z - z.mean()
    assert np.dot(r[:-1], r[1:]) / np.dot(r, r) == pytest.approx(0.7, abs=0.03)


def test_bursty_dropout_rate_and_length():
    zs = _draw(LaneNoise(burst_len=5.0), 0.2, n=50000)
    lost = np.array([z is None for z in zs])
    assert lost.mean() == pytest.approx(0.2, abs=0.015)
    runs, cur = [], 0
    for m in lost:
        if m:
            cur += 1
        elif cur:
            runs.append(cur)
            cur = 0
    assert np.mean(runs) == pytest.approx(5.0, rel=0.1)


def test_augmented_tracker_helps_with_strongly_correlated_noise():
    """5b: ρ = 0,9'da gürültüyü durum olarak taşıyan filtre, beyaz varsayan filtreden daha az yanal hata verir."""
    from loop import run
    from metrics import rms
    from paths import s_curve
    path = s_curve(50.0)
    noise = LaneNoise(rho=0.9)
    white = np.mean([rms(run(path, 10.0, noise, p_drop=0.1, seed=s).cte) for s in range(4)])
    aug = np.mean([rms(run(path, 10.0, noise, p_drop=0.1, seed=s, tracker_rho=0.9).cte) for s in range(4)])
    assert aug < 0.9 * white
