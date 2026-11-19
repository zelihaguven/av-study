"""01 grafiklerini üretir: results/circle.png ve results/dt_error.png.

Çalıştırma (repo kökünden):  python 01-vehicle-model/src/plots.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from bicycle import VehicleParams, simulate

P = VehicleParams()
RESULTS = Path(__file__).resolve().parents[1] / "results"
STEER = np.deg2rad(10.0)
V = 5.0
R = P.wheelbase / np.tan(STEER)


def one_lap(method: str, dt: float) -> np.ndarray:
    n = int(round(2 * np.pi * R / V / dt))
    return simulate(np.array([0.0, 0.0, 0.0, V]), np.zeros(n), np.full(n, STEER), dt, P, method)


def radius_error(method: str, dt: float) -> float:
    traj = one_lap(method, dt)
    r = np.linalg.norm(traj[:, :2] - np.array([0.0, R]), axis=1)
    return float(np.max(np.abs(r - R)) / R)


def plot_circle() -> None:
    th = np.linspace(0, 2 * np.pi, 400)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(R * np.sin(th), R - R * np.cos(th), "k--", lw=2, label=f"Teorik, R = L/tan δ = {R:.2f} m")
    for method, dt in [("euler", 0.1), ("rk4", 0.1)]:
        t = one_lap(method, dt)
        ax.plot(t[:, 0], t[:, 1], lw=1.5, label=f"{method.upper()}, dt = {dt} s")
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_title(f"Sabit direksiyon δ = 10°, v = {V} m/s, bir tur")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    fig.savefig(RESULTS / "circle.png", dpi=150)
    plt.close(fig)


def plot_dt_error() -> dict:
    dts = [0.001, 0.01, 0.05, 0.1]
    errs = {m: [radius_error(m, dt) for dt in dts] for m in ("euler", "rk4")}
    fig, ax = plt.subplots(figsize=(6, 4.5))
    for m, marker in [("euler", "o"), ("rk4", "s")]:
        ax.loglog(dts, errs[m], marker=marker, label=m.upper())
    ax.set_xlabel("dt [s]")
    ax.set_ylabel("Bağıl yarıçap hatası  max|r − R| / R")
    ax.set_title("Entegrasyon adımı ve hata (bir tam tur)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS / "dt_error.png", dpi=150)
    plt.close(fig)
    return {"dt": dts, **errs}


if __name__ == "__main__":
    RESULTS.mkdir(exist_ok=True)
    plot_circle()
    table = plot_dt_error()
    print(f"{'dt [s]':>8} {'Euler':>12} {'RK4':>12}")
    for i, dt in enumerate(table["dt"]):
        print(f"{dt:>8} {table['euler'][i]:>12.2e} {table['rk4'][i]:>12.2e}")
    print(f"Kaydedildi: {RESULTS / 'circle.png'}, {RESULTS / 'dt_error.png'}")
