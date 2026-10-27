"""01 araç modeli + 02 kontrolcüleri ile kapalı çevrim simülasyon."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class LoopResult:
    t: np.ndarray        # (N,)
    states: np.ndarray   # (N, 4)
    steer: np.ndarray    # (N,)
    cte: np.ndarray      # (N,), common.paths.cross_track_error


def run_closed_loop(path, controller: str, v_ref: float,
                    y0_offset: float = 0.0, dt: float = 0.02,
                    T: float | None = None) -> LoopResult:
    """controller ∈ {"pure_pursuit", "stanley"}.

    - Araç yolun başında, yol yönünde, y0_offset kadar sola kaydırılmış ve v_ref hızında başlar.
    - Hız PID ile v_ref'te tutulur.
    - T None ise yolun sonuna ulaşınca (en yakın indeks son noktaya yakınsa) durur.
    """
    raise NotImplementedError
