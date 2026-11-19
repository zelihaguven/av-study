"""Klasik kontrolcüler.

Durum: [x, y, yaw, v] (01'deki gibi, arka aks referanslı)
Yol: common.paths.RefPath
"""
from __future__ import annotations

import numpy as np

from paths import cross_track_error, nearest_index

# Hız PID kazançları (kp, ki, kd). Gerekçe: notes.md
SPEED_PID_GAINS: tuple[float, float, float] = (2.0, 0.1, 0.0)


def _wrap(a: float) -> float:
    return float((a + np.pi) % (2 * np.pi) - np.pi)


class PID:
    def __init__(self, kp: float, ki: float, kd: float,
                 out_min: float = -np.inf, out_max: float = np.inf):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.out_min, self.out_max = out_min, out_max
        self.reset()

    def reset(self) -> None:
        self.integral = 0.0
        self.prev_error: float | None = None

    def update(self, error: float, dt: float) -> float:
        """Çıkışı sınırla; sınırdayken integrali biriktirme (anti-windup)."""
        deriv = 0.0 if self.prev_error is None else (error - self.prev_error) / dt
        self.prev_error = error
        candidate = self.integral + error * dt
        u = self.kp * error + self.ki * candidate + self.kd * deriv
        u_sat = float(np.clip(u, self.out_min, self.out_max))
        # Koşullu entegrasyon: çıkış sınırdaysa ve hata onu daha da sınıra itiyorsa integrali dondur.
        saturated_same_dir = (u > self.out_max and error > 0) or (u < self.out_min and error < 0)
        if not saturated_same_dir:
            self.integral = candidate
        return u_sat


def pure_pursuit(state: np.ndarray, path, wheelbase: float,
                 lookahead: float | None = None, k_v: float = 0.5,
                 min_lookahead: float = 3.0) -> float:
    """Direksiyon açısı [rad].

    lookahead None ise Ld = max(min_lookahead, k_v * v).
    delta = atan(2 L sin(alpha) / Ld)
    """
    x, y, yaw, v = state
    ld = lookahead if lookahead is not None else max(min_lookahead, k_v * v)
    i0 = nearest_index(path, x, y)
    # En yakın noktadan ileri doğru, arka aksa uzaklığı ilk kez Ld'yi geçen yol noktası
    d = np.hypot(path.x[i0:] - x, path.y[i0:] - y)
    ahead = np.nonzero(d >= ld)[0]
    i = i0 + (int(ahead[0]) if len(ahead) else len(d) - 1)
    dx, dy = path.x[i] - x, path.y[i] - y
    dist = max(float(np.hypot(dx, dy)), 1e-6)   # yol sonunda Ld'den kısa olabilir
    alpha = np.arctan2(dy, dx) - yaw
    return float(np.arctan2(2.0 * wheelbase * np.sin(alpha), dist))


def stanley(state: np.ndarray, path, wheelbase: float,
            k: float = 1.0, k_soft: float = 1.0) -> float:
    """Direksiyon açısı [rad].

    Ön aks konumunu hesapla, en yakın yol noktasına göre:
    delta = yaw_error + atan(k * e_front / (k_soft + v))
    İşaret kuralı: common.paths (sol pozitif) ile tutarlı olmalı.
    Araç soldaysa (e > 0) sağa (negatif) dönmek gerekir, bu yüzden ikinci terim eksi işaretli.
    """
    x, y, yaw, v = state
    fx, fy = x + wheelbase * np.cos(yaw), y + wheelbase * np.sin(yaw)
    i = nearest_index(path, fx, fy)
    # Yol yönünü en yakın noktanın değeriyle değil, ön aksın izdüşümüne göre al: yaw(s) = yaw_i + κ_i·Δs.
    # Yoksa araç her adımda farklı sayıda yol noktası atladığında yaw basamaklı değişir
    # ve direksiyonda sahte sıçramalar görülür (ds = 0,1 m, v·dt = 0,2 m).
    along = np.cos(path.yaw[i]) * (fx - path.x[i]) + np.sin(path.yaw[i]) * (fy - path.y[i])
    yaw_error = _wrap(path.yaw[i] + path.kappa[i] * along - yaw)
    e_front = cross_track_error(path, fx, fy)
    return float(yaw_error - np.arctan2(k * e_front, k_soft + v))
