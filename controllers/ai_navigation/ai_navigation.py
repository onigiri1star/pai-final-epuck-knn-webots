"""Webots E-puck autonomous simulation: k-NN decisions + goal navigation.

Uses Webots Supervisor state to obtain perfect position and orientation. This
privileged localization is suitable for this simulation; a physical robot would
require a localization sensor/algorithm. No actual robot is required.
"""
import math
from pathlib import Path
from controller import Supervisor
from learned_policy import KNNPolicy, LABELS

MAX_SPEED = 6.28
GOAL = (0.76, 0.40)
# Simple waypoint route to make the first demo repeatable.
# Waypoints are given by the programmer; this is NOT AI-based global planning.
WAYPOINTS = [
    (-0.43, -0.43),
    (0.12, -0.47),
    (0.69, -0.12),
    (0.12, -0.47),
    (-0.43, -0.43),
    (-0.80, -0.34),
    (-0.43, -0.43),
    (0.12, -0.47),
    (0.69, -0.12),
    GOAL,
]
GOAL_RADIUS = 0.11
WAYPOINT_RADIUS = 0.13
MAX_SIM_SECONDS = 180
MODEL_PATH = Path(__file__).with_name('training_data.json')


def angle_difference(target, current):
    return (target - current + math.pi) % (2 * math.pi) - math.pi


def clamp(v, low, high):
    return max(low, min(high, v))


robot = Supervisor()
timestep = int(robot.getBasicTimeStep())
self_node = robot.getSelf()
model = KNNPolicy.from_json(MODEL_PATH)
sensors = [robot.getDevice(f'ps{i}') for i in range(8)]
for sensor in sensors:
    sensor.enable(timestep)

left_motor = robot.getDevice('left wheel motor')
right_motor = robot.getDevice('right wheel motor')
left_motor.setPosition(float('inf'))
right_motor.setPosition(float('inf'))
left_motor.setVelocity(0.0)
right_motor.setVelocity(0.0)

print('[PAI] AI robot started: supervised k-NN, synthetic labeled examples.')
print(f'[PAI] Goal: ({GOAL[0]:.2f}, {GOAL[1]:.2f}), radius {GOAL_RADIUS:.2f} m')
print('[PAI] Position/heading are read using Webots Supervisor (simulation-only localization).')
print('[PAI] Global waypoints are hand-designed; the local steering policy is learned (k-NN).')

avoid_action = None
avoid_ticks = 0
last_print_step = -1
step_count = 0
waypoint_index = 0

while robot.step(timestep) != -1:
    step_count += 1
    pose = self_node.getPosition()
    x, y = pose[0], pose[1]
    orientation = self_node.getOrientation()
    # E-puck faces local +X; the first column of this rotation matrix is its
    # forward axis expressed in world coordinates (Webots uses Z-up).
    heading = math.atan2(orientation[3], orientation[0])
    distance_to_goal = math.hypot(GOAL[0] - x, GOAL[1] - y)
    # Progress through manually specified safe corridor waypoints.
    waypoint = WAYPOINTS[waypoint_index]
    if waypoint_index < len(WAYPOINTS) - 1 and math.hypot(waypoint[0] - x, waypoint[1] - y) < WAYPOINT_RADIUS:
        waypoint_index += 1
        waypoint = WAYPOINTS[waypoint_index]
        print(f'[PAI] Waypoint {waypoint_index}/{len(WAYPOINTS) - 1} reached')

    if distance_to_goal < GOAL_RADIUS and waypoint_index == len(WAYPOINTS) - 1:
        left_motor.setVelocity(0.0)
        right_motor.setVelocity(0.0)
        print(f'[PAI] SUCCESS! Goal reached at t={robot.getTime():.1f}s')
        print(f'[PAI] Final position ({x:.3f},{y:.3f}); distance {distance_to_goal:.3f}m')
        break

    if robot.getTime() >= MAX_SIM_SECONDS:
        left_motor.setVelocity(0.0)
        right_motor.setVelocity(0.0)
        print(f'[PAI] TIMEOUT at 180s, distance from goal = {distance_to_goal:.3f}m')
        print('[PAI] Change obstacle positions or tune turn durations; do not claim success.')
        break

    raw = [s.getValue() for s in sensors]
    front_right = max(raw[0], raw[1], raw[2])
    front_left = max(raw[5], raw[6], raw[7])
    goal_direction = math.atan2(waypoint[1] - y, waypoint[0] - x)
    bearing = angle_difference(goal_direction, heading) / math.pi

    # Correct the E-puck sensor idle baseline.
    sensor_idle = 75.0
    features = [
        clamp((front_right - sensor_idle) / 325.0, 0.0, 1.0),
        clamp((front_left - sensor_idle) / 325.0, 0.0, 1.0),
        clamp(bearing, -1, 1)
    ]
    action = model.predict(features)

    # Maintain a short avoidance turn after a close obstacle. This prevents
    # reactive stop/go oscillations and acts as a safety state machine around AI.
    strong_obstacle = max(front_right, front_left) > 100.0
    if strong_obstacle and avoid_ticks == 0:
        avoid_action = action if action != 0 else (1 if front_right >= front_left else 2)
        avoid_ticks = max(1, round(0.65 * 1000 / timestep))
    if avoid_ticks > 0:
        action = avoid_action
        avoid_ticks -= 1

    # Speeds are radians per second; never exceed the e-puck wheel motor cap.
    if action == 0:            # forward
        left_speed, right_speed = 4.1, 4.1
    elif action == 1:          # counterclockwise / left
        left_speed, right_speed = -2.4, 2.4
    else:                     # clockwise / right
        left_speed, right_speed = 2.4, -2.4

    left_motor.setVelocity(clamp(left_speed, -MAX_SPEED, MAX_SPEED))
    right_motor.setVelocity(clamp(right_speed, -MAX_SPEED, MAX_SPEED))

    # Roughly once per 3 seconds print evidence for the demo and report.
    if last_print_step < 0 or step_count - last_print_step >= max(1, round(3000/timestep)):
        print(f'[PAI] t={robot.getTime():5.1f}s pos=({x:+.2f},{y:+.2f}) '
              f'goal_distance={distance_to_goal:.2f}m AI={LABELS[action]} '
              f'IR=({front_right:.0f},{front_left:.0f})')
        last_print_step = step_count
