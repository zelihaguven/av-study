# Bir otonom aracın yazılımı kaç parçadan oluşur? Modüler stack ile tek kameralı L2

*Otonom araç yazılımını sıfırdan öğrenme serisinin ilk yazısı. Kod ve diyagramlar:
[github.com/zelihaguven/av-study](https://github.com/zelihaguven/av-study/tree/main/00-architecture)*

Otonom sürüş deyince akla genelde tek bir "yapay zekâ" gelir. Açık kaynak sistemlerin koduna bakınca tablo
farklı: araç, her biri ayrı bir soruyu cevaplayan modüllerden oluşan bir boru hattı. Bu yazıda iki mimariyi
karşılaştırıyorum: Autoware'in tam modüler stack'i ve aynı ekosistemdeki tek kameralı L2 sistemi VisionPilot.
İkisini de kaynak koda ve dokümantasyona bakarak çizdim, bilmediğim yerleri "?" bıraktım.

## Modüler stack: altı soru, altı modül

Autoware'de veri şöyle akıyor:

- **Sensing:** "Sensörler ne görüyor?" Kamera görüntüsü, LiDAR noktaları, GNSS, IMU.
- **Localization:** "Haritada neredeyim?" Çıktı aracın konumu, hızı ve belirsizliği; en az 50 Hz.
- **Perception:** "Etrafımda ne var, nereye gidiyor?" Tahmini nesneler, trafik ışıkları; tracker 10 Hz.
- **Planning:** "Nereden gideyim?" Bir yörünge (trajectory).
- **Control:** "Bu yörüngeyi izlemek için direksiyonu ne kadar çevireyim?" Yaklaşık 33 Hz.
- **Vehicle interface:** Komutu araca iletir, aracın durumunu geri okur.

![Autoware veri akışı](docs/medium/img/autoware_mimari.png)

Diyagramı çizerken iki şey beni şaşırttı. Birincisi, oklar sanıldığı kadar tek yönlü değil: localization
perception'ı besliyor (nesneleri haritaya yerleştirmek için önce aracın kendi konumu gerekiyor), planning de
perception'a rotayı geri gönderiyor. İkincisi, frekanslar aşağıdan yukarıya artıyor: perception 10 Hz'de
çalışırken control 33 Hz'de. Planlama birkaç saniye ileriyi kapsadığı için her döngüde yeniden hesaplanması
gerekmiyor; kontrol ise rüzgâr, eğim gibi küçük bozucuları hızla düzeltmek zorunda.

Her modülün bir de "başarısız olursa ne olur" cevabı var. Control'e yeterince sık komut gelmezse araç acil duruş
yapıyor; planning bir sensör arızasında asgari risk manevrasına (MRM) geçiyor: acil duruş, konforlu duruş veya
kenara çekme. Bu tablolar mimarinin ne kadarının "normal sürüş" değil "bir şey bozulunca ne yapılır" olduğunu
gösteriyor.

## VisionPilot: tek kamera, üç model, klasik füzyon

VisionPilot'un hedefi çok daha dar: tek bir ön kamerayla L2 sürücü destek özellikleri (ACC, AEB, LKAS, LDW).
HD harita yok, LiDAR yok. README modelleri özelliklerle eşleştirmediği için akışı kaynak koddan çıkardım:

1. **Kamera** → iki ayrı ön işleme: kırpıp küçültme ve homografiyle başka bir perspektife çevirme.
2. **Üç model paralel:**
   - *AutoSteer*: ego yolun 64 noktası (nereye gidiyorum?)
   - *AutoSpeed*: nesne kutuları, öndeki en yakın araç (CIPO) sınıfıyla
   - *AutoDrive*: iki kareden uçtan uca CIPO mesafesi ve yol eğriliği
3. **Füzyon:** Kalman değil, parçacık filtreleri. Yol noktalarına RANSAC ile polinom uyduruluyor.
4. **Planlama/kontrol:** boylamsalda IDM (öndeki araca göre hız), yanalda MPC (10 m ileri bakan optimizasyon).
5. **Uyarılar:** FCW, AEB, LDW için sabit eşikler.

![VisionPilot veri akışı](docs/medium/img/visionpilot_mimari.png)

Burada da sürprizler vardı. Önceki VisionPilot anlatımlarında geçen EgoLanes modeli 1.0'ın ana uygulamasında
artık kullanılmıyor. Kodda bir de küçük tutarsızlık buldum: bir yorum "50 Hz kontrol periyodu" derken değer
`dt = 0.05`, yani 20 Hz. Mimari diyagramı koddan çizmenin faydası tam da bu: dokümantasyonun söylediğiyle kodun
yaptığı arasındaki farkı görmek.

## Uçtan uca mı, modüler mi?

VisionPilot kendini "hibrit" olarak tanımlıyor ve bence doğru: öğrenilmiş modeller algıyı yapıyor, ama çıktıları
yorumlanabilir ara büyüklükler (yol noktaları, mesafe, eğrilik). Sonrasında klasik filtreler ve kontrolcüler
geliyor. Tamamen uçtan uca bir modelde kameradan direksiyona kadar her şey tek bir ağın içinde gizli olurdu ve
bir hatanın algıdan mı kontrolden mi geldiğini ayırmak zorlaşırdı. Hibrit yapıda, ileriki yazılarda göreceğimiz
gibi, her katmanı ayrı ayrı test edip ölçmek mümkün.

İki mimari arasındaki en büyük fark sorumluluk. VisionPilot bir L2 sistemi: SAE J3016'ya göre sürüşü izlemek ve
gerektiğinde devralmak sürücünün işi. Bu yüzden mimaride yedekli sensörler veya kenara çekme manevrası yok,
belirsizlik büyüyünce özellik kapanıp sürücüye devrediyor. L4'e geçildiğinde fallback sisteme geçer ve modüler
stack'teki MRM, yedekli sensör, sürekli arıza izleme gibi parçalar zorunlu hâle gelir.

## Sırada

Bu serinin geri kalanında VisionPilot'un küçük bir kopyasını Python'da adım adım kuruyorum: önce aracın kendisi
(bisiklet modeli), sonra direksiyon kontrolü, sonra gürültülü algıyı süzen filtre ve en son gerçek modellerin
çıktısıyla kapalı çevrim.

*Bu bir öğrenme kaydıdır; Autoware'in resmi bir parçası değildir.*
