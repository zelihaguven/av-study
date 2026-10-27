# common — Ortak Araçlar

`02`, `03` ve `05` modüllerinin kullandığı referans yollar ve metrikler.
`01`'den sonra, `02`'den önce yazılır.

| Dosya | İçerik |
|---|---|
| `paths.py` | `RefPath` veri yapısı; `straight`, `circle_arc`, `s_curve` üreticileri; en yakın nokta ve **işaretli** yanal hata (CTE) |
| `metrics.py` | `rms`, `max_abs` |

**İşaret kuralı:** Yolun ilerleme yönüne göre aracın **solu pozitif** CTE.
Bu kurala her yerde uy; 02'deki Stanley ve 05'teki ölçüm modeli buna dayanır.

## Kabul kriteri

- [ ] `pytest common` yeşil
