# Bisiklet modeli, Pure Pursuit ve Stanley

Ders notlarındaki Bölüm 4 (kinematik bisiklet modeli) ve Bölüm 5'teki (Pure Pursuit,
Stanley) kavramların en küçük çalışan hali. Araç, yolun 2 m solundan başlayıp S şeklinde
bir yolu izliyor.

| Dosya | Ne yapar | Notlardaki bölüm |
|---|---|---|
| `arac_modeli.py` | Aracı küçük zaman adımlarıyla ilerletir | Bölüm 3–4 |
| `yol.py` | S-viraj yolunu üretir, yanal sapmayı hesaplar | Bölüm 5 |
| `pure_pursuit.py` | İleri bakarak direksiyon açısını hesaplar | Bölüm 5 |
| `stanley.py` | Ön aksın hatalarına bakarak direksiyon açısını hesaplar | Bölüm 5 |
| `dongu.py` | Ölç → karar ver → hareket et döngüsü | Bölüm 8 |
| `ciz.py` | Ortak grafik | |
| `simulasyon.py` | Deney 1: Pure Pursuit'te ileri bakış mesafesi | |
| `stanley_vs_pp.py` | Deney 2: Stanley ile Pure Pursuit aynı virajda | |

## Çalıştırma (Mac)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install numpy matplotlib
python simulasyon.py
python stanley_vs_pp.py
```

## Deneyebileceklerin

- Hızı 20 m/s'ye çıkar (`dongu.surus(..., hiz=20)`): hangi ayar bozuluyor?
- `yol.py`'de `R`'yi 15'e düşür: viraj keskinleşince ne oluyor?
- Pure Pursuit'te `L_d = 0.6 * v` kuralını dene.
- Stanley'de `k_s`'yi 0,1'e düşür ve hızı 2 m/s yap: düşük hızda tepki ne kadar sertleşiyor?
- Stanley'ye feedforward ekle: formüle `+ arctan(L · κ)` terimini ekle ve virajdaki sapmaya bak.
