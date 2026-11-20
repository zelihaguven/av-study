# Why do Pure Pursuit and Stanley behave differently on the same curve?

*Third post in the series. Code: [02-control](https://github.com/zelihaguven/av-study/tree/main/02-control)*

In the previous post I wrote a vehicle simulator. Now, who turns the wheel? In this post I compare the two best-known
geometric lateral controllers on the same road: **Pure Pursuit** and **Stanley**. The road is a deliberately hard
S-curve: 20 m straight, a 90° left turn with a 50 m radius, immediately followed by a 90° right turn, then straight
again. The curvature jumps twice. The car drives at 10 m/s.

## Two ideas

**Pure Pursuit:** pick a point `Ld` meters ahead on the path and connect the rear axle to it with an arc tangent to
the car's heading. The steering angle comes from that arc's curvature: `δ = atan(2L sin α / Ld)`. It's like a driver
"looking ahead".

**Stanley:** look at the front axle. How far off is your heading relative to the path, and how far are you from it?
`δ = heading error + atan(k · e / (k_soft + v))`. It doesn't look ahead; it only reacts to the current error.

## Results

| | RMS deviation | Max deviation | Max steering rate |
|---|---|---|---|
| Pure Pursuit (Ld = 5 m) | 2.2 cm | 10.3 cm | 8 °/s |
| Stanley (k = 1) | 6.3 cm | 7.3 cm | 22 °/s |

![Cross-track error and steering rate](02-control/results/en/s_curve_cte.png)

Both stay on the road, but their error profiles are completely different. The plot shows three things.

**1. Pure Pursuit is error-free mid-curve and cuts the corner at transitions.** Textbooks say "Pure Pursuit cuts
corners". My result is more nuanced: in the middle of a constant-curvature arc, the lookahead point lies on the same
circle, so the arc Pure Pursuit draws *is* the path and the error is zero. Corner cutting happens where the curvature
changes. When the lookahead point enters the new curve, the car is still on the straight and starts turning early.
The error starts rising about `Ld / v = 0.5 s` before the transition.

**2. Stanley reacts late but sharply.** Because it doesn't look ahead, it only notices the curvature change when the
front axle gets there, and the steering rate spikes (22 °/s).

**3. Stanley leaves a steady-state offset in the curve.** About 7 cm inside the curve. The reason: it doesn't know the
road's curvature, so it needs a non-zero error to keep the wheel turned. The fix is a curvature feedforward term
(`δ += atan(L · κ)`); I measure its effect in the last post.

## Lookahead distance: accuracy or smoothness?

![Ld sweep](02-control/results/en/lookahead_sweep.png)

Pure Pursuit has one knob, `Ld`. As the left panel shows, the error grows roughly quadratically with `Ld`: 0.2 cm at
2 m, 34 cm at 15 m. But as `Ld` shrinks, steering gets harsher: 20 °/s at 2 m, 3.7 °/s at 15 m.

The right panel surprised me. The classic advice is to scale lookahead with speed: `Ld = k · v`. In this experiment,
the scaled `Ld` **didn't improve tracking, it made it worse**: at 20 m/s, a fixed 5 m gives 2 cm, the scaled one
(10 m) gives 12 cm. What scaling buys is something else: recovering from a 1 m offset on a straight road at 20 m/s,
the steering rate is 12 °/s instead of 118 °/s. The same steering angle means much more lateral acceleration at high
speed; scaling keeps the lookahead *time* constant and stops the controller from getting harsher as speed rises.

It's worth noting that the simulation flatters the fixed `Ld` here: the model has no steering delay. A controller
asking for 118 °/s would oscillate on a real car with delay.

## Why is Stanley harsh at low speed?

![Stanley softening term](02-control/results/en/stanley_soft.png)

Stanley's cross-track term has speed in the denominator. As speed approaches zero, the gain goes to infinity and even
a small error slams the wheel to its limit. `k_soft` caps that gain: at 2 m/s, the initial steering is 25.5° with
`k_soft = 0.1` and 8.1° with `k_soft = 5`. The price is slower recovery (12.2 s instead of 5.7 s). At high speed the
effect disappears; it's a knob that only matters for parking and pulling away.

## A small debugging story

The first version of Stanley had meaningless spikes in the steering rate in the middle of the curve. The cause wasn't
physical: the path was defined by points 0.1 m apart and the car moved 0.2 m per step. Occasionally it skipped three
points, and the path heading changed in steps. Interpolating the heading at the projection point, instead of reading
it from the nearest point, fixed it. In a real system too, the resolution of the path shows up in the control output.

## Summary

Pure Pursuit looks ahead, so it's smooth and accurate in curves, but turns early when the curvature changes. Stanley
looks at the instantaneous error; without feedforward it leaves a steady-state offset in curves. VisionPilot's lateral
control is different from both: an MPC looking 10 m ahead, so it both sees ahead and carries the curvature in its model.

Next: what happens when the measurement going into the controller is noisy? The Kalman filter.

*This is a learning log; it is not an official part of Autoware.*
