"""03 grafiklerini üretir (results/ altına) ve sayısal özeti yazdırır.

Senaryo testlerdekiyle aynı: CIPO mesafesi, 20 Hz, gerçek ivme gürültüsü q = 0,5, ölçüm std 1 m.
Çalıştırma (repo kökünden):  python 03-tracking/src/plots.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from kalman import KalmanFilter, cv_model, nees

RESULTS = Path(__file__).resolve().parents[1] / "results"
DT, Q_TRUE, R_STD = 0.05, 0.5, 1.0
H = np.array([[1.0, 0.0]])
R = np.array([[R_STD ** 2]])
GAP = (200, 240)          # ölçüm kesintisi: 2 s, adım indisleri


def simulate(rng, n=400, gap=None):
    F, Q = cv_model(DT, Q_TRUE)
    x = np.array([40.0, -2.0])
    xs, zs = [], []
    for k in range(n):
        x = F @ x + rng.multivariate_normal(np.zeros(2), Q)
        xs.append(x.copy())
        lost = gap is not None and gap[0] <= k < gap[1]
        zs.append(None if lost else np.array([x[0] + rng.normal(0, R_STD)]))
    return np.array(xs), zs


def run(zs, q, x0=np.array([40.0, 0.0])):
    F, Q = cv_model(DT, q)
    kf = KalmanFilter(x0, np.diag([4.0, 4.0]))
    est, covs = [], []
    for z in zs:
        kf.predict(F, Q)
        kf.update(z, H, R)
        est.append(kf.x.copy())
        covs.append(kf.P.copy())
    return np.array(est), np.array(covs)


def rmse(a):
    return float(np.sqrt(np.mean(np.asarray(a) ** 2)))


def plot_cipo(xs, zs, est, covs):
    t = np.arange(len(xs)) * DT
    zt = np.array([np.nan if z is None else z[0] for z in zs])
    sd = np.sqrt(covs[:, 0, 0])
    sv = np.sqrt(covs[:, 1, 1])
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    ax.plot(t, zt, ".", color="0.6", ms=3, label="Ham ölçüm (σ = 1 m)")
    ax.fill_between(t, est[:, 0] - 2 * sd, est[:, 0] + 2 * sd, color="tab:blue", alpha=0.2, label="Filtre ±2σ")
    ax.plot(t, est[:, 0], color="tab:blue", lw=1.5, label="Kalman filtresi")
    ax.plot(t, xs[:, 0], "k", lw=1.2, label="Gerçek mesafe")
    ax2.plot(t, xs[:, 1], "k", lw=1.2, label="Gerçek göreli hız")
    ax2.fill_between(t, est[:, 1] - 2 * sv, est[:, 1] + 2 * sv, color="tab:blue", alpha=0.2)
    ax2.plot(t, est[:, 1], color="tab:blue", lw=1.5, label="Kestirim (hız hiç ölçülmüyor)")
    for a in (ax, ax2):
        a.axvspan(GAP[0] * DT, GAP[1] * DT, color="tab:red", alpha=0.08)
        a.grid(alpha=0.3)
    ax.text((GAP[0] + GAP[1]) / 2 * DT, 0.03, "ölçüm yok (2 s)", transform=ax.get_xaxis_transform(),
            ha="center", va="bottom", color="tab:red", fontsize=9)
    ax.set_ylabel("Mesafe d [m]")
    ax.legend(fontsize=8, loc="upper right", ncol=2)
    ax2.set_ylabel("ḋ [m/s]")
    ax2.set_xlabel("t [s]")
    ax2.legend(fontsize=8, loc="lower left")
    ax.set_title("CIPO takibi: sabit hız modeli, 20 Hz, q = 0,5 (filtre = gerçek)")
    fig.tight_layout()
    fig.savefig(RESULTS / "cipo.png", dpi=150)
    plt.close(fig)


def plot_q_sweep(xs, zs):
    t = np.arange(len(xs)) * DT
    qs = [0.005, 0.5, 50.0, 5000.0]
    fig, axes = plt.subplots(len(qs), 1, figsize=(10, 8), sharex=True, sharey=True)
    out = []
    for ax, q in zip(axes, qs):
        est, covs = run(zs, q)
        ok = [k for k in range(50, len(zs)) if zs[k] is not None]
        gap_err = float(np.max(np.abs(est[GAP[0]:GAP[1], 0] - xs[GAP[0]:GAP[1], 0])))
        out.append((q, rmse(est[ok, 0] - xs[ok, 0]), rmse(est[ok, 1] - xs[ok, 1]), gap_err))
        ax.plot(t, [np.nan if z is None else z[0] for z in zs], ".", color="0.7", ms=2)
        ax.plot(t, xs[:, 0], "k", lw=1)
        ax.plot(t, est[:, 0], color="tab:blue", lw=1.5)
        ax.axvspan(GAP[0] * DT, GAP[1] * DT, color="tab:red", alpha=0.08)
        tag = " (= gerçek)" if q == Q_TRUE else ""
        ax.set_title(f"q = {q:g}{tag}    q/r = {q / R_STD**2:g}    RMSE(d), ölçüm varken = {out[-1][1]:.2f} m    kesintide maks hata = {out[-1][3]:.1f} m", fontsize=9, loc="left")
        ax.grid(alpha=0.3)
        ax.set_ylabel("d [m]")
    axes[-1].set_xlabel("t [s]")
    fig.suptitle("Aynı veri, farklı süreç gürültüsü q (r = 1 m² sabit). Siyah: gerçek, gri: ölçüm, mavi: filtre")
    fig.tight_layout()
    fig.savefig(RESULTS / "q_r_sweep.png", dpi=150)
    plt.close(fig)
    return out


def plot_nees(n_runs=50):
    """Filtrenin q'su gerçek q'dan farklıyken ortalama NEES (testtekiyle aynı ölçüt)."""
    ratios = np.logspace(-2, 2, 13)
    means = []
    for ratio in ratios:
        vals = []
        for seed in range(n_runs):
            rng = np.random.default_rng(100 + seed)
            xs, zs = simulate(rng, n=200)
            est, covs = run(zs, Q_TRUE * ratio, x0=xs[0] + rng.normal(0, 2.0, 2))
            vals.append(np.mean([nees(xs[k], est[k], covs[k]) for k in range(50, 200)]))
        means.append(float(np.mean(vals)))
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.axhspan(1.48, 2.59, color="tab:green", alpha=0.15, label="Testteki kabul aralığı [1,48; 2,59]")
    ax.axhline(2.0, color="tab:green", lw=1, ls="--", label="Beklenen değer = durum boyutu = 2")
    ax.loglog(ratios, means, "o-", color="tab:blue", label="Ortalama NEES (50 koşu)")
    ax.axvline(1.0, color="k", lw=0.8, ls=":")
    ax.set_xlabel("Filtredeki q / gerçek q")
    ax.set_ylabel("Ortalama NEES")
    ax.text(0.012, means[0] * 0.75, "aşırı özgüvenli:\nP gerçek hatadan küçük", fontsize=8, va="top")
    ax.text(80, 3.2, "aşırı temkinli:\nP gerçek hatadan büyük", fontsize=8, ha="right")
    ax.set_title("Tutarlılık: NEES, filtrenin kendi belirsizliğini doğru bilip bilmediğini ölçer")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(RESULTS / "nees.png", dpi=150)
    plt.close(fig)
    return list(zip(ratios, means))


if __name__ == "__main__":
    RESULTS.mkdir(exist_ok=True)
    rng = np.random.default_rng(7)
    xs, zs = simulate(rng, gap=GAP)
    est, covs = run(zs, Q_TRUE)
    plot_cipo(xs, zs, est, covs)
    raw = [z[0] - x for z, x in zip(zs[50:], xs[50:, 0]) if z is not None]
    ok = [k for k in range(50, len(zs)) if zs[k] is not None]
    print(f"CIPO, q = gerçek: RMSE ham {rmse(raw):.2f} m, filtre {rmse(est[ok, 0] - xs[ok, 0]):.2f} m, "
          f"hız kestirimi {rmse(est[50:, 1] - xs[50:, 1]):.2f} m/s")
    k0, k1 = GAP[0] - 1, GAP[1] - 1
    print(f"Kesinti: σ_d {np.sqrt(covs[k0, 0, 0]):.2f} → {np.sqrt(covs[k1, 0, 0]):.2f} m, "
          f"kesinti sonu gerçek hata {abs(est[k1, 0] - xs[k1, 0]):.2f} m, "
          f"σ_d 0,5 s sonra {np.sqrt(covs[k1 + 10, 0, 0]):.2f} m")
    inside = np.abs(est[:, 0] - xs[:, 0]) < 2 * np.sqrt(covs[:, 0, 0])
    print(f"Gerçek değer ±2σ bandında: %{100 * inside.mean():.1f} (beklenen ~%95)")
    print("q taraması (q, ölçüm varken RMSE d [m] ve ḋ [m/s], kesintide maks |hata d| [m]):")
    for q, a, b, c in plot_q_sweep(xs, zs):
        print(f"  {q:8g}  {a:5.2f}  {b:5.2f}  {c:6.2f}")
    print("NEES (q oranı, ortalama NEES):")
    for r, m in plot_nees():
        print(f"  {r:8.3f}  {m:7.2f}")
