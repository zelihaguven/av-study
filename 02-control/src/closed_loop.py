"""01 araç modeli + 02 kontrolcüleri ile kapalı çevrim simülasyon."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from bicycle import VehicleParams, step
from controllers import PID, SPEED_PID_GAINS, pure_pursuit, stanley
from paths import cross_track_error, nearest_index


@dataclass
class LoopResult:
    t: np.ndarray        # (N,)
    states: np.ndarray   # (N, 4)
    steer: np.ndarray    # (N,)
    cte: np.ndarray      # (N,), common.paths.cross_track_error


def run_closed_loop(path, controller: str, v_ref: float,
                    y0_offset: float = 0.0, dt: float = 0.02,
                    T: float | None = None, params: VehicleParams = VehicleParams(),
                    **ctrl_kwargs) -> LoopResult:
    """controller ∈ {"pure_pursuit", "stanley"}.

    - Araç yolun başında, yol yönünde, y0_offset kadar sola kaydırılmış ve v_ref hızında başlar.
    - Hız PID ile v_ref'te tutulur.
    - T None ise yolun sonuna ulaşınca (en yakın indeks son noktaya yakınsa) durur.
    - ctrl_kwargs kontrolcüye aynen geçer (ör. lookahead=8.0 veya k=2.0); deneyler için.
    """
    if controller == "pure_pursuit":
        def ctrl(s):
            return pure_pursuit(s, path, params.wheelbase, **ctrl_kwargs)
    elif controller == "stanley":
        def ctrl(s):
            return stanley(s, path, params.wheelbase, **ctrl_kwargs)
    else:
        raise ValueError(f"bilinmeyen kontrolcü: {controller!r}")

    yaw0 = path.yaw[0]
    state = np.array([path.x[0] - y0_offset * np.sin(yaw0),
                      path.y[0] + y0_offset * np.cos(yaw0), yaw0, v_ref])
    pid = PID(*SPEED_PID_GAINS, out_min=-params.max_accel, out_max=params.max_accel)

    # T yoksa güvenlik sınırı: yolu v_ref ile iki kez gidecek kadar süre
    t_max = T if T is not None else 2.0 * path.s[-1] / max(v_ref, 0.1)
    n_max = int(round(t_max / dt))
    end_idx = len(path.x) - 2

    ts, states, steers, ctes = [], [], [], []
    for k in range(n_max + 1):
        delta = float(np.clip(ctrl(state), -params.max_steer, params.max_steer))
        ts.append(k * dt)
        states.append(state.copy())
        steers.append(delta)
        ctes.append(cross_track_error(path, state[0], state[1]))
        if T is None and nearest_index(path, state[0], state[1]) >= end_idx:
            break
        accel = pid.update(v_ref - state[3], dt)
        state = step(state, accel, delta, dt, params)

    return LoopResult(t=np.array(ts), states=np.array(states),
                      steer=np.array(steers), cte=np.array(ctes))
