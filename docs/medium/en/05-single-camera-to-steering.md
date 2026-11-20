# From a single camera to steering: does the tracking layer do the job we think it does?

*Last post in the series. Code: [04-perception](https://github.com/zelihaguven/av-study/tree/main/04-perception),
[05-integration](https://github.com/zelihaguven/av-study/tree/main/05-integration)*

In the previous posts I wrote a vehicle model, two steering controllers and a Kalman filter. In this post I put them
together and do two things: run VisionPilot's real models on an open driving video and measure how noisy their output
is, then build a small closed loop with that noise. The result was not what I expected.

## 1. What do the real models say?

I ported the C++ pre- and post-processing of VisionPilot's three ONNX models (AutoSteer, AutoSpeed, AutoDrive) to
Python and ran them on a CPU. The test data are Udacity's MIT-licensed dashcam videos (2,943 frames): highway, an
underpass and a winding forest road. To get the models to speak in meters I had to calibrate the camera: the lateral
scale from the 3.7 m lane width, the longitudinal scale from the dashed lane markings, and the focal length from
chessboard images.

![AutoSteer on the highway](04-perception/results/overlay_1_otoyol.png)

AutoSteer outputs 64 path points per frame. They are projected onto the ground and fitted with a second-order
polynomial; the cross-track and heading errors the controller needs come from that polynomial.

**How much jitter?** I don't know the true cross-track error, but a human driver's drift within the lane is slow and
the model's jitter is fast. I counted what remains after a 1-second moving average as jitter:

| | Highway | Forest road |
|---|---|---|
| Cross-track jitter σ | 3 cm | 8.5 cm (4.8 cm excluding hairpin) |
| Heading jitter σ | 0.3° | 3.2° |
| Frame-to-frame correlation | 0.66 | 0.65 |

![Jitter](04-perception/results/en/noise.png)

On the highway the model is surprisingly stable. But there are two caveats. First, the errors aren't independent: if
one frame is off to the right, the next one probably is too. Second, the real failures aren't jitter:

![Polynomial on a hairpin](04-perception/results/failures/4_polinom_modeli.png)

On the forest road's hairpin turns, RANSAC fits a meaningless curve with a 2 m radius. My first guess was that the
`y = a x² + b x + c` polynomial can't represent a sharp turn; I tried a more flexible, parametric fit and it didn't
help. The real problem is that the model's points right in front of the hood form a hook, and both fits follow it.
The other failures are sun glare and overexposure. These errors last for seconds, and none of them is "Gaussian noise".

**Side finding:** while reading the code I found an inconsistency in AutoSpeed. The model already passes its class
scores through a sigmoid, and the C++ post-processing applies another one. As a result, the threshold written as 0.6
actually behaves like 0.405 in probability. I plan to look into this further and ask the project team.

## 2. The closed loop: what is the filter for?

The closed loop: vehicle model → synthetic perception (truth plus noise and dropouts) → Kalman filter →
Stanley-type control with curvature feedforward → vehicle. Same 50 m S-curve, 10 m/s.

![Closed loop](05-integration/results/en/closed_loop.png)

| 10% dropout | Error seen by the controller | Vehicle's true cross-track error | Steering rate |
|---|---|---|---|
| No filter | 29 cm | 13.7 cm | 130 °/s |
| With filter | 8 cm | 15.2 cm | 19 °/s |

First, to keep the promise from the third post: Stanley's steady-state offset in curves shows up here too, and
feedforward removes it. With noise-free perception and curvature feedforward off, the car drifts 58 cm to the outside
of the curve; with it on, the largest deviation is 3.5 cm. You can get 58 cm by hand: feedback only produces the 3.1°
of steering needed for a 50 m curve once it sees an error of `11 · tan 3.1° ≈ 0.59 m`.

![Feedforward on / off](05-integration/results/en/ff_ablation.png)

Now the real question: the filter. When I first saw the table above, I thought it was a tuning bug. The filter
reduces the error the controller sees by 3.5×, yet the vehicle's true cross-track error stays the same. I swept the
filter's parameters and turned the noise off entirely: the result didn't change.

The reason: **the vehicle itself is a low-pass filter.** The steering angle changes the lateral position through two
integrations. Fast, white noise jerks the wheel left and right every frame, but those jerks cancel out in the
position. The filter's remaining error, on the other hand, drifts slowly and goes straight onto the road.

So is the filter useless? No, it's essential in two places:

1. **Steering:** a 130 °/s command is uncomfortable and something a real steering actuator can't do. Because the
   model's steering is ideal (no delay), this difference doesn't show up in the simulated cross-track error. Adding
   Autoware's steering delay values (0.24 s + 0.27 s), however, makes this controller unstable with or without the
   filter: even without noise, the car deviates by 3.4 m. The fix is delay compensation: the controller predicts the
   state forward to the moment the command reaches the wheels and steers for that. That brings the error down from
   173 cm to 15 cm. One more lesson: the filter should also use the angle that actually reaches the wheels in its
   prediction step, not the command, otherwise compensation doesn't work with the filter.

   ![Steering delay](05-integration/results/en/actuator_delay.png)

2. **Long dropouts:** as perception loss increases, the gap widens.

![Dropout sweep](05-integration/results/en/dropout_sweep.png)

At 80% dropout, the median maximum deviation is 0.84 m with the filter and 4.6 m without. Without the filter, the
system holds the last measurement when nothing arrives and keeps correcting an old error while the car moves on; with
the filter, the state is carried forward using the steering input.

## 3. The structure of the noise

Adding the correlation I measured on the real model (ρ ≈ 0.6) to the synthetic perception changed the picture again:

![Noise structure](05-integration/results/en/noise_structure.png)

- **The same σ doubles the cross-track error.** σ alone doesn't tell you how good a perception model is; how long its
  errors last matters too.
- **The filter can't remove correlated noise.** A Kalman filter works by averaging successive measurements; if 20
  frames are wrong in the same direction, so is their average. At a correlation of 0.95, the filter's error equals
  the raw measurement's.
- **The dropout rate is misleading.** The same 30% loss is harmless if it's independent; in 1-second gaps it takes
  the car out of its lane. What matters is not the average but the longest gap.

## What I learned

- The tracking layer's job isn't "knowing the position more precisely", as I assumed; it's making the steering
  feasible and staying up when perception drops out.
- When evaluating a perception model, the structure of its jitter matters as much as its size: correlated errors and
  clustered dropouts erode the filter's advantage.
- Real failures (hairpins, glare) fall outside Gaussian models. On the hairpin I first blamed the post-processing, but
  the problem wasn't there: a more flexible fit didn't help; what was broken were the model's points in front of the
  hood. A lesson in testing a hypothesis on real data.

This toy system differs from VisionPilot in many ways: here perception outputs the cross-track error directly, the
controller doesn't look ahead, there's no longitudinal control and the timing is ideal. The full list of differences
is in the repo. But writing and measuring a system's layers one by one certainly teaches far more than looking at
architecture diagrams.

*This is a learning log; it is not an official part of Autoware.*
