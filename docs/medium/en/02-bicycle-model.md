# The bicycle model: the smallest simulator in autonomous driving

*Second post in the series. Code: [01-vehicle-model](https://github.com/zelihaguven/av-study/tree/main/01-vehicle-model)*

You don't need a real car to test a steering controller, but you do need a model that tells you how the car moves.
The most common model in the autonomous driving literature is surprisingly simple: the **kinematic bicycle model**,
which collapses four wheels into two. In this post I implement it and answer two questions: how accurate is it
numerically, and when does it get the physics wrong?

## Four equations

The vehicle's state is four numbers: the rear axle position `(x, y)`, the heading `ψ` and the speed `v`. The inputs
are the steering angle `δ` and the acceleration `a`. Assuming the tires roll without slipping, in the direction they
point:

```
ẋ = v cos ψ
ẏ = v sin ψ
ψ̇ = v / L · tan δ
v̇ = a
```

`L` is the wheelbase (2.7 m here). The third equation is the heart of it: hold the steering constant and the car
drives a circle of radius `R = L / tan δ`. At 10° of steering, that's 15.3 m.

I chose the rear axle as the reference point because Pure Pursuit, in the next post, uses that definition. With the
center of gravity as the reference, the equations would gain a slip angle term.

## Numerical accuracy: Euler vs. RK4

On a computer, these equations are advanced in small time steps. The simplest way is Euler: move `dt` along the
tangent at each step. A better one is RK4: sample the slope four times within the step and take a weighted average.

The test is simple: drive one full lap with constant steering and see how far you drift from the circle.

![One lap with constant steering](01-vehicle-model/results/en/circle.png)

| dt | Euler error | RK4 error |
|---|---|---|
| 0.001 s | 1.6e-4 | 1.6e-12 |
| 0.01 s | 1.6e-3 | 1.4e-13 |
| 0.1 s | 1.6e-2 | 7.9e-10 |

![Error vs. dt](01-vehicle-model/results/en/dt_error.png)

Euler's error falls linearly with `dt` (first order), and because the car moves along the tangent at every step, it
spirals outwards. RK4's error is fourth order; at `dt = 0.01` it hits the floating-point limit. One interesting
detail: RK4's error rises slightly again at `dt = 0.001`. That's not the method, it's rounding error accumulating
over ten times as many steps.

The practical takeaway: with RK4 and a reasonable `dt`, numerical error is negligible. From here on, the accuracy of
the simulation is set by the model itself, not by the integrator.

## When is the model wrong?

This isn't the most important part of the code, but it's the most important note. The kinematic model rests on a
single assumption: the tires don't slip. Wherever that assumption breaks, the model is wrong:

1. **Fast corners.** Real tires slip slightly to generate lateral force. As speed rises, the car turns wider than
   the model says; the model still says `R = L / tan δ`.
2. **Slippery roads.** The model has no notion of friction; it can't tell dry asphalt from ice.
3. **Steering isn't instantaneous.** Real steering has a delay. Autoware's MPC settings assume a 0.24 s delay and a
   0.27 s time constant. A controller that ignores this can look fine in simulation and oscillate on a real car.
4. **No weight transfer, slope or powertrain dynamics.** The car is a rigid rod sliding on flat ground.

Bottom line: this model is good enough to *compare* controllers with each other, but it can't tell you *how well* a
controller will work on a real car. Every number in the rest of this series should be read with that caveat; item 3
in particular directly affects a result in the last post.

## Next

The simulator is ready. In the next post I put two classical steering controllers on top of it and race them on the
same S-curve: Pure Pursuit and Stanley.

*This is a learning log; it is not an official part of Autoware.*
