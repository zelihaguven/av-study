"""Kinematik bisiklet modeli (Ders notları, Bölüm 4).

Aracın durumu dört sayıdır:  [x, y, psi, v]
    x, y : arka aksın konumu (metre)
    psi  : aracın baktığı yön (radyan)
    v    : hız (m/s)
Araca verilen komutlar:  delta (direksiyon açısı, radyan) ve a (ivme, m/s²)
"""
import numpy as np

DINGIL_MESAFESI = 2.7               # L (metre)
MAKS_DIREKSIYON = np.deg2rad(35)    # direksiyon en fazla 35° dönebilir


def aci_sar(aci):
    """Açıyı -π ile +π arasına getirir (Bölüm 3, açı sarma)."""
    return (aci + np.pi) % (2 * np.pi) - np.pi


def degisim_hizi(durum, delta, a):
    """Bölüm 4'teki dört denklem: durumun saniyede ne kadar değiştiği."""
    x, y, psi, v = durum
    return np.array([
        v * np.cos(psi),                         # ẋ
        v * np.sin(psi),                         # ẏ
        v / DINGIL_MESAFESI * np.tan(delta),     # ψ̇
        a,                                       # v̇
    ])


def adim(durum, delta, a, dt):
    """Durumu dt saniye ilerletir (RK4 yöntemi, Bölüm 4)."""
    delta = np.clip(delta, -MAKS_DIREKSIYON, MAKS_DIREKSIYON)
    k1 = degisim_hizi(durum, delta, a)
    k2 = degisim_hizi(durum + dt / 2 * k1, delta, a)
    k3 = degisim_hizi(durum + dt / 2 * k2, delta, a)
    k4 = degisim_hizi(durum + dt * k3, delta, a)
    yeni = durum + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    yeni[2] = aci_sar(yeni[2])
    return yeni
