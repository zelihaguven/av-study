# 04 — Notlar

VisionPilot sürümü: `autoware.privately-owned-vehicles` @ `65375ec2cf` (17 Kas 2026). Satır referansları
`VisionPilot/` altına göre.

## Lisanslar

- **VisionPilot kodu ve ONNX ağırlıkları:** Apache 2.0 (reponun `LICENSE` dosyası). Ağırlıklar bu repoya
  kopyalanmadı, klondan okunuyor.
- **Test videoları:** Udacity `CarND-Advanced-Lane-Lines` (`project_video.mp4`, `challenge_video.mp4`,
  `harder_challenge_video.mp4`), MIT lisansı, © 2016-2018 Udacity. Videolar da repoya girmedi; sadece
  küçültülmüş örnek kareler `results/` altında.

## Dosya yolları (VisionPilot)

| Aşama | Dosya |
|---|---|
| Ana döngü | `app/vision_pilot.cpp` (ön işleme `:125`, `H_resized` `:131`) |
| Ön işleme | `modules/sensing/image_preprocessing/src/image_preprocessor.cpp` |
| 2:1 kırpma | `modules/common/include/common/utils.hpp:15-19` |
| Tensör dönüşümü, model çağrıları | `modules/models/src/inference.cpp` |
| AutoSteer | `modules/models/src/auto_steer.cpp`, `include/models/auto_steer.hpp` |
| AutoDrive | `modules/models/src/auto_drive.cpp`, `include/models/auto_drive.hpp` |
| AutoSpeed | `modules/models/src/auto_speed.cpp`, `include/models/auto_speed.hpp` |
| ONNX çalıştırma | `modules/engine/src/onnx_engine.cpp` |
| Yanal füzyon (yol → CTE, yaw, eğrilik) | `modules/safety_guardian/fusion/src/lateral_fusion.cpp` |
| Boylamsal füzyon (CIPO mesafesi) | `modules/safety_guardian/fusion/src/longitudinal_fusion.cpp` |
| Kalibrasyon | `config/H.yaml`, `scripts/find_homography_C_matrix.py`, `Calibration/` |
| Ağırlıklar | `modules/models/weights/{autosteer,autodrive,autospeed}_{fp32,int8}.onnx` |

## Postprocess: AutoSteer çıktısından e_y, e_ψ, κ'ya

Bu repodaki karşılığı `src/inspect_model.py:postprocess_autosteer`.

1. **Kırp ve küçült.** Ham kare üstten kırpılıp genişlik × genişlik/2'lik alt bant bırakılır (1280×720'de
   üstten 80 satır), 1024×512'ye küçültülür. Gökyüzünün bir kısmı atılır, yol kalır.
2. **Model.** 64 sabit satırın her biri için (v = i · 511/63) yol merkezinin normalize x'i (`lane_value`) ve bir
   `height` değeri. `height ≥ 0,5` olan satırlar geçerli. Bu bir olasılık değil: sigmoid uygulanmıyor ve
   değerler −0,3 ile 10 arasında. ONNX grafiğinde de son katman bir `Conv`, sigmoid yok.
3. **Zemine izdüşüm.** Her (u, v) noktası `H_resized = H · T` homografisiyle zemine gider (X ileri, Y sol, metre).
   `T` kırpma ve ölçeklemeyi geri alır, `H` kameranın kalibrasyonu. X < 0,5 m veya > 120 m olanlar atılır.
4. **RANSAC polinom.** `y = a x² + b x + c`, 80 iterasyon, 3 noktalık örnekler, inlier eşiği 0,20 m. En iyi inlier
   kümesine yeniden uydurulur. 12'den az inlier veya |CTE| > 3 m ise o kare "şerit yok" sayılır.
5. **Ölçüm noktası.** CTE ve yaw x = 0'da değil, **en yakın gözlenen noktada** (`x_ref = min x`)
   hesaplanır. Kamera aracın önünü göremediği için x = 0'a ekstrapolasyon yapılmıyor. Udacity kamerasında
   x_ref ≈ 4,6 m. Yani ölçülen "yanal hata", aracın kendisinin değil ~5 m önündeki noktanın yoldan uzaklığı.
6. **Değerler.** `CTE_VP = y(x_ref)`, `yaw_VP = atan(2a·x_ref + b)`. κ: [3, 25] m'deki inlier'larda
   `2a / (1 + (2ax + b)²)^1.5` değerlerinin medyanı.
7. **İşaret dönüşümü.** VisionPilot'ta CTE "+ = ego yolun sağında", yaw "+ = yol sola gidiyor". Bizim kural
   (`common`, 05) aracın konumunu ve yönünü yola göre ölçüyor: `e_y = −CTE_VP`, `e_ψ = −yaw_VP`, κ aynı.
   `tests/test_postprocess.py` bu dönüşümü sentetik bir kamerayla sabitliyor.
