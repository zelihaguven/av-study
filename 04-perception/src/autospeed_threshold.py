"""AutoSpeed çift sigmoid: VisionPilot/upstream davranışı (sigmoid(p) ≥ 0,6 ⇔ p ≥ 0,405) ile
düzeltilmiş davranışın (p ≥ 0,6) videodaki farkı. Sigmoid monoton olduğu için NMS sırası değişmez;
fark yalnızca eşiğin 0,405'e düşmesi.

    VISIONPILOT_DIR=... python 04-perception/src/autospeed_threshold.py VIDEO [VIDEO ...]
Çıktı: results/autospeed_threshold.csv (kare başına sayılar), results/autospeed_diff/*.png (örnek kareler).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import cv2
import numpy as np

from inspect_model import (cipo_distance, infer, load_model, postprocess_autospeed, preprocess,
                           udacity_calibration)

RESULTS = Path(__file__).resolve().parents[1] / "results"
EFFECTIVE = float(np.log(0.6 / 0.4))      # sigmoid(x) = 0,6 ⇔ x = ln(0,6/0,4) ≈ 0,405


def draw(img, dets_new, dets_old):
    """Her iki eşikte de olan kutular yeşil, sadece 0,405 eşiğinde (çift sigmoid) olanlar kırmızı."""
    out = img.copy()
    old = {tuple(np.round(d["box"], 1)) for d in dets_old}
    for d in dets_new:
        key = tuple(np.round(d["box"], 1))
        col = (0, 200, 0) if key in old else (0, 0, 255)
        x1, y1, x2, y2 = map(int, d["box"])
        cv2.rectangle(out, (x1, y1), (x2, y2), col, 2)
        cv2.putText(out, f"c{d['cls']} p={d['score']:.2f}", (x1, max(12, y1 - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1, cv2.LINE_AA)
    return out


def main() -> None:
    cal = udacity_calibration()
    model = load_model("autospeed")
    (RESULTS / "autospeed_diff").mkdir(parents=True, exist_ok=True)
    rows = []
    for video in sys.argv[1:]:
        name = Path(video).stem
        cap = cv2.VideoCapture(video)
        k = 0
        saved = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            prep = preprocess(frame, cal)
            raw = infer(model, prep.t_resized)
            # Model olasılık veriyor: apply_sigmoid=False ile p'yi doğrudan eşikle.
            a = postprocess_autospeed(raw, conf=EFFECTIVE, apply_sigmoid=False)   # = VisionPilot davranışı
            b = postprocess_autospeed(raw, conf=0.6, apply_sigmoid=False)         # düzeltilmiş
            ca, cb = cipo_distance(a, cal.H_resized), cipo_distance(b, cal.H_resized)
            row = {"video": name, "frame": k, "n_vp": len(a), "n_fixed": len(b),
                   "cipo_vp": int(ca is not None), "cipo_fixed": int(cb is not None),
                   "cipo_d_vp": ca[0] if ca else np.nan, "cipo_d_fixed": cb[0] if cb else np.nan}
            for c in range(4):
                row[f"vp_c{c}"] = sum(d["cls"] == c for d in a)
                row[f"fixed_c{c}"] = sum(d["cls"] == c for d in b)
            rows.append(row)
            if len(a) != len(b) and saved < 4 and k % 25 == 0:
                cv2.imwrite(str(RESULTS / "autospeed_diff" / f"{name}_{k:04d}.png"),
                            cv2.resize(draw(prep.resized, a, b), (768, 384), interpolation=cv2.INTER_AREA))
                saved += 1
            k += 1
    with open(RESULTS / "autospeed_threshold.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({kk: (f"{v:.4g}" if isinstance(v, float) else v) for kk, v in r.items()})

    print(f"Etkin eşik (çift sigmoid, conf = 0,6): p ≥ {EFFECTIVE:.3f}")
    for name in dict.fromkeys(r["video"] for r in rows):
        rs = [r for r in rows if r["video"] == name]
        n = len(rs)
        s = lambda key: sum(r[key] for r in rs)
        diff = sum(r["cipo_vp"] != r["cipo_fixed"] for r in rs)
        print(f"{name}: {n} kare | kutu VisionPilot {s('n_vp')} / düzeltilmiş {s('n_fixed')} "
              f"(+%{100 * (s('n_vp') / max(1, s('n_fixed')) - 1):.0f}) | CIPO karesi {s('cipo_vp')} / {s('cipo_fixed')} "
              f"| CIPO durumu farklı kare {diff}")
        print("   sınıf dağılımı VP/düzeltilmiş: " +
              ", ".join(f"c{c} {s(f'vp_c{c}')}/{s(f'fixed_c{c}')}" for c in range(4)))


if __name__ == "__main__":
    main()
