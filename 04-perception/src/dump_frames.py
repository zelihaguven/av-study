"""Belirli kareleri yeniden çalıştırıp overlay kaydeder.

    python 04-perception/src/dump_frames.py VIDEO 120:overlay_1 560:failures/gece ...
Her argüman "kare:çıktı_adı" (results/ altına, .png eklenir). Çıktı: ham kare (üst) + overlay (alt).
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

from inspect_model import infer, load_model, overlay, postprocess, preprocess, udacity_calibration

RESULTS = Path(__file__).resolve().parents[1] / "results"
PREV_GAP = 2


def main() -> None:
    video, specs = sys.argv[1], [s.split(":", 1) for s in sys.argv[2:]]
    cal = udacity_calibration()
    models = {n: load_model(n) for n in ("autosteer", "autospeed", "autodrive")}
    cap = cv2.VideoCapture(video)
    for k_str, out in specs:
        k = int(k_str)
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, k - PREV_GAP))
        _, prev = cap.read()
        cap.set(cv2.CAP_PROP_POS_FRAMES, k)
        _, frame = cap.read()
        prep, prep_prev = preprocess(frame, cal), preprocess(prev, cal)
        lane = postprocess("autosteer", infer(models["autosteer"], prep.t_resized), cal,
                           np.random.default_rng(0))
        dets = postprocess("autospeed", infer(models["autospeed"], prep.t_resized))
        drive = postprocess("autodrive", infer(models["autodrive"], (prep_prev.t_warped, prep.t_warped)))
        img = overlay(prep.resized, {"lane": lane, "dets": dets, "drive": drive}, cal)
        path = RESULTS / f"{out}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path), cv2.resize(img, (768, 384), interpolation=cv2.INTER_AREA))
        print(f"{k}: {path.relative_to(RESULTS.parent)}  valid={lane.valid} {lane.reason} "
              f"e_y={lane.e_y:+.2f} inl={lane.inliers} n={len(lane.wp_world)}")


if __name__ == "__main__":
    main()
