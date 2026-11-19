# 00 — Mimari

## Öğrenme hedefi

Bu modülün sonunda iki mimariyi kağıt kalem çizebilmeli ve aralarındaki farkı bir
mülakatta 2 dakikada anlatabilmelisin:

1. **Klasik modüler stack** (Autoware Universe):
   sensing → perception → localization → planning → control → vehicle interface
2. **Görüntü tabanlı L2 sistemi** (VisionPilot): tek kamera → öğrenilmiş modeller
   → klasik takip ve kontrol

Her modül için "ne alır, ne verir, ne sıklıkla, başarısız olursa ne olur" sorularını
cevaplayabilmek asıl hedef. Algoritmaların içine bu modülde girilmez.

## Okumalar

- Autoware dokümantasyonu: *Design* bölümü ve mimari genel bakış sayfaları
- Paden ve ark. (2016) survey: giriş ve mimari bölümleri
- Chen ve ark., *End-to-end Autonomous Driving: Challenges and Frontiers*: giriş ve modüler/E2E karşılaştırması
- [`autowarefoundation/autoware.privately-owned-vehicles`](https://github.com/autowarefoundation/autoware.privately-owned-vehicles) (VisionPilot): README, mimari görseli

## Görevler

- [x] `architecture.md` içindeki iki Mermaid diyagramını doldur
- [x] Modül arayüz tablosunu doldur (en az 6 satır, modüler stack için)
- [x] VisionPilot için aynı tabloyu doldur. Hangi model hangi özelliği (ACC, LKAS, AEB…) besliyor?
- [x] "Sorular" bölümündeki 6 soruyu kendi cümlelerinle cevapla

## Kabul kriteri

- [x] İki diyagram GitHub'da render oluyor ve her okun üzerinde **taşınan veri** yazıyor
      (ör. "point cloud", "trajectory", "steering angle"), sadece ok değil.
- [x] Arayüz tablosunda her satır için giriş, çıkış ve tipik frekans (Hz) var.
      Frekansı bilmiyorsan "?" yaz ve kaynağını bulunca güncelle. Uydurma sayı yok.
- [x] 6 sorunun her biri en az 3 cümle ve en az birinde kaynak referansı var.

## Yazı

→ `docs/writing-plan.md` #1
