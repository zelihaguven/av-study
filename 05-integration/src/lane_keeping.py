"""Şerit takibi (3 durumlu Kalman) ve şerit tutma direksiyon kuralı."""
from __future__ import annotations

import numpy as np


class LaneTracker:
    """Durum [e_y, e_psi, kappa].

    Tahmin adımı direksiyonu girdi olarak kullanır:
        e_y'    = v * e_psi
        e_psi'  = v / L * tan(delta) - v * kappa
        kappa'  = rastgele yürüyüş
    03'teki KalmanFilter'ı kullan; burada yeniden yazma.
    """

    def __init__(self, wheelbase: float, noise, q: tuple[float, float, float]):
        raise NotImplementedError

    def step(self, z: np.ndarray | None, v: float, delta_prev: float, dt: float) -> np.ndarray:
        """predict + (varsa) update; güncel tahmini döndürür."""
        raise NotImplementedError


def lane_keep_steer(e_y: float, e_psi: float, kappa: float, v: float,
                    wheelbase: float, k: float = 1.0, k_soft: float = 1.0,
                    use_feedforward: bool = True) -> float:
    """Feedforward: atan(L * kappa). Feedback: e_psi ve e_y'yi sıfıra götüren Stanley benzeri terim.
    İşaret kuralı README'de."""
    raise NotImplementedError
