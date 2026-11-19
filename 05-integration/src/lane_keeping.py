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

    def __init__(self, wheelbase: float, noise, q: tuple[float, float, float], meas_rho: float = 0.0):
        """meas_rho > 0: ölçüm gürültüsünün AR(1) olduğunu filtreye bildir (durum genişletme, 05 notları 5b).
        Durum [e_y, e_psi, kappa, n_y, n_psi, n_kappa] olur; z = x + n, n_{k+1} = ρ n_k + w,
        w'nin varyansı σ²(1 − ρ²) (durağan σ korunur). Çıktı yine ilk üç durum."""
        self.L = wheelbase
        self.q = np.asarray(q, dtype=float)
        self.rho = float(meas_rho)
        sig2 = np.array([noise.sigma_y ** 2, noise.sigma_psi ** 2, noise.sigma_kappa ** 2])
        P0 = np.diag([1.0, np.deg2rad(10.0) ** 2, 0.02 ** 2])
        if self.rho > 0:
            self.H = np.hstack([np.eye(3), np.eye(3)])
            self.R = np.diag(sig2) * 1e-4            # gürültü artık durumda; R sayısal kararlılık için küçük
            self.Qn = np.diag(sig2 * (1 - self.rho ** 2))
            P0 = np.block([[P0, np.zeros((3, 3))], [np.zeros((3, 3)), np.diag(sig2)]])
            self.kf = KalmanFilter(np.zeros(6), P0)
        else:
            self.H = np.eye(3)
            self.R = np.diag(sig2)
            # İlk ölçüme kadar belirsizlik büyük: ilk update neredeyse doğrudan ölçümü alır.
            self.kf = KalmanFilter(np.zeros(3), P0)

    def step(self, z: np.ndarray | None, v: float, delta_prev: float, dt: float) -> np.ndarray:
        """predict + (varsa) update; güncel tahmini döndürür."""
        F = np.array([[1.0, v * dt, -0.5 * v ** 2 * dt ** 2],
                      [0.0, 1.0, -v * dt],
                      [0.0, 0.0, 1.0]])
        B = np.array([[0.5 * v * dt ** 2], [dt], [0.0]])
        Q = np.diag(self.q) * dt
        u = v / self.L * np.tan(delta_prev)
        if self.rho > 0:
            Z = np.zeros((3, 3))
            F = np.block([[F, Z], [Z, self.rho * np.eye(3)]])
            B = np.vstack([B, np.zeros((3, 1))])
            Q = np.block([[Q, Z], [Z, self.Qn]])
        self.kf.predict(F, Q, B, u)
        self.kf.update(z, self.H, self.R)
        return self.kf.x[:3].copy()

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
