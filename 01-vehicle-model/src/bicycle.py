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
    return float((angle + np.pi) % (2 * np.pi) - np.pi)


def derivatives(state: np.ndarray, accel: float, steer: float,
                params: VehicleParams) -> np.ndarray:
    """[x_dot, y_dot, yaw_dot, v_dot] döndürür.

    İpucu: yaw_dot = v / L * tan(steer)
    """
    _, _, yaw, v = state
    return np.array([
        v * np.cos(yaw),
        v * np.sin(yaw),
        v / params.wheelbase * np.tan(steer),
        accel,
    ])


def step(state: np.ndarray, accel: float, steer: float, dt: float,
         params: VehicleParams, method: str = "rk4") -> np.ndarray:
    """Durumu dt kadar ilerletir.

    - steer [-max_steer, max_steer], accel [-max_accel, max_accel] aralığına sınırlanır.
    - Sonuçtaki yaw wrap_angle ile sarılır.
    - method: "euler" veya "rk4"; başka değer ValueError.
    """
    if method not in ("euler", "rk4"):
        raise ValueError(f"bilinmeyen entegrasyon yöntemi: {method!r}")
    state = np.asarray(state, dtype=float)
    steer = float(np.clip(steer, -params.max_steer, params.max_steer))
    accel = float(np.clip(accel, -params.max_accel, params.max_accel))

    def f(s):
        return derivatives(s, accel, steer, params)

    if method == "euler":
        new = state + dt * f(state)
    else:
        k1 = f(state)
        k2 = f(state + dt / 2 * k1)
        k3 = f(state + dt / 2 * k2)
        k4 = f(state + dt * k3)
        new = state + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    new[2] = wrap_angle(new[2])
    return new


def simulate(state0: np.ndarray, accels: np.ndarray, steers: np.ndarray,
             dt: float, params: VehicleParams,
             method: str = "rk4") -> np.ndarray:
    """N adımlık kontrol dizisiyle simülasyon. (N+1, 4) dizi döner, ilk satır state0."""
    accels = np.asarray(accels, dtype=float)
    steers = np.asarray(steers, dtype=float)
    if accels.shape != steers.shape:
        raise ValueError("accels ve steers aynı uzunlukta olmalı")
    traj = np.empty((len(accels) + 1, 4))
    traj[0] = state0
    for k in range(len(accels)):
        traj[k + 1] = step(traj[k], accels[k], steers[k], dt, params, method)
    return traj
