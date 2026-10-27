# 01 — Kinematik Bisiklet Modeli

## Öğrenme hedefi

Diğer tüm modüllerin üzerinde test edileceği **simülatörü** yazmak ve varsayımlarını bilmek.
Bu bir algoritma işidir: dört araba tekerleği iki tekerleğe indirgenir ve durum
`(x, y, yaw, v)` diferansiyel denklemlerle ilerletilir.

Modül sonunda şunları açıklayabilmelisin:
- Referans noktası arka aks mı, ağırlık merkezi mi? Seçim denklemleri nasıl değiştirir?
- Model hangi koşulda geçersizleşir? (Lastik kayması, yüksek yanal ivme.) Bu yüzden 02'deki testler hangi hız aralığında anlamlı?
- Euler ile RK4 entegrasyonu arasındaki fark ve `dt` seçiminin hataya etkisi

## Okumalar

- Kong ve ark. (2015), *Kinematic and Dynamic Vehicle Models for Autonomous Driving Control Design*
- Paden ve ark. (2016) survey: araç modelleri bölümü

## Arayüz (`src/bicycle.py`)

| Fonksiyon | Görev |
|---|---|
| `derivatives(state, accel, steer, params)` | `[ẋ, ẏ, ψ̇, v̇]` döndürür |
| `step(state, accel, steer, dt, params, method)` | Tek adım; `method` ∈ {`"euler"`, `"rk4"`}; direksiyon ve ivme sınırlanır, yaw `[-π, π]`'ye sarılır |
| `simulate(state0, accels, steers, dt, params, method)` | Dizi halinde kontrol girdisi alır, `(N+1, 4)` durum dizisi döner |

Referans noktası: **arka aks merkezi** (Pure Pursuit bu tanımı kullanır).

## Görevler

- [ ] `derivatives` ve `step` (Euler) → testleri geçir
- [ ] RK4 ekle
- [ ] `results/circle.png`: sabit direksiyonla çember, teorik çember üst üste
- [ ] `results/dt_error.png`: `dt` ∈ {0.001, 0.01, 0.05, 0.1} için Euler ve RK4 çember yarıçap hatası (log ölçek)
- [ ] `notes.md`: modelin geçersiz olduğu durumlar, kendi cümlelerinle

## Kabul kriteri

- [ ] `pytest 01-vehicle-model` tamamen yeşil
- [ ] `circle.png` ve `dt_error.png` üretilmiş ve bu README'den link verilmiş
- [ ] `notes.md`'de "model ne zaman yanlış söyler" sorusuna en az 3 maddelik cevap var

## Yazı

→ `docs/writing-plan.md` #2
