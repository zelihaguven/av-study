"""A4: VisionPilot'un y = f(x) 2. derece polinomu ile parametrik kübik uydurmanın (x(s), y(s)) karşılaştırması.

Aynı AutoSteer çıktısına iki son işleme uygulanır. Ölçütler: geçerli kare, titreşim (1 s ortalamaya göre),
anlamsız değerler (|e_ψ| > 30° veya |κ| > 0,2 1/m, yani R < 5 m), firkete bölümünün zaman serisi.

    VISIONPILOT_DIR=... python 04-perception/src/sharp_curve_fit.py HARDER_VIDEO PROJECT_VIDEO
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from analyze import smooth_residual
from inspect_model import (infer, load_model, postprocess_autosteer, postprocess_autosteer_parametric,
                           preprocess, project, udacity_calibration)

RESULTS = Path(__file__).resolve().parents[1] / "results"
METHODS = {"polinom (VisionPilot)": postprocess_autosteer, "parametrik kübik": postprocess_autosteer_parametric}
HAIRPIN = (39.0, 44.0)
SHOW_FRAME = 998


def run(video: str, model, cal, keep_frame: int | None = None):
    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    out = {m: {"valid": [], "e_y": [], "e_psi": [], "kappa": []} for m in METHODS}
    kept = None
    k = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        prep = preprocess(frame, cal)
        raw = infer(model, prep.t_resized)
        res = {}
        for m, f in METHODS.items():
            r = f(raw, cal.H_resized, np.random.default_rng(k))
            res[m] = r
            for key in ("e_y", "e_psi", "kappa"):
                out[m][key].append(getattr(r, key))
            out[m]["valid"].append(r.valid)
        if k == keep_frame:
            kept = (prep.resized.copy(), res)
        k += 1
    t = np.arange(k) / fps
    for m in METHODS:
        out[m] = {key: np.array(v, dtype=float) for key, v in out[m].items()}
    return t, out, kept


def summarize(name, t, out):
    print(f"== {name}")
    for m, d in out.items():
        v = d["valid"] > 0
        absurd = v & ((np.abs(np.rad2deg(d["e_psi"])) > 30) | (np.abs(d["kappa"]) > 0.2))
        _, r_y = smooth_residual(t, d["e_y"], v)
        _, r_p = smooth_residual(t, d["e_psi"], v)
        win = (t >= HAIRPIN[0]) & (t <= HAIRPIN[1])
        line = (f"  {m:22s} geçerli %{100 * v.mean():5.1f} | anlamsız {absurd.sum():3d} kare | "
                f"σ e_y {100 * np.nanstd(r_y):4.1f} cm, σ e_ψ {np.rad2deg(np.nanstd(r_p)):4.2f}°")
        if win.any() and name.startswith("harder"):
            _, ry_w = smooth_residual(t[win], d["e_y"][win], v[win])
            line += (f" | firkete: σ e_y {100 * np.nanstd(ry_w):4.1f} cm, maks |e_ψ| "
                     f"{np.nanmax(np.abs(np.rad2deg(np.where(v & win, d['e_psi'], np.nan)))):4.1f}°")
        print(line)


def figure(t, out, kept, cal):
    win = (t >= HAIRPIN[0] - 4) & (t <= HAIRPIN[1] + 2)
    fig = plt.figure(figsize=(13, 8))
    gs = fig.add_gridspec(3, 2, width_ratios=[1.6, 1])
    cols = {"polinom (VisionPilot)": "tab:red", "parametrik kübik": "tab:blue"}
    for row, (key, lab, sc) in enumerate([("e_y", "e_y [m]", 1), ("e_psi", "e_ψ [°]", np.rad2deg(1)),
                                          ("kappa", "κ [1/m]", 1)]):
        ax = fig.add_subplot(gs[row, 0])
        for m, d in out.items():
            y = np.where(d["valid"] > 0, d[key] * sc, np.nan)
            ax.plot(t[win], y[win], ".-", ms=2, lw=0.8, color=cols[m], label=m)
        ax.axvspan(*HAIRPIN, color="0.9")
        ax.set_ylabel(lab)
        ax.grid(alpha=0.3)
        if key == "kappa":
            ax.set_ylim(-0.25, 0.25)
            ax.set_xlabel("t [s]")
        if row == 0:
            ax.legend(fontsize=8)
            ax.set_title("harder_challenge, firkete bölümü (gri)", fontsize=10, loc="left")
    ax = fig.add_subplot(gs[:, 1])
    img, res = kept
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    ax.imshow(img)
    Hinv = np.linalg.inv(cal.H_resized)
    r0 = next(iter(res.values()))
    ax.plot(r0.wp_px[:, 0], r0.wp_px[:, 1], "o", color="yellow", ms=3, label="AutoSteer noktaları")
    for m, r in res.items():
        if m.startswith("polinom") and r.coef is not None:
            xs = np.linspace(r.wp_world[:, 0].min(), r.wp_world[:, 0].max(), 60)
            px = project(Hinv, np.c_[xs, np.polyval(r.coef, xs)])
        elif "cx" in r.extra:
            ss = np.linspace(0, r.extra["s"].max() if "s" in r.extra else 20, 60)
            px = project(Hinv, np.c_[np.polyval(r.extra["cx"], ss), np.polyval(r.extra["cy"], ss)])
        else:
            continue
        lab = f"{m}: R = {1 / r.kappa:+.0f} m, e_ψ = {np.rad2deg(r.e_psi):+.0f}°" if r.valid else f"{m}: geçersiz"
        ax.plot(px[:, 0], px[:, 1], "-", color=cols[m], lw=2.5, label=lab)
    ax.set_xlim(0, 1024)
    ax.set_ylim(512, 0)
    ax.set_title(f"Kare {SHOW_FRAME}", fontsize=10)
    ax.legend(fontsize=7, loc="upper left")
    ax.axis("off")
    fig.suptitle("A4: keskin virajda polinom ve parametrik uydurma, aynı AutoSteer çıktısı")
    fig.tight_layout()
    fig.savefig(RESULTS / "sharp_curve_fit.png", dpi=130)
    plt.close(fig)


def main():
    cal = udacity_calibration()
    model = load_model("autosteer")
    t, out, kept = run(sys.argv[1], model, cal, keep_frame=SHOW_FRAME)
    summarize("harder_challenge", t, out)
    figure(t, out, kept, cal)
    if len(sys.argv) > 2:
        t2, out2, _ = run(sys.argv[2], model, cal)
        summarize("project (kontrol)", t2, out2)


if __name__ == "__main__":
    main()
