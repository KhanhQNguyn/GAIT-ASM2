# ============================================================================
# frog.py
# Purpose
#   Player controlled agent. Moves with Arrive. Shoots bubbles.
#   Holds a short Hurt state for temporary invulnerability after damage.
# Update order
#   Compute steering, integrate velocity with dt, clamp to bounds, update bubbles.
# Drawing
#   Draw the frog body and a simple eye that points in the facing direction.
# ============================================================================

import time
import pygame
from pygame.math import Vector2 as V2
from settings import (
    WIDTH, HEIGHT, WHITE, GREEN, BLUE,
    FROG_RADIUS, FROG_SPEED,
    BUBBLE_RADIUS, BUBBLE_SPEED, BUBBLE_LIFETIME,
    HURT_INVULN, FROG_FACING_MIN_SPEED_SQ,
    ARRIVE_STOP_RADIUS, ARRIVE_STOP_DAMPING, ARRIVE_STOP_SNAP,
    PATH_WAYPOINT_RADIUS
)
from utils import clamp, draw_debug_overlay, circle_rect_intersect, nearest_point_on_rect
import debug_state
from steering import arrive, seek, integrate_velocity, apply_arrive_stop

class Bubble:
    """
    Simple projectile that moves in a straight line and pops after a short time.
    You can destroy it early when it hits a snake or an obstacle.
    """
    def __init__(self, pos, dir_vec):
        self.pos = V2(pos)
        self.vel = (dir_vec.normalize() if dir_vec.length_squared() > 0 else V2(1, 0)) * BUBBLE_SPEED
        self.birth = time.time()
        self.alive = True

    def update(self, dt):
        self.pos += self.vel * dt
        if time.time() - self.birth > BUBBLE_LIFETIME:
            self.alive = False

    def draw(self, surf):
        pygame.draw.circle(surf, BLUE, self.pos, BUBBLE_RADIUS)
        pygame.draw.circle(surf, WHITE, self.pos, BUBBLE_RADIUS, 2)

