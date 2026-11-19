"""VisionPilot modellerini (AutoSteer, AutoDrive, AutoSpeed) Python'da çalıştırma ve inceleme.

VisionPilot'un C++ ön/son işlemesinin Python karşılığı. Her adımın kaynağı yorumda
`VisionPilot/<dosya>:<satır>` olarak verildi (autoware.privately-owned-vehicles @ 65375ec2cf).

Bağımlılıklar: numpy her yerde; opencv-python-headless ve onnxruntime sadece görüntü ve model
fonksiyonlarında (fonksiyon içinde import edilir, böylece son işleme ve testler onlarsız çalışır).
Ağırlıklar bu repoya girmez: VisionPilot klonunun yolu VISIONPILOT_DIR ortam değişkeniyle verilir.

İşaret kuralı (05 ve common ile aynı): e_y araç yolun solundaysa pozitif, e_psi = yaw_araç − yaw_yol,
kappa sola dönüşte pozitif. VisionPilot'un CTE'si ters işaretli ("+ve = ego right of path",
VisionPilot/modules/safety_guardian/fusion/include/fusion/lateral_fusion.hpp:22), dönüşüm aşağıda.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

NET_W, NET_H = 1024, 512           # tüm modellerin girişi: [1, 3, 512, 1024]
N_WP = 64                          # AutoSteer yol noktası sayısı

# ZOD "model-view" homografisi: 1024×512 kanonik görüntü pikseli → zemin [m].
# VisionPilot/scripts/find_homography_C_matrix.py:13-21 ve lateral_fusion.hpp:190-194
V_ZOD = np.array([[0.00209514907, -0.000941721466, -9.24906396],
                  [0.00662758637, -0.000352940531, -3.33396502],
                  [0.000120077371, -0.00411343505, 1.0]])


# ── Kalibrasyon ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Calibration:
    """H: ham piksel (u, v) → zemin (X ileri, Y sol) [m]. size: (genişlik, yükseklik)."""
    H: np.ndarray
    size: tuple[int, int]
    note: str = ""

    @property
    def crop_top(self) -> int:
        """Üstten kırpılan satır: geriye genişlik × genişlik/2 (2:1) kalır.
        VisionPilot/modules/common/include/common/utils.hpp:15-19"""
        w, h = self.size
        return max(0, int(round(h - w / 2)))

    @property
    def H_resized(self) -> np.ndarray:
        """1024×512 yeniden boyutlanmış görüntü pikseli → zemin. H · T.
        VisionPilot/modules/models/src/inference.cpp:116-144"""
        w, h = self.size
        crop_h = h - self.crop_top
        T = np.array([[w / NET_W, 0, 0], [0, crop_h / NET_H, self.crop_top], [0, 0, 1.0]])
        return self.H @ T

    @property
    def C(self) -> np.ndarray:
        """Ham görüntü → AutoDrive'ın kanonik 1024×512 görünümü (kuşbakışı DEĞİL, ZOD perspektifi).
        Port: VisionPilot/scripts/find_homography_C_matrix.py:9-42"""
        world = np.array([[15, 5], [150, 5], [15, -5], [150, -5]], dtype=float)
        uv = project(np.linalg.inv(self.H), world)
        pq = project(np.linalg.inv(V_ZOD), world)
        return homography_from_4(uv, pq)


def udacity_calibration(K_fx: float = 1157.5) -> Calibration:
    """Udacity CarND-Advanced-Lane-Lines videoları (1280×720) için zemin homografisi.

    1. Kuşbakışı dönüşüm: Udacity'nin kendi kaynak/hedef noktaları (writeup_template.md:86-91).
    2. Yanal ölçek: hedefte şerit 640 px = 3,7 m (ABD şerit genişliği).
    3. Boylamsal ölçek: kesikli çizgi periyodu 12,19 m (10 ft çizgi + 30 ft boşluk) kuşbakışında
       362 px ölçüldü (test_images/straight_lines1.jpg). Belirsizlik ~%10–25, notes.md'de.
    4. X0 (kamera → görüntünün alt satırı): alt satırda şerit 924 px; odak uzaklığı satranç tahtası
       kalibrasyonundan fx = 1157,5 px ⇒ X0 ≈ fx · 3,7 / 924 ≈ 4,6 m.
    5. Yanal sıfır: asal nokta sütunu cx = 675 (kameranın aracın ortasında olduğu varsayımı).
    """
    src = np.array([[585, 460], [203, 720], [1127, 720], [695, 460]], dtype=float)
    dst = np.array([[320, 0], [320, 720], [960, 720], [960, 0]], dtype=float)
    M = homography_from_4(src, dst)                         # ham → kuşbakışı piksel
    sx, sy = 3.7 / 640, 12.19 / 362
    x0 = K_fx * 3.7 / (1127 - 203)
    xc = project(M, np.array([[675.0, 720.0]]))[0, 0]       # kamera ekseninin kuşbakışı sütunu
    A = np.array([[0, -sy, x0 + 720 * sy],                   # X = x0 + (720 − v_bev) · sy
                  [-sx, 0, xc * sx],                          # Y = −(u_bev − xc) · sx   (sol +)
                  [0, 0, 1.0]])
    return Calibration(H=A @ M, size=(1280, 720),
                       note=f"Udacity, sx={sx:.4f} m/px, sy={sy:.4f} m/px, X0={x0:.2f} m")


def homography_from_4(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    """4 nokta çiftinden homografi (DLT). cv2.getPerspectiveTransform'un numpy karşılığı."""
    A, b = [], []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    h = np.linalg.solve(np.array(A, dtype=float), np.array(b, dtype=float))
    return np.append(h, 1.0).reshape(3, 3)


