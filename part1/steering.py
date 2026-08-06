# ============================================================================
# steering.py
# Purpose
#   Implement all steering behaviours here. Each function computes a steering
#   force vector. Entities apply that force to their velocity each frame.
# Key idea
#   desired_velocity minus current_velocity gives the steering force.
#   Use dt in update loops when integrating velocity to keep motion consistent.
# ============================================================================

import math
from pygame.math import Vector2 as V2
from utils import limit, clamp, circlecast_hits_any_rect, nearest_point_on_rect
from settings import (
    ARRIVE_SLOW_RADIUS, ARRIVE_STOP_DAMPING, ARRIVE_STOP_RADIUS, ARRIVE_STOP_SNAP,
    AVOID_LOOKAHEAD, AVOID_ANGLE_INCREMENT, AVOID_MAX_ANGLE,
    ALI_STRENGTH, COH_DEAD_ZONE_RADIUS, COH_SLOW_ZONE_RADIUS,
    SNAKE_AVOID_RETREAT_RADIUS_MULT, STEER_MAX_FORCE
)

# ---------------- Base behaviours ----------------

def seek(pos, vel, target, max_speed):
    """
    Move toward a target. Returns a steering force.
    desired = direction_to_target * max_speed
    steering = desired - current_velocity
    """
    d = target - pos
    if d.length_squared() == 0:
        return V2()
    desired = d.normalize() * max_speed
    return desired - vel

def flee(pos, vel, target, max_speed):
    """
    Move away from a target. This is the opposite of seek.
    You need to implement the mirror of seek using direction from threat to self.
    """
    d = pos - target
    if d.length_squared() == 0:
        return V2()
    desired = d.normalize() * max_speed
    return desired - vel


def _braking_speed(dist, slow_radius, max_speed):
    """
    Kinematically-exact deceleration curve.

    We want a speed profile v(d) such that, under a constant maximum
    deceleration a_max, the agent reaches v = 0 at EXACTLY d = 0 with no
    residual creep and no overshoot. The physics for constant-deceleration
    braking gives:

        v(d) = sqrt(2 * a_max * d)

    We choose a_max so the curve is C0-continuous with the "cruise" branch
    (desired_vel = direction * max_speed) at d = slow_radius, i.e.
    v(slow_radius) = max_speed:

        max_speed = sqrt(2 * a_max * slow_radius)
        => a_max = max_speed^2 / (2 * slow_radius)

    Substituting back:

        v(d) = max_speed * sqrt(d / slow_radius)

    This is a strictly increasing, continuous function of d that starts at 0
    at the target and reaches max_speed exactly at the slow_radius boundary,
    with no seam/discontinuity and no tunable magic constant beyond the two
    radii that already define the behaviour.
    """
    t = clamp(dist / slow_radius, 0.0, 1.0)
    return max_speed * math.sqrt(t)


def _cancel_tangential(vel, direction, strength):
    """
    Orthogonal velocity cancellation via vector projection/rejection.

    Decompose vel into:
      radial_speed = vel . direction                (component along target dir)
      tangential   = vel - direction * radial_speed  (orthogonal rejection)

    Subtracting `tangential * strength` actively counters sideways drift
    instead of just letting the reduced-speed cruise vector "out-argue" it
    over distance/time. strength in [0, 1]; 1.0 fully removes the sideways
    component in a single step (subject to the max-force clamp applied later
    during integration), preventing the wide orbiting arcs around a target.
    """
    radial_speed = vel.dot(direction)
    tangential = vel - direction * radial_speed
    return -tangential * strength


def arrive(pos, vel, target, max_speed, slow_radius=ARRIVE_SLOW_RADIUS, stop_radius=ARRIVE_STOP_RADIUS):
    """
    Like seek when far, but slow down near the target using a kinematically
    exact braking curve (see _braking_speed), and actively cancels sideways
    (tangential) velocity while inside the slow zone so a fast approach from
    an angle settles in a straight line instead of arcing/orbiting.
    """
    d = target - pos
    dist = d.length()

    if dist < stop_radius:
        return -vel  # Cancel velocity to stop

    direction = d.normalize()

    if dist < slow_radius:
        desired_speed = _braking_speed(dist, slow_radius, max_speed)
        desired_vel = direction * desired_speed

        # Damp harder (cancel more of the sideways component) the closer we get,
        # so cornering tightens up right at the end instead of orbiting.
        t = dist / slow_radius
        cancel_strength = clamp(1.0 - t * 0.4, 0.6, 1.0)
        desired_vel += _cancel_tangential(vel, direction, cancel_strength)
    else:
        desired_vel = direction * max_speed

    return desired_vel - vel

