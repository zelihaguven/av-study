# Issue taslağı: planning `dt` (0,05 s, "50Hz" yorumlu) döngünün gerçek periyoduyla uyuşmuyor

**Durum:** Taslak, gönderilmedi. **Hedef:** `autowarefoundation/autoware.privately-owned-vehicles`.
**Güven:** A1'den düşük. C++'ı derleyip çalıştırmadım; etki kod okumasından ve basit hesaptan geliyor.

## Türkçe özet

- `planning/config.hpp`: `// 50Hz control period` yorumu, değer `dt = 0.05` (yani 20 Hz).
- Geçmiş: `dt = 0.05` Haziran 2026'da (`18dfb192`) zaman tabanlı MPC'nin adımı olarak doğmuş (N = 20, 1 s ufuk).
  Temmuz'da (`8f9907e0`) MPC uzamsal hâle gelmiş (`DS = 0.5` m) ve `dt` "hâlâ planning.cpp'de kullanılıyor" diye
  kalmış; "50Hz" yorumu o sırada eklenmiş. Kasım'da MISRA refactor'ıyla `config.hpp`'ye taşınmış.
- Bugünkü tek etkili kullanım: eğrilik türevi `dkappa_ds = Δκ / (v · dt)` (`planning.cpp:41-42`). Bu türev MPC'nin
  10 m'lik referans eğriliğini belirliyor (`c3 = dkappa_ds / 6`, `:79`). Ama planlama her kamera karesinde bir kez
  çağrılıyor, yani gerçek periyot kaynağa bağlı: V4L2 varsayılanı 10 fps (0,1 s), video dosyası kendi fps'i.
  Sabit 0,05 s ile türev 10 Hz'de **2 kat büyük**, 30 fps'te 0,67 kat küçük.
- `v_schedule` de `dt` ile ilerletiliyor ama bugün yalnız ilk elemanı kullanılıyor (`lateral_planning.cpp:40,132`),
  pratik etkisi yok; yine de zaman adımıyla uzamsal adımı karıştırıyor.
- Öneri: döngüler arasındaki gerçek süreyi (kare zaman damgası) kullan, yorumu düzelt.

---

## Issue metni (İngilizce)

**Title:** planning: `dt = 0.05` ("50Hz control period") does not match the actual planning loop period

### Summary

`VisionPilot/modules/safety_guardian/planning/include/planning/config.hpp` defines

```cpp
// 50Hz control period — used by planning.cpp
inline constexpr double dt = 0.05;
```

0.05 s is 20 Hz, not 50 Hz. More importantly, the planner is called once per camera frame
(`app/vision_pilot.cpp`, `planner.compute_plan(...)`), so the real cycle period is set by the input source
(`source.v4l2_fps = 10` by default, or the video file's FPS), not by `dt`.

### Where `dt` matters

- `planning.cpp:41-42`: `ds_cycle = v * dt; raw_dkappa_ds = (kappa - prev_kappa_) / ds_cycle;`
  `dkappa_ds` is the spatial rate of curvature change between consecutive cycles. It sets the cubic term of the
  MPC reference curve (`c3 = dkappa_ds / 6`, `planning.cpp:79`) and therefore the curvature schedule over the
  10 m horizon. If the loop actually runs at 10 Hz, the travelled distance is `v * 0.1`, so `dkappa_ds` is
  overestimated by 2× (before the `RATE_MAX = 0.15` clamp and the EMA). At 30 FPS video input it is underestimated
  by 1.5×.
- `planning.cpp:54-66`: `v_schedule` is propagated with `dt` over `N = 20` steps, while the MPC steps are spatial
  (`DS = 0.5` m, i.e. `DS / v` seconds per step). Today only `v_schedule[0]` is read
  (`lateral_planning.cpp:40,132`), so this has no effect yet, but it will if the full schedule is used later.

### History (for context)

- `18dfb192` (2026-06-11): `double dt = 0.05;` introduced as the time step of the original MPC (N = 20, 1 s horizon).
- `8f9907e0` (2026-07-24): MPC became spatial; `dt` kept with the comment `// 50Hz control period — still used by planning.cpp`.
- `0b0ae12e` (2026-11-16): moved to `config.hpp` in the MISRA refactor.

### Suggested fix

1. Pass the elapsed time since the previous plan (e.g. from frame timestamps) into `compute_plan` and use it for
   `ds_cycle`; keep a lower bound for robustness. Alternatively, accumulate odometry distance directly.
2. If a fixed period is intended, derive it from the configured camera rate and fix the comment (0.05 s = 20 Hz).
3. For `v_schedule`, step by `DS / max(v, v_min)` so that index `i` corresponds to the spatial step `i * DS`.

Related: the fusion modules also assume a fixed nominal `dt = 0.10` (`lateral_fusion` / `longitudinal_fusion`
defaults; `update()` is called without a dt in `inference.cpp:207`). A single source of truth for the cycle time
would make both consistent.

Question for maintainers: what is the intended planning/control rate for VisionPilot 1.0 (10 Hz like the fusion, or faster)?

---

## Göndermeden önce kontrol listesi

- [ ] `main`'de satırları yeniden doğrula
- [ ] Mümkünse C++'ı derleyip `dkappa_ds`'yi 10 Hz video ile logla (2× iddiasını ölçümle destekle)
- [ ] Mevcut issue ara
- [ ] Önce PoV WG Discussions'ta "amaçlanan hız nedir?" diye sormak daha uygun olabilir; issue sonra
