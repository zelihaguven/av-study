# common — Ortak Araçlar

`02`, `03` ve `05` modüllerinin kullandığı referans yollar ve metrikler.
`01`'den sonra, `02`'den önce yazılır.

| Dosya | İçerik |
|---|---|
| `paths.py` | `RefPath` veri yapısı; `straight`, `circle_arc`, `s_curve` üreticileri; en yakın nokta ve **işaretli** yanal hata (CTE) |
| `metrics.py` | `rms`, `max_abs` |

**İşaret kuralı:** Yolun ilerleme yönüne göre aracın **solu pozitif** CTE.
Bu kurala her yerde uy; 02'deki Stanley ve 05'teki ölçüm modeli buna dayanır.

**Yol üretimi:** Her yol bir eğrilik profili `κ(s)` olarak tanımlanır, `yaw = ∫κ ds` ve
`(x, y) = ∫(cos yaw, sin yaw) ds` ile entegre edilir. Her `ds` parçasında eğrilik sabit kabul
edildiği için parça kesin bir yay olarak eklenir (kiriş = `2 sin(Δψ/2) / κ`). Böylece çember
üzerinde birikmiş hata oluşmaz. Yeni bir yol eklemek = yeni bir `κ(s)` yazmak.

## Kabul kriteri

- [x] `pytest common` yeşil
