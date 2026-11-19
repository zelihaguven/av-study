# 01 — Notlar

## Model ne zaman yanlış söyler?

Kinematik bisiklet modeli tekerleklerin **kaymadan**, baktıkları yöne gittiğini varsayar. Bu varsayım
bozulduğu her durumda model yanlış sonuç verir.

1. **Yüksek yanal ivme (hızlı viraj).** Gerçek lastik yanal kuvvet üretmek için hafifçe kayar
   (kayma açısı). Hız ve viraj keskinliği arttıkça bu kayma büyür ve araç modelin söylediğinden daha
   geniş döner (understeer). Model bu durumda R = L / tan δ'yı hâlâ "doğru" sanır. Bu yüzden 02'deki
   testler düşük–orta hızda ve yumuşak virajlarda anlamlı; yüksek hızda
   dinamik bisiklet modeli (lastik kuvvetleri, kütle, atalet) gerekir (Kong ve ark., 2015).

2. **Kaygan zemin (ıslak, buzlu yol).** Sürtünme katsayısı düşünce lastiğin üretebileceği yanal kuvvet
   azalır ve kayma çok daha düşük hızlarda başlar. Modelde sürtünme diye bir parametre yok; kuru asfalt ile
   buz arasında aynı direksiyon açısı için aynı yörüngeyi verir.

3. **Direksiyon anında gerçekleşmez.** Model komut verilen açının o an tekerleğe geçtiğini varsayar.
   Gerçek direksiyon sisteminin gecikmesi ve zaman sabiti var; örneğin Autoware'in MPC ayarlarında
   gecikme 0,24 s, zaman sabiti 0,27 s alınmış (`mpc.param.yaml`, bkz. 00 arayüz tablosu). Bunu
   hesaba katmayan bir kontrolcü simülasyonda iyi, gerçek araçta salınımlı çalışabilir.

4. **Ağırlık transferi, yuvarlanma, eğim yok.** Fren yaparken yük öne, virajda dışa kayar; bu her
   tekerleğin tutuşunu değiştirir. Model aracı düz bir zeminde kayan rijit bir çubuk gibi ele alır; yol
   eğimi (dever) ve yokuş da yok. İvme komutu doğrudan hıza dönüşür, motor ve fren dinamiği yok.

5. **Sayısal hata (modelin değil, entegrasyonun hatası).** Euler'de `dt` büyükse araç çemberin
   dışına spiral çizer (dt = 0,1 s'de %1,6 yarıçap hatası, bkz. `results/dt_error.png`). RK4 ile
   `dt ≤ 0,05` s'de bu hata ihmal edilebilir; yani 02–05'te asıl sınır 1–4. maddeler.

**Sonuç:** Bu model kontrolcüleri birbiriyle *karşılaştırmak* için yeterli, ama bir kontrolcünün gerçek
araçta *ne kadar iyi* çalışacağını söylemez. Simülasyondaki sapma rakamları alt sınır gibi okunmalı.
