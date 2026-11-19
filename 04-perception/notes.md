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

GÜRÜLTÜ_YER_TUTUCU
