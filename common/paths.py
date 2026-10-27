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


def straight(length: float = 100.0, ds: float = 0.1) -> RefPath:
    """Orijinden +x yönünde düz yol."""
    raise NotImplementedError


def circle_arc(radius: float, angle: float, ds: float = 0.1) -> RefPath:
    """Orijinden +x yönünde başlayan, sola dönen yay (angle radyan)."""
    raise NotImplementedError


def s_curve(radius: float = 50.0, ds: float = 0.1, lead_in: float = 20.0) -> RefPath:
    """lead_in m düz + radius yarıçaplı 90° sola + 90° sağa + lead_in m düz.

    Eğrilik süreksiz değişir (0 → +1/R → -1/R → 0); kontrolcüler için kasıtlı zor durum.
    """
    raise NotImplementedError


def nearest_index(path: RefPath, x: float, y: float) -> int:
    """(x, y)'ye en yakın yol noktasının indisi."""
    raise NotImplementedError


def cross_track_error(path: RefPath, x: float, y: float) -> float:
    """İşaretli yanal hata: yol yönüne göre solda pozitif."""
    raise NotImplementedError
