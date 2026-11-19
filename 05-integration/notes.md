# 05 — Notlar

Tüm sayılar `python 05-integration/src/plots.py` çıktısından. Senaryo testlerle aynı: S-virajı
R = 50 m, 10 m/s, 20 Hz sentetik algı. Gürültü `LaneNoise` varsayılanları: σ_y = 0,3 m,
σ_ψ = 3°, σ_κ = 0,005 1/m. Bu değerler tahmin; 04'te gerçek model çıktısıyla karşılaştırıldı (aşağıda "04 ölçümleriyle karşılaştırma").

## Tasarım

- **Algı:** Gerçek durumdan arka aks referanslı `[e_y, e_ψ, κ]` + bağımsız Gaussian gürültü, `p_drop`
  olasılıkla kare kaybı. Kayıp olsa da olmasa da aynı rastgele sayılar çekiliyor, böylece aynı tohumla
  farklı kayıp oranları aynı gürültü dizisini paylaşıyor.
- **Takip:** 03'teki `KalmanFilter`, 3 durumlu model. Tahmin adımı bir önceki direksiyonu bilinen girdi
  olarak kullanıyor: `e_ψ' = v/L · tan δ − v κ`. Bunun için 03'ün `predict`'ine isteğe bağlı `B·u`
  eklendi (geriye uyumlu, 03 testleri değişmedi).
- **Kontrol:** `δ = atan(L κ) − e_ψ − atan(k · e_front / (k_soft + v))`, `e_front = e_y + L sin e_ψ`.
  Feedforward virajı tek başına döner (01: R = L / tan δ), Stanley tipi geri besleme sapmayı düzeltir.
- **Takip süreç gürültüsü `TRACKER_Q = (0,01; 1e-4; 1e-3)`:** 36 kombinasyonu 5 tohumla taradım. En
  düşük RMS CTE'yi `(1e-4; 1e-3; 1e-2)` verdi: 12,5 cm, direksiyon hızı 27 °/s. Seçilen değer 13,9 cm ve
  19,6 °/s. 1,4 cm için %40 daha pürüzlü direksiyonu kabul etmedim. `q_κ` S-virajındaki eğrilik
  sıçramalarını ne kadar hızlı yakalayacağını belirliyor, `q_y`'nin etkisi neredeyse yok.

## Sorular

### 1. Takip katmanı kaldırılınca ne bozulur: yanal hata mı, direksiyon pürüzsüzlüğü mü? Neden?

**Direksiyon pürüzsüzlüğü bozuluyor, yanal hata düşük kayıpta neredeyse hiç bozulmuyor.**
`closed_loop.png` (seed 0, %10 kayıp):

| | Kontrolcünün gördüğü e_y hatası | Gerçek CTE RMS | Maks | Direksiyon hızı RMS |
|---|---|---|---|---|
| Takipsiz | 29,1 cm | 13,7 cm | 35,9 cm | 130 °/s |
| Takipli | 8,2 cm | 15,2 cm | 36,6 cm | 19 °/s |

Takip katmanı kontrolcünün gördüğü hatayı 3,5 kat azaltıyor. Ama aracın gerçek yanal hatası aynı kalıyor,
bu koşuda biraz kötü bile. Sebep: **araç kendisi bir alçak geçiren filtre.** Direksiyon açısı yanal
konumu iki kez entegre ederek değiştiriyor (δ → yaw hızı → yaw → yanal hız → konum). Ham ölçümdeki hızlı,
beyaz gürültü direksiyonu her karede sağa sola atıyor ama bu atışlar konumda birbirini götürüyor. Takip
çıktısının kalan hatası ise yavaş kayan, düşük frekanslı bir hata. O araçtan geçip doğrudan yola yansıyor
(grafikte orta panel, mavi eğri t = 15–18 s'de gerçek e_y'nin altında yavaşça kayıyor).

