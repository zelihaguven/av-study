# How many pieces make up an autonomous vehicle's software? A modular stack vs. a single-camera L2 system

*First post in a series on learning autonomous driving software from scratch. Code and diagrams:
[github.com/zelihaguven/av-study](https://github.com/zelihaguven/av-study/tree/main/00-architecture)*

When people think of self-driving, they often picture a single "AI". Open-source codebases tell a different story:
the vehicle runs a pipeline of modules, each answering one question. In this post I compare two architectures:
Autoware's full modular stack, and VisionPilot, a single-camera L2 system from the same ecosystem. I drew both from
the source code and documentation, and marked what I couldn't find with a "?".

## The modular stack: six questions, six modules

In Autoware, data flows like this:

- **Sensing:** "What do the sensors see?" Camera images, LiDAR points, GNSS, IMU.
- **Localization:** "Where am I on the map?" Output: the vehicle's pose, velocity and uncertainty, at 50 Hz or more.
- **Perception:** "What is around me, and where is it going?" Predicted objects, traffic lights; the tracker runs at 10 Hz.
- **Planning:** "Which way should I go?" A trajectory.
- **Control:** "How much should I steer to follow that trajectory?" About 33 Hz.
- **Vehicle interface:** Sends the command to the vehicle and reads its status back.

![Autoware data flow](docs/medium/img/en/autoware_architecture.png)

Two things surprised me while drawing this. First, the arrows are not as one-directional as you might expect:
localization feeds perception (you need to know where you are before you can place objects on the map), and planning
sends the route back to perception. Second, rates increase towards the bottom of the stack: perception runs at 10 Hz,
control at 33 Hz. A plan covers a few seconds ahead, so it doesn't need recomputing every cycle; control, on the other
hand, has to correct small disturbances like wind or road slope quickly.

Every module also has an answer to "what happens if this fails?". If control stops receiving commands often enough,
the vehicle performs an emergency stop; if a sensor fails, planning switches to a minimal risk maneuver (MRM):
emergency stop, comfortable stop or pull over. These tables show how much of the architecture is about "what to do
when something breaks" rather than normal driving.

## VisionPilot: one camera, three models, classical fusion

VisionPilot's goal is much narrower: L2 driver assistance features (ACC, AEB, LKAS, LDW) from a single front camera.
No HD map, no LiDAR. The README doesn't map models to features, so I traced the flow through the source code:

1. **Camera** → two separate preprocessing steps: crop and resize, and a homography warp into a different perspective.
2. **Three models in parallel:**
   - *AutoSteer*: 64 points of the ego path (where am I going?)
   - *AutoSpeed*: object boxes, with the closest in-path object (CIPO) as a class
   - *AutoDrive*: end-to-end CIPO distance and road curvature from two frames
3. **Fusion:** particle filters, not Kalman filters. A polynomial is fitted to the path points with RANSAC.
4. **Planning/control:** IDM longitudinally (speed relative to the lead vehicle), MPC laterally (an optimizer looking 10 m ahead).
5. **Warnings:** fixed thresholds for FCW, AEB and LDW.

![VisionPilot data flow](docs/medium/img/en/visionpilot_architecture.png)

There were surprises here too. The EgoLanes model, which earlier descriptions of VisionPilot mention, is no longer
used in the 1.0 application. I also found a small inconsistency in the code: a comment says "50 Hz control period",
but the value is `dt = 0.05`, which is 20 Hz. This is exactly the value of drawing an architecture from the code:
you see where the documentation and the code disagree.

## End-to-end or modular?

VisionPilot describes itself as "hybrid", and I think that's accurate: learned models do the perception, but their
outputs are interpretable intermediate quantities (path points, distance, curvature). Classical filters and
controllers come after. In a fully end-to-end model, everything from camera to steering would be hidden inside one
network, and telling whether an error came from perception or control would be much harder. With a hybrid design,
as the following posts show, each layer can be tested and measured on its own.

The biggest difference between the two architectures is responsibility. VisionPilot is an L2 system: under SAE J3016,
monitoring the drive and taking over when needed is the driver's job. That is why the architecture has no redundant
sensors or pull-over maneuver; when uncertainty grows, the feature switches off and hands over to the driver. At L4
the fallback moves to the system, and the modular stack's MRM, redundant sensors and continuous fault monitoring
become mandatory.

## Next

In the rest of this series I build a small copy of VisionPilot in Python, step by step: first the vehicle itself
(the bicycle model), then steering control, then the filter that cleans up noisy perception, and finally a closed
loop driven by the real models' outputs.

*This is a learning log; it is not an official part of Autoware.*
