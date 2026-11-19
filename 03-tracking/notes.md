# 03 — Notlar

Tüm sayılar `python 03-tracking/src/plots.py` çıktısından. Senaryo testlerle aynı: öndeki aracın
mesafesi (CIPO), 20 Hz, sabit hız modeli, gerçek ivme gürültüsü q = 0,5 m²/s³, ölçüm std'si 1 m.
Yalnızca mesafe ölçülüyor, göreli hız hiç ölçülmüyor.

## Uygulama ayrıntıları

- **Joseph formu:** `P = (I − KH) P (I − KH)ᵀ + K R Kᵀ`. Kısa form `(I − KH) P` cebirsel olarak aynı, ama
  yuvarlama hatasında simetriyi ve pozitif tanımlılığı kaybedebilir. Ayrıca her adımda `P = (P + Pᵀ)/2`.
- **Kazanç açık ters almadan:** `K = P Hᵀ S⁻¹` yerine `S` ile `solve`. NEES de `P⁻¹` yerine `solve` ile.
- **`lane_model`'de Q:** `diag(q_y, q_psi) · dt`, yani `q_y` ve `q_psi` spektral yoğunluk (cv_model'deki
  `q` gibi). `e_y`'ye doğrudan gürültü eklemek, modelde olmayan yol eğriliği ve rüzgâr gibi bozucuları
  temsil ediyor.

## Sorular

### 1. Q ile R oranı filtrenin ölçüme mi modele mi güveneceğini nasıl belirler?

Kalman kazancı kabaca "tahminin belirsizliği / (tahminin belirsizliği + ölçümün belirsizliği)". Q büyükse
her predict adımında P çok büyür, kazanç 1'e yaklaşır ve filtre ölçümü izler. Q küçükse P küçük kalır,
kazanç 0'a yaklaşır ve filtre modele (sabit hız varsayımına) yapışır. Yalnızca **oran** önemli: Q'yu da
R'yi de 10 ile çarpmak kestirimi değiştirmez, sadece P'yi ölçekler.

`q_r_sweep.png`, aynı veri, r = 1 m² sabit:

| Filtredeki q | q / q_gerçek | Ölçüm varken RMSE(d) | RMSE(ḋ) | Kesintide maks hata |
|---|---|---|---|---|
| 0,005 | 0,01 | 1,62 m | 1,24 m/s | 10,1 m |
| **0,5** | **1** | **0,42 m** | **0,77 m/s** | **1,7 m** |
| 50 | 100 | 0,50 m | 1,76 m/s | 3,4 m |
| 5000 | 10⁴ | 0,74 m | 8,90 m/s | 30,1 m |

- **q çok küçük:** Filtre modele fazla güveniyor. Araç hızlandığında (t ≈ 8–10 s) geride kalıyor;
  ham ölçümden (0,94 m) bile kötü.
- **q çok büyük:** Mesafe neredeyse ham ölçüm kadar gürültülü. Asıl zarar ölçülmeyen durumda: hız
  kestirimi ardışık gürültülü ölçümlerin farkından geliyor (RMSE 8,9 m/s). Kesintide araç bu yanlış hızla
  2 s ötelendiği için hata 30 m'ye çıkıyor (grafikte en alt panel). Yani yanlış q'nun bedeli en çok
  ölçüm olmadığında ödeniyor.
- Doğru q her ölçütte en iyi. Bu sentetik veride beklenen bir sonuç, çünkü veri tam olarak filtrenin
  modelinden üretildi. Gerçek algıda q'yu bulmanın yolu 3. sorudaki tutarlılık testi.

### 2. Ölçüm gelmediğinde ne yapılır ve kovaryans neden büyür?

Ölçüm yoksa sadece `predict` çalışır, `update` atlanır (`z is None`). Durum modelle ileri taşınır:
mesafe son kestirilen hızla artmaya devam eder. `cipo.png`'de 10–12 s arasında mavi çizgi düz bir doğru,
hız kestirimi sabit.

Kovaryans büyür, çünkü her predict adımında `P ← F P Fᵀ + Q` ile belirsizlik ekleniyor ve onu küçültecek
bir ölçüm gelmiyor. Ayrıca `F` hızdaki belirsizliği mesafeye aktarıyor (`d += ḋ · dt`), bu yüzden mesafe
belirsizliği zamanla doğrusaldan hızlı büyüyor. Grafikte ±2σ bandı kesinti boyunca huni gibi açılıyor:
σ_d 0,34 m'den 1,89 m'ye çıkıyor. Kesinti sonunda gerçek hata 1,74 m, yani bandın içinde. Filtre hem
"bilmiyorum" diyor hem de ne kadar bilmediğini doğru söylüyor. İlk ölçümle σ_d 0,5 s içinde 0,37 m'ye
iniyor.

