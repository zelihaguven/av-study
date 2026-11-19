"""Sentetik şerit algısı: gerçek durumdan gürültülü ve aralıklı ölçüm üretir."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from paths import cross_track_error, nearest_index


@dataclass(frozen=True)
class LaneNoise:
    sigma_y: float = 0.3                       # [m]
    sigma_psi: float = float(np.deg2rad(3.0))  # [rad]
    sigma_kappa: float = 0.005                 # [1/m]
    # İsteğe bağlı gürültü yapısı (04'teki ölçümlerden). Varsayılanlar eski davranışı birebir korur.
    rho: float = 0.0                           # AR(1) katsayısı, kare başına: n_k = ρ n_{k−1} + √(1−ρ²) w_k
    burst_len: float | None = None             # None: bağımsız kayıp. Sayı: ortalama kesinti uzunluğu [kare]


@dataclass
class NoiseMemory:
    """AR(1) gürültüsü ve kümeli kayıp için kareler arası durum. Her koşuda yeni bir tane."""
    n: np.ndarray | None = None
    dropped: bool = False
    extra: dict = field(default_factory=dict)


def _wrap(a: float) -> float:
    return float((a + np.pi) % (2 * np.pi) - np.pi)


def true_lane_state(state: np.ndarray, path) -> np.ndarray:
    """Gürültüsüz [e_y, e_psi, kappa], arka aks referanslı."""
    x, y, yaw = state[0], state[1], state[2]
    i = nearest_index(path, x, y)
    return np.array([cross_track_error(path, x, y), _wrap(yaw - path.yaw[i]), path.kappa[i]])


def _drop_prob(p_drop: float, noise: LaneNoise, mem: NoiseMemory | None) -> float:
    """Bu karenin kayıp olma olasılığı.

    Kümeli kayıp: iki durumlu Markov zinciri (Gilbert modeli). Kayıptayken kalma olasılığı 1 − 1/L
    (ortalama kesinti L kare); kayıp yokken kayba girme olasılığı, uzun dönem kayıp oranı p_drop olacak
    şekilde seçilir: p_in = p/(1−p) · 1/L. Böylece aynı p_drop ile bağımsız ve kümeli kayıp karşılaştırılabilir.
    """
    if noise.burst_len is None or mem is None:
        return p_drop
    L = max(noise.burst_len, 1.0)
    if mem.dropped:
        return 1.0 - 1.0 / L
    return min(1.0, p_drop / max(1e-9, 1.0 - p_drop) / L)


def measure_lane(state: np.ndarray, path, rng: np.random.Generator,
                 noise: LaneNoise, p_drop: float,
                 memory: NoiseMemory | None = None) -> np.ndarray | None:
    """p_drop olasılıkla None, değilse [e_y, e_psi, kappa] + gürültü.

    e_y: common.paths.cross_track_error; e_psi: wrap(yaw - path.yaw[i]);
    kappa: path.kappa[i] (i en yakın indeks).
    memory verilirse ve noise.rho > 0 veya noise.burst_len ayarlıysa gürültü kareler arası ilişkili olur.
    """
    # Rastgele sayılar kayıp olsun olmasın aynı sırayla çekilir: böylece aynı tohumla
    # farklı p_drop değerleri aynı gürültü dizisini paylaşır (karşılaştırmalar adil olur).
    dropped = rng.random() < _drop_prob(p_drop, noise, memory)
    w = rng.normal(0.0, 1.0, 3)
    if memory is not None:
        if memory.n is None or noise.rho == 0.0:
            unit = w
        else:
            # Durağan AR(1): varyans her karede 1 kalır, böylece σ'lar anlamını korur.
            unit = noise.rho * memory.n + np.sqrt(1.0 - noise.rho ** 2) * w
        memory.n = unit
        memory.dropped = dropped
    else:
        unit = w
    n = unit * np.array([noise.sigma_y, noise.sigma_psi, noise.sigma_kappa])
    if dropped:
        return None
    return true_lane_state(state, path) + n
