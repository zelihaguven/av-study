"""Şerit takibi (3 durumlu Kalman) ve şerit tutma direksiyon kuralı."""
from __future__ import annotations

import numpy as np

from kalman import KalmanFilter


class LaneTracker:
    """Durum [e_y, e_psi, kappa].

    Tahmin adımı direksiyonu girdi olarak kullanır:
        e_y'    = v * e_psi
        e_psi'  = v / L * tan(delta) - v * kappa
        kappa'  = rastgele yürüyüş
    03'teki KalmanFilter'ı kullan; burada yeniden yazma.

    Ayrıklaştırma (dt boyunca delta ve kappa sabit, küçük açı):
        F = [[1, v dt, -v² dt²/2],      B = [v dt²/2,
             [0, 1,    -v dt    ],           dt,
             [0, 0,     1       ]]           0     ],   u = v/L · tan(delta)
    q = (q_y, q_psi, q_kappa): spektral yoğunluklar, Q = diag(q) · dt.
    """

    def __init__(self, wheelbase: float, noise, q: tuple[float, float, float]):
        self.L = wheelbase
        self.q = np.asarray(q, dtype=float)
        self.H = np.eye(3)
        self.R = np.diag([noise.sigma_y ** 2, noise.sigma_psi ** 2, noise.sigma_kappa ** 2])
        # İlk ölçüme kadar belirsizlik büyük: ilk update neredeyse doğrudan ölçümü alır.
        self.kf = KalmanFilter(np.zeros(3), np.diag([1.0, np.deg2rad(10.0) ** 2, 0.02 ** 2]))

    def step(self, z: np.ndarray | None, v: float, delta_prev: float, dt: float) -> np.ndarray:
        """predict + (varsa) update; güncel tahmini döndürür."""
        F = np.array([[1.0, v * dt, -0.5 * v ** 2 * dt ** 2],
                      [0.0, 1.0, -v * dt],
                      [0.0, 0.0, 1.0]])
        B = np.array([[0.5 * v * dt ** 2], [dt], [0.0]])
        u = v / self.L * np.tan(delta_prev)
        self.kf.predict(F, np.diag(self.q) * dt, B, u)
        self.kf.update(z, self.H, self.R)
        return self.kf.x.copy()

    @property
    def P(self) -> np.ndarray:
        return self.kf.P


def lane_keep_steer(e_y: float, e_psi: float, kappa: float, v: float,
                    wheelbase: float, k: float = 1.0, k_soft: float = 1.0,
                    use_feedforward: bool = True) -> float:
    """Feedforward: atan(L * kappa). Feedback: e_psi ve e_y'yi sıfıra götüren Stanley benzeri terim.
    İşaret kuralı README'de.

    e_y ve e_psi arka aksta ölçülüyor; Stanley'nin kullandığı ön aks hatası
    e_front = e_y + L·sin(e_psi). Araç soldaysa (e > 0) veya sola bakıyorsa (e_psi > 0) sağa,
    yani negatif direksiyon gerekir:
        delta = atan(L κ) − e_psi − atan(k · e_front / (k_soft + v))
    Düzgün bir virajda feedforward tek başına aracı yolda tutar (R = L / tan δ, bkz. 01);
    feedback sadece sapmayı düzeltir.
    """
    e_front = e_y + wheelbase * np.sin(e_psi)
    ff = np.arctan(wheelbase * kappa) if use_feedforward else 0.0
    return float(ff - e_psi - np.arctan2(k * e_front, k_soft + v))
