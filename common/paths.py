"""Referans yollar ve yanal hata hesabı."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class RefPath:
    x: np.ndarray          # [m]
    y: np.ndarray          # [m]
    yaw: np.ndarray        # teğet yönü [rad]
    kappa: np.ndarray      # eğrilik [1/m], sola dönüş pozitif
    s: np.ndarray          # yay uzunluğu [m], s[0] = 0


def _from_curvature(kappa_of_s, length: float, ds: float) -> RefPath:
    """Eğrilik profilinden yol üretir: yaw = ∫κ ds, (x, y) = ∫(cos yaw, sin yaw) ds.

    Orta nokta kuralı kullanılır; böylece sabit eğrilikte yay tam çember üzerinde kalır.
    """
    n = max(int(round(length / ds)), 1)
    s = np.linspace(0.0, length, n + 1)
    h = s[1] - s[0]
    kappa = np.array([kappa_of_s(si) for si in s])
    k_mid = np.array([kappa_of_s(si + h / 2) for si in s[:-1]])
    dyaw = k_mid * h
    yaw = np.concatenate([[0.0], np.cumsum(dyaw)])
    # Sabit eğrilikli parçada kesin çözüm: kiriş = 2 sin(Δψ/2)/κ = h · sinc(Δψ / 2π)
    chord = h * np.sinc(dyaw / (2 * np.pi))
    mid_yaw = yaw[:-1] + dyaw / 2
    x = np.concatenate([[0.0], np.cumsum(chord * np.cos(mid_yaw))])
    y = np.concatenate([[0.0], np.cumsum(chord * np.sin(mid_yaw))])
    return RefPath(x=x, y=y, yaw=yaw, kappa=kappa, s=s)


def straight(length: float = 100.0, ds: float = 0.1) -> RefPath:
    """Orijinden +x yönünde düz yol."""
    return _from_curvature(lambda s: 0.0, length, ds)


def circle_arc(radius: float, angle: float, ds: float = 0.1) -> RefPath:
    """Orijinden +x yönünde başlayan, sola dönen yay (angle radyan)."""
    return _from_curvature(lambda s: 1.0 / radius, radius * angle, ds)


def s_curve(radius: float = 50.0, ds: float = 0.1, lead_in: float = 20.0) -> RefPath:
    """lead_in m düz + radius yarıçaplı 90° sola + 90° sağa + lead_in m düz.

    Eğrilik süreksiz değişir (0 → +1/R → -1/R → 0); kontrolcüler için kasıtlı zor durum.
    """
    arc = radius * np.pi / 2
    s1, s2, s3 = lead_in, lead_in + arc, lead_in + 2 * arc

    def kappa(s: float) -> float:
        if s < s1:
            return 0.0
        if s < s2:
            return 1.0 / radius
        if s < s3:
            return -1.0 / radius
        return 0.0

    return _from_curvature(kappa, s3 + lead_in, ds)


def nearest_index(path: RefPath, x: float, y: float) -> int:
    """(x, y)'ye en yakın yol noktasının indisi."""
    return int(np.argmin((path.x - x) ** 2 + (path.y - y) ** 2))


def cross_track_error(path: RefPath, x: float, y: float) -> float:
    """İşaretli yanal hata: yol yönüne göre solda pozitif.

    En yakın noktadaki teğete dik (sol normal) bileşen: -sin(yaw)·dx + cos(yaw)·dy.
    """
    i = nearest_index(path, x, y)
    dx, dy = x - path.x[i], y - path.y[i]
    return float(-np.sin(path.yaw[i]) * dx + np.cos(path.yaw[i]) * dy)
