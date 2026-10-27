"""Deney 1: Pure Pursuit'te ileri bakış mesafesinin etkisi.

Çalıştırmak için:  python simulasyon.py
"""
import matplotlib.pyplot as plt
from dongu import surus, ozet
from ciz import ciz
from pure_pursuit import pure_pursuit

if __name__ == "__main__":
    sonuclar = []
    for ileri_bakis, renk in [(3, "tab:red"), (8, "tab:blue"), (15, "tab:green")]:
        kontrolcu = lambda d, yol, Ld=ileri_bakis: pure_pursuit(d, yol[0], yol[1], Ld)
        kayit, yol = surus(kontrolcu)
        etiket = f"L_d = {ileri_bakis} m"
        en_buyuk, sallanti = ozet(kayit)
        print(f"{etiket:>12}:  virajda en büyük sapma {en_buyuk:.2f} m,  sallantı {sallanti:.1f} °/s")
        sonuclar.append((etiket, renk, kayit))
    ciz(sonuclar, yol, "Pure Pursuit: ileri bakış mesafesi", "sonuc.png")
    plt.show()
