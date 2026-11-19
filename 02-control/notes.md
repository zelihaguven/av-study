# 02 — Notlar

Tüm sayılar `python 02-control/src/plots.py` çıktısından. Araç modeli 01'deki kinematik bisiklet
(direksiyon gecikmesi yok, lastik kayması yok), `dt = 0,02 s`.

## Seçilen kazançlar ve gerekçe

**Hız PID'i: `(kp, ki, kd) = (2,0; 0,1; 0)`, çıkış ±3 m/s² ile sınırlı.**

- Tesis `v' = a`, yani saf bir integratör. İntegratörlü bir tesiste yalnız P bile kalıcı hatayı sıfıra
  götürür; `kp = 2` kapalı çevrimi zaman sabiti 0,5 s olan birinci dereceden sisteme çevirir.
- 0 → 10 m/s'de ilk ~3 s çıkış zaten +3 m/s²'de doymuş (10 / 3 ≈ 3,3 s). Sonuç: %2 bandına
  3,8 s'de giriliyor, aşma 0,03 m/s (test: 5 s, < 1 m/s).
- `ki = 0,1` küçük tutuldu: modelde eğim ve sürtünme yok ama gerçek araçta sabit bir bozucu kuvvet
  olur, onu ancak integral yok eder. `ki = 1` denediğimde anti-windup olmasına rağmen aşma
  0,20 m/s'ye, yerleşme 4,9 s'ye çıktı (doyumdan çıkınca integral hâlâ birikiyor).
- `kd = 0`: basamak referansta türev "tekme" atar, gerçek hız ölçümünde de gürültüyü büyütür.
  İntegratör tesiste sönüm için gerek yok.

**Pure Pursuit: `Ld = max(3 m, 0,5 s · v)`.** İleri bakış noktası her hızda ~0,5 s ileride.
10 m/s'de Ld = 5 m. Alt sınır 3 m: çok düşük hızda Ld → 0 olursa direksiyon sertleşir.

