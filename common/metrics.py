"""Basit performans metrikleri."""
import numpy as np


def rms(values: np.ndarray) -> float:
    """Karekök ortalama kare: sqrt(mean(v^2))."""
    v = np.asarray(values, dtype=float)
    return float(np.sqrt(np.mean(v ** 2)))


def max_abs(values: np.ndarray) -> float:
    """En büyük mutlak değer."""
    return float(np.max(np.abs(np.asarray(values, dtype=float))))
