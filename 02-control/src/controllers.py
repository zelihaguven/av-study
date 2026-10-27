"""Klasik kontrolcüler.

Durum: [x, y, yaw, v] (01'deki gibi, arka aks referanslı)
Yol: common.paths.RefPath
"""
from __future__ import annotations

import numpy as np

# Hız PID kazançları (kp, ki, kd). test_pid_speed bunları kullanır; ayarla.
SPEED_PID_GAINS: tuple[float, float, float] = (0.0, 0.0, 0.0)


class PID:
    def __init__(self, kp: float, ki: float, kd: float,
                 out_min: float = -np.inf, out_max: float = np.inf):
        raise NotImplementedError

    def reset(self) -> None:
        raise NotImplementedError

    def update(self, error: float, dt: float) -> float:
        """Çıkışı sınırla; sınırdayken integrali biriktirme (anti-windup)."""
        raise NotImplementedError


def pure_pursuit(state: np.ndarray, path, wheelbase: float,
                 lookahead: float | None = None, k_v: float = 0.5,
                 min_lookahead: float = 3.0) -> float:
    """Direksiyon açısı [rad].

    lookahead None ise Ld = max(min_lookahead, k_v * v).
    delta = atan(2 L sin(alpha) / Ld)
    """
    raise NotImplementedError


def stanley(state: np.ndarray, path, wheelbase: float,
            k: float = 1.0, k_soft: float = 1.0) -> float:
    """Direksiyon açısı [rad].

    Ön aks konumunu hesapla, en yakın yol noktasına göre:
    delta = yaw_error + atan(k * e_front / (k_soft + v))
    İşaret kuralı: common.paths (sol pozitif) ile tutarlı olmalı.
    """
    raise NotImplementedError