def project(H: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """(N, 2) noktaları homografiyle dönüştürür."""
    pts = np.atleast_2d(np.asarray(pts, dtype=float))
    p = np.c_[pts, np.ones(len(pts))] @ H.T
    return p[:, :2] / p[:, 2:3]


# ── Model ────────────────────────────────────────────────────────────────────

def weights_dir() -> Path:
    vp = os.environ.get("VISIONPILOT_DIR")
    if not vp:
        raise RuntimeError("VISIONPILOT_DIR ayarla: autoware.privately-owned-vehicles klonunun yolu")
    return Path(vp) / "VisionPilot" / "modules" / "models" / "weights"


def load_model(name: str, precision: str = "fp32"):
    """name ∈ {"autosteer", "autodrive", "autospeed"}. onnxruntime CPU oturumu döndürür."""
    import onnxruntime as ort
    if name not in ("autosteer", "autodrive", "autospeed"):
        raise ValueError(name)
    opts = ort.SessionOptions()
    return ort.InferenceSession(str(weights_dir() / f"{name}_{precision}.onnx"), opts,
                                providers=["CPUExecutionProvider"])


@dataclass
class Prepared:
    resized: np.ndarray        # 1024×512 BGR, AutoSteer + AutoSpeed
    warped: np.ndarray         # 1024×512 BGR, AutoDrive
    t_resized: np.ndarray      # [1,3,512,1024] float32, RGB/255
    t_warped: np.ndarray       # [1,3,512,1024] float32, RGB/255 + ImageNet normalizasyonu


IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)   # RGB sırası
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)    # inference.cpp:22-23


def preprocess(frame: np.ndarray, calib: Calibration) -> Prepared:
    """Ham BGR kare → iki görüntü ve iki tensör.
    VisionPilot/modules/sensing/image_preprocessing/src/image_preprocessor.cpp:13-21,
    VisionPilot/modules/models/src/inference.cpp:25-68"""
    import cv2
    warped = cv2.warpPerspective(frame, calib.C, (NET_W, NET_H), flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_REFLECT_101)
    resized = cv2.resize(frame[calib.crop_top:], (NET_W, NET_H), interpolation=cv2.INTER_LINEAR)

    def chw(bgr, imagenet):
        x = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        if imagenet:
            x = (x - IMAGENET_MEAN) / IMAGENET_STD
        return np.ascontiguousarray(x.transpose(2, 0, 1)[None])

    return Prepared(resized, warped, chw(resized, False), chw(warped, True))


