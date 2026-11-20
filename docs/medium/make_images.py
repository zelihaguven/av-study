"""Medium yazıları için görsel klasörü: kapaklar + yazıdaki sırayla numaralanmış görseller.

    python docs/medium/make_images.py
Çıktı: docs/medium/gorseller/<yazı>/00_kapak.png, 01_..., 02_... (Medium'a bu sırayla yüklenir) ve
İngilizce sürüm docs/medium/gorseller/en/<post>/00_cover.png, 01_...
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
POSTS_EN = [
    ("01-architecture", "1-architecture", "How many pieces make\nup an autonomous\nvehicle's software?", "A modular stack vs. a single-camera L2 system", None),
    ("02-bicycle-model", "2-bicycle-model", "The bicycle model", "The smallest simulator in autonomous driving", "01-vehicle-model/results/en/circle.png"),
    ("03-pure-pursuit-stanley", "3-pure-pursuit-stanley", "Pure Pursuit and\nStanley on the\nsame curve", "Why do they behave differently?", "02-control/results/en/s_curve_paths.png"),
    ("04-kalman", "4-kalman", "The Kalman filter:\nknowing how much\nyou don't know", "From noisy measurements to a reliable state", "03-tracking/results/en/cipo.png"),
    ("05-single-camera-to-steering", "5-single-camera-to-steering", "From a single\ncamera to\nsteering", "Does the tracking layer do the job we think it does?", "04-perception/results/overlay_1_otoyol.png"),
]
BG, FG, ACCENT, MUTED = "#0f1b2d", "#f4f6fa", "#4aa3ff", "#9fb0c8"


def flow(fig, en=False):
    """1. kapak: büyük kutulu mini akış (geniş mimari diyagram kapakta okunmuyor)."""
    ax = fig.add_axes([0.55, 0.10, 0.41, 0.80])
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    steps = (["Camera", "Perception (learned)", "Tracking (filter)", "Control", "Vehicle"] if en
             else ["Kamera", "Algı (öğrenilmiş)", "Takip (filtre)", "Kontrol", "Araç"])
    for k, s in enumerate(steps):
        y = 0.9 - k * 0.2
        col = ACCENT if k in (1, 2) else "#24364f"
        ax.add_patch(plt.Rectangle((0.15, y - 0.07), 0.7, 0.12, color=col, ec=FG, lw=1.5))
        ax.text(0.5, y - 0.01, s, color=FG, fontsize=20, ha="center", va="center", weight="bold")
        if k < len(steps) - 1:
            ax.annotate("", xy=(0.5, y - 0.12), xytext=(0.5, y - 0.07),
                        arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=2))


def cover(i, title, subtitle, figure, path, en=False):
    fig = plt.figure(figsize=(14, 7.88), dpi=100)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    tag = "AUTONOMOUS DRIVING SOFTWARE" if en else "OTONOM ARAÇ YAZILIMI"
    ax.text(0.06, 0.86, f"{tag} · {i}/5", color=ACCENT, fontsize=17, weight="bold")
    ax.text(0.06, 0.76, title, color=FG, fontsize=38, weight="bold", va="top", linespacing=1.15)
    ax.text(0.06, 0.25, subtitle, color=MUTED, fontsize=22, va="top")
    ax.plot([0.06, 0.16], [0.31, 0.31], color=ACCENT, lw=4)
    ax.text(0.06, 0.08, "github.com/zelihaguven/av-study", color=MUTED, fontsize=14)
    if figure is None:
        flow(fig, en)
    else:
        img = mpimg.imread(ROOT / figure)
        ia = fig.add_axes([0.56, 0.12, 0.40, 0.76])
        ia.imshow(img)
        ia.set_axis_off()
    fig.savefig(path, facecolor=BG)
    plt.close(fig)


def table_png(rows, path, en):
    """Markdown tablosunu görsele çevirir (Medium'da tablo yok). Kalın (**) hücreler kalın çizilir."""
    clean = [[c.replace("`", "") for c in r] for r in rows]
    bold = [[c.startswith("**") and c.endswith("**") for c in r] for r in clean]
    clean = [[c.strip("*") for c in r] for r in clean]
    ncol = len(clean[0])
    widths = [max(len(r[j]) for r in clean) for j in range(ncol)]
    total = sum(widths)
    fig_w = min(14, max(7, 0.13 * total + 1.5))
    fig_h = 0.55 * len(clean) + 0.5
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=150)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
    ax.set_axis_off()
    tb = ax.table(cellText=clean, cellLoc="left", loc="center",
                  colWidths=[w / total for w in widths], bbox=[0, 0, 1, 1])
    tb.auto_set_font_size(False)
    for (r, c), cell in tb.get_celld().items():
        cell.set_edgecolor("#d0d7e2")
        cell.set_text_props(fontsize=12, color="#1b2433")
        cell.PAD = 0.04
        if r == 0:
            cell.set_facecolor(BG)
            cell.set_text_props(color=FG, weight="bold", fontsize=12)
        else:
            cell.set_facecolor("#f4f7fb" if r % 2 == 0 else "white")
            if bold[r][c]:
                cell.set_text_props(weight="bold")
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def blocks_in_order(text):
    """Yazıdaki görselleri ve tabloları okuma sırasıyla döndürür: (tür, veri, bölüm, önceki paragrafın başı,
    araya metin girmeden önceki bloğun sırası veya None)."""
    out, lines, i = [], text.split("\n"), 0
    heading, para_start, prev_blank, text_since = "", "", True, False
    while i < len(lines):
        ln = lines[i]
        m = re.match(r"\s*!\[([^\]]*)\]\(([^)]+\.png)\)", ln)
        stacked = len(out) if (out and not text_since) else None
        if ln.startswith("#"):
            heading = ln.lstrip("# ").strip()
            para_start, text_since = "", True
        if m:
            out.append(("img", (m.group(1), m.group(2)), heading, para_start, stacked))
            text_since = False
        elif ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            out.append(("table", rows, heading, para_start, stacked))
            text_since, prev_blank = False, False
            continue
        elif ln.strip() and not ln.startswith(("```", "*Bu bir", "*This is")) and not ln.startswith("#"):
            if prev_blank or re.match(r"\s*(\d+\.|-) ", ln):
                para_start = ln.strip()
            text_since = True
        prev_blank = not ln.strip()
        i += 1
    return out