def apply_arrive_stop(
    pos,
    vel,
    target,
    dt,
    stop_radius=ARRIVE_STOP_RADIUS,
    damping=ARRIVE_STOP_DAMPING,
    snap=ARRIVE_STOP_SNAP,
):
    """
    Apply the final convergence after velocity integration.

    Uses exact exponential decay exp(-damping * dt) rather than the linear
    approximation (1 - damping * dt). The linear form can overshoot into
    negative scale (and thus flip velocity direction) if dt * damping > 1 on
    a slow frame; the exponential form is bounded in (0, 1] for any dt >= 0,
    so it stays frame-rate independent even under frame-time spikes.
    """

    if (target - pos).length() < stop_radius:
        vel *= math.exp(-damping * dt)

        if vel.length() < snap:
            vel = V2()

    return vel

def integrate_velocity(vel, force, dt, max_speed):
    """
    Apply a steering force to velocity using Euler integration.
    Then clamp to max speed and return the new velocity.
    Use this inside agent update methods after computing steering forces.
    """
    vel += limit(force, STEER_MAX_FORCE) * dt
    if vel.length() > max_speed:
        vel.scale_to_length(max_speed)
    return vel

# ---------------- Boids components ----------------

def boids_separation(me_pos, me_vel, neighbors, sep_radius, max_speed):
    """
    Push away from neighbors that are too close.
    """
    steering = V2()
    count = 0
    for n_pos, n_vel in neighbors:
        d = me_pos - n_pos
        dist = d.length()
        if 0 < dist < sep_radius:
            # Scale the repulsion so closer neighbors push harder
            steering += d.normalize() * (sep_radius / dist)
            count += 1
            
    if count > 0:
        steering /= count
        # Calculate standard steering force
        steering = steering.normalize() * max_speed
        return steering - me_vel
        
    return V2()

def boids_cohesion(me_pos, me_vel, neighbors, max_speed, dead_zone_radius=COH_DEAD_ZONE_RADIUS, slow_zone_radius=COH_SLOW_ZONE_RADIUS):
    """
    Pull toward the center of mass of neighbors.
    """
    if not neighbors:
        return V2()
        
    avg_pos = V2()
    for n_pos, n_vel in neighbors:
        avg_pos += n_pos
    avg_pos /= len(neighbors)

    target_vec = avg_pos - me_pos
    dist = target_vec.length()

    # Cancel out velocity if perfectly centered
    if dist < dead_zone_radius:
        return -me_vel * 0.5 
        
    # Scale desired speed similar to Arrive behavior
    if dist < slow_zone_radius:
        desired_speed = max_speed * (dist / slow_zone_radius)
    else:
        desired_speed = max_speed
        
    desired_vel = target_vec.normalize() * desired_speed
    return desired_vel - me_vel

def boids_alignment(me_vel, neighbors, max_speed):
    """
    Match the average velocity of neighbors.
    """
    if not neighbors:
        return V2()
        
    avg_vel = V2()
    for n_pos, n_vel in neighbors:
        avg_vel += n_vel
    avg_vel /= len(neighbors)

    if avg_vel.length_squared() == 0:
        return V2()

    # The average velocity direction is our desired direction
    desired_vel = avg_vel.normalize() * max_speed
    return desired_vel - me_vel

# ---------------- Obstacle avoidance blend ----------------

