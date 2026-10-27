"""Kinematik bisiklet modeli (arka aks referanslı).

Durum vektörü: [x, y, yaw, v]
    x, y : arka aks merkezinin dünya koordinatı [m]
    yaw  : yön açısı [rad], [-pi, pi] aralığında tutulur
    v    : boylamsal hız [m/s]
Girdi: accel [m/s^2], steer (ön teker açısı) [rad]
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class VehicleParams:
    wheelbase: float = 2.7          # L [m]
    max_steer: float = float(np.deg2rad(35.0))
    max_accel: float = 3.0          # [m/s^2], fren için -max_accel


def wrap_angle(angle: float) -> float:
    """Açıyı [-pi, pi] aralığına sarar."""
    raise NotImplementedError


def derivatives(state: np.ndarray, accel: float, steer: float,
                params: VehicleParams) -> np.ndarray:
    """[x_dot, y_dot, yaw_dot, v_dot] döndürür.

    İpucu: yaw_dot = v / L * tan(steer)
    """
    raise NotImplementedError


def step(state: np.ndarray, accel: float, steer: float, dt: float,
         params: VehicleParams, method: str = "rk4") -> np.ndarray:
    """Durumu dt kadar ilerletir.

    - steer [-max_steer, max_steer], accel [-max_accel, max_accel] aralığına sınırlanır.
    - Sonuçtaki yaw wrap_angle ile sarılır.
    - method: "euler" veya "rk4"; başka değer ValueError.
    """
    raise NotImplementedError


def simulate(state0: np.ndarray, accels: np.ndarray, steers: np.ndarray,
             dt: float, params: VehicleParams,
             method: str = "rk4") -> np.ndarray:
    """N adımlık kontrol dizisiyle simülasyon. (N+1, 4) dizi döner, ilk satır state0."""
    raise NotImplementedError
