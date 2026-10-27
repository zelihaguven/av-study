"""Pure Pursuit kontrolcü (Ders notları, Bölüm 5)."""
import numpy as np
from arac_modeli import DINGIL_MESAFESI
from yol import en_yakin_nokta


def pure_pursuit(durum, yol_x, yol_y, ileri_bakis, ds=0.2):
    x, y, psi, v = durum

    # 1. Yolda bana en yakın noktayı bul, oradan ileri_bakis metre ilerideki hedefi seç
    i = en_yakin_nokta(yol_x, yol_y, x, y)
    j = min(len(yol_x) - 1, i + round(ileri_bakis / ds))
    hx, hy = yol_x[j], yol_y[j]

    # 2. α: hedef, aracın baktığı yöne göre kaç radyan yanda?
    alfa = np.arctan2(hy - y, hx - x) - psi
    L_d = np.hypot(hx - x, hy - y)

    # 3. Formül: δ = arctan(2 L sin α / L_d)
    return np.arctan2(2 * DINGIL_MESAFESI * np.sin(alfa), L_d)