def infer(model, inputs):
    """inputs: tek tensör veya (önceki, şimdiki) çifti (AutoDrive). Ham çıktı listesi."""
    names = [i.name for i in model.get_inputs()]
    if isinstance(inputs, (tuple, list)):
        feed = dict(zip(names, inputs))
    else:
        feed = {names[0]: inputs}
    return model.run(None, feed)


# ── Son işleme (yalnız numpy) ─────────────────────────────────────────────────

@dataclass
class LaneResult:
    """AutoSteer son işleme çıktısı."""
    valid: bool
    reason: str                               # geçersizse neden
    wp_px: np.ndarray                         # (k, 2) geçerli yol noktaları, 1024×512 piksel
    wp_world: np.ndarray                      # (k, 2) zemin [m], X ileri Y sol
    coef: np.ndarray | None = None            # y = a x² + b x + c
    inliers: int = 0
    x_ref: float = float("nan")
    e_y: float = float("nan")                 # bizim işaret: araç soldaysa +
    e_psi: float = float("nan")               # yaw_araç − yaw_yol
    kappa: float = float("nan")               # sola +
    extra: dict = field(default_factory=dict)


def fit_path_ransac(pts: np.ndarray, rng: np.random.Generator, iters: int = 80,
                    thresh: float = 0.20, min_inliers: int = 12):
    """y = a x² + b x + c için RANSAC. Port: lateral_fusion.cpp:226-262, 298-315.
    VisionPilot rastgeleliği random_device ile tohumluyor; burada tekrarlanabilirlik için rng veriliyor.
    Döndürür: (coef, inlier_maskesi) veya (None, None)."""
    n = len(pts)
    if n < 3:
        return None, None
    X = np.c_[pts[:, 0] ** 2, pts[:, 0], np.ones(n)]
    best = None
    if n > 3:
        for _ in range(iters):
            idx = rng.choice(n, 3, replace=False)
            coef, *_ = np.linalg.lstsq(X[idx], pts[idx, 1], rcond=None)
            mask = np.abs(X @ coef - pts[:, 1]) < thresh
            if best is None or mask.sum() > best.sum():
                best = mask
    else:
        best = np.ones(n, bool)
    if best.sum() < 3:
        return None, None
    coef, *_ = np.linalg.lstsq(X[best], pts[best, 1], rcond=None)
    if best.sum() < min_inliers:
        return coef, None
    return coef, best


def path_curvature(pts: np.ndarray, coef: np.ndarray, x_min: float = 3.0, x_max: float = 25.0) -> float:
    """[3, 25] m'deki noktalarda κ = 2a / (1 + (2ax + b)²)^1.5 medyanı. lateral_fusion.cpp:266-294"""
    a, b, _ = coef
    xs = pts[(pts[:, 0] >= x_min) & (pts[:, 0] <= x_max), 0]
    if len(xs) == 0:
        xs = np.array([x_min])
    return float(np.median(2 * a / (1 + (2 * a * xs + b) ** 2) ** 1.5))


