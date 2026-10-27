"""Lineer Kalman filtresi ve iki hareket modeli."""
from __future__ import annotations

import numpy as np


class KalmanFilter:
    def __init__(self, x0: np.ndarray, P0: np.ndarray):
        raise NotImplementedError

    @property
    def x(self) -> np.ndarray:
        raise NotImplementedError

    @property
    def P(self) -> np.ndarray:
        raise NotImplementedError

    def predict(self, F: np.ndarray, Q: np.ndarray) -> None:
        raise NotImplementedError

    def update(self, z: np.ndarray | None, H: np.ndarray, R: np.ndarray) -> None:
        """z None ise hiçbir şey yapma. P simetrik kalmalı (Joseph formu önerilir)."""
        raise NotImplementedError


def cv_model(dt: float, q: float) -> tuple[np.ndarray, np.ndarray]:
    """Durum [pozisyon, hız]. Q = q * [[dt^3/3, dt^2/2], [dt^2/2, dt]]."""
    raise NotImplementedError


def lane_model(dt: float, v: float, q_y: float, q_psi: float) -> tuple[np.ndarray, np.ndarray]:
    """Durum [e_y, e_psi]. e_y' = v * e_psi, e_psi rastgele yürüyüş."""
    raise NotImplementedError


def nees(x_true: np.ndarray, x_est: np.ndarray, P: np.ndarray) -> float:
    """e^T P^-1 e"""
    raise NotImplementedError