Yani takipsiz sistem simülasyonda "çalışıyor" görünüyor, çünkü modelde direksiyon sınırsız hızda dönebiliyor
ve gecikmesiz. Gerçek araçta 130 °/s RMS'lik bir komut hem konforsuz hem de direksiyon aktüatörünün
yapamayacağı bir şey. Gecikme eklenince ne olduğu aşağıdaki "Direksiyon aktüatörü" bölümünde ölçüldü: çıkarımım kısmen yanlış çıktı.

Kayıp oranı arttıkça yanal hatada da fark açılıyor (3. soru).

### 2. Eğrilik feedforward'ı hangi hatayı ortadan kaldırır?

**Virajdaki kalıcı (steady-state) yanal hatayı.** `ff_ablation.png`, üst panel gürültüsüz:

| | RMS | Maks |
|---|---|---|
| Feedforward kapalı | 46,3 cm | 58,6 cm |
| Feedforward açık | 1,0 cm | 3,5 cm |

R = 50 m'lik virajı dönmek için `atan(L/R) = 3,1°` direksiyon gerekiyor. Feedforward yoksa bu açıyı
geri besleme üretmek zorunda, o da ancak sıfırdan farklı bir hata görürse üretiyor:
`atan(e / (k_soft + v)) = 3,1°` ⇒ `e ≈ 11 · tan 3,1° ≈ 0,59 m`. Grafikteki 58 cm'lik plato tam bu
değer. Araç virajın dışına kayıyor. 02'de Stanley'nin virajda bıraktığı 7 cm'lik kalıcı sapma da aynı
kökten geliyor.

Feedforward açıkken kalan 3,5 cm sadece eğrilik geçişlerinde. Sebebi, κ'nın arka aksın bulunduğu noktada
ölçülmesi: araç virajı ancak içine girince öğreniyor. İleri bakışlı bir ölçüm (ya da MPC) bunu da
kaldırırdı.

Gürültülü durumda (alt panel) fark daha az çarpıcı ama aynı: 48,0 → 19,4 cm.

### 3. Algı kaybı oranı arttıkça sistem nerede ve nasıl çöker?

`dropout_sweep.png`, her kayıp oranında 20 koşu, maks |CTE|:

| p_drop | 0 | 0,3 | 0,5 | 0,7 | 0,8 | 0,9 |
|---|---|---|---|---|---|---|
| Takipli, medyan | 0,29 m | 0,33 m | 0,41 m | 0,55 m | 0,84 m | 1,61 m |
| Takipli, en kötü | 0,45 m | 0,45 m | 0,54 m | 0,84 m | 3,54 m | 10,4 m |
| Takipsiz, medyan | 0,27 m | 0,38 m | 0,55 m | 1,33 m | 4,64 m | 12,5 m |
| Takipsiz, en kötü | 0,37 m | 0,63 m | 1,18 m | 4,10 m | 14,5 m | 21,3 m |

- **Nasıl:** Takipsiz sistem ölçüm gelmeyince son ölçümü tutuyor. Araç bu arada hareket ettiği hâlde
  kontrolcü eski hatayı düzeltmeye devam ediyor. Uzun bir kesintide düzeltmeyi aşıyor ve karşı tarafa
  geçiyor. Takipli sistem kesintide direksiyon girdisiyle durumu ileri taşıyor (`predict`). Kısa
  kesintilerde bu neredeyse doğru, uzun kesintilerde κ ve e_ψ'deki küçük hatalar karesel büyüyor.
- **Nerede:** Belirleyici olan ortalama kayıp değil, **en uzun kesinti**. Bağımsız kayıpta n karelik bir
  koşudaki en uzun kesinti kabaca `ln n / ln(1/p)` kare. Burada n ≈ 400 kare: p = 0,5'te ~9 kare
  (0,4 s), p = 0,8'de ~27 kare (1,3 s), p = 0,9'da ~57 kare (2,8 s). Takipsiz sistem p ≈ 0,5–0,7'de,
  takipli p ≈ 0,8–0,9'da çöküyor. Takip katmanı çöküşü kabaca iki kat daha uzun kesintiye erteliyor.
