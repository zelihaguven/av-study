# Bisiklet modeli: otonom sürüşün en küçük simülatörü

*Serinin ikinci yazısı. Kod: [01-vehicle-model](https://github.com/zelihaguven/av-study/tree/main/01-vehicle-model)*

Bir direksiyon kontrolcüsünü test etmek için gerçek bir araca ihtiyacınız yok, ama aracın nasıl hareket ettiğini
söyleyen bir modele ihtiyacınız var. Otonom sürüş literatüründe en sık kullanılan model şaşırtıcı derecede basit:
dört tekerleği ikiye indiren **kinematik bisiklet modeli**. Bu yazıda onu yazıp iki soruyu cevaplıyorum: sayısal
olarak ne kadar doğru, ve fiziksel olarak ne zaman yanlış söylüyor?

## Dört denklem

Aracın durumu dört sayı: arka aksın konumu `(x, y)`, baktığı yön `ψ` ve hızı `v`. Girdiler direksiyon açısı `δ` ve
ivme `a`. Lastiklerin kaymadan, baktıkları yöne gittiğini varsayınca:

```
ẋ = v cos ψ
ẏ = v sin ψ
ψ̇ = v / L · tan δ
v̇ = a
```

`L` dingil mesafesi (burada 2,7 m). Üçüncü denklem işin özü: direksiyonu sabit tutarsanız araç `R = L / tan δ`
yarıçaplı bir çember çizer. 10° direksiyonda bu 15,3 m.

Referans noktası olarak arka aksı seçtim, çünkü sonraki yazıdaki Pure Pursuit bu tanımı kullanıyor. Ağırlık
merkezini seçseydiniz denklemlere bir kayma açısı terimi eklenirdi.

## Sayısal doğruluk: Euler ve RK4

Bu denklemleri bilgisayarda küçük zaman adımlarıyla ilerletmek gerekiyor. En basit yol Euler: her adımda teğet
boyunca `dt` kadar git. Daha iyisi RK4: adım içinde dört kez eğimi ölçüp ağırlıklı ortalamasını al.

Test basit: sabit direksiyonla bir tam tur at, çemberden ne kadar saptığına bak.

![Sabit direksiyonla bir tur](01-vehicle-model/results/circle.png)

| dt | Euler hatası | RK4 hatası |
|---|---|---|
| 0,001 s | 1,6e-4 | 1,6e-12 |
| 0,01 s | 1,6e-3 | 1,4e-13 |
| 0,1 s | 1,6e-2 | 7,9e-10 |

![dt ile hata](01-vehicle-model/results/dt_error.png)

Euler'de hata `dt` ile doğrusal düşüyor (1. mertebe) ve araç her adımda teğet boyunca gittiği için çemberin
dışına doğru spiral çiziyor. RK4'te hata 4. mertebe; `dt = 0,01`'de bilgisayarın kayan nokta sınırına iniyor.
Grafiğin ilginç bir detayı: RK4'ün hatası `dt = 0,001`'de tekrar biraz artıyor. Bu yöntemin değil, 10 kat fazla
adımda biriken yuvarlama hatasının izi.

Pratik sonuç: RK4 ve makul bir `dt` ile sayısal hata ihmal edilebilir. Simülasyonun ne kadar doğru olduğunu artık
entegrasyon değil, modelin kendisi belirliyor.

## Model ne zaman yanlış söyler?

Bu, yazdığım kodun en önemli kısmı değil ama en önemli notu. Kinematik model tek bir varsayıma dayanıyor:
tekerlekler kaymıyor. Bu varsayım bozulduğu her yerde model yanlış:

1. **Hızlı viraj.** Gerçek lastik yanal kuvvet üretmek için hafifçe kayar. Hız arttıkça araç modelin
   söylediğinden geniş döner; model hâlâ `R = L / tan δ` der.
2. **Kaygan zemin.** Modelde sürtünme diye bir şey yok; kuru asfaltla buzu ayırt etmez.
3. **Direksiyon anında dönmez.** Gerçek sistemde gecikme var. Autoware'in MPC ayarları 0,24 s gecikme ve
   0,27 s zaman sabiti varsayıyor. Bunu yok sayan bir kontrolcü simülasyonda iyi, gerçek araçta salınımlı olabilir.
4. **Ağırlık transferi, eğim, motor dinamiği yok.** Araç düz zeminde kayan rijit bir çubuk.

Sonuç: bu model kontrolcüleri birbiriyle *karşılaştırmak* için yeterli, ama bir kontrolcünün gerçek araçta *ne
kadar iyi* çalışacağını söylemez. Serinin geri kalanındaki bütün sayıları bu uyarıyla okumak gerekiyor; özellikle
3. madde, son yazıda bir sonucu doğrudan etkiliyor.

## Sırada

Simülatör hazır. Bir sonraki yazıda üzerine iki klasik direksiyon kontrolcüsünü koyup aynı S-virajında
yarıştırıyorum: Pure Pursuit ve Stanley.

*Bu bir öğrenme kaydıdır; Autoware'in resmi bir parçası değildir.*
