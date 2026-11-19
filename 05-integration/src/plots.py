"""05 grafiklerini üretir (results/ altına) ve sayısal özeti yazdırır.

Senaryo testlerle aynı: S-virajı R = 50 m, v = 10 m/s, 20 Hz sentetik algı, LaneNoise varsayılanları.
Çalıştırma (repo kökünden):  python 05-integration/src/plots.py
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
NOISE = LaneNoise()
SEEDS = range(20)


def steer_rate(r):
    return np.diff(r.steer) / np.diff(r.t)


def plot_closed_loop():
    a = run(PATH, V, NOISE, p_drop=0.1, use_tracker=True, seed=0)
    b = run(PATH, V, NOISE, p_drop=0.1, use_tracker=False, seed=0)
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    zt = np.array([np.nan if z is None else z[0] for z in a.measured])
    axes[0].plot(a.t, zt, ".", color="0.7", ms=3, label="Ölçülen e_y (σ = 0,3 m, %10 kayıp)")
    axes[0].plot(a.t, a.estimate[:, 0], color="tab:blue", lw=1.2, label="Takip çıktısı e_y")
    axes[0].plot(a.t, a.cte, "k", lw=1.2, label="Gerçek e_y")
    axes[0].set_ylabel("e_y [m]")
    axes[0].set_title("Takipli koşu: ölçüm, kestirim, gerçek", fontsize=10, loc="left")
    axes[1].plot(b.t, b.cte, color="tab:red", lw=1.2, label=f"Takipsiz, RMS {rms(b.cte)*100:.1f} cm")
    axes[1].plot(a.t, a.cte, color="tab:blue", lw=1.2, label=f"Takipli, RMS {rms(a.cte)*100:.1f} cm")
    axes[1].set_ylabel("Gerçek CTE [m]")
    axes[1].set_title("Aracın gerçek yanal hatası", fontsize=10, loc="left")
    axes[2].plot(b.t, np.rad2deg(b.steer), color="tab:red", lw=0.8,
                 label=f"Takipsiz, dir. hızı RMS {np.rad2deg(rms(steer_rate(b))):.0f} °/s")
    axes[2].plot(a.t, np.rad2deg(a.steer), color="tab:blue", lw=1.5,
                 label=f"Takipli, dir. hızı RMS {np.rad2deg(rms(steer_rate(a))):.0f} °/s")
    axes[2].set_ylabel("Direksiyon [°]")
    axes[2].set_xlabel("t [s]")
    axes[2].set_title("Direksiyon komutu", fontsize=10, loc="left")
    for ax in axes:
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8, loc="upper right")
    fig.suptitle("Mini VisionPilot: S-virajı, 10 m/s, aynı gürültü dizisi (seed 0)")
    fig.tight_layout()
    fig.savefig(RESULTS / "closed_loop.png", dpi=150)
    plt.close(fig)
    return a, b


def dropout_sweep():
    ps = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9]
    out = {}
    for tr in (True, False):
        mx, rate = [], []
        for p in ps:
            runs = [run(PATH, V, NOISE, p_drop=p, use_tracker=tr, seed=s) for s in SEEDS]
            mx.append([max_abs(r.cte) for r in runs])
            rate.append(np.mean([np.rad2deg(rms(steer_rate(r))) for r in runs]))
        out[tr] = (np.array(mx), np.array(rate))
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    for tr, col, name in [(True, "tab:blue", "Takipli"), (False, "tab:red", "Takipsiz (son ölçümü tut)")]:
        mx, rate = out[tr]
        med = np.median(mx, axis=1)
        ax.plot(ps, med, "o-", color=col, label=f"{name}, medyan")
        ax.fill_between(ps, mx.min(axis=1), mx.max(axis=1), color=col, alpha=0.15, label=f"{name}, 20 koşu min–maks")
        ax2.plot(ps, rate, "o-", color=col, label=name)
    ax.axhline(0.75, color="k", ls=":", lw=1)
    ax.text(0.01, 0.78, "test eşiği (p = 0,3'te) 0,75 m", fontsize=8, va="bottom")
    ax.set_yscale("log")
    ax.set_xlabel("Algı kayıp oranı p_drop")
    ax.set_ylabel("Maks |CTE| [m] (log)")
    ax.set_title("Kayıp oranı ve en büyük sapma")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)
    ax2.set_xlabel("Algı kayıp oranı p_drop")
    ax2.set_ylabel("Direksiyon hızı RMS [°/s]")
    ax2.set_title("Kayıp oranı ve direksiyon pürüzlülüğü")
    ax2.legend(fontsize=8)
    ax2.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(RESULTS / "dropout_sweep.png", dpi=150)
    plt.close(fig)
    return ps, out


def ff_ablation():
    a = run(PATH, V, NOISE, p_drop=0.1, use_feedforward=True, seed=2)
    b = run(PATH, V, NOISE, p_drop=0.1, use_feedforward=False, seed=2)
    nf = LaneNoise(1e-9, 1e-9, 1e-9)       # gürültüsüz: sadece feedforward'ın etkisi
    c = run(PATH, V, nf, p_drop=0.0, use_feedforward=True)
    d = run(PATH, V, nf, p_drop=0.0, use_feedforward=False)
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    ax.plot(d.t, d.cte * 100, color="tab:red", label=f"Feedforward kapalı, RMS {rms(d.cte)*100:.1f} cm")
    ax.plot(c.t, c.cte * 100, color="tab:green", label=f"Feedforward açık, RMS {rms(c.cte)*100:.1f} cm")
    ax.set_title("Gürültüsüz algı: yalnız kontrol yapısının etkisi", fontsize=10, loc="left")
    ax2.plot(b.t, b.cte * 100, color="tab:red", label=f"Feedforward kapalı, RMS {rms(b.cte)*100:.1f} cm")
    ax2.plot(a.t, a.cte * 100, color="tab:green", label=f"Feedforward açık, RMS {rms(a.cte)*100:.1f} cm")
    ax2.set_title("Gürültülü algı (%10 kayıp, seed 2), takip açık", fontsize=10, loc="left")
    ax2.set_xlabel("t [s]")
    for x in (ax, ax2):
        x.set_ylabel("Gerçek CTE [cm]")
        x.axhline(0, color="k", lw=0.8)
        x.grid(alpha=0.3)
        x.legend(fontsize=8, loc="upper left")
    fig.suptitle("Eğrilik feedforward'ı açık / kapalı, S-virajı 10 m/s")
    fig.tight_layout()
    fig.savefig(RESULTS / "ff_ablation.png", dpi=150)
    plt.close(fig)
    return a, b, c, d


if __name__ == "__main__":
    RESULTS.mkdir(exist_ok=True)
    a, b = plot_closed_loop()
    print("Seed 0, %10 kayıp:")
    for name, r in [("takipli", a), ("takipsiz", b)]:
        print(f"  {name:9s} gerçek CTE RMS {rms(r.cte)*100:5.1f} cm, maks {max_abs(r.cte)*100:5.1f} cm, "
              f"dir. hızı RMS {np.rad2deg(rms(steer_rate(r))):6.1f} °/s, kontrolcünün gördüğü e_y hatası RMS "
              f"{rms(r.estimate[:, 0] - r.cte)*100:5.1f} cm")
    ps, out = dropout_sweep()
    print("Kayıp taraması, 20 koşu (p, takipli medyan/maks maks|CTE| m, takipsiz medyan/maks, dir. hızı RMS takipli/takipsiz °/s):")
    for i, p in enumerate(ps):
        t_mx, t_r = out[True][0][i], out[True][1][i]
        n_mx, n_r = out[False][0][i], out[False][1][i]
        print(f"  {p:4.1f}  {np.median(t_mx):5.2f}/{t_mx.max():5.2f}   {np.median(n_mx):5.2f}/{n_mx.max():5.2f}   "
              f"{t_r:6.1f}/{n_r:6.1f}")
    a, b, c, d = ff_ablation()
    print(f"Feedforward: gürültüsüz RMS açık {rms(c.cte)*100:.1f} / kapalı {rms(d.cte)*100:.1f} cm, "
          f"maks {max_abs(c.cte)*100:.1f} / {max_abs(d.cte)*100:.1f} cm; "
          f"gürültülü RMS {rms(a.cte)*100:.1f} / {rms(b.cte)*100:.1f} cm")
