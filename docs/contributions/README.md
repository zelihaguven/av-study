# Katkı taslakları

VisionPilot (`autowarefoundation/autoware.privately-owned-vehicles`) için hazırlanan issue/PR taslakları.
**Hiçbiri gönderilmedi;** göndermek kullanıcının kararı. Her taslağın sonunda bir "göndermeden önce" listesi var.

| Taslak | Tür | Güven | Özet |
|---|---|---|---|
| [`autospeed-double-sigmoid.md`](autospeed-double-sigmoid.md) | Issue | Yüksek (ONNX grafiği + ölçüm) | Etkin eşik 0,6 değil 0,405; öneri anlamı düzeltmek, davranışı korumak |
| [`planning-dt-mismatch.md`](planning-dt-mismatch.md) | Issue / soru | Orta (kod okuması, ölçüm yok) | `dt = 0.05` döngü periyoduyla uyuşmuyor; eğrilik türevi 10 Hz'de 2× |
| [`stale-comments-pr.md`](stale-comments-pr.md) | PR (yalnız yorum) | Yüksek | Kodla uyuşmayan 6 yorum |

Önerilen sıra: önce yorum PR'ı (küçük, tartışmasız, projeyi tanımak için), sonra AutoSpeed issue'su, en son dt sorusu
(önce PoV WG Discussions'ta sormak daha uygun olabilir).
