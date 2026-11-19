# Pure Pursuit ile Stanley aynı virajda neden farklı davranır?

*Serinin üçüncü yazısı. Kod: [02-control](https://github.com/zelihaguven/av-study/tree/main/02-control)*

Önceki yazıda bir araç simülatörü yazdım. Şimdi direksiyonu kim çevirecek? Bu yazıda en bilinen iki geometrik
yanal kontrolcüyü aynı yolda karşılaştırıyorum: **Pure Pursuit** ve **Stanley**. Yol kasıtlı olarak zor bir
S-virajı: 20 m düz, 50 m yarıçaplı 90° sola, hemen ardından 90° sağa, sonra yine düz. Eğrilik iki kez aniden
değişiyor. Araç 10 m/s ile gidiyor.

## İki fikir

**Pure Pursuit:** yol üzerinde `Ld` metre ilerideki bir noktayı seç, arka aksı o noktaya teğet bir yayla bağla.
Direksiyon açısı bu yayın eğriliğinden çıkıyor: `δ = atan(2L sin α / Ld)`. Bir sürücünün "ileriye bakarak sürmesi"
gibi.

**Stanley:** ön aksa bak. Yola göre ne kadar yanlış yöne bakıyorsun ve yoldan ne kadar uzaktasın?
`δ = yön hatası + atan(k · e / (k_soft + v))`. İleriye bakmıyor, sadece şu anki hataya tepki veriyor.

## Sonuç

| | RMS sapma | Maks sapma | Maks direksiyon hızı |
|---|---|---|---|
| Pure Pursuit (Ld = 5 m) | 2,2 cm | 10,3 cm | 8 °/s |
| Stanley (k = 1) | 6,3 cm | 7,3 cm | 22 °/s |

![Sapma ve direksiyon hızı](02-control/results/s_curve_cte.png)

İkisi de yolda kalıyor, ama hata profilleri tamamen farklı. Grafik üç şey gösteriyor.

**1. Pure Pursuit virajın ortasında hatasız, geçişlerde içeri kesiyor.** Ders kitapları "Pure Pursuit virajda
içeri keser" der. Benim sonucum daha nüanslı: sabit eğrilikli bir çemberin ortasında, ileri bakış noktası da
aynı çember üzerinde olduğu için Pure Pursuit'in çizdiği yay yolun kendisi ve hata sıfır. İçeri kesme eğriliğin
değiştiği yerde oluyor. İleri bakış noktası yeni virajın içine girdiğinde araç henüz düzde ve dönmeye erken
başlıyor. Hata çizgiden yaklaşık `Ld / v = 0,5 s` önce yükselmeye başlıyor.

**2. Stanley geç ama sert tepki veriyor.** İleriyi görmediği için eğrilik değişimini ancak ön aks oraya varınca
fark ediyor ve direksiyon hızında sivri bir tepe yapıyor (22 °/s).

**3. Stanley virajda kalıcı bir sapma bırakıyor.** Virajın içinde yaklaşık 7 cm. Sebep yol eğriliğini bilmemesi:
direksiyonu virajda tutmak için sıfırdan farklı bir hataya ihtiyaç duyuyor. Çözümü bir eğrilik ileri besleme
terimi (`δ += atan(L · κ)`); son yazıda bunun etkisini ölçeceğim.

## İleri bakış mesafesi: doğruluk mu, yumuşaklık mı?

![Ld taraması](02-control/results/lookahead_sweep.png)

Pure Pursuit'in tek ayarı `Ld`. Sol grafikte görüldüğü gibi hata `Ld` ile kabaca karesel büyüyor: 2 m'de 0,2 cm,
15 m'de 34 cm. Ama `Ld` küçüldükçe direksiyon sertleşiyor: 2 m'de 20 °/s, 15 m'de 3,7 °/s.

Sağ grafik beni şaşırttı. Klasik öneri ileri bakışı hızla ölçeklemek: `Ld = k · v`. Bu deneyde ölçeklenen `Ld`
takip hatasını **iyileştirmedi, kötüleştirdi**: 20 m/s'de sabit 5 m ile 2 cm, ölçeklenen (10 m) ile 12 cm.
Ölçeklemenin kazandırdığı şey başka: düz yolda 1 m ofsetten toparlanırken direksiyon hızı 20 m/s'de 118 °/s
yerine 12 °/s. Aynı direksiyon açısı yüksek hızda çok daha büyük yanal ivme demek; ölçekleme ileri bakış
*süresini* sabit tutarak kontrolcünün hızla sertleşmesini engelliyor.

Simülasyonun burada sabit `Ld`'yi olduğundan iyi gösterdiğini de not etmek gerek: modelde direksiyon gecikmesi
yok. 118 °/s isteyen bir kontrolcü gecikmeli gerçek bir araçta salınıma girer.

## Stanley düşük hızda neden sert?

![Stanley yumuşatma terimi](02-control/results/stanley_soft.png)

Stanley'nin yanal hata teriminin paydasında hız var. Hız sıfıra yaklaştıkça kazanç sonsuza gider ve küçük bir
hata bile direksiyonu sınıra dayatır. `k_soft` bu kazancı sınırlıyor: 2 m/s'de `k_soft = 0,1` ile ilk direksiyon
25,5°, `k_soft = 5` ile 8,1°. Bedeli toparlanmanın yavaşlaması (5,7 s yerine 12,2 s). Yüksek hızda etkisi
kayboluyor; sadece park ve kalkışı ilgilendiren bir ayar.

## Küçük bir hata ayıklama hikâyesi

Stanley'nin ilk sürümünde direksiyon hızında virajın ortasında anlamsız sıçramalar vardı. Sebebi fiziksel
değildi: yol 0,1 m aralıklı noktalarla tanımlıydı ve araç her adımda 0,2 m ilerliyordu. Ara sıra 3 nokta
atlayınca yol yönü basamaklı değişiyordu. Yönü en yakın noktadan değil, izdüşüme göre interpolasyonla
hesaplayınca düzeldi. Gerçek bir sistemde de yolun çözünürlüğü kontrol çıkışında görünür.

## Özet

Pure Pursuit ileriye baktığı için yumuşak ve virajda doğru, ama eğrilik değişiminde erken dönüyor. Stanley anlık
hataya bakıyor; ileri besleme olmadan virajda kalıcı sapma bırakıyor. VisionPilot'un yanal kontrolü ikisinden
de farklı: 10 m ileri bakan bir MPC, yani hem ileriyi görüyor hem eğriliği modelin içinde taşıyor.

Sırada: kontrolcüye giden ölçüm gürültülü olursa ne olur? Kalman filtresi.

*Bu bir öğrenme kaydıdır; Autoware'in resmi bir parçası değildir.*
