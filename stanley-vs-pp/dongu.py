"""Kapalı çevrim: ölç → karar ver → hareket et (Ders notları, Bölüm 8).

Her kontrolcü aynı şekilde çağrılır: kontrolcu(durum, yol) → direksiyon açısı
"""
import numpy as np
from arac_modeli import adim, MAKS_DIREKSIYON
from yol import s_viraj, en_yakin_nokta, yanal_sapma

DT = 0.05  # saniyede 20 adım


def surus(kontrolcu, hiz=10.0, baslangic_ofset=2.0):
    yol = s_viraj()
    yol_x, yol_y, yol_psi = yol
    durum = np.array([0.0, baslangic_ofset, 0.0, hiz])
    kayit = {"x": [], "y": [], "sapma": [], "direksiyon": [], "t": []}
    t = 0.0
    while en_yakin_nokta(yol_x, yol_y, durum[0], durum[1]) < len(yol_x) - 5:
        delta = np.clip(kontrolcu(durum, yol), -MAKS_DIREKSIYON, MAKS_DIREKSIYON)
        kayit["x"].append(durum[0])
        kayit["y"].append(durum[1])
        kayit["sapma"].append(yanal_sapma(yol_x, yol_y, yol_psi, durum[0], durum[1]))
        kayit["direksiyon"].append(np.rad2deg(delta))
        kayit["t"].append(t)
        durum = adim(durum, delta, a=0.0, dt=DT)
        t += DT
    return {k: np.array(v) for k, v in kayit.items()}, yol


def ozet(kayit):
    """Virajdaki en büyük sapma (ilk 2,5 s'lik ofset düzeltmesi hariç) ve direksiyon sallantısı."""
    viraj = kayit["t"] > 2.5
    en_buyuk = np.max(np.abs(kayit["sapma"][viraj]))
    sallanti = np.sqrt(np.mean((np.diff(kayit["direksiyon"]) / DT) ** 2))
    return en_buyuk, sallanti
