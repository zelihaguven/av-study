"""B8: direksiyon aktüatörü gecikmesi eklenince takipsiz sistem hâlâ "yanal hatada iyi" mi?

05 notları 1. soruda bir çıkarım yapıyordu: modelde direksiyon ideal olduğu için takipsiz sistem olduğundan iyi
görünüyor; gecikme eklenince yanal hatası da bozulur. Burada ölçülüyor. Aktüatör: 0,24 s saf gecikme + 0,27 s
birinci derece gecikme (Autoware mpc.param.yaml değerleri).

    python 05-integration/src/actuator_delay.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "common"), str(ROOT / "01-vehicle-model" / "src"),
                str(ROOT / "03-tracking" / "src"), str(Path(__file__).parent)]

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from loop import run
from metrics import max_abs, rms
from paths import s_curve
from perception_sim import LaneNoise

RESULTS = Path(__file__).resolve().parents[1] / "results"
PATH = s_curve(50.0)
V = 10.0
SEEDS = range(12)
ACTUATORS = {"ideal": (0.0, 0.0), "gecikme 0,24 s": (0.24, 0.0), "Autoware (0,24 s + τ 0,27 s)": (0.24, 0.27)}
SCENARIOS = {"05 varsayılanı (σ 0,3 m, %10 kayıp)": (LaneNoise(), 0.1),
             "04 otoyol (σ 2,4 cm, ρ 0,6)": (LaneNoise(0.024, np.deg2rad(0.26), 0.0003, rho=0.6), 0.0)}


def stats(noise, p_drop, tracker, delay, tau):
    rs = [run(PATH, V, noise, p_drop=p_drop, use_tracker=tracker, seed=s, steer_delay=delay, steer_tau=tau)
          for s in SEEDS]
    return (np.mean([rms(r.cte) for r in rs]), np.median([max_abs(r.cte) for r in rs]),
            np.mean([np.rad2deg(rms(np.diff(r.steer) / np.diff(r.t))) for r in rs]))


def main():
    table = {}
    for sc, (noise, pd) in SCENARIOS.items():
        for act, (d, tau) in ACTUATORS.items():
            for tr in (True, False):
                table[(sc, act, tr)] = stats(noise, pd, tr, d, tau)

    fig, axes = plt.subplots(1, len(SCENARIOS), figsize=(12, 4.5))
    x = np.arange(len(ACTUATORS))
    for ax, sc in zip(axes, SCENARIOS):
        for off, tr, col, name in [(-0.2, True, "tab:blue", "Takipli"), (0.2, False, "tab:red", "Takipsiz")]:
            vals = [table[(sc, a, tr)][0] * 100 for a in ACTUATORS]
            ax.bar(x + off, vals, 0.4, color=col, label=name)
            for xi, v in zip(x + off, vals):
                ax.text(xi, v, f"{v:.1f}", ha="center", va="bottom", fontsize=8)
        ax.set_xticks(x, [a.replace(" (", "\n(") for a in ACTUATORS], fontsize=8)
        ax.set_ylabel("RMS gerçek CTE [cm]")
        ax.set_title(sc, fontsize=10)
        ax.grid(alpha=0.3, axis="y")
        ax.legend(fontsize=8)
    fig.suptitle("Direksiyon aktüatörü gecikmesi: S-virajı 10 m/s, 12 koşu")
    fig.tight_layout()
    fig.savefig(RESULTS / "actuator_delay.png", dpi=150)
    plt.close(fig)

    for sc in SCENARIOS:
        print(f"== {sc}")
        for act in ACTUATORS:
            a, b = table[(sc, act, True)], table[(sc, act, False)]
            print(f"  {act:30s} takipli {a[0]*100:5.1f} / {a[1]*100:5.1f} cm / {a[2]:5.1f} °/s | "
                  f"takipsiz {b[0]*100:5.1f} / {b[1]*100:5.1f} cm / {b[2]:5.1f} °/s   (RMS / maks medyan / dir. hızı)")


if __name__ == "__main__":
    main()
