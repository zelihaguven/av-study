# Sıradaki Adımlar

**Sıra:** Önce ana TODO listesinde kalanlar (aşağıda "0", tamamlandı). Ek işler (A, B) **en son**, ana liste bitince.

## 0. Ana listeden kalanlar (önce bunlar)

Ana TODO'nun 35 maddesinin 34'ü bitti, okuma günlüğü çıkarıldı:

- [x] `docs/glossary.md` tanımları
- [x] Medium yazıları (`docs/writing-plan.md`): 5 taslak, `docs/medium/` altında (yayımlama senin kararın)
  - [x] #1 Mimari (00)
  - [x] #2 Bisiklet modeli (01)
  - [x] #3 Pure Pursuit vs Stanley (02)
  - [x] #4 Kalman (03)
  - [x] #5 Tek kameradan direksiyona (04 + 05)

---

Aşağıdakiler ana liste bittikten sonra. Öncelik sırasıyla, her madde en fazla birkaç saatlik.

## A. VisionPilot'a katkı adayları

Hepsi 04'te `65375ec2cf` sürümünde bulundu (`04-perception/notes.md`). Issue açmadan önce `main`'de hâlâ
geçerli olduğunu kontrol et.

1. **AutoSpeed çift sigmoid (en güçlü aday).** ONNX çıktısı zaten olasılık (`Concat(kutu, Sigmoid(sınıf))`),
   `modules/models/src/auto_speed.cpp:139` ikinci kez sigmoid uyguluyor; `conf_thres = 0.6` aslında 0,405.
   - [x] `auto_speed` Python kodu: çift sigmoid orada da var; eğitim/doğrulama çıktıyı olasılık olarak kullanıyor
   - [x] Etkiyi ölç: CIPO kareleri 109 → 25 (challenge), kaybolanlar gerçek uzak araçlar (etiket yok, kesinlik ölçülmedi)
   - [x] Issue taslağı: `docs/contributions/autospeed-double-sigmoid.md`. Gönderme kararı kullanıcıda; kontrol listesi taslakta.
2. **Kontrol periyodu tutarsızlığı.** `modules/safety_guardian/planning/include/planning/config.hpp`: yorum "50Hz",
   değer `dt = 0.05` (20 Hz). Füzyon ise `dt = 0.10` (10 Hz) varsayıyor ve `update()` dt'siz çağrılıyor
   (`inference.cpp:207`).
   - [x] Commit geçmişi: `dt` eski zaman tabanlı MPC'den kalma; etkili tek kullanımı `dkappa_ds`. Taslak: `docs/contributions/planning-dt-mismatch.md`
3. **Bayat yorumlar (küçük "good first PR").** `auto_speed.hpp:35-36` (letterbox yok), `image_preprocessor.hpp:14`
   ("BEV" değil), `lateral_fusion.hpp:34-35,55` (CTE x = 0'da değil `x_ref`'te), `lateral_fusion.hpp:93,99`
   (0,25 → 0,20, 15 → 12).
   - [x] Tek bir dokümantasyon PR'ı taslağı: `docs/contributions/stale-comments-pr.md`
4. **Keskin virajda son işleme.** `y = a x² + b x + c` yana dönen yolu temsil edemiyor (04, başarısızlık 4).
   - [ ] Alternatifi dene: yay uzunluğuna göre parametrik uydurma veya `x(y)` + `y(x)` arasında seçim; harder_challenge
     firkete bölümünde (39–44 s) karşılaştır
   - [ ] Sonuç iyiyse issue olarak öner (önce tartışma, sonra PR)

## B. Bu repoda derinleştirme

5. [x] 05: ilişkili (AR(1)) gürültü ve kümeli kayıp (sıra dışı yapıldı) (`05-integration/notes.md`, "Gürültünün yapısı")
5b. [ ] 05: takip katmanına ilişkili gürültüyü bildir (gürültüyü durum olarak ekle / shaping filter) ve ρ = 0,6'da
   yanal hatanın düşüp düşmediğini ölç
6. [ ] 04: INT8'in bu CPU'da neden yavaş olduğunu doğrula (`lscpu` bayrakları, onnxruntime profili)
7. [ ] 04: modelleri `std::async` gibi paralel çalıştırınca kare süresi (ThreadPool ile)
8. [ ] 02/05: direksiyon gecikmesi (0,24 s) ve hız sınırı ekleyip takipsiz sistemin yanal hatasını yeniden ölç
   (05 notlarında "ölçmedim, çıkarım" olarak geçen iddia)
