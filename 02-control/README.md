# 02 — Kontrol: PID, Pure Pursuit, Stanley

## Öğrenme hedefi

Aynı araç modeli (01) ve aynı referans yollar (`common`) üzerinde üç klasik kontrolcüyü
yazıp **ölçerek** karşılaştırmak:

- **PID**: boylamsal hız kontrolü (ACC'nin en basit hali)
- **Pure Pursuit**: geometrik yanal kontrol, ileri bakış noktasına yay çizer
- **Stanley**: yön hatası + yanal hata, ön aks referanslı

Modül sonunda şunları cevaplayabilmelisin:
- Pure Pursuit virajda neden içeri keser? Bu hatayı ileri bakış mesafesi nasıl değiştirir?
- Stanley düşük hızda neden sert davranır ve yumuşatma terimi ne işe yarar?
- Hızla ölçeklenen ileri bakış (`Ld = k·v`) neden sabit ileri bakıştan iyidir?
- Eğrilik süreksizliğinde (S-viraj geçişi) hangi kontrolcü nasıl bozulur?

## Okumalar

- Snider (2009), *Automatic Steering Methods for Autonomous Automobile Path Tracking*
- Paden ve ark. (2016) survey: path tracking bölümü

## Arayüz

| Dosya | İçerik |
|---|---|
| `src/controllers.py` | `PID` sınıfı, `pure_pursuit(...)`, `stanley(...)` |
| `src/closed_loop.py` | `run_closed_loop(path, controller, v_ref, x0_offset, dt, T)`: 01'in modeliyle kapalı çevrim; zaman, durumlar, direksiyon, CTE döndürür |

Kazançlar (`k`, `Ld`, PID katsayıları) senin seçimin; varsayılan değerleri koda yaz,
seçim gerekçesini `notes.md`'ye.

## Görevler

- [ ] PID hız kontrolü → `test_pid_speed` yeşil
- [ ] Pure Pursuit → düz yolda 1 m ofsetten toparlanma
- [ ] Stanley → aynı test
- [ ] S-virajda (R = 50 m, v = 10 m/s) iki kontrolcü
- [ ] `results/s_curve_paths.png`: yol + iki kontrolcünün yörüngesi
- [ ] `results/s_curve_cte.png`: CTE(t), iki kontrolcü üst üste
- [ ] `results/lookahead_sweep.png`: Pure Pursuit için `Ld` ∈ [2, 15] m vs RMS CTE ve maks |direksiyon hızı|
- [ ] `notes.md`: yukarıdaki 4 soruya grafiklere dayanan cevaplar

## Kabul kriteri

- [ ] `pytest 02-control` tamamen yeşil (eşikler `tests/test_control.py` içinde)
- [ ] 3 grafik üretilmiş ve bu README'den link verilmiş
- [ ] `notes.md`'de her soru için en az bir grafiğe atıf var

## Yazı

→ `docs/writing-plan.md` #3
