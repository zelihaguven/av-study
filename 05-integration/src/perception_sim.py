"""Sentetik şerit algısı: gerçek durumdan gürültülü ve aralıklı ölçüm üretir."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LaneNoise:
    sigma_y: float = 0.3                       # [m]
    sigma_psi: float = float(np.deg2rad(3.0))  # [rad]
    sigma_kappa: float = 0.005                 # [1/m]


def measure_lane(state: np.ndarray, path, rng: np.random.Generator,
                 noise: LaneNoise, p_drop: float) -> np.ndarray | None:
    """p_drop olasılıkla None, değilse [e_y, e_psi, kappa] + gürültü.

    e_y: common.paths.cross_track_error; e_psi: wrap(yaw - path.yaw[i]);
    kappa: path.kappa[i] (i en yakın indeks).
    """
    raise NotImplementedError
