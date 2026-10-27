# av-study — Otonom Araç Mimarisi Çalışma Reposu

Otonom sürüş yazılım mimarisini modül modül, **çalışan kod ve ölçülebilir kabul kriterleriyle**
öğrenmek için tutulan çalışma reposu. Hedef referans sistem: Autoware ekosistemi ve özellikle
tek kameralı L2 ADAS sistemi **VisionPilot** (Autoware Privately Owned Vehicle Working Group).

> Bu repo bir öğrenme kaydıdır. Autoware'in resmi bir parçası değildir ve Autoware'e katkı iddiası taşımaz.

## Kapsam

| Dahil | Dahil değil |
|---|---|
| Algoritma: araç modeli, kontrol, takip (filtreleme), algı modellerinin çıktısını kullanma | Gömülü sistem, mikrodenetleyici, firmware |
| Mimari: modüler stack ile uçtan uca (E2E) yaklaşımın karşılaştırması | Mekatronik, donanım kurulumu, sensör kalibrasyonu |
| Saf Python simülasyon (numpy + matplotlib) | Başlangıçta ROS 2 / CARLA (ileride opsiyonel) |

## Yapı

| Modül | Konu | Ne öğreniliyor | Durum |
|---|---|---|---|
| [`00-architecture`](00-architecture/) | Mimari | Modüler stack, VisionPilot veri akışı, modül arayüzleri | ⬜ |
| [`01-vehicle-model`](01-vehicle-model/) | Kinematik bisiklet modeli | Diğer modüllerin test edileceği simülatör | ⬜ |
| [`02-control`](02-control/) | Yanal/boylamsal kontrol | PID, Pure Pursuit, Stanley karşılaştırması | ⬜ |
| [`03-tracking`](03-tracking/) | Durum kestirimi | Kalman filtresi: şerit ve öndeki araç (CIPO) | ⬜ |
| [`04-perception`](04-perception/) | Öğrenilmiş algı | EgoLanes / AutoSteer çıktılarını okuma ve yorumlama | ⬜ |
| [`05-integration`](05-integration/) | Kapalı çevrim | Algı → takip → kontrol: mini VisionPilot | ⬜ |
| [`common`](common/) | Ortak araçlar | Referans yollar, metrikler, çizim | ⬜ |

Durum: ⬜ başlanmadı · 🟨 devam ediyor · ✅ kabul kriterleri sağlandı

**Bağımlılık sırası:** `00` → `01` → `common` → `02` → `03` → `04` → `05`.
`04`, `01–03`'ten bağımsız çalışılabilir; `05` hepsine bağlıdır.

## Her modülün düzeni

```
NN-modul/
├── README.md     # öğrenme hedefi, okumalar, görevler, KABUL KRİTERİ, yazı fikri
├── notes.md      # kendi notların (okurken / denerken)
├── src/          # implementasyon
├── tests/        # kabul kriterlerini kodlayan testler
└── results/      # üretilen grafikler ve sayılar (README'de referans verilir)
```

**Kural:** Bir modül, `tests/` altındaki testlerin hepsi geçtiğinde ve README'deki
"Kabul kriteri" bölümündeki yazılı maddeler (grafik, açıklama) tamamlandığında ✅ olur.
Testler baştan yazılı olduğu için başlangıçta **kırmızıdır**. İlerleme = yeşile dönen testler.

## Kurulum

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest                      # tüm modüller
pytest 02-control           # tek modül
```

`04-perception` ek bağımlılık ister, o modülün README'sine bak.

## Dokümanlar

- [`docs/reading-log.md`](docs/reading-log.md) — okunanlar ve her birinden 3 cümlelik çıkarım
- [`docs/glossary.md`](docs/glossary.md) — terimler sözlüğü (TR/EN)
- [`docs/writing-plan.md`](docs/writing-plan.md) — modül ↔ Medium yazısı eşleşmesi

## Lisans

MIT — bkz. [`LICENSE`](LICENSE).