- **Şerit payıyla karşılaştırma:** Tipik bir otoyol şeridi ~3,5 m, binek araç ~1,8 m genişlikte. Yani her
  iki yanda kabaca 0,8 m pay var (genel bilgi, ölçüm değil). Bu ölçüyle takipsiz sistem p = 0,5'te bile
  bazı koşularda şeritten çıkıyor, takipli sistem p = 0,7'ye kadar içeride kalıyor.
- **Sistem ne yapmalı:** Kovaryans burada da işe yarıyor (03, 2. soru). Kesinti uzadıkça `P` büyüyor;
  gerçek bir L2 sistemi belli bir eşikte özelliği kapatıp sürücüye devretmeli (00, 6. soru: L2'de fallback
  sürücü). Bu simülasyonda devretme yok, araç kesinti ne kadar uzun olursa olsun sürmeye devam ediyor.

## Direksiyon aktüatörü (B8)

1. sorudaki "modelde direksiyon ideal, gecikme eklenince takipsiz sistemin yanal hatası da bozulur" çıkarımını
ölçtüm. `run(..., steer_delay, steer_tau)`: komut saf gecikme ve birinci derece gecikmeyle tekerleğe geçiyor;
Autoware'in MPC ayarları 0,24 s ve 0,27 s (`mpc.param.yaml`). Varsayılanlar ideal, eski sonuçlar değişmedi.
`actuator_delay.png`, `python 05-integration/src/actuator_delay.py`, 12 koşu, RMS gerçek CTE:

| Aktüatör | 05 varsayılanı, takipli / takipsiz | 04 otoyol (ρ 0,6), takipli / takipsiz | Gürültüsüz |
|---|---|---|---|
| İdeal | 13,5 / 11,5 cm | 2,4 / 2,1 cm | 1,0 cm |
| 0,24 s gecikme | 31,0 / 26,2 cm | 11,2 / 10,2 cm | 9,5 cm |
| 0,27 s zaman sabiti | | | 6,4 cm |
| 0,24 s + 0,27 s (Autoware) | 63 / 187 cm | 186 / 172 cm | **173 cm, direksiyon %43 sınırda** |

- **Çıkarımım kısmen yanlış.** Saf gecikmede iki sistem de 2–5 kat kötüleşiyor ve takipsiz sistem yanal hatada yine
  biraz önde. Takip katmanı gecikmeye karşı koruma sağlamıyor.
- **Asıl bulgu: kontrol döngüsü kararsızlaşıyor.** Gecikme ve zaman sabiti birlikteyken gürültüsüz durumda bile
  araç 3,4 m sapıyor ve direksiyon zamanın %43'ünde sınıra dayanıyor (sınır çevrimi). Kontrolcü (Stanley tipi
  geri besleme, k = 1, + eğrilik ileri beslemesi) ideal aktüatöre göre ayarlandı; toplam ~0,5 s gecikmeye
  dayanmıyor. Gecikme 0,12 s'ye inince kararlı (10 cm).
- Kararsız durumda takipli/takipsiz farkı (63 / 187 cm) anlamlı bir karşılaştırma değil; sınır çevriminin
  genliği gürültüye bağlı ve düzensiz.
- Sonuç: gerçek bir araçta önce kontrolcünün aktüatör gecikmesini hesaba katması gerekiyor (gecikme telafisi,
  düşük kazanç ya da aktüatör modelli MPC). Autoware'in MPC'si `input_delay` parametresini tam bunun için
  taşıyor; VisionPilot'un uzamsal MPC'si de aynı soruyu cevaplamak zorunda. Gecikme telafisi bu repoda denenmedi
  (`docs/next-steps.md`, 8b).

## 04 ölçümleriyle karşılaştırma

