"""Gürültünün YAPISI kapalı çevrimi nasıl etkiliyor? (04'te ölçülen: ρ₁ ≈ 0,7, kümeli kayıp)

1. AR(1) korelasyonu ρ taraması: aynı σ, farklı ρ.
2. Kümeli kayıp: aynı ortalama kayıp oranı, farklı ortalama kesinti uzunluğu.
3. 04'ten "gerçekçi" senaryo özeti.

Çalıştırma (repo kökünden):  python 05-integration/src/noise_structure.py   (~1 dk)
"""
import sys
from dataclasses import replace
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
from i18n import L, results_dir

RESULTS = results_dir(Path(__file__).resolve().parents[1] / "results")
PATH = s_curve(50.0)
V = 10.0
SEEDS = range(12)


def steer_rate(r):
    return np.rad2deg(rms(np.diff(r.steer) / np.diff(r.t)))


def stats(noise, p_drop, tracker):
    rs = [run(PATH, V, noise, p_drop=p_drop, use_tracker=tracker, seed=s) for s in SEEDS]
    return {"rms": np.mean([rms(r.cte) for r in rs]),
            "max_med": np.median([max_abs(r.cte) for r in rs]),
            "max_worst": np.max([max_abs(r.cte) for r in rs]),
            "rate": np.mean([steer_rate(r) for r in rs]),
            "seen": np.mean([rms(r.estimate[:, 0] - r.cte) for r in rs])}


def main():
    RESULTS.mkdir(exist_ok=True)
    base = LaneNoise()
    rhos = [0.0, 0.3, 0.6, 0.8, 0.9, 0.95]
    rho_res = {tr: [stats(replace(base, rho=r), 0.1, tr) for r in rhos] for tr in (True, False)}

    bursts = [None, 2.0, 5.0, 10.0, 20.0]
    P_B = 0.3
    burst_res = {tr: [stats(replace(base, burst_len=b), P_B, tr) for b in bursts] for tr in (True, False)}

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    ax = axes[0]
    for tr, col, name in [(True, "tab:blue", L("Takipli", "With tracker")), (False, "tab:red", L("Takipsiz", "No tracker"))]:
        ax.plot(rhos, [s["rms"] * 100 for s in rho_res[tr]], "o-", color=col, label=L(f"{name}: gerçek CTE", f"{name}: true CTE"))
        ax.plot(rhos, [s["seen"] * 100 for s in rho_res[tr]], "s--", color=col, alpha=0.6,
                label=L(f"{name}: kontrolcünün gördüğü e_y hatası", f"{name}: e_y error seen by controller"))
    ax.set_xlabel(L("Gürültü korelasyonu ρ (kare başına, 20 Hz)", "Noise correlation ρ (per frame, 20 Hz)"))
    ax.set_ylabel("RMS [cm]")
    ax.set_title(L("Aynı σ = 0,3 m, artan korelasyon", "Same σ = 0.3 m, increasing correlation"))
    ax.axvspan(0.55, 0.65, color="tab:green", alpha=0.15)
    ax.text(0.6, 0.02, L("04'te\nölçülen", "measured\nin 04"), transform=ax.get_xaxis_transform(), ha="center", fontsize=8)
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)

    ax = axes[1]
    for tr, col, name in [(True, "tab:blue", L("Takipli", "With tracker")), (False, "tab:red", L("Takipsiz", "No tracker"))]:
        ax.plot(rhos, [s["rate"] for s in rho_res[tr]], "o-", color=col, label=name)
    ax.set_xlabel(L("Gürültü korelasyonu ρ", "Noise correlation ρ"))
    ax.set_ylabel(L("Direksiyon hızı RMS [°/s]", "Steering rate RMS [°/s]"))
    ax.set_title(L("Korelasyon ve direksiyon pürüzlülüğü", "Correlation and steering roughness"))
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    ax = axes[2]
    xl = [L("bağımsız", "independent")] + [f"{b:.0f}" for b in bursts[1:]]
    x = np.arange(len(bursts))
    for off, tr, col, name in [(-0.2, True, "tab:blue", L("Takipli", "With tracker")), (0.2, False, "tab:red", L("Takipsiz", "No tracker"))]:
        med = [s["max_med"] for s in burst_res[tr]]
        worst = [s["max_worst"] for s in burst_res[tr]]
        ax.bar(x + off, med, 0.4, color=col, alpha=0.8, label=L(f"{name}: medyan", f"{name}: median"))
        ax.scatter(x + off, worst, color=col, marker="v", zorder=3, label=L(f"{name}: en kötü", f"{name}: worst"))
    ax.set_xticks(x, xl)
    ax.set_yscale("log")
    ax.set_xlabel(L(f"Ortalama kesinti uzunluğu [kare], kayıp oranı hep %{P_B * 100:.0f}", f"Mean gap length [frames], dropout rate always {P_B * 100:.0f}%"))
    ax.set_ylabel("Maks |CTE| [m] (log)")
    ax.set_title(L("Aynı kayıp oranı, farklı kümelenme", "Same dropout rate, different clustering"))
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3, axis="y")
    fig.suptitle(L("Gürültünün yapısı: S-virajı 10 m/s, 12 koşu", "Noise structure: S-curve 10 m/s, 12 runs"))
    fig.tight_layout()
    fig.savefig(RESULTS / "noise_structure.png", dpi=150)
    plt.close(fig)

    print("ρ taraması (σ varsayılan, %10 bağımsız kayıp):  ρ | takipli RMS, gördüğü, dir.hızı | takipsiz RMS, gördüğü, dir.hızı")
    for i, r in enumerate(rhos):
        a, b = rho_res[True][i], rho_res[False][i]
        print(f"  {r:4.2f} | {a['rms']*100:5.1f} cm {a['seen']*100:5.1f} cm {a['rate']:6.1f} °/s | "
              f"{b['rms']*100:5.1f} cm {b['seen']*100:5.1f} cm {b['rate']:6.1f} °/s")
    print(f"Kümelenme (kayıp %{P_B*100:.0f}): L | takipli maks medyan/en kötü | takipsiz maks medyan/en kötü")
    for i, b in enumerate(bursts):
        a, c = burst_res[True][i], burst_res[False][i]
        print(f"  {str(b):5s} | {a['max_med']:5.2f} / {a['max_worst']:5.2f} m | {c['max_med']:5.2f} / {c['max_worst']:5.2f} m")

    # 04'ten gerçekçi senaryolar (σ'lar MAD tabanlı, ρ 25 fps → 20 Hz: 0,66^(25/20) ≈ 0,6)
    print("04 senaryoları (12 koşu): takipli RMS / maks medyan / dir.hızı | takipsiz")
    for name, nz, pd in [
        ("otoyol, bağımsız", LaneNoise(0.024, np.deg2rad(0.26), 0.0003), 0.0),
        ("otoyol, ρ=0,6", LaneNoise(0.024, np.deg2rad(0.26), 0.0003, rho=0.6), 0.0),
        ("zor yol, ρ=0,6, kümeli", LaneNoise(0.034, np.deg2rad(0.95), 0.0035, rho=0.6, burst_len=3.0), 0.0025),
    ]:
        a, b = stats(nz, pd, True), stats(nz, pd, False)
        print(f"  {name:24s} {a['rms']*100:5.1f} cm / {a['max_med']*100:5.1f} cm / {a['rate']:5.1f} °/s | "
              f"{b['rms']*100:5.1f} cm / {b['max_med']*100:5.1f} cm / {b['rate']:5.1f} °/s")


if __name__ == "__main__":
    main()
