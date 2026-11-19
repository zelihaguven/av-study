# Gürültülü ölçümden güvenilir duruma: Kalman filtresi ve "ne kadar bilmediğini bilmek"

*Serinin dördüncü yazısı. Kod: [03-tracking](https://github.com/zelihaguven/av-study/tree/main/03-tracking)*

Öğrenilmiş bir algı modelinin çıktısı kareden kareye titrer ve bazen hiç gelmez. Bu çıktıyı doğrudan
kontrolcüye vermek direksiyonu titretir. Algı ile kontrol arasına klasik bir **takip** katmanı koyulur. Bu yazıda
en basit hâlini, lineer Kalman filtresini, öndeki aracın mesafesini takip ederek anlatıyorum: 20 Hz'de, 1 m
gürültüyle ölçülen bir mesafe. Göreli hız hiç ölçülmüyor.

## Tahmin et, düzelt

Kalman filtresi iki adımı tekrarlar:

- **Tahmin (predict):** "Sabit hızla gidiyorsa 0,05 s sonra nerede olur?" Durum ileri taşınır, belirsizlik (`P`)
  büyür.
- **Düzeltme (update):** Ölçüm gelir. Filtre tahmini ile ölçümü, ikisinin belirsizliğine göre ağırlıklandırarak
  birleştirir; belirsizlik küçülür.

![CIPO takibi](03-tracking/results/cipo.png)

Sonuç: ham ölçümün hatası 0,94 m, filtrenin 0,42 m. Daha ilginci alt panel: hiç ölçülmeyen göreli hız 0,77 m/s
hatayla kestiriliyor. Filtre ardışık mesafe ölçümlerinden hızı kendisi çıkarıyor.

## Ölçüm gelmezse

Grafikte 10–12 s arasında 2 saniye ölçüm yok. Filtre bu sırada sadece tahmin yapıyor: mavi çizgi düz bir doğru.
Belirsizlik bandı huni gibi açılıyor: σ 0,34 m'den 1,89 m'ye çıkıyor. Kesinti sonunda gerçek hata 1,74 m, yani
bandın içinde.

Bence bu filtrenin en önemli özelliği: sadece "bilmiyorum" demiyor, ne kadar bilmediğini doğru söylüyor. Bir ACC
veya AEB sistemi bu σ'ya bakıp karar verebilir: belirsizlik çok büyüyünce fren yerine sürücüye uyarı.

## Q ve R: kime güveneceğim?

Filtrenin iki ayarı var: Q (model ne kadar yanılabilir) ve R (ölçüm ne kadar gürültülü). Önemli olan oranları.

![q taraması](03-tracking/results/q_r_sweep.png)

| q / gerçek q | Ölçüm varken hata | Hız hatası | Kesintide maks hata |
|---|---|---|---|
| 0,01 | 1,62 m | 1,24 m/s | 10,1 m |
| **1** | **0,42 m** | **0,77 m/s** | **1,7 m** |
| 10 000 | 0,74 m | 8,90 m/s | 30,1 m |

q çok küçükse filtre modele fazla güveniyor ve araç hızlanınca geride kalıyor. q çok büyükse mesafe neredeyse ham
ölçüm kadar gürültülü, ama asıl zarar görünmeyen yerde: hız kestirimi ardışık gürültülü ölçümlerin farkından
geliyor ve kesintide araç bu yanlış hızla 2 s ötelendiği için hata 30 m'ye çıkıyor. Yanlış ayarın bedeli en çok
ölçüm olmadığında ödeniyor.

## Tutarlılık: NEES

Gerçek bir sistemde doğru q'yu nereden bileceğiz? Bir filtrenin hatasının küçük olması yetmez; hatası kendi
söylediği belirsizlik kadar olmalı. Buna **tutarlılık** deniyor. "Hatam 1 cm" diyen ama 40 cm yanılan bir filtre
tehlikeli.

NEES (`eᵀ P⁻¹ e`) hatayı filtrenin kendi belirsizliğiyle normalize ediyor. Filtre tutarlıysa ortalaması durum
boyutuna (burada 2) eşit. q'yu bilerek yanlış ayarlayınca:

![NEES ve yanlış q](03-tracking/results/nees.png)

- q çok küçük → NEES 77: **aşırı özgüvenli**. Filtre yanılıyor ama emin. En tehlikeli durum.
- q çok büyük → NEES 1'e iniyor: **aşırı temkinli**. Güvenli ama işe yaramaz; σ hep büyük olduğu için ona bakan
  sistem gereksiz yere özelliği kapatır.

Bu yüzden NEES testi bir **aralık** kontrolü: [1,48; 2,59]. Yalnızca üst sınır koysaydık sonsuz q'lu, hiçbir şeye
güvenmeyen bir filtre testten geçerdi. Aralığın genişliği istatistikten geliyor: 50 koşunun ortalaması bile
rastgele bir sayı, doğru ayarlanmış filtre de tam 2,00 vermiyor (burada 1,90).

## VisionPilot ne kullanıyor?

İlginç bir şekilde Kalman değil. VisionPilot 1.0'ın takip katmanı parçacık filtreleri kullanıyor: dağılımı
yüzlerce örnekle temsil eden, Gaussian olmayan durumları da taşıyabilen ama daha pahalı bir yöntem. Lineer Kalman
yine de ikisinin ortak temelini, tahmin et ve düzelt döngüsünü, en açık hâliyle gösteriyor.

Sırada: bütün parçaları birleştiriyorum. Gerçek VisionPilot modelleri, filtre ve kontrolcü tek bir kapalı
çevrimde, ve bir sürpriz: filtre sanıldığı işi yapmıyor.

*Bu bir öğrenme kaydıdır; Autoware'in resmi bir parçası değildir.*