8. **Sonrası (VisionPilot'ta, bu modülde değil).** CTE/yaw 300 parçacıklı bir filtreye gider (ölçüm std'si
   CTE 0,15 m, yaw 0,05 rad), eğrilik AutoDrive'ın eğriliğiyle başka bir parçacık filtresinde birleşir, oradan
   MPC'ye. 05'teki Kalman bu katmanın basit karşılığı.

## Kalibrasyon: Udacity kamerası için homografi

VisionPilot'un `config/H.yaml` dosyası OpenLane'in 1920×1080 kamerası için kalibre edilmiş. Udacity videosu
farklı bir kamera, o yüzden kendi `H`'sini kurdum (`udacity_calibration()`):

| Adım | Kaynak / ölçüm | Değer |
|---|---|---|
| Kuşbakışı dönüşüm | Udacity'nin kendi noktaları (`writeup_template.md:86-91`) | 4 nokta |
| Yanal ölçek | Kuşbakışında şerit genişliği 640 px = 3,7 m (ABD şerit genişliği) | 0,0058 m/px |
| Boylamsal ölçek | Kesikli çizgi periyodu 12,19 m (10 ft + 30 ft), kuşbakışında 362 px | 0,0337 m/px |
| Odak uzaklığı | 17 satranç tahtası görüntüsüyle `cv2.calibrateCamera`, yeniden izdüşüm hatası 1,19 px | fx = 1157,5 px, yatay FOV 57,9° |
| Kamera → alt satır | Alt satırda şerit 924 px ⇒ X0 = fx · 3,7 / 924 | 4,6 m |

**Belirsizlikler:**
- Boylamsal ölçek: otokorelasyon 335 px, ardışık çizgi başlangıçları 362 px veriyor, çizgi/periyot oranı
  standart 0,25 yerine 0,36 çıkıyor. Ya Udacity'nin noktaları tam metrik değil ya da bu yol farklı bir çizgi
  standardı kullanıyor. Boylamsal ölçekte %10–25 hata olabilir. Bu e_ψ ve κ'yı doğrudan ölçekler; e_y'yi
  çok az etkiler.
- Lens bozulması düzeltilmedi (VisionPilot da düzeltmiyor). Udacity kamerasında kenarlarda belirgin bozulma
  var.
- Kamera yatay FOV'u 57,9°, VisionPilot'un önerdiği 52–55°'ye yakın. Model bu kameraya makul ölçüde uygun.

## Bulgu: AutoSpeed'de sigmoid iki kez uygulanıyor

- ONNX grafiğinin son düğümü `Concat(Mul(kutu), Sigmoid(sınıf))`: model sınıf **olasılığı** veriyor (çıkışın
  4–7. kanalları 0–1 aralığında; ör. bir karede en yüksek değer 0,94).
- C++ son işleme bu değere bir kez daha sigmoid uyguluyor (`modules/models/src/auto_speed.cpp:139`).
- Sonuç: skorlar 0,5–0,73 aralığına sıkışıyor ve `conf_thres = 0.6` (`auto_speed.hpp:57`) aslında olasılıkta
  **0,405** eşiği oluyor. Her anchor'ın skoru en az 0,5 olduğu için 0,5'in altındaki bir eşik her şeyi
  geçirirdi.
- `tests/test_postprocess.py::test_autospeed_double_sigmoid_lowers_threshold` bunu bir örnekle gösteriyor.
  `postprocess_autospeed(..., apply_sigmoid=False)` düzeltilmiş hâli.
- Bu PoV WG'ye küçük ve somut bir katkı adayı: ya C++'tan sigmoid kaldırılmalı ve eşik yeniden seçilmeli, ya da
  export'taki sigmoid kaldırılmalı. Hangisinin doğru olduğu eğitim kodunun ne beklediğine bağlı; issue açmadan
  önce `auto_speed` reposundaki Python inference'a bakmak gerekir.

Ayrıca kodda yorum ile değerin uyuşmadığı küçük yerler (hata değil, ama okuyanı yanıltıyor):
- `auto_speed.hpp:35-36` "letterbox, pad 114" diyor; ön işlemede letterbox yok.
- `image_preprocessor.hpp:14` warp edilmiş görüntüye "BEV" diyor; aslında ZOD perspektif görünümü, kuşbakışı değil.
- `lateral_fusion.hpp:34-35,55` "CTE = c, Yaw = atan(b)" diyor; kod CTE'yi x = 0'da değil `x_ref`'te hesaplıyor.
- `lateral_fusion.hpp:93,99` yorumlar 0,25 m eşik ve 15 inlier diyor, değerler 0,20 ve 12.
- 00'daki not: `planning/config.hpp` "50Hz" diyor, `dt = 0.05` (20 Hz). Füzyon ise `dt = 0.10` (10 Hz) varsayıyor.

