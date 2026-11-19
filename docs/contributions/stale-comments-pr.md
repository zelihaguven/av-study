# PR taslağı: VisionPilot'ta kodla uyuşmayan yorumlar (sadece dokümantasyon)

**Durum:** Taslak, gönderilmedi. **Hedef:** `autowarefoundation/autoware.privately-owned-vehicles`.
**Tür:** Yalnız yorum değişikliği; davranış değişmez. "Good first PR" boyutunda.
Satırlar `65375ec2cf`'e göre (19 Kas 2026'da `main` ile aynı).

## Değişiklikler

| Dosya:satır | Şu an | Gerçek | Önerilen yorum |
|---|---|---|---|
| `VisionPilot/modules/models/include/models/auto_speed.hpp:16, 35-36` | "letterbox… padding with (114, 114, 114)", "reverse the letterbox" | Ön işleme letterbox yapmıyor; üstten 2:1 kırpıp 1024×512'ye küçültüyor (`image_preprocessor.cpp:18-21`) | "Input: frame top-cropped to 2:1 and resized to 1024×512 (no letterbox), see image_preprocessor.cpp" |
| `VisionPilot/modules/sensing/image_preprocessing/include/.../image_preprocessor.hpp:14` | "raw camera pixel → warped 1024×512 BEV" | `C` ham kareyi ZOD kanonik perspektif görünümüne çeviriyor; kuşbakışı değil (ufuk ~260. satırda) | "raw camera pixel → canonical (ZOD model-view) 1024×512 perspective image used by AutoDrive" |
| `VisionPilot/modules/safety_guardian/fusion/include/fusion/lateral_fusion.hpp:35, 55, 134` | "CTE = c", "Yaw = atan(b)", "= atan(b)" | CTE ve yaw en yakın gözlenen noktada (`x_ref = min x`) hesaplanıyor: `y(x_ref)`, `atan(2a·x_ref + b)` (`lateral_fusion.cpp:323-336`) | "CTE = y(x_ref), yaw = atan(2a·x_ref + b), x_ref = nearest observed waypoint (no extrapolation to x = 0)" |
| `lateral_fusion.hpp:88` | "thresh raised 0.20→0.25 m" | değer `0.20f` (`:93`) | yorumu 0,20 m'ye göre düzelt (veya değer gerçekten 0,25 olmalıysa ayrı tartışma) |
| `lateral_fusion.hpp:90` | "min_inliers lowered 20→15" | değer `12` (`:99`) | yorumu 12'ye göre düzelt |
| `VisionPilot/modules/safety_guardian/planning/include/planning/config.hpp` (kapanış) | `} // namespace visionpilot::models` | namespace `planning` | `} // namespace planning` |
| `config.hpp` `dt` yorumu | "50Hz control period" | 0,05 s = 20 Hz | Ayrı issue'da ele alınıyor (`planning-dt-mismatch.md`); bu PR'a karıştırma |

`auto_speed.hpp:54`'teki "sigmoid class probability threshold" yorumu da yanıltıcı, ama A1 issue'sunda konuşulacağı için
bu PR'a dahil değil.

## PR açıklaması (İngilizce)

**Title:** docs(VisionPilot): fix comments that no longer match the code

Comment-only changes, no functional impact:

- `auto_speed.hpp`: preprocessing is a 2:1 top crop + resize, not a letterbox with 114 padding.
- `image_preprocessor.hpp`: the `C` warp produces the canonical ZOD model-view perspective image for AutoDrive, not a BEV.
- `lateral_fusion.hpp`: CTE/yaw are evaluated at `x_ref` (nearest observed waypoint), not at `x = 0`; RANSAC
  threshold and min-inlier comments updated to the actual values (0.20 m, 12).
- `planning/config.hpp`: closing namespace comment.

Found while re-implementing the VisionPilot pre/post-processing in Python for a study project.

## Göndermeden önce

- [ ] `main`'de satırları yeniden doğrula
- [ ] Reponun katkı kurallarına (`CONTRIBUTING.md`, DCO `Signed-off-by` gerekiyor mu) bak; geçmişteki commit'lerde `Signed-off-by` var
- [ ] Fork + dal + tek commit
