# Issue taslağı: AutoSpeed sınıf skorlarına sigmoid iki kez uygulanıyor

**Durum:** Taslak. GitHub'a gönderilmedi; göndermek kullanıcının kararı.
**Önerilen hedef:** `autowarefoundation/autoware.privately-owned-vehicles` (VisionPilot, dağıtılan C++ yolu).
Aynı kalıp `autowarefoundation/auto_speed` reposunun Python inference kodunda da var; issue'da ona da referans veriliyor.
İsterseniz ikinci bir kısa issue olarak oraya da açılabilir.

## Türkçe özet

- AutoSpeed modelinin ONNX çıktısı sınıf **olasılığı** veriyor (çıkış katmanında sigmoid var). Eğitimdeki doğrulama
  kodu da çıktıyı doğrudan olasılık olarak kullanıyor.
- Çıkarım yollarının üçü de (VisionPilot C++, `auto_speed` PyTorch inference, `auto_speed` ONNX görselleştirme) üstüne
  bir sigmoid daha uyguluyor ve 0,6 eşiğiyle karşılaştırıyor. Sigmoid monoton olduğu için bu, olasılıkta
  **0,405** eşiğine denk.
- Ölçüm (Udacity MIT videoları): düzeltilmiş eşik (p ≥ 0,6) kutu sayısını %22–25 azaltıyor ve CIPO karelerini
  challenge videosunda 109'dan 25'e, otoyol videosunda 10'dan 0'a düşürüyor. Kaybolan CIPO'lar baktığım
  örneklerde ego şeritte 40–70 m ilerideki **gerçek** araçlar.
- Yani düşük etkin eşik şu an işe yarıyor gibi görünüyor. Öneri davranışı değiştirmek değil, anlamı düzeltmek:
  ek sigmoid'i kaldırıp eşiği açıkça ~0,4 yapmak. Bu, davranışı birebir korur ve skorları gerçek olasılık hâline getirir.
- Etiketli veriyle kesinlik/duyarlılık ölçmedim; issue bunu açıkça söylüyor ve ekipten doğru eşiği seçmek için
  veri istiyor.

---

## Issue metni (İngilizce)

**Title:** AutoSpeed: sigmoid applied twice to class scores in post-processing (effective threshold is 0.405, not 0.6)

### Summary

The AutoSpeed ONNX model already outputs class **probabilities** (the detection head applies `sigmoid` in eval mode),
but the VisionPilot C++ post-processing applies `sigmoid` again before comparing with `conf_thres = 0.6`. Because
sigmoid is monotonic, `sigmoid(p) >= 0.6` is equivalent to `p >= ln(0.6/0.4) ≈ 0.405`. So the configured threshold of
0.6 behaves like a probability threshold of ~0.405, and all reported scores are compressed into [0.5, 0.731].

The same double sigmoid exists in the Python inference code of `auto_speed`, so the C++ port faithfully reproduces it.
The training/validation code, however, treats the outputs as probabilities without an extra sigmoid.

I am not proposing to change the detection behaviour (see measurements below, the lower effective threshold seems to
help with distant CIPOs). I am proposing to make the threshold mean what it says.

### Evidence

Versions: `autoware.privately-owned-vehicles` @ `65375ec2cf` (also checked on `main` as of 2026-11-19),
`auto_speed` @ `b62e55b93b`.

1. **The model outputs probabilities.**
   - `auto_speed/Models/model_components/auto_speed/auto_speed_head.py:66`:
     `return torch.cat(tensors=(box * self.strides, cls.sigmoid()), dim=1)` (eval mode).
   - The shipped `VisionPilot/modules/models/weights/autospeed_fp32.onnx` ends with
     `Concat(Mul(box), Sigmoid(cls))`; class channels 4–7 are in [0, 1].