Pratik anlamı: ACC/AEB gibi bir özellik σ'ya bakarak karar verebilir. Örneğin σ_d belli bir eşiği geçerse
fren kararı vermeyip sürücüye uyarı verir. Kovaryans büyümeseydi kesinti sonunda filtre yanlış bir
mesafeye tam güvenle sahip olurdu.

### 3. Filtrenin tutarlı olması ne demektir, NEES bunu nasıl ölçer?

Tutarlı filtre, hatası kendi söylediği belirsizlik kadar olan filtredir. P "σ = 0,4 m" diyorsa gerçek hata
da tipik olarak 0,4 m civarında olmalı. Bu, hatanın küçük olmasından farklı bir şey: küçük hatalı ama
"hatam 1 cm" diyen bir filtre, hatası 40 cm ise tehlikelidir.

NEES `eᵀ P⁻¹ e`, hatayı filtrenin kendi belirsizliğiyle normalize eder. Filtre tutarlıysa ve hata Gaussian
ise NEES, serbestlik derecesi durum boyutuna (burada 2) eşit bir ki-kare dağılımına uyar. Beklenen değeri
2'dir. `nees.png` filtrenin q'sunu bilerek yanlış ayarlayınca ne olduğunu gösteriyor:

| q_filtre / q_gerçek | 0,01 | 0,1 | 0,46 | **1** | 2,2 | 10 | 100 |
|---|---|---|---|---|---|---|---|
| Ortalama NEES | 77,7 | 10,0 | 2,94 | **1,90** | 1,43 | 1,12 | 1,06 |

- **NEES ≫ 2: aşırı özgüvenli.** P gerçek hatadan küçük. En tehlikeli durum: filtre yanılıyor ama emin.
- **NEES ≪ 2: aşırı temkinli.** P gerçek hatadan büyük. Güvenli ama işe yaramaz: σ hep büyük olduğu için
  ona bakan bir karar mekanizması gereksiz yere uyarı verir ya da özelliği kapatır. Burada NEES 1'in altına
  inmiyor, çünkü mesafe doğrudan ölçülüyor ve mesafe belirsizliği hiçbir zaman ölçüm gürültüsünden
  (r = 1 m²) büyük olamıyor. NEES'e o bileşen her zaman ~1 katkı veriyor.

**NEES testi neden bir aralık kontrolü?** İki yönde de başarısızlık var. Yalnız üst sınır koysak aşırı
temkinli bir filtre testten geçerdi. Sonsuz q ile bile NEES düşük kalır ve filtre "tutarlı" görünürdü.
Tutarlılık "hata ≈ söylenen belirsizlik" demek, yani "çok küçük" de "çok büyük" de ihlal.

Aralığın genişliği istatistikten geliyor. Ortalama NEES rastgele bir sayı: 50 koşunun ortalaması,
serbestlik derecesi 50 × 2 = 100 olan ki-kareyi 50'ye bölmekle aynı dağılıma sahip. Doğru ayarlanmış bir
filtre bile tam 2,00 vermez (burada 1,90). %95 güven aralığı [1,48; 2,59], doğru filtrenin 20 denemenin
19'unda düştüğü bölge. Grafikte bu aralık q'yu kabaca 0,5–2 kat yanlış ayarlamayı yakalıyor: q iki kat
büyük (NEES 1,43) ve yarısı (2,94) zaten aralığın dışında.

Dikkat: test zamana göre de ortalıyor (her koşuda 150 adım) ve ardışık adımların hataları bağımsız değil.
Bu yüzden testin docstring'i aralığı "gevşek" diye niteliyor: gerçek dağılım chi²(100)/50'den daha geniş.

## VisionPilot ile fark

VisionPilot 1.0 bu katmanda Kalman değil **parçacık filtresi** kullanıyor (00 notları, 2. bölüm): CIPO için
500 parçacıkla [mesafe, hız]. Parçacık filtresi Gaussian olmayan dağılımları (ör. "araç ya 30 m'de ya
60 m'de", iki modlu) taşıyabilir ve aykırı ölçümlere daha dayanıklı olabilir, ama daha pahalıdır ve NEES
gibi bir tutarlılık testini kurmak zordur. Lineer Kalman, ikisinin de temeli olan predict/update
mantığını en açık hâliyle öğretiyor.
