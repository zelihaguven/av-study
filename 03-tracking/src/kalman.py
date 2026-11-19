"""Lineer Kalman filtresi ve iki hareket modeli."""
from __future__ import annotations

import numpy as np


class KalmanFilter:
    def __init__(self, x0: np.ndarray, P0: np.ndarray):
        self._x = np.asarray(x0, dtype=float).copy()
        self._P = np.asarray(P0, dtype=float).copy()

    @property
    def x(self) -> np.ndarray:
        return self._x

    @property
    def P(self) -> np.ndarray:
        return self._P

    def predict(self, F: np.ndarray, Q: np.ndarray,
                B: np.ndarray | None = None, u: np.ndarray | float | None = None) -> None:
        """x ← F x (+ B u),  P ← F P Fᵀ + Q

        B, u isteğe bağlı kontrol girdisi (ör. 05'te direksiyon). Bilinen bir girdi belirsizlik eklemez.
        """
        self._x = F @ self._x
        if B is not None and u is not None:
            self._x = self._x + np.asarray(B, dtype=float) @ np.atleast_1d(np.asarray(u, dtype=float))
        P = F @ self._P @ F.T + Q
        self._P = 0.5 * (P + P.T)

    def update(self, z: np.ndarray | None, H: np.ndarray, R: np.ndarray) -> None:
        """z None ise hiçbir şey yapma. P simetrik kalmalı (Joseph formu önerilir)."""
        if z is None:
            return
        y = np.asarray(z, dtype=float) - H @ self._x          # innovation
        S = H @ self._P @ H.T + R                              # innovation kovaryansı
        K = np.linalg.solve(S.T, (self._P @ H.T).T).T          # K = P Hᵀ S⁻¹, açık ters almadan
        self._x = self._x + K @ y
        # Joseph formu: P = (I − K H) P (I − K H)ᵀ + K R Kᵀ
        # Kısa form (I − K H) P'den farkı: yuvarlama hatasında bile simetrik ve pozitif tanımlı kalır.
        I_KH = np.eye(len(self._x)) - K @ H
        P = I_KH @ self._P @ I_KH.T + K @ R @ K.T
        self._P = 0.5 * (P + P.T)


def cv_model(dt: float, q: float) -> tuple[np.ndarray, np.ndarray]:
    """Durum [pozisyon, hız]. Q = q * [[dt^3/3, dt^2/2], [dt^2/2, dt]].

    q: sürekli beyaz ivme gürültüsünün spektral yoğunluğu [m²/s³].
    """
    F = np.array([[1.0, dt], [0.0, 1.0]])
    Q = q * np.array([[dt ** 3 / 3, dt ** 2 / 2], [dt ** 2 / 2, dt]])
    return F, Q


def lane_model(dt: float, v: float, q_y: float, q_psi: float) -> tuple[np.ndarray, np.ndarray]:
    """Durum [e_y, e_psi]. e_y' = v * e_psi, e_psi rastgele yürüyüş.

    q_y, q_psi: her duruma eklenen sürekli beyaz gürültünün spektral yoğunlukları;
    ayrık Q = diag(q_y, q_psi) · dt. e_y'deki gürültü, modelde olmayan yol eğriliği ve
    rüzgâr gibi yanal bozucuları temsil eder.
    """
    F = np.array([[1.0, v * dt], [0.0, 1.0]])
    Q = np.diag([q_y, q_psi]) * dt
    return F, Q


def nees(x_true: np.ndarray, x_est: np.ndarray, P: np.ndarray) -> float:
    """e^T P^-1 e"""
    e = np.asarray(x_true, dtype=float) - np.asarray(x_est, dtype=float)
    return float(e @ np.linalg.solve(P, e))
