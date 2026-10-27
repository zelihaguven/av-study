# 05 — Entegrasyon: Mini VisionPilot

## Öğrenme hedefi

Önceki modülleri tek bir kapalı çevrimde birleştirmek:

```
araç modeli (01) ──durum──▶ sentetik algı ──z (gürültülü, aralıklı)──▶ takip (03) ──x̂──▶ şerit tutma kontrolü ──δ──▶ araç modeli
```

Gerçek bir kamera yerine **sentetik algı** kullanılır: simülasyondaki gerçek durumdan
`[e_y, e_ψ, κ]` hesaplanır, üstüne gürültü ve kayıp eklenir. Gürültü değerlerini 04'te
gözlemlediklerine göre ayarla. Bu yapı, VisionPilot'un "öğrenilmiş algı + klasik takip +
feedforward/feedback kontrol" fikrinin oyuncak bir kopyasıdır.

Modül sonunda şunları açıklayabilmelisin:
- Takip katmanı kaldırılınca ne bozulur: yanal hata mı, direksiyon pürüzsüzlüğü mü? Neden?
- Eğrilik feedforward'ı hangi hatayı ortadan kaldırır?
- Algı kaybı oranı arttıkça sistem nerede ve nasıl çöker?

## İşaret kuralları

- `e_y`: yanal hata, yol yönüne göre sol pozitif (`common` ile aynı)
- `e_ψ = yaw_araç − yaw_yol`
- `κ`: yol eğriliği, sola dönüş pozitif

## Arayüz

| Dosya | İçerik |
|---|---|
| `src/perception_sim.py` | `measure_lane(state, path, rng, noise, p_drop)` → `z` veya `None` |
| `src/lane_keeping.py` | `LaneTracker` (03'ün `KalmanFilter`'ını kullanır, 3 durumlu model senin), `lane_keep_steer(...)` |
| `src/loop.py` | `run(path, v, noise, p_drop, use_tracker, seed)` → zaman, durumlar, direksiyon, gerçek CTE |

## Görevler

- [ ] Sentetik algı + kayıp
- [ ] 3 durumlu şerit modeli `[e_y, e_ψ, κ]`, direksiyonu girdi olarak kullanan tahmin adımı
- [ ] Feedforward (`κ`'dan) + feedback (`e_y`, `e_ψ`'den) direksiyon
- [ ] `results/closed_loop.png`: tracker'lı / tracker'sız CTE ve direksiyon, alt alta
- [ ] `results/dropout_sweep.png`: kayıp oranı ∈ {0, 0.1, 0.2, 0.3, 0.5} vs maks |CTE|
- [ ] `results/ff_ablation.png`: feedforward açık/kapalı
- [ ] `notes.md`: 3 soruya grafiklere dayanan cevaplar ve VisionPilot mimarisiyle karşılaştırma (00'daki diyagrama atıf)

## Kabul kriteri

- [ ] `pytest 05-integration` tamamen yeşil
- [ ] 3 grafik üretilmiş, README'den link verilmiş
- [ ] `notes.md`'de modelin VisionPilot'tan **nerede farklı olduğu** en az 3 maddeyle yazılmış (dürüstlük bölümü)

## Yazı

→ `docs/writing-plan.md` #5
