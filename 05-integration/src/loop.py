"""Kapalı çevrim: araç → sentetik algı → (takip) → kontrol → araç."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from bicycle import VehicleParams, step
from lane_keeping import LaneTracker, lane_keep_steer
from paths import cross_track_error, nearest_index
from perception_sim import NoiseMemory, measure_lane

# Takip katmanının süreç gürültüsü (q_y, q_psi, q_kappa). Gerekçe: notes.md
TRACKER_Q: tuple[float, float, float] = (0.01, 1e-4, 1e-3)


@dataclass
class IntegrationResult:
    t: np.ndarray
    states: np.ndarray
    steer: np.ndarray
    cte: np.ndarray        # GERÇEK yanal hata (ölçülen değil)
    measured: list = field(default_factory=list)     # her adımdaki z (veya None)
    estimate: np.ndarray | None = None               # takip çıktısı (use_tracker=False ise kullanılan değer)


def run(path, v: float, noise, p_drop: float, use_tracker: bool = True,
        use_feedforward: bool = True, seed: int = 0,
        dt: float = 0.05, params: VehicleParams = VehicleParams(),
        tracker_q: tuple[float, float, float] = TRACKER_Q,
        steer_delay: float = 0.0, steer_tau: float = 0.0) -> IntegrationResult:
    """dt = kamera periyodu (20 Hz). Araç modeli 01'deki step ile ilerletilir.

    use_tracker=False: ölçüm doğrudan kontrolcüye gider; ölçüm yoksa son ölçüm tutulur.
    Hız sabit kabul edilebilir (boylamsal kontrol bu modülün konusu değil).

    Direksiyon aktüatörü (isteğe bağlı, varsayılan ideal): komut `steer_delay` saniye saf gecikmeyle ve
    `steer_tau` zaman sabitli birinci derece gecikmeyle tekerleğe geçer. Autoware'in MPC ayarları
    0,24 s ve 0,27 s kullanıyor (mpc.param.yaml; 00 notları). `steer` kaydı komutu, araç uygulananı görür.
    Takip katmanı tahminde komutu kullanır (gerçek açıyı bilmez).
    """
    rng = np.random.default_rng(seed)
    memory = NoiseMemory()        # ilişkili gürültü / kümeli kayıp için (LaneNoise.rho, burst_len)
    state = np.array([path.x[0], path.y[0], path.yaw[0], v])
    tracker = LaneTracker(params.wheelbase, noise, tracker_q)
    held = np.zeros(3)            # tracker'sız modda son geçerli ölçüm
    delta = 0.0
    n_delay = int(round(steer_delay / dt))
    cmd_queue = [0.0] * n_delay       # gecikme hattı
    applied = 0.0                     # tekerleğe geçen açı
    lag = 1.0 - np.exp(-dt / steer_tau) if steer_tau > 0 else 1.0
    end_idx = len(path.x) - 2
    n_max = int(round(2.0 * path.s[-1] / max(v, 0.1) / dt))

    ts, states, steers, ctes, zs, ests = [], [], [], [], [], []
    for k in range(n_max + 1):
        z = measure_lane(state, path, rng, noise, p_drop, memory)
        if use_tracker:
            est = tracker.step(z, v, delta, dt)
        else:
            if z is not None:
                held = z
            est = held
        delta = float(np.clip(
            lane_keep_steer(est[0], est[1], est[2], v, params.wheelbase, use_feedforward=use_feedforward),
            -params.max_steer, params.max_steer))

        ts.append(k * dt)
        states.append(state.copy())
        steers.append(delta)
        ctes.append(cross_track_error(path, state[0], state[1]))
        zs.append(z)
        ests.append(np.array(est, dtype=float))
        if nearest_index(path, state[0], state[1]) >= end_idx:
            break
        cmd_queue.append(delta)
        applied += lag * (cmd_queue.pop(0) - applied)
        state = step(state, 0.0, applied, dt, params)

    return IntegrationResult(t=np.array(ts), states=np.array(states), steer=np.array(steers),
                             cte=np.array(ctes), measured=zs, estimate=np.array(ests))