## Çalıştırma süresi (CPU)

Donanım: bulut konteyneri, Intel Xeon @ 2,1 GHz, 4 vCPU, GPU yok. onnxruntime 1.20.1, CPUExecutionProvider,
varsayılan iş parçacığı ayarı. Video boyunca medyan (`analyze.py`, ms):

| Ön işleme | AutoSteer | AutoSpeed | AutoDrive | Toplam |
|---|---|---|---|---|
| 21 | 40 | 86 | 87 | ~234 ms ≈ 4,3 Hz |

- VisionPilot 10 Hz için tasarlanmış (`Sensing/README.md:5`, füzyonda `dt = 0.10`). Bu CPU'da üç model
  sırayla çalışınca hedefin yarısına bile ulaşılmıyor. VisionPilot modelleri `std::async` ile paralel çalıştırıyor;
  burada sırayla çalıştı.
- **INT8 bu CPU'da hızlandırmıyor.** Tek bir karede ayrı ölçüm (15 tekrar medyanı): AutoSteer fp32 53 / int8 82 ms,
  AutoSpeed 68 / 123 ms, AutoDrive 62 / 47 ms. Olası sebep, bu sanal CPU'da INT8 hızlandırma
  komutlarının (VNNI) bulunmaması; doğrulamadım. INT8 çıktısı fp32'ye yakın (aynı karede e_y −0,152 / −0,166 m).
- Ayrı ölçüm ile video medyanı farklı (AutoSteer 53 / 40 ms): ısınma ve önbellek etkisi. Sayılar ±%30 okunmalı.

## Başarısızlık kareleri

Hepsi `harder_challenge_video.mp4`'ten (dar, virajlı orman yolu, güneş). Kırmızı noktalar AutoSteer'in geçerli
noktaları, yeşil eğri RANSAC polinomu.

| Kare | Dosya | Ne oluyor | Neden (tahmin) |
|---|---|---|---|
| 816 | `failures/1_parlama.png` | Sadece 13 nokta, eğri kısa ve kıvrık (R = 8 m) | Güneş doğrudan kameraya vuruyor, ön camdaki pus ve aşırı pozlama yol dokusunu siliyor; model ancak kaputun hemen önünü görüyor. |
| 1040 | `failures/2_serit_yok.png` | "Şerit yok": 1 geçerli nokta | Yol yüzeyi güneşte beyaza doymuş ve firkete viraj yolu kadrajın dışına taşıyor; ikisi bir araya gelince modelin hiçbir satırda güveni kalmıyor. |
| 994 | `failures/3_firkete_yaw.png` | e_ψ = +44° | 15 mph'lik firkete: yol görüntüde neredeyse yatay gidiyor. Ölçüm doğru olabilir ama kinematik model ve 05'teki küçük açı varsayımı bu açıda geçersiz. |
| 998 | `failures/4_polinom_modeli.png` | e_ψ = −20°, R = −2 m, eğri S çiziyor | `y = a x² + b x + c` modeli, x'e göre yana dönen (neredeyse x sabitken y değişen) bir yolu temsil edemiyor; RANSAC 16 noktadan 13'üne anlamsız bir parabol uyduruyor. Model değil, son işleme hatası. |
| 1017 | `failures/5_yakin_nokta_sicramasi.png` | e_y = +1,10 m (1 s önce ~0) | Sadece 5–8 m'deki yakın noktalar görülüyor ve hepsi viraja doğru sağa kayık; CTE en yakın noktada (`x_ref`) ölçüldüğü için virajın eğimi yanal hata gibi görünüyor. |

Ortak tema: Model kendisi çoğu karede makul bir yol çiziyor. Bozulmanın yarısı **son işlemede**: 2. derece
polinom ve x_ref'te ölçüm keskin virajda çöküyor. Diğer yarısı görüntü kalitesi (parlama, doygunluk).
Hiçbiri 05'teki "bağımsız Gaussian gürültü" modeline uymuyor: hatalar birkaç saniye süren, birbirini izleyen
karelerde aynı yöne kayık sistematik hatalar.

İyi kareler: `overlay_1_otoyol.png` (project 100: düz otoyol), `overlay_2_zemin_degisimi.png` (project 612:
asfalt rengi değişiyor, yol yine doğru), `overlay_3_orman_viraji.png` (harder 300: gölgeli orman virajı).

**AutoSpeed hakkında:** Videolardaki araçların çoğu sınıf 3 olarak etiketleniyor ve VisionPilot sınıf 3'ü yok
sayıyor (sadece 1 = aynı şerit, 2 = komşu şerit). project_video'da 1260 karenin 10'unda, challenge'da 484'ün 109'unda
bir CIPO bulundu. Sınıf 0 ve 3'ün anlamı kodda tanımlı değil; sınıf 3 büyük ihtimalle "ilgisiz araç".