04'te AutoSteer'i Udacity videolarında çalıştırıp titreşimi ölçtüm (`04-perception/notes.md`, "05 için gürültü
tahmini"). Aynı S-virajında 10 koşu ortalaması:

| Gürültü | Takip | RMS CTE | Maks CTE | Direksiyon hızı RMS |
|---|---|---|---|---|
| 05 varsayılanı (0,3 m, 3°, %10 kayıp) | var | 13,9 cm | 33,6 cm | 19,5 °/s |
| 05 varsayılanı | yok | 11,4 cm | 27,3 cm | 124,5 °/s |
| 04 otoyol (0,03 m, 0,32°, kayıp yok) | var | 1,9 cm | 5,7 cm | 9,3 °/s |
| 04 otoyol | yok | 1,5 cm | 4,3 cm | 16,6 °/s |
| 04 zor yol (0,085 m, 3,2°, %0,3) | var | 16,6 cm | 39,1 cm | 39,0 °/s |
| 04 zor yol | yok | 14,8 cm | 36,5 cm | 175,4 °/s |

Varsayılanlar otoyol titreşimine göre ~10 kat kötümser; değiştirmedim, çünkü 04'ün yöntemi yavaş ve sistematik
hataları göremiyor ve testler bu stres senaryosuna göre yazılmış. 1. sorudaki sonuç her gürültü seviyesinde
geçerli: takip katmanı yanal hatayı değil direksiyonu iyileştiriyor. Gerçek gürültü ilişkili (ρ₁ ≈ 0,7); bunun
etkisi bir sonraki bölümde.

## Gürültünün yapısı: ilişkili gürültü ve kümeli kayıp

04'te ölçülen iki özelliği sentetik algıya ekledim (`LaneNoise.rho`, `LaneNoise.burst_len`; varsayılanlar eski
davranışı birebir koruyor, 05'in testleri ve grafikleri değişmedi):

- **AR(1) gürültü:** `n_k = ρ n_{k−1} + √(1−ρ²) w_k`. σ aynı kalıyor, sadece hatanın ne kadar "kalıcı" olduğu değişiyor.
  04'teki ρ₁ = 0,66 (25 fps) 20 Hz'e çevrilince ≈ 0,6.
- **Kümeli kayıp:** iki durumlu Markov zinciri (Gilbert modeli). Ortalama kesinti L kare, uzun dönem kayıp oranı
  p_drop ile aynı tutuluyor; böylece aynı kayıp oranında bağımsız ve kümeli kayıp karşılaştırılabiliyor.
- `tests/test_noise_models.py` üçünü de doğruluyor: varsayılanlar eskiyle aynı, AR(1) σ'yı ve ρ₁'i, Markov
  kaybı oranı ve ortalama kesinti uzunluğunu tutturuyor.

`noise_structure.png`, `python 05-integration/src/noise_structure.py`, 12 koşu:

**1. Aynı σ ile korelasyon arttıkça (σ_y = 0,3 m, %10 bağımsız kayıp):**

| ρ | Takipli gerçek CTE | Takipli gördüğü hata | Takipli dir. hızı | Takipsiz gerçek CTE | Takipsiz dir. hızı |
|---|---|---|---|---|---|
| 0 | 13,5 cm | 8,6 cm | 19,6 °/s | 11,5 cm | 126 °/s |
| 0,6 | 25,2 cm | 15,0 cm | 15,3 °/s | 21,3 cm | 82 °/s |
| 0,9 | 50,5 cm | 25,5 cm | 10,7 °/s | 42,6 cm | 42 °/s |
| 0,95 | 64,5 cm | 29,9 cm | 9,2 °/s | 54,6 cm | 30 °/s |

- **Aynı σ, çok farklı sonuç.** 04'te ölçülen ρ ≈ 0,6'da yanal hata bağımsız gürültüye göre ~2 kat. σ tek başına
  bir algı modelinin ne kadar iyi olduğunu söylemiyor; hatanın ne kadar sürdüğü de önemli.
- **Filtre ilişkili gürültüyü silemiyor.** Kalman ardışık ölçümlerin ortalamasını alarak gürültüyü azaltır. Bu ancak
  hatalar bağımsızsa işe yarar. ρ = 0,95'te filtrenin çıktısındaki hata (29,9 cm) ham ölçümünkiyle (30 cm) aynı.
  Ardışık 20 kare aynı yönde yanlışsa ortalamaları da yanlış.
- **Araç da silemiyor.** 1. sorudaki "araç alçak geçiren filtredir" etkisi tersine dönüyor. Yavaş değişen hata
  aracın filtreleyebildiği frekansın altına iniyor ve doğrudan yola yansıyor.
- **Takipsiz sistemin direksiyonu yumuşuyor** (126 → 30 °/s), çünkü ölçüm artık yavaş değişiyor. Takip katmanının
  direksiyondaki avantajı 6,4 kattan 3,3 kata düşüyor.
- Akla gelen çözüm, filtreye ilişkili gürültüyü bildirmek: gürültüyü ayrı bir durum olarak ekleyip (durum genişletme,
  `LaneTracker(meas_rho=ρ)`, `run(..., tracker_rho=ρ)`) filtreye "bu hata kalıcı" demek. Denedim (5b), 12 koşu:

  | Senaryo | Beyaz varsayan filtre | Gürültüyü durum olarak taşıyan filtre | Takipsiz |
  |---|---|---|---|
  | σ 0,3 m, ρ = 0,6 | 25,2 cm / 15 °/s | 24,1 cm / 20 °/s | 21,3 cm / 82 °/s |
  | σ 0,3 m, ρ = 0,9 | 50,5 cm / 11 °/s | 39,2 cm / 24 °/s | 42,6 cm / 42 °/s |
  | 04 otoyol, ρ = 0,6 | 2,4 cm / 9 °/s | 2,5 cm / 9 °/s | 2,1 cm / 12 °/s |

  Kazanç sadece yüksek korelasyonda var (ρ = 0,9'da %22) ve direksiyon pürüzlüleşiyor. Ölçülen ρ ≈ 0,6'da
  (20 Hz'de ~0,1 s korelasyon süresi) filtre kalıcı hatayı yoldaki gerçek değişimden ayıramıyor; süreç gürültüsü
  `q`'yu değiştirmek de sonucu değiştirmedi. Doğru modellenmiş bir filtre bile, sinyale benzeyen gürültüyü
  silemiyor. `tests/test_noise_models.py` ρ = 0,9'daki kazancı sabitliyor.

**2. Aynı kayıp oranı (%30), farklı kümelenme:**

| Ortalama kesinti | Takipli maks CTE medyan / en kötü | Takipsiz medyan / en kötü |
|---|---|---|
| bağımsız (~1,4 kare) | 0,34 / 0,42 m | 0,36 / 0,63 m |
| 5 kare (0,25 s) | 0,52 / 1,05 m | 1,03 / 2,33 m |
| 10 kare (0,5 s) | 1,05 / 7,1 m | 2,85 / 5,8 m |
| 20 kare (1 s) | 2,81 / 53 m | 12,1 / 36 m |

- **Kayıp oranı yanıltıcı bir ölçüt.** %30 bağımsız kayıpta sistem rahat, aynı %30 1 s'lik kesintiler hâlinde
  gelirse araç şeritten çıkıyor. 3. sorudaki "en uzun kesinti belirler" sonucunun doğrudan deneyi bu.
- Takip katmanı kümeli kayıpta da en değerli (5–10 kare kesintide medyan hata yarı yarıya), ama 1 s'lik
  kesintilerde o da dağılıyor. En kötü koşuda 53 m: araç yolu tamamen kaybetmiş. Bir L2 sistemi burada çoktan
  sürücüye devretmiş olmalı (00, 6. soru).

**3. 04'ün ölçtüğü gerçekçi senaryolar** (σ'lar MAD tabanlı):

| Senaryo | Takipli RMS / maks / dir. hızı | Takipsiz RMS / maks / dir. hızı |
|---|---|---|
| Otoyol, bağımsız gürültü | 1,7 / 5,3 cm / 9,3 °/s | 1,4 / 4,2 cm / 14,7 °/s |
| Otoyol, ρ = 0,6 | 2,4 / 6,4 cm / 8,9 °/s | 2,1 / 5,2 cm / 11,8 °/s |
| Zor yol, ρ = 0,6, 3 karelik kesintiler | 8,5 / 20,1 cm / 11,9 °/s | 7,5 / 18,2 cm / 27,8 °/s |

Gerçekçi gürültüde takip katmanının direksiyon avantajı küçülüyor (otoyolda 1,3 kat) ve yanal hataya katkısı
yok. Bu senaryolarda sistemi zorlayan şey titreşim değil, 04'teki başarısızlık kareleri gibi saniyeler süren
sistematik hatalar. Onları bu Gaussian modellerden hiçbiri temsil etmiyor.

## VisionPilot ile farklar (dürüstlük bölümü)

00'daki VisionPilot diyagramına (`00-architecture/architecture.md`, 2. bölüm) göre bu model şu
noktalarda gerçek sistemden ayrılıyor:

1. **Algı çıktısı farklı.** Burada algı doğrudan `[e_y, e_ψ, κ]` veriyor. VisionPilot'ta AutoSteer ego yolun
   64 noktasını ve güvenlerini, AutoDrive eğriliği veriyor. Yanal füzyon bu noktalara RANSAC ile polinom
   uydurup hataları kendisi çıkarıyor. Aradaki adım (piksel → metre için homografi, polinom uydurma)
   burada yok.
2. **Gürültü gerçekçi değil.** Varsayılan gürültü bağımsız ve Gaussian. İlişkili gürültü ve kümeli kayıp artık
   seçenek olarak var (yukarıdaki bölüm), ama 04'te görülen aykırı değerler (zor yolda %10) ve sahneye bağlı
   sistematik hatalar (parlama, firkete; `04-perception/results/failures/`) hâlâ modellenmiyor.
3. **Takip filtresi farklı.** Burada tek bir lineer Kalman var. VisionPilot CTE/yaw ve eğrilik için ayrı
   parçacık filtreleri kullanıyor ve eğriliği iki kaynaktan (AutoSteer yolu + AutoDrive) birleştiriyor.
4. **Kontrolcü ileriyi görmüyor.** Burada Stanley + feedforward, κ'yı arka aksta okuyor. VisionPilot'ta
   yanal kontrol uzamsal bir MPC (N = 20 × 0,5 m = 10 m ileri bakış). Eğrilik geçişlerindeki 3,5 cm'lik
   kalıntı orada olmaz.
5. **Boylamsal kontrol yok.** Hız sabit. VisionPilot'ta IDM öndeki araca göre hız ayarlıyor ve viraj
   için `sqrt(μg/|κ|)` hız sınırı uyguluyor. Virajda yavaşlamak yanal hatayı da etkiler.
6. **Zamanlama ideal.** Algı, takip ve kontrol aynı 20 Hz'de, gecikmesiz ve aynı anda çalışıyor. Gerçekte
   çıkarım süresi gecikme ekler. VisionPilot'un V4L2 varsayılanı 10 fps, kontrol periyodunun da 20 mi
   50 Hz mi olduğu kodda net değil (00'daki not).
7. **Araç ideal.** Kinematik bisiklet modeli: kayma yok, direksiyon gecikmesi ve hız sınırı yok (01 notları).
   Autoware'in gecikme değerleri eklenince bu kontrolcü kararsızlaşıyor ("Direksiyon aktüatörü" bölümü).
8. **Devretme ve güvenlik katmanı yok.** VisionPilot LDW, FCW ve AEB uyarıları üretiyor. Burada kesinti
   veya büyük kovaryans durumunda sürücüye devretme mantığı yok.
