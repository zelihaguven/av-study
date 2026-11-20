# Medium yazı taslakları

**English versions:** [`en/`](en/) (posts), [`gorseller/en/`](gorseller/en/) (covers and figures in reading order).
English figures are generated with `AV_LANG=en` into each module's `results/en/`.

`docs/writing-plan.md`'deki 5 yazının taslakları. Kurallar:

- Yazılar öğrenileni anlatır; Autoware'e katkı yapıldığını ima etmez.
- Sayılar ve grafikler repodaki koddan; her yazı ilgili klasöre ve `results/` grafiğine link verir.
- Linkler `main` dalına göre: yayımlamadan önce `claude/kind-ride-m3ydf3` dalının `main`'e birleştirilmiş olması gerekir.
- Görseller Medium'a ayrıca yüklenir. Hepsi [`gorseller/`](gorseller/) altında, yazı başına bir klasörde ve yazıdaki
  sırayla numaralı: `00_kapak.png` (kapak), `01_…`, `02_…`. Yeniden üretmek için `python docs/medium/make_images.py`.
- Yayımlamadan önce kendi sesinle gözden geçir; bunlar taslak.

| # | Dosya | Modül |
|---|---|---|
| 1 | [`01-mimari.md`](01-mimari.md) | 00 |
| 2 | [`02-bisiklet-modeli.md`](02-bisiklet-modeli.md) | 01 |
| 3 | [`03-pure-pursuit-stanley.md`](03-pure-pursuit-stanley.md) | 02 |
| 4 | [`04-kalman.md`](04-kalman.md) | 03 |
| 5 | [`05-tek-kameradan-direksiyona.md`](05-tek-kameradan-direksiyona.md) | 04, 05 |
