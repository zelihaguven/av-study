"""run_video.py'nin CSV çıktılarından 05 için gürültü ve kayıp kestirimi, süre tablosu ve results/noise.png.

Yöntem: Gerçek e_y bilinmiyor (videoda ölçüm yok). İnsan sürücü şeritte yavaş salınır, model gürültüsü
ise kareden kareye değişir. Bu yüzden gerçek değerin yerine 1 s'lik merkezli hareketli ortalama alınır,
kalan (ölçüm − ortalama) gürültü kabul edilir. Bu yöntem 1 s'den yavaş hataları (kalibrasyon sapması,
sistematik hata) GÖREMEZ; yalnız kareden kareye titreşimi ölçer.

Çalıştırma (repo kökünden):  python 04-perception/src/analyze.py
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RESULTS = Path(__file__).resolve().parents[1] / "results"
VIDEOS = ["project_video", "challenge_video", "harder_challenge_video"]
WIN_S = 1.0


def load(name: str) -> dict[str, np.ndarray]:
    with open(RESULTS / f"{name}.csv") as f:
        rows = list(csv.DictReader(f))
    out = {}
    for k in rows[0]:
        if k == "reason":
            out[k] = np.array([r[k] for r in rows])
            continue
        try:
            out[k] = np.array([float(r[k]) if r[k] != "" else np.nan for r in rows])
        except ValueError:
            out[k] = np.array([r[k] for r in rows])
    return out


def smooth_residual(t: np.ndarray, x: np.ndarray, valid: np.ndarray, win_s: float = WIN_S):
    """Geçerli karelerde merkezli hareketli ortalama ve kalan. Geçersiz kareler NaN."""
    fps = 1.0 / np.median(np.diff(t))
    half = int(round(win_s * fps / 2))
    xs = np.where(valid, x, np.nan)
    sm = np.full_like(xs, np.nan)
    for i in range(len(xs)):
        seg = xs[max(0, i - half): i + half + 1]
        if np.sum(~np.isnan(seg)) >= half:          # pencerenin en az yarısı dolu olsun
            sm[i] = np.nanmean(seg)
    return sm, xs - sm


def longest_run(mask: np.ndarray) -> int:
    best = cur = 0
    for m in mask:
        cur = cur + 1 if m else 0
        best = max(best, cur)
    return best


def lag1(r: np.ndarray) -> float:
    r = r[~np.isnan(r)]
    r = r - r.mean()
    return float(np.dot(r[:-1], r[1:]) / np.dot(r, r))


def main() -> None:
    stats = {}
    for name in VIDEOS:
        d = load(name)
        valid = d["valid"] > 0
        s = {"frames": len(valid), "valid": valid.mean(), "longest_gap": longest_run(~valid),
             "fps": 1.0 / np.median(np.diff(d["t"]))}
        for key, scale in [("e_y", 1.0), ("e_psi", np.rad2deg(1.0)), ("kappa", 1.0)]:
            sm, res = smooth_residual(d["t"], d[key], valid)
            s[key + "_std"] = float(np.nanstd(res) * scale)
            s[key + "_lag1"] = lag1(res)
            s[key + "_sm"], s[key + "_res"] = sm, res
        s["reasons"] = {r: int(np.sum(d["reason"] == r)) for r in set(d["reason"]) if r}
        for m in ("ms_pre", "ms_steer", "ms_speed", "ms_drive"):
            s[m] = float(np.nanmedian(d[m]))
        s["data"] = d
        stats[name] = s

    print("Gürültü (1 s hareketli ortalamaya göre kalan std) ve kayıp:")
    print(f"{'video':24s} {'kare':>5s} {'geçerli':>8s} {'en uzun':>8s} {'σ e_y':>7s} {'ρ1':>5s} "
          f"{'σ e_ψ':>7s} {'σ κ':>8s}")
    for name, s in stats.items():
        print(f"{name:24s} {s['frames']:5d} {100 * s['valid']:7.1f}% {s['longest_gap']:5d} kr "
              f"{s['e_y_std']:6.3f}m {s['e_y_lag1']:5.2f} {s['e_psi_std']:6.2f}° {s['kappa_std']:8.5f}  {s['reasons']}")
    print("Medyan süre [ms]: ön işleme / AutoSteer / AutoSpeed / AutoDrive")
    for name, s in stats.items():
        print(f"  {name:24s} {s['ms_pre']:5.1f} / {s['ms_steer']:5.1f} / {s['ms_speed']:5.1f} / {s['ms_drive']:5.1f}")

    # Grafik: proje videosu e_y, e_psi zaman serisi + kalan histogramı
    fig, axes = plt.subplots(3, 2, figsize=(12, 8), gridspec_kw={"width_ratios": [3, 1]})
    for row, name in enumerate(VIDEOS):
        s, d = stats[name], stats[name]["data"]
        ax, axh = axes[row]
        valid = d["valid"] > 0
        ax.plot(d["t"], np.where(valid, d["e_y"], np.nan), ".", ms=2, color="0.6", label="AutoSteer e_y (kare)")
        ax.plot(d["t"], s["e_y_sm"], color="tab:blue", lw=1.5, label="1 s ortalama")
        bad = ~valid
        if bad.any():
            ax.plot(d["t"][bad], np.zeros(bad.sum()), "|", color="tab:red", ms=10, label="şerit yok")
        ax.set_ylabel("e_y [m]")
        ax.set_title(f"{name}: geçerli %{100 * s['valid']:.1f}, en uzun kesinti {s['longest_gap']} kare",
                     fontsize=9, loc="left")
        ax.grid(alpha=0.3)
        r = s["e_y_res"][~np.isnan(s["e_y_res"])]
        axh.hist(r * 100, bins=40, color="tab:blue", alpha=0.7)
        axh.set_title(f"kalan σ = {100 * s['e_y_std']:.1f} cm, ρ₁ = {s['e_y_lag1']:.2f}", fontsize=9)
        axh.set_xlabel("e_y − ortalama [cm]")
        axh.grid(alpha=0.3)
    axes[0, 0].legend(fontsize=8, loc="upper right", ncol=3)
    axes[-1, 0].set_xlabel("t [s]")
    fig.suptitle("AutoSteer → e_y titreşimi, Udacity videoları (25 fps)")
    fig.tight_layout()
    fig.savefig(RESULTS / "noise.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
