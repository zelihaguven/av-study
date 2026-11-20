"""02 grafiklerini üretir (results/ altına) ve sayısal özeti yazdırır.

Çalıştırma (repo kökünden):  python 02-control/src/plots.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "common"), str(ROOT / "01-vehicle-model" / "src"), str(Path(__file__).parent)]

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from closed_loop import run_closed_loop
from metrics import max_abs, rms
from paths import nearest_index, s_curve, straight
from i18n import L, results_dir

RESULTS = results_dir(Path(__file__).resolve().parents[1] / "results")
R, V, DT, LEAD = 50.0, 10.0, 0.02, 20.0
PATH = s_curve(R)
SEGMENT_S = [LEAD, LEAD + R * np.pi / 2, LEAD + R * np.pi]   # eğriliğin sıçradığı s değerleri
COLORS = {"pure_pursuit": "tab:blue", "stanley": "tab:orange"}
LABELS = {"pure_pursuit": L("Pure Pursuit (Ld = max(3, 0,5·v) = 5 m)", "Pure Pursuit (Ld = max(3, 0.5·v) = 5 m)"), "stanley": "Stanley (k = 1, k_soft = 1)"}


def steer_rate(res) -> np.ndarray:
    return np.diff(res.steer) / DT


def segment_times(res) -> list[float]:
    """Arka aksın eğrilik sıçrama noktalarından geçtiği anlar."""
    s_car = np.array([PATH.s[nearest_index(PATH, x, y)] for x, y in res.states[:, :2]])
    return [float(res.t[np.argmax(s_car >= s)]) for s in SEGMENT_S]


def plot_paths(runs) -> None:
    fig, (ax, axz) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [1.2, 1]})
    for a in (ax, axz):
        a.plot(PATH.x, PATH.y, "k--", lw=1.5, label=L("Referans yol", "Reference path"))
        for c, r in runs.items():
            a.plot(r.states[:, 0], r.states[:, 1], color=COLORS[c], lw=1.5, label=LABELS[c])
        a.set_aspect("equal")
        a.grid(alpha=0.3)
        a.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_title(L(f"S-virajı, R = {R:.0f} m, v = {V:.0f} m/s", f"S-curve, R = {R:.0f} m, v = {V:.0f} m/s"))
    ax.legend(fontsize=8, loc="upper left")
    # Yakınlaştırma: sol virajın ortası, Pure Pursuit'un içeri kestiği yer
    i = nearest_index(PATH, *[PATH.x[np.argmin(np.abs(PATH.s - (LEAD + R * np.pi / 4)))],
                              PATH.y[np.argmin(np.abs(PATH.s - (LEAD + R * np.pi / 4)))]])
    cx, cy = PATH.x[i], PATH.y[i]
    axz.set_xlim(cx - 1.0, cx + 1.0)
    axz.set_ylim(cy - 1.0, cy + 1.0)
    axz.set_title(L("Yakınlaştırma: sol virajın ortası (2 m × 2 m)", "Zoom: middle of the left curve (2 m × 2 m)"))
    ax.add_patch(plt.Rectangle((cx - 4, cy - 4), 8, 8, fill=False, ec="gray"))
    fig.tight_layout()
    fig.savefig(RESULTS / "s_curve_paths.png", dpi=150)
    plt.close(fig)


def plot_cte(runs) -> None:
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    for c, r in runs.items():
        ax.plot(r.t, r.cte * 100, color=COLORS[c], label=LABELS[c])
        ax2.plot(r.t[1:], np.rad2deg(steer_rate(r)), color=COLORS[c])
    for a in (ax, ax2):
        for tb, name in zip(segment_times(runs["stanley"]), [L("düz→sol", "straight→left"), L("sol→sağ", "left→right"), L("sağ→düz", "right→straight")]):
            a.axvline(tb, color="gray", ls=":", lw=1)
            if a is ax:
                a.text(tb, 1.0, name, transform=a.get_xaxis_transform(), ha="center", va="bottom", fontsize=8)
        a.grid(alpha=0.3)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_ylabel(L("CTE [cm]  (sol +)", "CTE [cm]  (left +)"))
    ax.legend(fontsize=8)
    ax2.set_ylabel(L("Direksiyon hızı [°/s]", "Steering rate [°/s]"))
    ax2.set_xlabel("t [s]")
    fig.suptitle(L("S-virajında yanal hata ve direksiyon hızı (noktalı çizgiler: eğrilik sıçramaları)", "Cross-track error and steering rate on the S-curve (dotted lines: curvature jumps)"))
    fig.tight_layout()
    fig.savefig(RESULTS / "s_curve_cte.png", dpi=150)
    plt.close(fig)


def lookahead_sweep():
    lds = np.arange(2.0, 15.01, 0.5)
    out = {"ld": lds, "rms": [], "rate": []}
    for ld in lds:
        r = run_closed_loop(PATH, "pure_pursuit", V, dt=DT, lookahead=float(ld))
        out["rms"].append(rms(r.cte))
        out["rate"].append(np.rad2deg(max_abs(steer_rate(r))))
    # Hızla ölçeklenen Ld = k_v·v: aynı kural, farklı hızlar
    speeds = [5.0, 10.0, 15.0, 20.0]
    out["speeds"] = speeds
    out["fixed5"] = [rms(run_closed_loop(PATH, "pure_pursuit", v, dt=DT, lookahead=5.0).cte) for v in speeds]
    out["scaled"] = [rms(run_closed_loop(PATH, "pure_pursuit", v, dt=DT, k_v=0.5).cte) for v in speeds]
    out["fixed5_rate"] = [np.rad2deg(max_abs(steer_rate(run_closed_loop(
        straight(200.0), "pure_pursuit", v, y0_offset=1.0, dt=DT, T=10.0, lookahead=5.0)))) for v in speeds]
    out["scaled_rate"] = [np.rad2deg(max_abs(steer_rate(run_closed_loop(
        straight(200.0), "pure_pursuit", v, y0_offset=1.0, dt=DT, T=10.0, k_v=0.5)))) for v in speeds]

    fig, (ax, axb) = plt.subplots(1, 2, figsize=(12, 4.5))
    ax.plot(lds, np.array(out["rms"]) * 100, "o-", color="tab:blue", ms=4)
    ax.set_xlabel(L("İleri bakış mesafesi Ld [m]", "Lookahead distance Ld [m]"))
    ax.set_ylabel("RMS CTE [cm]", color="tab:blue")
    ax.grid(alpha=0.3)
    ax2 = ax.twinx()
    ax2.plot(lds, out["rate"], "s-", color="tab:red", ms=4)
    ax2.set_ylabel(L("Maks |direksiyon hızı| [°/s]", "Max |steering rate| [°/s]"), color="tab:red")
    ax.set_title(L(f"Pure Pursuit, S-virajı, v = {V:.0f} m/s: Ld taraması", f"Pure Pursuit, S-curve, v = {V:.0f} m/s: Ld sweep"))

    x = np.arange(len(speeds))
    axb.bar(x - 0.2, np.array(out["fixed5"]) * 100, 0.4, label=L("Sabit Ld = 5 m", "Fixed Ld = 5 m"))
    axb.bar(x + 0.2, np.array(out["scaled"]) * 100, 0.4, label=L("Ld = max(3, 0,5·v)", "Ld = max(3, 0.5·v)"))
    axb.set_xticks(x, [f"{v:.0f} m/s" for v in speeds])
    axb.set_ylabel(L("RMS CTE [cm], S-virajı", "RMS CTE [cm], S-curve"))
    axb.set_title(L("Sabit ve hızla ölçeklenen ileri bakış", "Fixed vs speed-scaled lookahead"))
    axb.legend(fontsize=8)
    axb.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(RESULTS / "lookahead_sweep.png", dpi=150)
    plt.close(fig)
    return out


def stanley_softening():
    """Düşük hızda (2 m/s) 1 m ofsetten toparlanma; k_soft'un etkisi."""
    v = 2.0
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    out = {}
    for ks, col in [(0.1, "tab:red"), (1.0, "tab:orange"), (5.0, "tab:green")]:
        r = run_closed_loop(straight(60.0), "stanley", v, y0_offset=1.0, dt=DT, T=15.0, k=1.0, k_soft=ks)
        out[ks] = (np.rad2deg(max_abs(r.steer)), np.rad2deg(max_abs(steer_rate(r))),
                   float(r.t[np.argmax(np.abs(r.cte) < 0.05)]))
        ax.plot(r.t, r.cte, color=col, label=f"k_soft = {ks}")
        ax2.plot(r.t, np.rad2deg(r.steer), color=col)
    ax2.axhline(-35, color="k", ls=":", lw=1)
    ax2.text(14.8, -34, L("direksiyon sınırı −35°", "steering limit −35°"), ha="right", va="bottom", fontsize=8)
    ax.set_ylabel("CTE [m]")
    ax.legend(fontsize=8)
    ax2.set_ylabel(L("Direksiyon [°]", "Steering [°]"))
    ax2.set_xlabel("t [s]")
    for a in (ax, ax2):
        a.grid(alpha=0.3)
    fig.suptitle(L(f"Stanley, v = {v:.0f} m/s, 1 m sol ofset, k = 1: yumuşatma terimi k_soft", f"Stanley, v = {v:.0f} m/s, 1 m left offset, k = 1: softening term k_soft"))
    fig.tight_layout()
    fig.savefig(RESULTS / "stanley_soft.png", dpi=150)
    plt.close(fig)
    return out