class Frog:
    def __init__(self, pos, rects=None):
        self.pos = V2(pos)
        self.vel = V2()
        self.target = V2(pos)

        # A* path-following state (Assignment 2, Part 1). When self.path is
        # non-empty, update() steers through these waypoints instead of
        # jumping straight at self.target.
        self.path = []          # list[V2] of smoothed A* waypoints
        self.path_index = 0
        self.path_cost = 0.0

        self.radius = FROG_RADIUS
        self.speed = FROG_SPEED
        self.facing = V2(1, 0)   # used to aim bubbles when frog is not moving
        self.bubbles = []
        self.rects = rects if rects is not None else []
        self.hurt_timer = 0.0

    def set_target(self, p):
        """Set a new target the frog will move toward using Arrive."""
        self.target = V2(p)

    def set_path(self, path_points, cost=0.0):
        """Replace the current A* path with a new list of world-space waypoints."""
        self.path = [V2(p) for p in path_points]
        self.path_index = 0
        self.path_cost = cost
        if self.path:
            self.target = self.path[-1]

    def shoot(self):
        """Spawn a bubble just in front of the frog, moving along the facing direction."""
        dir_vec = self.vel if self.vel.length_squared() > FROG_FACING_MIN_SPEED_SQ else self.facing
        origin = self.pos + dir_vec.normalize() * (self.radius + 6)
        self.bubbles.append(Bubble(origin, dir_vec))

    def start_hurt(self):
        """Begin the invulnerability window after damage."""
        if self.hurt_timer <= 0:
            self.hurt_timer = HURT_INVULN

    def can_be_hurt(self):
        """Return True if the frog can take damage right now."""
        return self.hurt_timer <= 0

    def update(self, dt):
        # --- A* path following (Assignment 2, Part 1) -----------------------
        # Intermediate waypoints use seek() to keep full speed through turns
        # (Arrive's slow-down would make the frog visibly brake at every
        # corner). Only the FINAL waypoint uses arrive(), for a smooth stop
        # at the true destination. If no path is set, fall back to the
        # original Assignment 1 direct-Arrive behaviour (legacy left-click).
        if self.path and self.path_index < len(self.path):
            wp = self.path[self.path_index]
            is_last = (self.path_index == len(self.path) - 1)

            if not is_last and (wp - self.pos).length_squared() < PATH_WAYPOINT_RADIUS ** 2:
                self.path_index += 1
                wp = self.path[self.path_index]
                is_last = (self.path_index == len(self.path) - 1)

            if is_last:
                self.target = wp
                steer = arrive(self.pos, self.vel, wp, self.speed)
            else:
                steer = seek(self.pos, self.vel, wp, self.speed)

            final_dest = self.path[-1]
        else:
            steer = arrive(self.pos, self.vel, self.target, self.speed)
            final_dest = self.target

        self.vel = integrate_velocity(
            self.vel,
            steer,
            dt,
            self.speed,
        )

        # Only apply the hard-stop damping toward the TRUE final destination
        # (last path waypoint, or the legacy direct target) - applying it on
        # intermediate waypoints would brake the frog at every corner.
        self.vel = apply_arrive_stop(
            self.pos,
            self.vel,
            final_dest,
            dt,
        )

        # Path is finished once we've arrived and stopped at the last waypoint
        if self.path and self.path_index == len(self.path) - 1:
            if (final_dest - self.pos).length() < ARRIVE_STOP_RADIUS and self.vel.length() < 1.0:
                self.path = []


        # Move the frog
        self.pos += self.vel * dt

        # Face in the direction of motion when moving
        if self.vel.length_squared() > FROG_FACING_MIN_SPEED_SQ:
            self.facing = self.vel.normalize()

        # Keep inside bounds
        self.pos.x = clamp(self.pos.x, self.radius, WIDTH - self.radius)
        self.pos.y = clamp(self.pos.y, self.radius, HEIGHT - self.radius)

        # Push frog out of any obstacle rectangle it overlaps
        # for rect in self.rects:
        #     if circle_rect_intersect(self.pos, self.radius, rect):
        #         nearest = nearest_point_on_rect(self.pos, rect)
        #         diff = self.pos - nearest
        #         if diff.length_squared() > 0:
        #             push_dir = diff.normalize()
        #         else:
        #             push_dir = V2(0, -1)
        #         self.pos = nearest + push_dir * self.radius
        #         # Kill velocity component pushing further into the obstacle
        #         into_wall = self.vel.dot(push_dir)
        #         if into_wall < 0:
        #             self.vel -= push_dir * into_wall

        # Update bubbles and remove popped ones
        for b in list(self.bubbles):
            b.update(dt)
            if not b.alive:
                self.bubbles.remove(b)

        # Count down invulnerability
        if self.hurt_timer > 0:
            self.hurt_timer -= dt

    def draw(self, surf):
        # Flash while hurt. This provides player feedback and helps debugging.
        color = GREEN
        if self.hurt_timer > 0:
            t = int(pygame.time.get_ticks() * 0.01) % 2
            color = (220, 220, 220) if t == 0 else (160, 160, 160)

        # Body
        pygame.draw.circle(surf, color, self.pos, self.radius)

        # Eye looks in facing direction
        eye = self.pos + self.facing * (self.radius - 4)
        pygame.draw.circle(surf, WHITE, eye, 5)
        pygame.draw.circle(surf, (30, 30, 30), eye, 2)

        # Bubbles
        for b in self.bubbles:
            b.draw(surf)
        
        # Debug overlay when enabled
        if debug_state.DEBUG:
            draw_debug_overlay(surf, self.pos, self.vel, [], "khanh", vel_color=(120, 255, 160))
            
            # Draw crosshair at target
            pygame.draw.circle(surf, (200, 200, 200), self.target, 3)
            pygame.draw.line(surf, (200, 200, 200), self.target - V2(8, 0), self.target + V2(8, 0), 1)
            pygame.draw.line(surf, (200, 200, 200), self.target - V2(0, 8), self.target + V2(0, 8), 1)
            
            # Draw ARRIVE_SLOW_RADIUS and ARRIVE_STOP_RADIUS around the target
            from settings import ARRIVE_SLOW_RADIUS, ARRIVE_STOP_RADIUS
            pygame.draw.circle(surf, (255, 200, 100), self.target, ARRIVE_SLOW_RADIUS, 1)
            pygame.draw.circle(surf, (255, 100, 100), self.target, ARRIVE_STOP_RADIUS, 1)