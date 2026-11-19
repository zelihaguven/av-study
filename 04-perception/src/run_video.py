"""Bir videonun her karesinde AutoSteer, AutoSpeed ve AutoDrive'ı çalıştırır, kare başına sonuçları
results/<video>.csv'ye, istenen kareleri overlay olarak kaydeder.

Çalıştırma (repo kökünden):
    VISIONPILOT_DIR=/yol/autoware.privately-owned-vehicles \\
    python 04-perception/src/run_video.py /yol/project_video.mp4 [--every 1] [--save 120,560]
"""
from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

import cv2
import numpy as np

from inspect_model import (cipo_distance, infer, load_model, overlay, postprocess, preprocess,
                           udacity_calibration)

RESULTS = Path(__file__).resolve().parents[1] / "results"
PREV_GAP = 2      # AutoDrive'ın "önceki" karesi: 2 kare = 0,08 s @ 25 fps (VisionPilot 10 Hz'de 0,1 s)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--save", default="", help="overlay kaydedilecek kare indisleri, virgülle")
    ap.add_argument("--max-frames", type=int, default=0)
    a = ap.parse_args()

    cal = udacity_calibration()
    models = {n: load_model(n) for n in ("autosteer", "autospeed", "autodrive")}
    save = {int(s) for s in a.save.split(",") if s}
    name = Path(a.video).stem
    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    rng = np.random.default_rng(0)
    warped_hist: list[np.ndarray] = []
    rows = []
    k = 0
    while True:
        ok, frame = cap.read()
        if not ok or (a.max_frames and k >= a.max_frames):
            break
        t0 = time.perf_counter()
        prep = preprocess(frame, cal)
        t1 = time.perf_counter()
        raw_s = infer(models["autosteer"], prep.t_resized)
        t2 = time.perf_counter()
        raw_d = infer(models["autospeed"], prep.t_resized)
        t3 = time.perf_counter()
        warped_hist.append(prep.t_warped)
        warped_hist = warped_hist[-(PREV_GAP + 1):]
        drive = None
        t4 = t3
        if len(warped_hist) > PREV_GAP:
            drive = postprocess("autodrive", infer(models["autodrive"], (warped_hist[0], prep.t_warped)))
            t4 = time.perf_counter()
        lane = postprocess("autosteer", raw_s, cal, rng)
        dets = postprocess("autospeed", raw_d)
        cipo = cipo_distance(dets, cal.H_resized)
        rows.append({
            "frame": k, "t": k / fps, "valid": int(lane.valid), "reason": lane.reason,
            "n_pts": len(lane.wp_world), "inliers": lane.inliers,
            "e_y": lane.e_y, "e_psi": lane.e_psi, "kappa": lane.kappa, "x_ref": lane.x_ref,
            "ad_kappa": drive["curvature"] if drive else np.nan,
            "ad_flag": drive["flag_prob"] if drive else np.nan,
            "ad_dist": drive["distance"] if drive else np.nan,
            "n_det": len(dets), "cipo_dist": cipo[0] if cipo else np.nan,
            "cipo_cutin": int(cipo[1]) if cipo else 0,
            "ms_pre": 1e3 * (t1 - t0), "ms_steer": 1e3 * (t2 - t1), "ms_speed": 1e3 * (t3 - t2),
            "ms_drive": 1e3 * (t4 - t3) if drive else np.nan,
        })
        if k in save:
            img = overlay(prep.resized, {"lane": lane, "dets": dets, "drive": drive}, cal)
            cv2.imwrite(str(RESULTS / f"_cand_{name}_{k:04d}.png"), img)
        k += 1
    RESULTS.mkdir(exist_ok=True)
    with open(RESULTS / f"{name}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({kk: (f"{v:.5g}" if isinstance(v, float) else v) for kk, v in r.items()})
    valid = np.array([r["valid"] for r in rows])
    print(f"{name}: {k} kare, geçerli şerit %{100 * valid.mean():.1f}, "
          f"AutoSteer medyan {np.median([r['ms_steer'] for r in rows]):.0f} ms")


if __name__ == "__main__":
    main()
