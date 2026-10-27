# 04 — Öğrenilmiş Algı: VisionPilot Modellerini Okumak

## Öğrenme hedefi

Bu modülde model eğitilmez. Hedef, mevcut açık kaynak modellerin **arayüzünü** ve
**sınırlarını** anlamaktır. Bir modelin ne aldığını, ne verdiğini, çıktısının
sonradan nasıl işlenip kontrolcünün kullanabileceği bir sayıya dönüştürüldüğünü
ve nerede bozulduğunu bilmek istiyoruz.

Odak modeller (VisionPilot):
- **EgoLanes**: tek kareden şerit çizgisi bölütleme ve sınıflandırma (ego sol / ego sağ / diğer)
- **AutoSteer**: ardışık iki kareden direksiyon / ego yol tahmini

Bu modül, 05'teki **sentetik ölçüm modelinin** gerçekçi olmasını sağlar: 05'te kullanacağın
gürültü seviyesi ve kayıp oranı burada gözlemlediğin davranışa dayanmalı.

Bu modül ayrıca vision_pilot kodunu okumanın gerekçesidir. Katkı fikri büyük ihtimalle buradan çıkar.

## Kurulum

Ek bağımlılıklar (PyTorch / ONNX Runtime / OpenCV vb.) ve model ağırlıklarının nereden
indirileceği **vision_pilot reposunun kendi README'sinden** alınmalı. Buraya sürüm yazılmadı
çünkü repo hızlı değişiyor. Bulduğun kurulum adımlarını aşağıya kendin yaz.

- Model ağırlıkları ve videolar **repoya commit edilmez** (`.gitignore` kapsıyor).
- Kullandığın modellerin ve verinin **lisansını** `notes.md`'ye not et.

```
# Kurulum adımları (doldur):
```

## Arayüz (`src/inspect_model.py`)

| Fonksiyon | Görev |
|---|---|
| `load_model(name)` | Modeli yükler |
| `preprocess(frame)` | Ham kare → modelin beklediği tensör |
| `infer(model, inputs)` | Ham çıktı |
| `postprocess(name, raw)` | Ham çıktı → yorumlanabilir sonuç (maske, şerit eğrisi, açı) |
| `overlay(frame, result)` | Görselleştirme |

## Görevler

- [ ] vision_pilot'ta EgoLanes ve AutoSteer için inference kodunu bul; dosya yollarını `notes.md`'ye yaz
- [ ] Giriş/çıkış tensör şekillerini, normalizasyonu ve renk sırasını **koddan** belgele (dosya:satır referansıyla)
- [ ] Lisansı uygun bir açık sürüş videosu üzerinde iki modeli çalıştır
- [ ] `results/overlay_*.png`: en az 3 iyi kare
- [ ] `results/failures/`: en az 5 başarısızlık karesi (gece, yağmur, silik çizgi, şerit değiştirme, kavşak…)
- [ ] CPU'da kare başına süreyi ölç (kendi makinen, donanımını yaz)
- [ ] Maskeden kontrolcünün kullandığı `e_y`, `e_ψ`'ye giden yolu (postprocess) adım adım `notes.md`'de anlat

## Kabul kriteri

- [ ] Tensör tablosu dolu ve her satırda kod referansı var
- [ ] 5 başarısızlık karesinin her birine bir cümlelik **neden** tahmini yazılmış
- [ ] Ölçülen `e_y` titreşiminden 05 için gürültü std ve kayıp oranı tahmini çıkarılmış (sayı + nasıl ölçtüğün)

### Tensör tablosu

| Model | Giriş şekli | Normalizasyon | Çıkış şekli | Çıkışın anlamı | Kod referansı |
|---|---|---|---|---|---|
| EgoLanes | | | | | |
| AutoSteer | | | | | |

## Yazı

→ `docs/writing-plan.md` #5 (05 ile birlikte)
