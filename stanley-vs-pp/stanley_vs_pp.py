"""Deney 2: Stanley ile Pure Pursuit aynı virajda.

Çalıştırmak için:  python stanley_vs_pp.py
"""
import matplotlib.pyplot as plt
from dongu import surus, ozet
from ciz import ciz
from pure_pursuit import pure_pursuit
from stanley import stanley

KONTROLCULER = [
    ("Pure Pursuit, L_d = 8 m", "tab:blue",
     lambda d, yol: pure_pursuit(d, yol[0], yol[1], 8.0)),
    ("Stanley, k = 0,5", "tab:orange",
     lambda d, yol: stanley(d, yol[0], yol[1], yol[2], k=0.5)),
    ("Stanley, k = 2", "tab:purple",
     lambda d, yol: stanley(d, yol[0], yol[1], yol[2], k=2.0)),
]

if __name__ == "__main__":
    sonuclar = []
    for etiket, renk, kontrolcu in KONTROLCULER:
        kayit, yol = surus(kontrolcu)
        en_buyuk, sallanti = ozet(kayit)
        print(f"{etiket:>24}:  virajda en büyük sapma {en_buyuk:.2f} m,  sallantı {sallanti:.1f} °/s")
        sonuclar.append((etiket, renk, kayit))
    ciz(sonuclar, yol, "Stanley ve Pure Pursuit", "stanley_vs_pp.png")
    plt.show()
