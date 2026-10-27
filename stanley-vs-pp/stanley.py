"""Stanley kontrolcü (Ders notları, Bölüm 5).

    δ = −e_ψ − arctan( k · e_y / (k_s + v) )

e_ψ : yön hatası = aracın yönü − yolun yönü
e_y : ÖN AKSIN yola göre yanal sapması (solda pozitif)
k   : yanal sapmaya ne kadar sert tepki verileceği
k_s : yumuşatma sabiti (hız sıfıra yaklaşınca payda sıfır olmasın diye)
"""
import numpy as np
from arac_modeli import DINGIL_MESAFESI, aci_sar
from yol import en_yakin_nokta


def stanley(durum, yol_x, yol_y, yol_psi, k=1.0, k_s=1.0):
    x, y, psi, v = durum

    # 1. Durum arka aksı tarif ediyor; Stanley ön aksa bakar.
    #    Ön aks, arka aksın L kadar önündedir (aracın baktığı yönde).
    on_x = x + DINGIL_MESAFESI * np.cos(psi)
    on_y = y + DINGIL_MESAFESI * np.sin(psi)

    # 2. Ön aksa en yakın yol noktası
    i = en_yakin_nokta(yol_x, yol_y, on_x, on_y)

    # 3. Yanal sapma e_y: ön aksın, yolun o noktasına göre ne kadar solda olduğu
    dx, dy = on_x - yol_x[i], on_y - yol_y[i]
    e_y = -np.sin(yol_psi[i]) * dx + np.cos(yol_psi[i]) * dy

    # 4. Yön hatası e_ψ (açı sarma ile -π..+π aralığına)
    e_psi = aci_sar(psi - yol_psi[i])

    # 5. Formül: önce yönü düzelt, sonra sapmayı
    return -e_psi - np.arctan2(k * e_y, k_s + v)