if __name__ == "__main__":
    RESULTS.mkdir(exist_ok=True)
    runs = {c: run_closed_loop(PATH, c, V, dt=DT) for c in ("pure_pursuit", "stanley")}
    plot_paths(runs)
    plot_cte(runs)
    print("S-virajı (R = 50 m, v = 10 m/s):")
    for c, r in runs.items():
        cte_left = r.cte[(r.t > segment_times(r)[0] + 3) & (r.t < segment_times(r)[1])]
        print(f"  {c:13s} RMS {rms(r.cte)*100:5.1f} cm  maks {max_abs(r.cte)*100:5.1f} cm  "
              f"sol viraj ort. {np.mean(cte_left)*100:+5.1f} cm  maks dir. hızı {np.rad2deg(max_abs(steer_rate(r))):5.1f} °/s")
    sw = lookahead_sweep()
    print("Ld taraması (Ld, RMS cm, maks dir. hızı °/s):")
    for ld, a, b in zip(sw["ld"], sw["rms"], sw["rate"]):
        if ld in (2.0, 3.0, 5.0, 8.0, 10.0, 15.0):
            print(f"  {ld:5.1f}  {a*100:6.1f}  {b:6.1f}")
    print("Sabit Ld = 5 m ve Ld = 0,5·v (hız, RMS cm sabit/ölçekli, ofset dir. hızı °/s sabit/ölçekli):")
    for v, a, b, c, d in zip(sw["speeds"], sw["fixed5"], sw["scaled"], sw["fixed5_rate"], sw["scaled_rate"]):
        print(f"  {v:4.0f}  {a*100:6.1f} / {b*100:6.1f}   {c:6.1f} / {d:6.1f}")
    print("Stanley v = 2 m/s (k_soft: maks |dir.| °, maks dir. hızı °/s, |CTE|<5 cm süresi s):")
    for ks, (a, b, c) in stanley_softening().items():
        print(f"  {ks:4.1f}  {a:5.1f}  {b:6.1f}  {c:5.2f}")
