"""Referans yol: düz giriş + sola viraj + sağa viraj + düz çıkış (S-viraj)."""
import numpy as np


def s_viraj(R=30.0, duz=20.0, ds=0.2):
    """Yolu küçük adımlarla (ds metre) çizer. Her nokta için x, y ve yön (psi) döner."""
    n_duz = round(duz / ds)
    n_viraj = round(R * np.pi / 2 / ds)          # 90° = çeyrek çember
    # Her noktadaki eğrilik (κ = 1/R; sola dönüş pozitif, Bölüm 5)
    kappa = np.concatenate([
        np.zeros(n_duz),
        np.full(n_viraj, 1 / R),
        np.full(n_viraj, -1 / R),
        np.zeros(n_duz + 1),
    ])
    x, y, psi = [0.0], [0.0], [0.0]
    for k in kappa[:-1]:
        orta = psi[-1] + k * ds / 2
        x.append(x[-1] + ds * np.cos(orta))
        y.append(y[-1] + ds * np.sin(orta))
        psi.append(psi[-1] + k * ds)
    return np.array(x), np.array(y), np.array(psi)


def en_yakin_nokta(yol_x, yol_y, x, y):
    return int(np.argmin((yol_x - x) ** 2 + (yol_y - y) ** 2))


def yanal_sapma(yol_x, yol_y, yol_psi, x, y):
    """e_y: yolun gidiş yönüne göre solda pozitif (Bölüm 5)."""
    i = en_yakin_nokta(yol_x, yol_y, x, y)
    dx, dy = x - yol_x[i], y - yol_y[i]
    return -np.sin(yol_psi[i]) * dx + np.cos(yol_psi[i]) * dy