def seek_with_avoid(pos, vel, target, max_speed, radius, rects, preferred_angle=0.0):
    """
    Move towards a target, but sweep a path ahead using circle casts.
    If the direct path is blocked, try looking left and right at increasing angles
    until a clear path is found.

    Contract: this function ALWAYS commands full max_speed along whatever
    direction it returns (never a slowed-down speed). Deceleration is the
    exclusive responsibility of the Arrive layer above it, and only once
    this function reports a clear line of sight (angle == 0.0).
    """
    d = target - pos
    if d.length_squared() == 0:
        return (V2(0, 0), 0.0)
        
    base_dir = d.normalize()
    look_ahead = AVOID_LOOKAHEAD  # how far ahead the snake scans
    
    # Angles to test: straight ahead (0) first, then sweep outward on both sides
    angles_to_check = [0]
    angle = AVOID_ANGLE_INCREMENT
    while angle <= AVOID_MAX_ANGLE:
        angles_to_check.extend([-angle, angle])
        angle += AVOID_ANGLE_INCREMENT
        
    if preferred_angle != 0.0 and preferred_angle in angles_to_check:
        angles_to_check.remove(preferred_angle)
        angles_to_check.insert(1, preferred_angle)  # right after 0, not before it
    
    for angle in angles_to_check:
        # Rotate the base direction to get the candidate heading
        check_dir = base_dir.rotate(angle)
        
        # Sweep endpoint for the circle cast
        p1 = pos + check_dir * look_ahead
        
        # Circle-cast (swept-circle test) against every obstacle rect
        hit_wall = circlecast_hits_any_rect(pos, p1, radius, rects)
        
        if not hit_wall:
            # Clear corridor found - always commit at full speed
            desired = check_dir * max_speed
            return (desired - vel, angle)
            
    # Every tested angle is still blocked: don't ram forward, back away from the
    # nearest obstacle so the snake repositions and gets a fresh angle next frame.
    nearest_obstacle_point = None
    nearest_dist = float('inf')
    for r in rects:
        np = nearest_point_on_rect(pos, r)
        d = (pos - np).length()
        if d < nearest_dist:
            nearest_dist = d
            nearest_obstacle_point = np

    if nearest_obstacle_point is not None and nearest_dist < radius * SNAKE_AVOID_RETREAT_RADIUS_MULT:
        away = pos - nearest_obstacle_point
        retreat_dir = away.normalize() if away.length_squared() > 0 else -base_dir
        desired = retreat_dir * max_speed * 0.6
    else:
        # Not actually touching anything nearby — safe to creep forward slowly and re-try
        desired = base_dir * max_speed * 0.4

    return (desired - vel, 0.0)

def arrive_with_avoid(pos, vel, target, max_speed, radius, rects, preferred_angle=0.0,
                       slow_radius=ARRIVE_SLOW_RADIUS, stop_radius=ARRIVE_STOP_RADIUS):
    """
    Unified Arrive + obstacle avoidance, for Patrol-style states.

    The old Patrol code called arrive(target) and seek_with_avoid(target)
    separately and ADDED the two resulting forces together — two complete,
    independently-computed steering forces that can point in different
    directions near an obstacle, which is what caused the rattling near
    trees. This function instead picks ONE direction — whatever
    seek_with_avoid decides on (straight at the target if clear, or a
    corridor-adjusted direction if something is in the way) — and applies
    Arrive's slow/stop-radius speed profile to that single direction, the
    same way Aggro lets seek_with_avoid have full authority over direction
    rather than fighting it with a separately-aimed force.

    Returns (force, angle) — same shape as seek_with_avoid, so callers can
    keep passing the returned angle back in as preferred_angle next frame.
    """
    d = target - pos
    dist = d.length()

    if dist < stop_radius:
        return -vel, preferred_angle  # same "cancel velocity" rule as arrive()

    avoid_force, angle = seek_with_avoid(pos, vel, target, max_speed, radius, rects,
                                          preferred_angle=preferred_angle)
    # seek_with_avoid returned avoid_force = desired_velocity - vel, so add
    # vel back to recover the DIRECTION it picked internally — we want to
    # reuse that direction, just re-scale its SPEED using Arrive's taper.
    desired_dir_vel = avoid_force + vel
    direction = desired_dir_vel.normalize() if desired_dir_vel.length_squared() > 0 else d.normalize()

    if dist < slow_radius:
        desired_speed = max_speed * (dist / slow_radius)
    else:
        desired_speed = max_speed

    desired_vel = direction * desired_speed
    return desired_vel - vel, angle

