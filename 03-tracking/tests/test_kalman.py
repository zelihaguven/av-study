"""03 kabul testleri. Veriler sentetik ve tohumlu; sonuçlar tekrarlanabilir."""
import numpy as np

from kalman import KalmanFilter, cv_model, lane_model, nees

DT = 0.05            # 20 Hz kamera
Q_TRUE = 0.5         # gerçek ivme gürültüsü yoğunluğu
R_STD = 1.0          # mesafe ölçüm gürültüsü [m]
H = np.array([[1.0, 0.0]])
R = np.array([[R_STD ** 2]])


def _simulate_cipo(rng, n=400, dropout=0.0):
    F, Q = cv_model(DT, Q_TRUE)
    x = np.array([40.0, -2.0])
    xs, zs = [], []
    for _ in range(n):
        x = F @ x + rng.multivariate_normal(np.zeros(2), Q)
        xs.append(x.copy())
        z = None if rng.random() < dropout else np.array([x[0] + rng.normal(0, R_STD)])
        zs.append(z)
    return np.array(xs), zs


def _run(zs, x0=None):
    F, Q = cv_model(DT, Q_TRUE)
    kf = KalmanFilter(np.array([40.0, 0.0]) if x0 is None else x0, np.diag([4.0, 4.0]))
    est, covs = [], []
    for z in zs:
        kf.predict(F, Q)
        kf.update(z, H, R)
        est.append(kf.x.copy())
        covs.append(kf.P.copy())
    return np.array(est), np.array(covs)


def test_filter_beats_raw_measurement():
    rng = np.random.default_rng(0)
    xs, zs = _simulate_cipo(rng)
    est, _ = _run(zs)
    raw_err = np.array([z[0] for z in zs]) - xs[:, 0]
    filt_err = est[:, 0] - xs[:, 0]
    assert np.sqrt(np.mean(filt_err[50:] ** 2)) < 0.5 * np.sqrt(np.mean(raw_err[50:] ** 2))


def test_missed_detection_grows_covariance():
    rng = np.random.default_rng(1)
    _, zs = _simulate_cipo(rng, n=100)
    zs[60:70] = [None] * 10
    _, covs = _run(zs)
    assert covs[69, 0, 0] > covs[59, 0, 0]          # kesintide belirsizlik artar
    assert covs[75, 0, 0] < covs[69, 0, 0]          # ölçüm dönünce azalır


def test_covariance_symmetric_positive_definite():
    rng = np.random.default_rng(2)
    _, zs = _simulate_cipo(rng, dropout=0.2)
    _, covs = _run(zs)
    for P in covs:
        assert np.allclose(P, P.T)
        assert np.all(np.linalg.eigvalsh(P) > 0)


def test_nees_consistency():
    """50 Monte Carlo koşusu, ısınma sonrası ortalama NEES.

    Durum boyutu 2 olduğundan tutarlı bir filtrede beklenen değer 2'dir.
    Gevşek %95 aralığı: chi2(100)/50 → [1.48, 2.59].
    """
    vals = []
    for seed in range(50):
        rng = np.random.default_rng(100 + seed)
        xs, zs = _simulate_cipo(rng, n=200)
        est, covs = _run(zs, x0=xs[0] + rng.normal(0, 2.0, 2))
        vals.append(np.mean([nees(xs[k], est[k], covs[k]) for k in range(50, 200)]))
    assert 1.48 < np.mean(vals) < 2.59


def test_lane_tracking_reduces_offset_noise():
    rng = np.random.default_rng(3)
    v, n = 15.0, 400
    F, Q = lane_model(DT, v, q_y=0.01, q_psi=1e-4)
    x = np.array([0.3, 0.01])
    Hl = np.eye(2)
    Rl = np.diag([0.3 ** 2, np.deg2rad(3.0) ** 2])
    kf = KalmanFilter(np.zeros(2), np.diag([1.0, 0.1]))
    truth, raw, est = [], [], []
    for _ in range(n):
        x = F @ x + rng.multivariate_normal(np.zeros(2), Q)
        z = x + rng.multivariate_normal(np.zeros(2), Rl)
        kf.predict(F, Q)
        kf.update(z, Hl, Rl)
        truth.append(x[0]); raw.append(z[0]); est.append(kf.x[0])
    truth, raw, est = map(np.array, (truth, raw, est))
    assert np.sqrt(np.mean((est - truth)[50:] ** 2)) < 0.6 * np.sqrt(np.mean((raw - truth)[50:] ** 2))
