"""Ortak grafik: aracın izi, yanal sapma, direksiyon açısı."""
import matplotlib.pyplot as plt


def ciz(sonuclar, yol, baslik, dosya):
    """sonuclar: [(etiket, renk, kayit), ...]"""
    fig, (ust, orta, alt) = plt.subplots(3, 1, figsize=(9, 11))
    for etiket, renk, k in sonuclar:
        ust.plot(k["x"], k["y"], color=renk, label=etiket)
        orta.plot(k["t"], k["sapma"], color=renk, label=etiket)
        alt.plot(k["t"], k["direksiyon"], color=renk, label=etiket)
    ust.plot(yol[0], yol[1], "k--", lw=1, label="yol")
    ust.set_aspect("equal"); ust.set_title(baslik); ust.set_xlabel("x (m)"); ust.set_ylabel("y (m)")
    orta.axhline(0, color="k", lw=0.5); orta.set_title("Yanal sapma"); orta.set_ylabel("e_y (m)")
    alt.set_title("Direksiyon açısı"); alt.set_ylabel("δ (derece)"); alt.set_xlabel("zaman (s)")
    for ax in (ust, orta, alt):
        ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(dosya, dpi=120)
    print(f"Grafik kaydedildi: {dosya}")
