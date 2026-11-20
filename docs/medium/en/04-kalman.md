# From noisy measurements to a reliable state: the Kalman filter and "knowing how much you don't know"

*Fourth post in the series. Code: [03-tracking](https://github.com/zelihaguven/av-study/tree/main/03-tracking)*

The output of a learned perception model jitters from frame to frame, and sometimes doesn't arrive at all. Feeding it
straight into the controller makes the steering jitter too. So a classical **tracking** layer sits between perception
and control. In this post I explain its simplest form, the linear Kalman filter, by tracking the distance to the
vehicle ahead: a distance measured at 20 Hz with 1 m of noise. The relative speed is never measured.

## Predict, then correct

The Kalman filter repeats two steps:

- **Predict:** "If it keeps a constant speed, where will it be in 0.05 s?" The state moves forward and the uncertainty
  (`P`) grows.
- **Update:** A measurement arrives. The filter blends the prediction and the measurement, weighting each by its
  uncertainty; the uncertainty shrinks.

![CIPO tracking](03-tracking/results/en/cipo.png)

Result: the raw measurement error is 0.94 m, the filter's is 0.42 m. More interesting is the bottom panel: the
relative speed, which is never measured, is estimated to within 0.77 m/s. The filter infers the speed from consecutive
distance measurements by itself.

## When measurements stop

Between 10 and 12 s in the plot there are no measurements for 2 seconds. During that time the filter only predicts:
the blue line is straight. The uncertainty band opens like a funnel: σ grows from 0.34 m to 1.89 m. At the end of the
gap the true error is 1.74 m, inside the band.

To me this is the filter's most important property: it doesn't just say "I don't know", it says correctly *how much*
it doesn't know. An ACC or AEB system can make decisions based on that σ: when the uncertainty gets too large, warn
the driver instead of braking.

## Q and R: whom do I trust?

The filter has two knobs: Q (how wrong the model can be) and R (how noisy the measurement is). What matters is
their ratio.

![q sweep](03-tracking/results/en/q_r_sweep.png)

| q / true q | Error with measurements | Speed error | Max error in gap |
|---|---|---|---|
| 0.01 | 1.62 m | 1.24 m/s | 10.1 m |
| **1** | **0.42 m** | **0.77 m/s** | **1.7 m** |
| 10,000 | 0.74 m | 8.90 m/s | 30.1 m |

If q is too small, the filter trusts the model too much and falls behind when the car accelerates. If q is too large,
the distance is almost as noisy as the raw measurement, but the real damage is somewhere you can't see: the speed
estimate comes from differences of noisy measurements, and during the gap the car is extrapolated with that wrong
speed for 2 s, so the error reaches 30 m. You pay for a bad setting mostly when there are no measurements.

## Consistency: NEES

How would you know the right q in a real system? A small error isn't enough; the filter's error should match the
uncertainty it reports. This is called **consistency**. A filter that says "my error is 1 cm" but is off by 40 cm is
dangerous.

NEES (`eᵀ P⁻¹ e`) normalizes the error by the filter's own uncertainty. If the filter is consistent, its average equals
the state dimension (2 here). Deliberately mis-tuning q:

![NEES and mis-tuned q](03-tracking/results/en/nees.png)

- q too small → NEES 77: **overconfident**. The filter is wrong but sure of itself. The most dangerous case.
- q too large → NEES drops to 1: **overcautious**. Safe but useless; σ is always large, so a system watching it
  switches the feature off for no reason.

That's why the NEES test is an **interval** check: [1.48, 2.59]. With only an upper bound, a filter with infinite q,
trusting nothing, would pass. The width of the interval comes from statistics: even the average of 50 runs is a random
number, and a correctly tuned filter doesn't give exactly 2.00 either (1.90 here).

## What does VisionPilot use?

Interestingly, not a Kalman filter. VisionPilot 1.0's tracking layer uses particle filters: a method that represents
the distribution with hundreds of samples, can carry non-Gaussian states, but is more expensive. The linear Kalman
filter still shows their common foundation, the predict-and-correct loop, in its clearest form.

Next: I put all the pieces together. Real VisionPilot models, the filter and the controller in one closed loop, and a
surprise: the filter doesn't do the job you'd expect.

*This is a learning log; it is not an official part of Autoware.*