**Stanley: `k = 1`, `k_soft = 1 m/s`.** Testleri ilk denemede geçti. `k` büyüdükçe virajdaki kalıcı sapma
azalır ama direksiyon sertleşir (`stanley-vs-pp`: k = 2'de sapma 0,13 m, salınım 12,5 °/s;
k = 0,5'te 0,80 m, 6,4 °/s). Bu modülde kalıcı sapma 7 cm, test eşiğinin (25 cm) çok altında.

**Bir uygulama ayrıntısı:** Stanley yol yönünü en yakın noktanın `yaw` değerinden okuyunca direksiyon
hızında virajın ortasında sahte sıçramalar çıktı. Sebep: yol 0,1 m aralıklı, araç adım başına 0,2 m
gidiyor ve bazen 3 nokta atlıyor, bu yüzden yaw basamaklı değişiyor. İzdüşüme göre
`yaw_i + κ_i · Δs` ile düzeldi. Gerçek bir sistemde de yol çözünürlüğü kontrol çıkışında görünür.

## Sorular

### 1. Pure Pursuit virajda neden içeri keser? İleri bakış mesafesi bunu nasıl değiştirir?

Pure Pursuit arka aksı ileri bakış noktasına teğet bir yayla bağlar. Sabit eğrilikli bir çemberin ortasında
bu yay yolun kendisidir. Bu yüzden virajın ortasında hata sıfıra iner: `s_curve_cte.png`'de mavi eğri
t = 4–9 s arasında 0'da. İçeri kesme **eğriliğin değiştiği yerlerde** oluyor. İleri bakış noktası virajın
içine girdiğinde araç henüz düzdedir ve dönmeye erken başlar: düz→sol geçişinde CTE çizgiden önce
yükselmeye başlıyor ve +5 cm'e (sol, yani virajın içi) çıkıyor. Sol→sağ geçişinde hata −10 cm. Bu, ileri bakış
noktası diğer virajın içine geçerken iki kat eğrilik değişimi demek.

Hata Ld ile kabaca karesel büyüyor (`lookahead_sweep.png`, sol): Ld = 2 m'de RMS 0,2 cm,
5 m'de 2,2 cm, 10 m'de 12,4 cm, 15 m'de 33,9 cm. Ld'yi küçültmenin bedeli direksiyon hızı:
2 m'de 20 °/s, 15 m'de 3,7 °/s. Ld bir doğruluk ↔ yumuşaklık ayarıdır.

### 2. Stanley düşük hızda neden sert davranır, yumuşatma terimi ne işe yarar?

Yanal hata terimi `atan(k · e / (k_soft + v))`. Paydada hız var: v → 0 iken kazanç `k / v` sonsuza
gider ve çok küçük bir yanal hata bile direksiyonu sınıra dayatır. `k_soft` bu kazancı
`k / k_soft` ile sınırlar. `stanley_soft.png` (v = 2 m/s, 1 m ofset):

| k_soft | İlk direksiyon | Maks direksiyon hızı | \|CTE\| < 5 cm süresi |
|---|---|---|---|
| 0,1 | 25,5° | 41,6 °/s | 5,7 s |
| 1 | 18,4° | 25,7 °/s | 6,8 s |
| 5 | 8,1° | 8,4 °/s | 12,2 s |

Yani `k_soft` sertliği azaltıyor ama düşük hızda toparlanmayı yavaşlatıyor. Yüksek hızda (v ≫ k_soft)
etkisi kayboluyor, bu yüzden sadece park ve kalkış hızlarını ilgilendiren bir ayar.

### 3. Hızla ölçeklenen ileri bakış (`Ld = k·v`) neden sabit ileri bakıştan iyidir?

**Bu deneyde takip hatası açısından iyi değil.** `lookahead_sweep.png` (sağ): S-virajında sabit Ld = 5 m
her hızda ~2 cm RMS verirken ölçeklenen Ld, 20 m/s'de Ld = 10 m olduğu için 12,1 cm veriyor
(1. sorudaki Ld → hata ilişkisi).

Ölçeklemenin kazandırdığı şey kararlılık ve konfor. Düz yolda 1 m ofsetten toparlanırken maksimum
direksiyon hızı:

| v | Sabit Ld = 5 m | Ld = max(3, 0,5·v) |
|---|---|---|
| 5 m/s | 43 °/s | 79 °/s |
| 10 m/s | 67 °/s | 67 °/s |
| 15 m/s | 88 °/s | 22 °/s |
| 20 m/s | 118 °/s | 12 °/s |

Sabit Ld'de aynı direksiyon açısı yüksek hızda çok daha büyük bir yanal ivme demek (`a_y = v² · tan δ / L`),
ve sabit Ld ile kontrolcü hız arttıkça sertleşiyor. Ölçekleme ileri bakış *süresini* (≈ 0,5 s) sabit tutar.
Simülasyonun sabit Ld'yi olduğundan iyi gösterdiğine dikkat: modelde direksiyon gecikmesi yok
(01 notları, madde 3). Gecikmeli gerçek bir araçta 118 °/s isteyen kontrolcü salınıma girer.

### 4. Eğrilik süreksizliğinde (S-viraj geçişi) hangi kontrolcü nasıl bozulur?

`s_curve_cte.png`, noktalı çizgiler arka aksın eğrilik sıçramasını geçtiği anlar:

- **Pure Pursuit önceden tepki veriyor.** CTE ve direksiyon çizgiden ~0,5 s önce (Ld / v) değişmeye başlıyor.
  Direksiyon hızı düşük (maks 8 °/s) ve düzgün. Hata geçişte tepe yapıp (+5 / −10 / +5 cm) virajın ortasında sıfıra iniyor.
- **Stanley geç ama sert tepki veriyor.** Yalnızca ön aksın gördüğüne bakar, ileriyi görmez. Ön aks
  çizgiyi geçtiği anda (arka akstan 2,7 m, ~0,27 s önce) direksiyon hızında 11–22 °/s'lik sivri tepe var.
  En büyüğü sol→sağ geçişinde, eğrilik +1/R'den −1/R'ye atlarken.
- **Stanley virajda kalıcı sapma bırakıyor.** Virajın içinde ~7 cm (sol virajda +, sağda −). Sebep: yol
  eğriliğini bilmiyor, direksiyonu tutmak için sıfırdan farklı bir hataya ihtiyaç duyuyor. Pure Pursuit'te
  bu sapma yok. Düzeltmesi bir eğrilik ileri besleme terimi: `δ += atan(L · κ)`
  (`stanley-vs-pp/README.md`'deki deneme önerisi).

**Özet:** Pure Pursuit RMS'te (2,2 cm vs 6,3 cm) ve direksiyon yumuşaklığında (8 vs 22 °/s) önde, ama
geçişlerde maks hata daha büyük (10,3 vs 7,3 cm). Stanley'nin zayıflığı ileri besleme eksikliği.
VisionPilot'un yanal MPC'si (00 notları) ileriyi görür (N = 20 adım × 0,5 m = 10 m) ve eğriliği modelin
içinde taşır; yani iki kontrolcünün iyi taraflarını birleştirir.