# ---------------- New behaviours to be implemented ----------------

def predict_future_position(pos, target_pos, target_vel, max_speed):
    """
    Shared prediction helper used by pursue(), evade(), and Aggro's unified
    seek_with_avoid call.
    Uses the combined closing speed (pursuer + target) to estimate a more
    accurate interception time_horizon than using either speed alone.
    """
    distance = (target_pos - pos).length()
    target_speed = target_vel.length()
    
    # Target is effectively stationary - no need to predict ahead
    if target_speed < 5.0:
        return target_pos
        
    # Combined closing speed gives a more realistic time-to-intercept
    closing_speed = max_speed + target_speed
    
    # Cap the horizon so long-range chases don't extrapolate too far ahead
    time_horizon = min(distance / closing_speed, 1.5)
    
    return target_pos + target_vel * time_horizon

def pursue(pos, vel, target_pos, target_vel, max_speed):
    """
    Predict the future position of the target then seek that point.
    Suggested
      distance = |target_pos - pos|
      time_horizon = distance / (max_speed + small_eps)
      predicted    = target_pos + target_vel * time_horizon
      return seek toward predicted
    Replace simple seek in Snake Aggro with pursue for better interception.
    """
    predicted = predict_future_position(pos, target_pos, target_vel, max_speed)
    return seek(pos, vel, predicted, max_speed)

def evade(pos, vel, threat_pos, threat_vel, max_speed, predict_speed=None):
    """
    Predict the future position of a threat then flee from that point.
    This is the inverse of pursue. Use the same prediction idea.

    predict_speed: speed used to scale the prediction time horizon
    (time_horizon = distance / predict_speed). Defaults to max_speed (the
    evader's own speed) for backward compatibility — but when the evader is
    much SLOWER than the threat (a fly evading the faster frog), that
    default inflates the time horizon and can push the predicted point past
    the evader's own position, flipping the flee direction so the evader
    briefly steers TOWARD the threat instead of away from it. Pass the
    threat's own speed here (e.g. FROG_SPEED) to fix that.
    """
    if predict_speed is None:
        predict_speed = max_speed
    predicted = predict_future_position(pos, threat_pos, threat_vel, predict_speed)
    return flee(pos, vel, predicted, max_speed)

import random
def wander_force(me_vel, jitter_deg=8.0, circle_distance=24.0, circle_radius=18.0,
                  rng_seed=None, smoothing=0.85):
    """
    Return a small random steering vector for gentle drift.
    Classic wander: project a small circle ahead along current heading,
    then jitter the target point on that circle by a tiny random angle
    each update.

    smoothing (0-1): exponential low-pass filter applied to the OUTPUT
    force, not the underlying angle random-walk. 0 = no smoothing (raw
    circle-wander output, can look twitchy at 60 FPS). Closer to 1 = each
    frame's force is mostly last frame's force with a small nudge, which
    is what actually removes the "steering noise" look without needing to
    swap in Perlin/OU noise — the circle-wander angle is already a random
    walk (smooth), the twitchiness was coming from applying its full
    output un-damped every frame.
    """
    if not hasattr(wander_force, "_state"):
        wander_force._state = {}

    if rng_seed not in wander_force._state:
        rng = random.Random(rng_seed) if rng_seed is not None else random.Random()
        wander_force._state[rng_seed] = {
            'angle': rng.uniform(0, 360),
            'rng': rng,
            'smoothed_force': V2(0, 0),
        }

    state = wander_force._state[rng_seed]
    rng = state['rng']

    # Jitter the angle (unchanged — this part was already correct)
    state['angle'] += rng.uniform(-jitter_deg, jitter_deg)

    if me_vel.length_squared() == 0:
        heading = V2(1, 0)
    else:
        heading = me_vel.normalize()

    circle_center = heading * circle_distance
    displacement = V2(circle_radius, 0).rotate(state['angle'])

    desired = circle_center + displacement
    raw_force = desired - me_vel

    # Low-pass filter: blend toward the new raw force instead of jumping to it
    state['smoothed_force'] = (
        state['smoothed_force'] * smoothing + raw_force * (1.0 - smoothing)
    )
    return state['smoothed_force']