"""Kapalı çevrim: araç → sentetik algı → (takip) → kontrol → araç."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class IntegrationResult:
    t: np.ndarray
    states: np.ndarray
    steer: np.ndarray
    cte: np.ndarray        # GERÇEK yanal hata (ölçülen değil)


def run(path, v: float, noise, p_drop: float, use_tracker: bool = True,
        use_feedforward: bool = True, seed: int = 0,
        dt: float = 0.05) -> IntegrationResult:
    """dt = kamera periyodu (20 Hz). Araç modeli 01'deki step ile ilerletilir.

    use_tracker=False: ölçüm doğrudan kontrolcüye gider; ölçüm yoksa son ölçüm tutulur.
    Hız sabit kabul edilebilir (boylamsal kontrol bu modülün konusu değil).
    """
    raise NotImplementedError
