"""04 son işleme testleri. Model ağırlığı, onnxruntime veya OpenCV gerektirmez."""
import numpy as np
import pytest

from inspect_model import (Calibration, fit_path_ransac, homography_from_4, path_curvature,
                           postprocess_autodrive, postprocess_autospeed, postprocess_autosteer,
                           project, udacity_calibration)

# Basit, doğrulanabilir bir "kamera": 1024×512 piksel → zemin.
# X = 5 + (511 − v) · 0,2  (alt satır 5 m, yukarı çıktıkça uzak), Y = −(u − 512) · 0,01 (sol +)
H_TOY = np.array([[0.0, -0.2, 5 + 511 * 0.2],
                  [-0.01, 0.0, 5.12],
                  [0.0, 0.0, 1.0]])
ROWS = np.arange(64) * 511 / 63


def _xp_for_path(y_of_x):
    """Zeminde y = f(x) yolunu veren AutoSteer çıktısı (xp normalize, h = 1)."""
    X = 5 + (511 - ROWS) * 0.2
    u = 512 - y_of_x(X) / 0.01
    return [u / 1024, np.ones(64)]


def test_homography_and_project_roundtrip():
    src = np.array([[0, 0], [10, 0], [10, 5], [0, 5]], float)
    dst = np.array([[1, 2], [21, 3], [19, 14], [2, 12]], float)
    H = homography_from_4(src, dst)
    np.testing.assert_allclose(project(H, src), dst, atol=1e-9)
    np.testing.assert_allclose(project(np.linalg.inv(H), dst), src, atol=1e-9)


def test_ransac_rejects_outliers():
    rng = np.random.default_rng(0)
    x = np.linspace(5, 60, 30)
    y = 0.002 * x ** 2 - 0.03 * x + 0.4 + rng.normal(0, 0.02, 30)
    y[[3, 11, 20]] += 2.0                                  # üç aykırı nokta
    coef, inl = fit_path_ransac(np.c_[x, y], rng)
    assert inl.sum() == 27 and not inl[[3, 11, 20]].any()
    np.testing.assert_allclose(coef, [0.002, -0.03, 0.4], atol=0.02)


def test_too_few_inliers_is_invalid():
    rng = np.random.default_rng(0)
    pts = np.c_[np.linspace(5, 20, 8), np.zeros(8)]
    _, inl = fit_path_ransac(pts, rng)
    assert inl is None


def test_sign_convention_path_left_means_vehicle_right():
    """Yol 0,5 m solda (Y = +0,5) ⇒ araç yolun sağında ⇒ bizim e_y = −0,5 (VisionPilot CTE = +0,5)."""
    res = postprocess_autosteer(_xp_for_path(lambda X: 0.5 + 0 * X), H_TOY)
    assert res.valid
    assert res.e_y == pytest.approx(-0.5, abs=1e-6)
    assert res.e_psi == pytest.approx(0.0, abs=1e-6)
    assert res.x_ref == pytest.approx(5.0, abs=1e-6)       # CTE en yakın noktada, x = 0'da değil


def test_heading_sign():
    """Yol sola doğru açılıyor (dy/dx = +0,05) ⇒ araç yola göre sağa bakıyor ⇒ e_psi < 0."""
    res = postprocess_autosteer(_xp_for_path(lambda X: 0.05 * X), H_TOY)
    assert res.e_psi == pytest.approx(-np.arctan(0.05), abs=1e-6)


def test_curvature_of_left_arc():
    """y ≈ x² / (2R) sola dönen yay ⇒ κ ≈ +1/R."""
    R = 200.0
    res = postprocess_autosteer(_xp_for_path(lambda X: X ** 2 / (2 * R)), H_TOY)
    assert res.kappa == pytest.approx(1 / R, rel=0.05)
    assert path_curvature(res.wp_world, res.coef) == pytest.approx(res.kappa)


def test_low_height_points_dropped():
    xp, h = _xp_for_path(lambda X: 0 * X)
    h[:40] = 0.2                                          # üst 40 satır eşik altında
    res = postprocess_autosteer([xp, h], H_TOY)
    assert len(res.wp_px) == 24


def test_autodrive_conversions():
    out = postprocess_autodrive([np.array([[0.8]]), np.array([[0.1]]), np.array([[0.0]])])
    assert out["distance"] == pytest.approx(30.0)
    assert out["curvature"] == pytest.approx(0.021)
    assert out["flag_prob"] == pytest.approx(0.5)


def _speed_raw(boxes, probs):
    """boxes: (n, 4) cx, cy, w, h; probs: (n, 4) sınıf olasılıkları → [1, 8, n]."""
    return [np.concatenate([np.asarray(boxes, float).T, np.asarray(probs, float).T])[None]]


def test_autospeed_nms_and_class():
    raw = _speed_raw([[100, 100, 40, 40], [102, 101, 40, 40], [400, 200, 30, 30]],
                     [[0, 0.9, 0, 0], [0, 0.8, 0, 0], [0, 0, 0.7, 0]])
    dets = postprocess_autospeed(raw, apply_sigmoid=False)
    assert [d["cls"] for d in dets] == [1, 2]             # örtüşen ikinci kutu bastırıldı
    assert dets[0]["box"] == pytest.approx([80, 80, 120, 120])


def test_autospeed_double_sigmoid_lowers_threshold():
    """Model 0,45 olasılık veriyor. Olasılık olarak 0,6 eşiğinin altında, ama C++ gibi bir kez daha
    sigmoid uygulanınca sigmoid(0,45) = 0,61 ≥ 0,6 olup geçiyor."""
    raw = _speed_raw([[100, 100, 40, 40]], [[0, 0.45, 0, 0]])
    assert postprocess_autospeed(raw, apply_sigmoid=False) == []
    assert len(postprocess_autospeed(raw, apply_sigmoid=True)) == 1


def test_udacity_calibration_lane_width():
    """Kalibrasyonun kendisini kontrol: alt satırdaki iki şerit çizgisi arası 3,7 m, ileri yönde eşit X."""
    cal = udacity_calibration()
    left, right = project(cal.H, [[203, 720], [1127, 720]])
    assert right[1] - left[1] == pytest.approx(-3.7, abs=1e-6)
    assert left[0] == pytest.approx(right[0], abs=1e-6)
    assert isinstance(cal, Calibration) and cal.crop_top == 80