def postprocess_autosteer(raw, H_resized: np.ndarray, rng: np.random.Generator | None = None) -> LaneResult:
    """Ham (xp[64], h[64]) → yol noktaları → zemin → RANSAC polinom → e_y, e_psi, kappa.
    lateral_fusion.cpp:183-196 (nokta seçimi), 323-336 (CTE ve yaw)."""
    rng = rng if rng is not None else np.random.default_rng(0)
    xp, h = np.asarray(raw[0]).ravel(), np.asarray(raw[1]).ravel()
    rows = np.arange(N_WP) * (NET_H - 1) / (N_WP - 1)     # sabit satırlar
    keep = h >= 0.5                                        # sigmoid YOK, ham değer eşikleniyor (:189)
    px = np.c_[xp[keep] * NET_W, rows[keep]]
    world = project(H_resized, px) if len(px) else np.zeros((0, 2))
    ok = (world[:, 0] >= 0.5) & (world[:, 0] <= 120.0)
    px, world = px[ok], world[ok]
    coef, inl = fit_path_ransac(world, rng)
    if coef is None:
        return LaneResult(False, f"yetersiz nokta ({len(world)})", px, world)
    if inl is None:
        return LaneResult(False, "inlier < 12", px, world, coef=coef)
    x_ref = float(world[inl, 0].min())                   # en yakın gözlenen nokta, x = 0 DEĞİL
    cte_vp = float(np.polyval(coef, x_ref))              # VisionPilot: + = yol solda = ego sağda
    if abs(cte_vp) > 3.0:
        return LaneResult(False, "|CTE| > 3 m", px, world, coef=coef, inliers=int(inl.sum()))
    yaw_vp = float(np.arctan(2 * coef[0] * x_ref + coef[1]))   # + = yol sola gidiyor
    return LaneResult(True, "", px, world, coef=coef, inliers=int(inl.sum()), x_ref=x_ref,
                      e_y=-cte_vp, e_psi=-yaw_vp, kappa=path_curvature(world[inl], coef))


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.asarray(x, dtype=float)))


def postprocess_autodrive(raw) -> dict:
    """distance = 150·(1 − d) [m], curvature = 0,21·c [1/m], flag = sigmoid.
    auto_drive.cpp:81-83, longitudinal_fusion.cpp:78, lateral_fusion.hpp:97-98"""
    d, c, f = (float(np.asarray(r).ravel()[0]) for r in raw)
    return {"distance": 150.0 * (1.0 - d), "curvature": 0.21 * c, "flag_prob": float(sigmoid(f))}


AUTOSPEED_CLASSES = {1: "CIPO L1 (aynı şerit)", 2: "CIPO L2 (komşu, araya girebilir)"}


def postprocess_autospeed(raw, conf: float = 0.6, iou: float = 0.45,
                          apply_sigmoid: bool = True) -> list[dict]:
    """[1, 4+C, N] → sınıf-bağımsız NMS sonrası kutular (1024×512 piksel).
    auto_speed.cpp:98-203, eşikler auto_speed.hpp:57-58

    apply_sigmoid=True C++'ı birebir taklit eder (auto_speed.cpp:139 sınıf çıkışına sigmoid uygular).
    Ama ONNX grafiğinin son düğümü Concat(kutu, Sigmoid(sınıf)): model zaten olasılık veriyor.
    Yani C++'ta sigmoid iki kez uygulanıyor; conf = 0,6 aslında olasılıkta 0,405 eşiği demek.
    apply_sigmoid=False olasılığı olduğu gibi kullanır (notes.md, "AutoSpeed çift sigmoid")."""
    out = np.asarray(raw[0])[0]                 # (8, N)
    cx, cy, w, hh = out[:4]
    prob = sigmoid(out[4:]) if apply_sigmoid else out[4:]
    cls = prob.argmax(axis=0)
    score = prob.max(axis=0)
    keep = np.nonzero(score >= conf)[0]
    keep = keep[np.argsort(-score[keep])]
    boxes = np.c_[cx - w / 2, cy - hh / 2, cx + w / 2, cy + hh / 2][keep]
    chosen = []
    alive = np.ones(len(keep), bool)
    for i in range(len(keep)):
        if not alive[i]:
            continue
        chosen.append(i)
        x1 = np.maximum(boxes[i, 0], boxes[:, 0]); y1 = np.maximum(boxes[i, 1], boxes[:, 1])
        x2 = np.minimum(boxes[i, 2], boxes[:, 2]); y2 = np.minimum(boxes[i, 3], boxes[:, 3])
        inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
        area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
        ious = inter / (area[i] + area - inter + 1e-6)
        alive &= ious <= iou
        alive[i] = False
    return [{"box": boxes[i].tolist(), "cls": int(cls[keep[i]]), "score": float(score[keep[i]])}
            for i in chosen]


