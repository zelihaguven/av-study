# Tek kameradan direksiyona: takip katmanı sandığımız işi yapıyor mu?

*Serinin son yazısı. Kod: [04-perception](https://github.com/zelihaguven/av-study/tree/main/04-perception),
[05-integration](https://github.com/zelihaguven/av-study/tree/main/05-integration)*

Önceki yazılarda bir araç modeli, iki direksiyon kontrolcüsü ve bir Kalman filtresi yazdım. Bu yazıda
hepsini birleştiriyorum ve iki şey yapıyorum: VisionPilot'un gerçek modellerini açık bir sürüş videosunda
çalıştırıp çıktılarının ne kadar gürültülü olduğunu ölçüyorum, sonra bu gürültüyle küçük bir kapalı çevrim
kuruyorum. Sonuç beklediğimden farklı çıktı.

## 1. Gerçek modeller ne söylüyor?

VisionPilot'un üç ONNX modelini (AutoSteer, AutoSpeed, AutoDrive) C++ ön ve son işlemesini Python'a taşıyarak
CPU'da çalıştırdım. Test verisi Udacity'nin MIT lisanslı dashcam videoları (2943 kare): otoyol, köprü altı ve
virajlı bir orman yolu. Modellerin metre cinsinden konuşabilmesi için kamerayı kalibre etmem gerekti: yanal
ölçeği 3,7 m'lik şerit genişliğinden, boylamsal ölçeği kesikli çizgilerden, odak uzaklığını satranç tahtası
görüntülerinden.

![Otoyolda AutoSteer](04-perception/results/overlay_1_otoyol.png)

AutoSteer her karede yolun 64 noktasını veriyor. Bunlar zemine izdüşürülüp 2. derece bir polinoma uyduruluyor;
kontrolcünün ihtiyacı olan yanal hata ve yön hatası bu polinomdan çıkıyor.

**Titreşim ne kadar?** Gerçek yanal hatayı bilmiyorum, ama insan sürücünün şerit içindeki salınımı yavaş, modelin
titreşimi hızlı. 1 saniyelik ortalamadan kalan sapmayı titreşim saydım:

| | Otoyol | Orman yolu |
|---|---|---|
| Yanal hata titreşimi σ | 3 cm | 8,5 cm (firkete hariç 4,8 cm) |
| Yön hatası titreşimi σ | 0,3° | 3,2° |
| Ardışık kareler arası korelasyon | 0,66 | 0,65 |

![Titreşim](04-perception/results/noise.png)

Otoyolda model şaşırtıcı derecede kararlı. Ama iki uyarı var. Birincisi, hatalar bağımsız değil: bir kare sağa
kayıksa sonraki de büyük ihtimalle sağa kayık. İkincisi, asıl başarısızlıklar titreşim değil:

![Firkete virajda polinom](04-perception/results/failures/4_polinom_modeli.png)

Orman yolundaki firkete virajlarda RANSAC 2 m yarıçaplı anlamsız bir eğri uyduruyor. İlk tahminim
`y = a x² + b x + c` polinomunun keskin virajı temsil edemediğiydi; daha esnek, parametrik bir uydurma denedim
ve iyileşmedi. Asıl sorun modelin kaputun hemen önündeki noktalarının kanca çizmesi; her iki uydurma da o kancayı
izliyor. Diğer başarısızlıklar güneş parlaması ve aşırı pozlama. Bu hatalar saniyelerce sürüyor ve hiçbiri
"Gaussian gürültü" değil.

**Yan bulgu:** Kodu okurken AutoSpeed'de bir tutarsızlık buldum. Model sınıf olasılıklarını zaten sigmoid'den
geçirip veriyor, C++ son işleme ise bir sigmoid daha uyguluyor. Bu yüzden 0,6 olarak yazılmış eşik aslında
olasılıkta 0,405 gibi çalışıyor. Bunu ayrıca inceleyip proje ekibine sormayı planlıyorum.

## 2. Kapalı çevrim: filtre ne işe yarıyor?

Kapalı çevrim şöyle: araç modeli → sentetik algı (gerçek duruma gürültü ve kayıp eklenmiş) → Kalman filtresi →
eğrilik ileri beslemeli Stanley tipi kontrol → araç. Yol yine 50 m'lik S-virajı, 10 m/s.

![Kapalı çevrim](05-integration/results/closed_loop.png)

| %10 kayıp | Kontrolcünün gördüğü hata | Aracın gerçek yanal hatası | Direksiyon hızı |
|---|---|---|---|
| Filtresiz | 29 cm | 13,7 cm | 130 °/s |
| Filtreli | 8 cm | 15,2 cm | 19 °/s |

İlk baktığımda bunu bir ayar hatası sandım. Filtre kontrolcünün gördüğü hatayı 3,5 kat azaltıyor, ama aracın
gerçek yanal hatası aynı kalıyor. Filtrenin ayarlarını taradım, gürültüyü tamamen kapattım: sonuç değişmedi.

Sebep şu: **araç kendisi bir alçak geçiren filtre.** Direksiyon açısı yanal konumu iki kez entegre ederek
değiştiriyor. Hızlı, beyaz gürültü direksiyonu her karede sağa sola atıyor ama bu atışlar konumda birbirini
götürüyor. Filtrenin kalan hatası ise yavaş kayan bir hata ve doğrudan yola yansıyor.

Peki filtre gereksiz mi? Hayır, iki yerde vazgeçilmez:

1. **Direksiyon:** 130 °/s'lik bir komut hem konforsuz hem de gerçek bir direksiyon aktüatörünün yapamayacağı
   bir şey. Modelde direksiyon sınırsız hızlı olduğu için filtresiz sistem simülasyonda olduğundan iyi görünüyor.
2. **Uzun kesintiler:** Algı kaybı arttıkça fark açılıyor.

![Kayıp taraması](05-integration/results/dropout_sweep.png)

%80 kayıpta filtreli sistemin medyan maksimum sapması 0,84 m, filtresizin 4,6 m. Filtresiz sistem ölçüm
gelmeyince son ölçümü tutuyor ve araç hareket ettiği hâlde eski hatayı düzeltmeye devam ediyor; filtreli sistem
direksiyon girdisiyle durumu ileri taşıyor.

## 3. Gürültünün yapısı

04'te ölçtüğüm korelasyonu (ρ ≈ 0,6) sentetik algıya ekleyince tablo bir kez daha değişti:

![Gürültünün yapısı](05-integration/results/noise_structure.png)

- **Aynı σ ile yanal hata 2 katına çıkıyor.** σ tek başına bir algı modelinin ne kadar iyi olduğunu söylemiyor;
  hatanın ne kadar sürdüğü de önemli.
- **Filtre ilişkili gürültüyü silemiyor.** Kalman ardışık ölçümlerin ortalamasını alarak çalışıyor; 20 kare
  aynı yönde yanlışsa ortalamaları da yanlış. Korelasyon 0,95'e çıkınca filtrenin hatası ham ölçümünkiyle aynı.
- **Kayıp oranı yanıltıcı.** Aynı %30 kayıp bağımsız gelirse sistem rahat; 1 saniyelik kesintiler hâlinde gelirse
  araç şeritten çıkıyor. Belirleyici olan ortalama değil, en uzun kesinti.

## Ne öğrendim?

- Takip katmanının işi sanıldığı gibi "konumu daha doğru bilmek" değil; direksiyonu uygulanabilir kılmak ve
  algı kaybolduğunda ayakta kalmak.
- Bir algı modelini değerlendirirken titreşimin büyüklüğü kadar yapısı da önemli: ilişkili hatalar ve kümeli
  kayıplar filtrenin avantajını eritiyor.
- Gerçek başarısızlıklar (firkete, parlama) Gaussian modellerin dışında kalıyor. Firketede ilk suçladığım son
  işleme çıktı ama değildi: daha esnek bir uydurma denedim, iyileşmedi; bozuk olan modelin kaputun önündeki
  noktalarıydı. "Bir hipotezi gerçek veride test et" dersi.

Bu oyuncak sistem VisionPilot'tan birçok yerde farklı: algı burada doğrudan yanal hata veriyor, kontrolcü
ileriye bakmıyor, boylamsal kontrol yok, zamanlama ideal. Farkların tam listesi repoda. Ama bir sistemin
katmanlarını tek tek yazıp ölçmenin, mimari diyagramlarına bakmaktan çok daha fazlasını öğrettiği kesin.

*Bu bir öğrenme kaydıdır; Autoware'in resmi bir parçası değildir.*
