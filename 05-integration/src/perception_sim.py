"""Sentetik şerit algısı: gerçek durumdan gürültülü ve aralıklı ölçüm üretir."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from paths import cross_track_error, nearest_index


@dataclass(frozen=True)
class LaneNoise:
    sigma_y: float = 0.3                       # [m]
    sigma_psi: float = float(np.deg2rad(3.0))  # [rad]
    sigma_kappa: float = 0.005                 # [1/m]


def _wrap(a: float) -> float:
    return float((a + np.pi) % (2 * np.pi) - np.pi)


def true_lane_state(state: np.ndarray, path) -> np.ndarray:
    """Gürültüsüz [e_y, e_psi, kappa], arka aks referanslı."""
    x, y, yaw = state[0], state[1], state[2]
    i = nearest_index(path, x, y)
    return np.array([cross_track_error(path, x, y), _wrap(yaw - path.yaw[i]), path.kappa[i]])


def measure_lane(state: np.ndarray, path, rng: np.random.Generator,
                 noise: LaneNoise, p_drop: float) -> np.ndarray | None:
    """p_drop olasılıkla None, değilse [e_y, e_psi, kappa] + gürültü.

    e_y: common.paths.cross_track_error; e_psi: wrap(yaw - path.yaw[i]);
    kappa: path.kappa[i] (i en yakın indeks).
    """
    # Rastgele sayılar kayıp olsun olmasın aynı sırayla çekilir: böylece aynı tohumla
    # farklı p_drop değerleri aynı gürültü dizisini paylaşır (karşılaştırmalar adil olur).
    dropped = rng.random() < p_drop
    n = rng.normal(0.0, 1.0, 3) * np.array([noise.sigma_y, noise.sigma_psi, noise.sigma_kappa])
    if dropped:
        return None
    return true_lane_state(state, path) + n