def snippet(s, n=9):
    words = re.sub(r"[*`]", "", s).split()
    return " ".join(words[:n]) + (" …" if len(words) > n else "")


def build(posts, md_dir, out, cover_name, en):
    for i, (md, folder, title, subtitle, figure) in enumerate(posts, 1):
        d = out / folder
        d.mkdir(parents=True)
        cover(i, title, subtitle, figure, d / cover_name, en)
        text = (md_dir / f"{md}.md").read_text()
        guide = ([f"# {title.replace(chr(10), ' ')}: image order", "",
                  "| # | File | What it shows | Place it after |", "|---|---|---|---|",
                  f"| 00 | `{cover_name}` | Cover | Story header (top of the post) |"] if en else
                 [f"# {title.replace(chr(10), ' ')}: görsel sırası", "",
                  "| # | Dosya | Ne gösteriyor | Nereye |", "|---|---|---|---|",
                  f"| 00 | `{cover_name}` | Kapak | Yazının en üstü (kapak görseli) |"])
        nt = 0
        for k, (kind, data, heading, before, stacked) in enumerate(blocks_in_order(text), 1):
            if kind == "img":
                alt, src = data
                name = f"{k:02d}_{Path(src).name}"
                shutil.copy(ROOT / src, d / name)
                what = alt
            else:
                nt += 1
                name = f"{k:02d}_{'table' if en else 'tablo'}_{nt}.png"
                table_png(data, d / name, en)
                what = ("Table: " if en else "Tablo: ") + " / ".join(c.strip("*") for c in data[0] if c)
            if stacked:
                where = (f"Right below the previous one ({stacked:02d})" if en else f"Hemen bir öncekinin ({stacked:02d}) altına")
            else:
                where = (f"“{heading}” section, after the paragraph starting “{snippet(before)}”" if en
                         else f"“{heading}” bölümü, “{snippet(before)}” diye başlayan paragraftan sonra")
            guide.append(f"| {k:02d} | `{name}` | {what} | {where} |")
        (d / ("ORDER.md" if en else "SIRA.md")).write_text("\n".join(guide) + "\n")
        print(folder, sorted(p.name for p in d.iterdir()))


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    here = Path(__file__).resolve().parent
    build(POSTS, here, OUT, "00_kapak.png", en=False)
    build(POSTS_EN, here / "en", OUT / "en", "00_cover.png", en=True)


if __name__ == "__main__":
    main()
