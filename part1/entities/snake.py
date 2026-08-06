# ============================================================================
# snake.py
# Purpose
#   Predator agent with a five-state FSM.
#   States: PatrolAway, PatrolHome, Aggro, Harmless, Confused.
#   Aggro chases the frog. Harmless returns home after pacification.
#   Confused wanders briefly after reaching home, then resumes patrol.
# Update order
#   Evaluate transitions first, then run the behavior for the active state.
# Drawing
#   Simple circle with a tiny eye that turns toward the current velocity.
# ============================================================================

from enum import Enum, auto
import math, random
import pygame
from pygame.math import Vector2 as V2
import settings
from settings import (
    WIDTH, HEIGHT, WHITE,
    SNAKE_RADIUS, SNAKE_SPEED, DEAGGRO_RANGE
)
from utils import draw_debug_overlay, nearest_point_on_rect, circle_rect_intersect
import debug_state
from steering import arrive, seek, seek_with_avoid, arrive_with_avoid, integrate_velocity, pursue, wander_force, predict_future_position
class SnakeState(Enum):
    PatrolAway = auto()
    PatrolHome = auto()
    Aggro      = auto()
    Harmless   = auto()
    Confused   = auto()

class Snake:
    def __init__(self, pos, patrol_point, rects):
        # Motion and shape
        self.pos = V2(pos)
        self.vel = V2(1, 0)
        self.radius = SNAKE_RADIUS
        self.speed = SNAKE_SPEED

        # Home base and patrol destination
        self.home = V2(pos)
        self.patrol_point = V2(patrol_point)

        # Initial state
        self.state = SnakeState.PatrolAway

        # Obstacles for avoidance
        self.rects = rects

        # Drawing hint for head direction
        self.heading_deg = 0.0

        # Color varies by state for quick visual debug
        self.color = (190, 130, 110)

        # Confused state timer
        self.confused_timer = 0.0

        # RNG for wander if needed
        self._rng_seed = random.randint(0, 999999)
        self._avoid_angle = 0.0

        # Debug overlay info
        self._debug_target = None
        self._debug_steer = V2()
        self._debug_avoid = V2()

    def set_state(self, st):
        """Switch to a new FSM state and log the transition for debug overlay."""
        if st != self.state:
            debug_state.log_transition("Snake", id(self) % 1000, self.state.name, st.name)
        self.state = st
        
        # Start the confused timer immediately when entering the state
        if self.state == SnakeState.Confused:
            self.confused_timer = settings.SNAKE_CONFUSED_DURATION

    def update(self, dt, frog):
        """
        Update state transitions based on distance to frog and timers.
        Then compute a steering force for the active state and integrate motion.
        """

        # Distance to frog for transitions
        dist = (frog.pos - self.pos).length()

        # ---------------- FSM transitions ----------------
        if self.state == SnakeState.Aggro:
            if dist > DEAGGRO_RANGE:
                self.set_state(SnakeState.PatrolHome)

        elif self.state in (SnakeState.PatrolHome, SnakeState.PatrolAway):
            if dist < settings.AGGRO_RANGE:
                self.set_state(SnakeState.Aggro)

        elif self.state == SnakeState.Confused:
            self.confused_timer -= dt
            if self.confused_timer <= 0:
                self.set_state(SnakeState.PatrolAway)

        elif self.state == SnakeState.Harmless:
            # Walk home, then resume patrol
            if (self.home - self.pos).length() < settings.SNAKE_ARRIVE_THRESHOLD:
                self.set_state(SnakeState.Confused)

        # ---------------- State behaviours ----------------
        if self.state == SnakeState.Aggro:
            self.color = (255, 150, 150)
            # Predict where the frog will be, then let the corridor search pick the actual
            # direction toward that point — avoidance has full authority when something is
            # in the way, instead of being a weak add-on to a separately-computed chase force
            predicted = predict_future_position(self.pos, frog.pos, frog.vel, self.speed)
            steer, self._avoid_angle = seek_with_avoid(
                self.pos, self.vel, predicted, self.speed, self.radius, self.rects,
                preferred_angle=self._avoid_angle)

        elif self.state == SnakeState.PatrolAway:
            self.color = (180, 200, 255)
            steer, self._avoid_angle = arrive_with_avoid(
                self.pos, self.vel, self.patrol_point, self.speed, self.radius, self.rects,
                preferred_angle=self._avoid_angle)
            if (self.patrol_point - self.pos).length() < settings.SNAKE_ARRIVE_THRESHOLD:
                self.set_state(SnakeState.PatrolHome)

        elif self.state == SnakeState.PatrolHome:
            self.color = (180, 220, 180)
            steer, self._avoid_angle = arrive_with_avoid(
                self.pos, self.vel, self.home, self.speed, self.radius, self.rects,
                preferred_angle=self._avoid_angle)
            if (self.home - self.pos).length() < settings.SNAKE_ARRIVE_THRESHOLD:
                self.set_state(SnakeState.PatrolAway)

        elif self.state == SnakeState.Harmless:
            self.color = (190, 180, 255)
            steer, self._avoid_angle = arrive_with_avoid(
                self.pos, self.vel, self.home, self.speed * settings.SNAKE_HARMLESS_SPEED_MULT,
                self.radius, self.rects, preferred_angle=self._avoid_angle)

        else:  # Confused
            self.color = (245, 210, 160)
            steer = wander_force(self.vel, rng_seed=self._rng_seed)

        # Integrate velocity and update position
        self.vel = integrate_velocity(self.vel, steer, dt, self.speed)
        self.pos += self.vel * dt

        # Hard fallback: guarantee the snake never ends up overlapping an obstacle, even on
        # frames where the soft avoidance steering wasn't enough (tight corners, high speed)
        for rect in self.rects:
            if circle_rect_intersect(self.pos, self.radius, rect):
                nearest = nearest_point_on_rect(self.pos, rect)
                diff = self.pos - nearest
                if diff.length_squared() > 0:
                    push_dir = diff.normalize()
                else:
                    push_dir = V2(0, -1)
                self.pos = nearest + push_dir * self.radius
                into_wall = self.vel.dot(push_dir)
                if into_wall < 0:
                    self.vel -= push_dir * into_wall

        # Smooth eye heading based on velocity
        spd = self.vel.length()
        if spd > 4:
            def lerp(a, b, t): return a + (b - a) * t
            self.heading_deg = lerp(self.heading_deg, math.degrees(math.atan2(self.vel.y, self.vel.x)), 0.15)

        # Keep inside arena
        if self.pos.x < self.radius: self.pos.x = self.radius
        if self.pos.x > WIDTH - self.radius: self.pos.x = WIDTH - self.radius
        if self.pos.y < self.radius: self.pos.y = self.radius
        if self.pos.y > HEIGHT - self.radius: self.pos.y = HEIGHT - self.radius

    def draw(self, surf):
        # Body
        pygame.draw.circle(surf, self.color, self.pos, self.radius)
        # Simple eye in heading direction
        head = self.pos + V2(1, 0).rotate(self.heading_deg) * (self.radius - 2)
        pygame.draw.circle(surf, (30, 30, 30), head, 3)
        pygame.draw.circle(surf, WHITE, head, 5, 1)
        
        # Debug overlay when enabled
        if debug_state.DEBUG:
            perception_radii = [
                (settings.AGGRO_RANGE, (255, 100, 100)),
                (DEAGGRO_RANGE, (100, 100, 255))
            ]
            draw_debug_overlay(surf, self.pos, self.vel, perception_radii, self.state.name, vel_color=(255, 130, 100))
            
            # Draw individual forces
            scale = 0.3
            if self._debug_steer.length_squared() > 0.01:
                pygame.draw.line(surf, (100, 255, 100), self.pos, self.pos + self._debug_steer * scale, 2) # Green for base steer
            if self._debug_avoid.length_squared() > 0.01:
                pygame.draw.line(surf, (255, 200, 100), self.pos, self.pos + self._debug_avoid * scale, 2) # Orange for avoid force
                
            # Draw marker at active target
            if self._debug_target:
                pygame.draw.line(surf, (255, 50, 50), self._debug_target - V2(6, 6), self._debug_target + V2(6, 6), 2)
                pygame.draw.line(surf, (255, 50, 50), self._debug_target - V2(6, -6), self._debug_target + V2(6, -6), 2)