## 05 için gürültü tahmini

**Yöntem** (`src/analyze.py`): Videoda gerçek e_y bilinmiyor. İnsan sürücünün şerit içindeki salınımı yavaş
(saniyeler), modelin titreşimi hızlı (kareden kareye). Gerçek değer yerine 1 s'lik merkezli hareketli ortalama
alındı, kalan (ölçüm − ortalama) titreşim kabul edildi. Aykırı değerlere dayanıklı olsun diye MAD ile de
hesaplandı (σ ≈ 1,4826 · medyan |r|). Kayıp oranı = RANSAC'ın reddettiği karelerin oranı.

| Video | Kare | Kayıp | En uzun kesinti | σ e_y (std / MAD) | σ e_ψ (std / MAD) | σ κ (std / MAD) | ρ₁ (e_y) |
|---|---|---|---|---|---|---|---|
| project (otoyol) | 1260 | %0 | 0 | 3,0 / 2,4 cm | 0,32 / 0,26° | 0,00038 / 0,00031 | 0,66 |
| challenge (otoyol, köprü altı) | 484 | %0 | 0 | 2,4 / 2,0 cm | 0,32 / 0,27° | 0,00051 / 0,00049 | 0,75 |
| harder (orman, firkete) | 1199 | %0,25 | 3 kare | 8,5 / 3,4 cm | 3,2 / 0,95° | 0,025 / 0,0035 | 0,65 |

Harder videoda std ile MAD arasındaki büyük fark aykırı değerlerden geliyor: kalanların %10'u 3σ_MAD'den büyük
ve çoğu 39–44 s'deki firkete bölümünde. O bölüm çıkarılınca σ e_y 4,8 cm'e iniyor (`noise.png`).

**05 için sonuç:**

| | 05 varsayılanı (`LaneNoise`) | Ölçülen, otoyol | Ölçülen, zor yol |
|---|---|---|---|
| σ_y | 0,30 m | 0,03 m | 0,03–0,08 m (+ sistematik sıçramalar) |
| σ_ψ | 3° | 0,3° | 1–3° |
| σ_κ | 0,005 1/m | 0,0004 1/m | 0,0035–0,025 1/m |
| Kayıp | %10 | %0 | %0,25, kümeli (3 ardışık kare) |
| Kareler arası ilişki | bağımsız | ρ₁ ≈ 0,7 | ρ₁ ≈ 0,65 |

1. **05'in varsayılan titreşimi otoyolda ~10 kat kötümser.** Ölçülen değerlerle 05 (S-virajı, 10 koşu ortalaması,
   takipli) RMS 13,9 cm yerine 1,9 cm, direksiyon hızı 19,5 °/s yerine 9,3 °/s veriyor. Zor yolun değerleriyle
   16,6 cm, 39 °/s.
2. **Ama 05'in varsayılanlarını değiştirmiyorum.** Bu ölçüm sadece kareden kareye titreşimi görüyor; 1 s'den yavaş
   hataları (kalibrasyon sapması, firketede birkaç saniye süren yanlış yol) göremiyor. 05'in 0,3 m'si bu görünmeyen
   hatalar için kaba bir pay olarak kalabilir. 05'in testleri de o varsayıma göre yazılmış bir stres testi.
3. **Asıl eksik gürültünün *yapısı*.** Gerçek hatalar ilişkili (ρ₁ ≈ 0,7) ve kümeli; bağımsız Gaussian değil. 05'i
   gerçekçi yapmanın bir sonraki adımı, sentetik algıya AR(1) gürültü (`n_k = 0,7 n_{k−1} + w_k`) ve kümeli kayıp
   eklemek olur. İlişkili gürültüyü filtre ortalama alarak silemez; takip katmanının avantajı küçülür.
4. **Kayıp oranı** bu videolarda neredeyse sıfır, çünkü VisionPilot'un reddetme kuralları gevşek (12 inlier):
   bozuk kareler "geçerli" sayılıp yanlış bir değerle geçiyor (998. kare). Kayıp yerine **aykırı değer** oranı daha
   anlamlı: otoyolda %1–3, zor yolda %10–14 (3σ_MAD dışı).

**Sınırlar:** Kalibrasyon (boylamsal ölçek %10–25 belirsiz) e_ψ ve κ'yı ölçekler. Video 25 fps, VisionPilot 10 Hz,
05 20 Hz çalışıyor; ilişkili gürültüde σ kare hızından az, ρ₁ ise çok etkilenir. Kameranın gerçek konumu (araç
ekseninde mi) bilinmiyor; bu e_y'ye sabit bir sapma ekler ve titreşim ölçümünü etkilemez.
