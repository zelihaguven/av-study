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
yapamayacağı bir şey. Hız sınırı ve gecikme (01 notları, madde 3) eklenince takipsiz sistemin yanal hatası da
bozulur. Ölçmedim, bu bir çıkarım.

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
geçerli: takip katmanı yanal hatayı değil direksiyonu iyileştiriyor. Gerçek gürültü ilişkili (ρ₁ ≈ 0,7) ve bunu
burada modellemedim; sıradaki adım AR(1) gürültü olur.

## VisionPilot ile farklar (dürüstlük bölümü)

00'daki VisionPilot diyagramına (`00-architecture/architecture.md`, 2. bölüm) göre bu model şu
noktalarda gerçek sistemden ayrılıyor:

1. **Algı çıktısı farklı.** Burada algı doğrudan `[e_y, e_ψ, κ]` veriyor. VisionPilot'ta AutoSteer ego yolun
   64 noktasını ve güvenlerini, AutoDrive eğriliği veriyor. Yanal füzyon bu noktalara RANSAC ile polinom
   uydurup hataları kendisi çıkarıyor. Aradaki adım (piksel → metre için homografi, polinom uydurma)
   burada yok.
2. **Gürültü gerçekçi değil.** Burada gürültü bağımsız, Gaussian ve kareden kareye ilişkisiz. 04'te ölçülen
   AutoSteer hataları ilişkili (ρ₁ ≈ 0,7), aykırı değerler içeriyor (zor yolda %10) ve sahneye bağlı (parlama,
   firkete; `04-perception/results/failures/`). Kayıplar da kümeli. 3. sorudaki analiz bu yüzden iyimser.
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
   Bu yüzden takipsiz sistemin yanal hatası olduğundan iyi görünüyor (1. soru).
8. **Devretme ve güvenlik katmanı yok.** VisionPilot LDW, FCW ve AEB uyarıları üretiyor. Burada kesinti
   veya büyük kovaryans durumunda sürücüye devretme mantığı yok.