2. **Training/validation uses them as probabilities.** `auto_speed/Models/training/auto_speed_util.py:124`
   (`non_max_suppression`, `confidence_threshold=0.001`) thresholds `outputs[:, 4:]` directly; called from
   `auto_speed_trainer.py:495`. The INT8 QDQ evaluation (`exports/quantization/auto_speed_qdq.py:227`) does the same.
3. **Inference applies sigmoid again.**
   - VisionPilot C++: `VisionPilot/modules/models/src/auto_speed.cpp:139`
     `const float prob = 1.f / (1.f + std::exp(-data[(4 + c) * N + n]));`, compared at `:147` with `conf_thres`
     (default 0.6, `include/models/auto_speed.hpp:57`; the comment at `:54` calls it a "sigmoid class probability threshold").
   - `auto_speed/Models/inference/auto_speed_infer.py:69`: `torch.max(class_probs.sigmoid(), dim=1)`, `conf_thres=0.6`.
   - `auto_speed/Models/visualizations/video_visualization.py:69`: `1 / (1 + np.exp(-class_probs))`, `conf_thres=0.6`.
4. Downstream, the score is only used for the threshold and NMS ordering (`longitudinal_fusion.cpp` uses class and box),
   so NMS results are identical between "double sigmoid + 0.6" and "single sigmoid + 0.405".

### Measured impact

I re-implemented the VisionPilot pre/post-processing in Python (onnxruntime, CPU) and ran AutoSpeed on two public dashcam
clips (Udacity `CarND-Advanced-Lane-Lines`, MIT licence, 1280×720, camera HFOV ≈ 58°, calibrated with my own ground
homography). "Current" = double sigmoid at 0.6 (= p ≥ 0.405); "probability 0.6" = no extra sigmoid at 0.6.

| Clip | Frames | Boxes, current / prob. 0.6 | Frames with a CIPO (class 1/2), current / prob. 0.6 |
|---|---|---|---|
| project_video (highway) | 1260 | 3506 / 2735 | 10 / 0 |
| challenge_video (highway) | 484 | 3378 / 2530 | 109 / 25 |

Inspecting the CIPOs that only pass at the current (lower) effective threshold: they are small (13–19 px wide) but real
vehicles in the ego lane, about 40–70 m ahead (crops attached). So simply removing the extra sigmoid while keeping 0.6
would reduce CIPO recall on these clips. I did not have labels, so I could not measure precision/recall properly.

*(Attach: `04-perception/results/autospeed_diff/cipo_crops.png` and one or two of the full-frame diffs from the same folder.)*

### Suggested fix

Option A (keeps current behaviour, fixes semantics; my suggestion):
- Remove the extra sigmoid in `auto_speed.cpp:139` (use the probability directly).
- Set the default `conf_thres` to `0.4` (≈ the current effective value 0.405) and update the comment.
- Apply the same change to `auto_speed_infer.py:69` and `video_visualization.py:69` in `auto_speed`.

Option B (if 0.6 on probabilities was the original intent):
- Remove the extra sigmoid and keep 0.6, accepting fewer detections, ideally after validating on labelled data that
  the drop is mostly false positives.

Either way, the reported scores become real probabilities, which matters for anyone tuning thresholds or using the
score downstream (e.g. weighting the AutoSpeed measurement in the longitudinal fusion).

Happy to open a PR for Option A if that direction sounds right. Which threshold was intended?

---

## Göndermeden önce kontrol listesi

- [ ] `main`'de satır numaralarını yeniden doğrula (repo hızlı değişiyor)
- [x] `auto_speed`'de "sigmoid" geçen issue/PR yok (GitHub araması, 19 Kas 2026)
- [ ] `autoware.privately-owned-vehicles`'da ara (bu oturumun erişimi o repoda aramaya izin vermedi)
- [ ] Görselleri ekle: `cipo_crops.png` + bir tam kare farkı
- [ ] Kendi hesabından gönder; repoda PoV WG'nin issue şablonu varsa ona uyarla
