"""Medium yazıları için görsel klasörü: kapaklar + yazıdaki sırayla numaralanmış görseller.

    python docs/medium/make_images.py
Çıktı: docs/medium/gorseller/<yazı>/00_kapak.png, 01_..., 02_... (Medium'a bu sırayla yüklenir).
"""
import re
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "gorseller"
POSTS = [
    ("01-mimari", "1-mimari", "Bir otonom aracın\nyazılımı kaç\nparçadan oluşur?", "Modüler stack ile tek kameralı L2", None),
    ("02-bisiklet-modeli", "2-bisiklet-modeli", "Bisiklet modeli", "Otonom sürüşün en küçük simülatörü", "01-vehicle-model/results/circle.png"),
    ("03-pure-pursuit-stanley", "3-pure-pursuit-stanley", "Pure Pursuit ile Stanley\naynı virajda", "Neden farklı davranırlar?", "02-control/results/s_curve_paths.png"),
    ("04-kalman", "4-kalman", "Kalman filtresi:\nne kadar\nbilmediğini bilmek", "Gürültülü ölçümden güvenilir duruma", "03-tracking/results/cipo.png"),
    ("05-tek-kameradan-direksiyona", "5-tek-kameradan-direksiyona", "Tek kameradan\ndireksiyona", "Takip katmanı sandığımız işi yapıyor mu?", "04-perception/results/overlay_1_otoyol.png"),
]
BG, FG, ACCENT, MUTED = "#0f1b2d", "#f4f6fa", "#4aa3ff", "#9fb0c8"


def flow(fig):
    """1. kapak: büyük kutulu mini akış (geniş mimari diyagram kapakta okunmuyor)."""
    ax = fig.add_axes([0.55, 0.10, 0.41, 0.80])
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    steps = ["Kamera", "Algı (öğrenilmiş)", "Takip (filtre)", "Kontrol", "Araç"]
    for k, s in enumerate(steps):
        y = 0.9 - k * 0.2
        col = ACCENT if k in (1, 2) else "#24364f"
        ax.add_patch(plt.Rectangle((0.15, y - 0.07), 0.7, 0.12, color=col, ec=FG, lw=1.5))
        ax.text(0.5, y - 0.01, s, color=FG, fontsize=20, ha="center", va="center", weight="bold")
        if k < len(steps) - 1:
            ax.annotate("", xy=(0.5, y - 0.12), xytext=(0.5, y - 0.07),
                        arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=2))


def cover(i, title, subtitle, figure, path):
    fig = plt.figure(figsize=(14, 7.88), dpi=100)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.06, 0.86, f"OTONOM ARAÇ YAZILIMI · {i}/5", color=ACCENT, fontsize=17, weight="bold")
    ax.text(0.06, 0.76, title, color=FG, fontsize=38, weight="bold", va="top", linespacing=1.15)
    ax.text(0.06, 0.25, subtitle, color=MUTED, fontsize=22, va="top")
    ax.plot([0.06, 0.16], [0.31, 0.31], color=ACCENT, lw=4)
    ax.text(0.06, 0.08, "github.com/zelihaguven/av-study", color=MUTED, fontsize=14)
    if figure is None:
        flow(fig)
    else:
        img = mpimg.imread(ROOT / figure)
        ia = fig.add_axes([0.56, 0.12, 0.40, 0.76])
        ia.imshow(img)
        ia.set_axis_off()
    fig.savefig(path, facecolor=BG)
    plt.close(fig)


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    for i, (md, folder, title, subtitle, figure) in enumerate(POSTS, 1):
        d = OUT / folder
        d.mkdir(parents=True)
        cover(i, title, subtitle, figure, d / "00_kapak.png")
        text = (Path(__file__).resolve().parent / f"{md}.md").read_text()
        imgs = re.findall(r"!\[[^\]]*\]\(([^)]+\.png)\)", text)
        for k, src in enumerate(imgs, 1):
            shutil.copy(ROOT / src, d / f"{k:02d}_{Path(src).name}")
        print(folder, ["00_kapak.png"] + sorted(p.name for p in d.iterdir() if p.name != "00_kapak.png"))


if __name__ == "__main__":
    main()