def cipo_distance(dets: list[dict], H_resized: np.ndarray) -> tuple[float, bool] | None:
    """En yakın L1 kutusu; daha yakın bir L2 varsa o (araya girme). Mesafe: kutunun alt-orta
    noktasının zemindeki uzaklığı. longitudinal_fusion.cpp:183-216"""
    best = {1: None, 2: None}
    for d in dets:
        if d["cls"] not in best:
            continue
        x1, _, x2, y2 = d["box"]
        X, Y = project(H_resized, [[(x1 + x2) / 2, y2]])[0]
        dist = float(np.hypot(X, Y))
        if best[d["cls"]] is None or dist < best[d["cls"]]:
            best[d["cls"]] = dist
    if best[1] is None and best[2] is None:
        return None
    if best[2] is not None and (best[1] is None or best[2] < best[1]):
        return best[2], True
    return best[1], False


def postprocess(name: str, raw, calib: Calibration | None = None, rng=None):
    if name == "autosteer":
        return postprocess_autosteer(raw, calib.H_resized, rng)
    if name == "autodrive":
        return postprocess_autodrive(raw)
    if name == "autospeed":
        return postprocess_autospeed(raw)
    raise ValueError(name)


# ── Görselleştirme ────────────────────────────────────────────────────────────

def overlay(frame: np.ndarray, result: dict, calib: Calibration) -> np.ndarray:
    """1024×512 görüntü üzerine: AutoSteer noktaları (kırmızı), RANSAC polinomu (yeşil),
    AutoSpeed kutuları, metin. result: {"lane": LaneResult, "drive": dict|None, "dets": list}."""
    import cv2
    img = frame.copy()
    lane: LaneResult = result["lane"]
    for u, v in lane.wp_px:
        cv2.circle(img, (int(u), int(v)), 4, (0, 0, 255), -1)
    if lane.valid:
        xs = np.linspace(lane.wp_world[:, 0].min(), lane.wp_world[:, 0].max(), 40)
        px = project(np.linalg.inv(calib.H_resized), np.c_[xs, np.polyval(lane.coef, xs)])
        cv2.polylines(img, [px.astype(np.int32)], False, (0, 255, 0), 3)
    for d in result.get("dets", []):
        x1, y1, x2, y2 = map(int, d["box"])
        col = {1: (0, 0, 255), 2: (0, 165, 255)}.get(d["cls"], (200, 200, 200))
        cv2.rectangle(img, (x1, y1), (x2, y2), col, 2)
        cv2.putText(img, f"c{d['cls']} {d['score']:.2f}", (x1, max(12, y1 - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1, cv2.LINE_AA)
    lines = []
    if lane.valid:
        lines.append(f"e_y {lane.e_y:+.2f} m  e_psi {np.rad2deg(lane.e_psi):+.1f} deg  "
                     f"R {1 / lane.kappa if abs(lane.kappa) > 1e-4 else float('inf'):+.0f} m  inl {lane.inliers}")
    else:
        lines.append(f"SERIT YOK: {lane.reason}")
    drv = result.get("drive")
    if drv:
        lines.append(f"AutoDrive: kappa {drv['curvature']:+.4f}  CIPO p {drv['flag_prob']:.2f}  d {drv['distance']:.0f} m")
    for k, t in enumerate(lines):
        y = 24 + 24 * k
        cv2.putText(img, t, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(img, t, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    return img


if __name__ == "__main__":
    import argparse

    import cv2
    ap = argparse.ArgumentParser(description="Tek kare üzerinde üç modeli çalıştırır ve overlay kaydeder.")
    ap.add_argument("image")
    ap.add_argument("-o", "--out", default="overlay.png")
    a = ap.parse_args()
    cal = udacity_calibration()
    fr = cv2.imread(a.image)
    prep = preprocess(fr, cal)
    lane = postprocess("autosteer", infer(load_model("autosteer"), prep.t_resized), cal)
    dets = postprocess("autospeed", infer(load_model("autospeed"), prep.t_resized))
    cv2.imwrite(a.out, overlay(prep.resized, {"lane": lane, "dets": dets}, cal))
    print(lane.valid, lane.reason, lane.e_y, lane.e_psi, lane.kappa)
