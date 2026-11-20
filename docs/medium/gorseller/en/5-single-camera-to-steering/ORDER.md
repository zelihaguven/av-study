# From a single camera to steering: image order

| # | File | What it shows | Place it after |
|---|---|---|---|
| 00 | `00_cover.png` | Cover | Story header (top of the post) |
| 01 | `01_overlay_1_otoyol.png` | AutoSteer on the highway | “1. What do the real models say?” section, after the paragraph starting “I ported the C++ pre- and post-processing of VisionPilot's …” |
| 02 | `02_table_1.png` | Table: Highway / Forest road | “1. What do the real models say?” section, after the paragraph starting “How much jitter? I don't know the true cross-track …” |
| 03 | `03_noise.png` | Jitter | Right below the previous one (02) |
| 04 | `04_4_polinom_modeli.png` | Polynomial on a hairpin | “1. What do the real models say?” section, after the paragraph starting “On the highway the model is surprisingly stable. But …” |
| 05 | `05_closed_loop.png` | Closed loop | “2. The closed loop: what is the filter for?” section, after the paragraph starting “The closed loop: vehicle model → synthetic perception (truth …” |
| 06 | `06_table_2.png` | Table: 10% dropout / Error seen by the controller / Vehicle's true cross-track error / Steering rate | Right below the previous one (05) |
| 07 | `07_ff_ablation.png` | Feedforward on / off | “2. The closed loop: what is the filter for?” section, after the paragraph starting “First, to keep the promise from the third post: …” |
| 08 | `08_actuator_delay.png` | Steering delay | “2. The closed loop: what is the filter for?” section, after the paragraph starting “1. Steering: a 130 °/s command is uncomfortable and …” |
| 09 | `09_dropout_sweep.png` | Dropout sweep | “2. The closed loop: what is the filter for?” section, after the paragraph starting “2. Long dropouts: as perception loss increases, the gap …” |
| 10 | `10_noise_structure.png` | Noise structure | “3. The structure of the noise” section, after the paragraph starting “Adding the correlation I measured on the real model …” |
