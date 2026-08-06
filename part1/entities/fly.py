# ============================================================================
# fly.py
# Purpose
#   Autonomous flocking agent with a small FSM.
#   States: Flock, Fleeing, Idle.
#   Flock uses boids separation, cohesion, alignment.
#   Fleeing uses flee or the new evade behavior.
#   Idle uses a gentle wander to drift when far from danger.
# Update order
#   Compute state transitions from triggers, then apply the behavior for state.
# ============================================================================

import random
from enum import Enum, auto
import pygame
from pygame.math import Vector2 as V2
import settings
from settings import (
    WIDTH, HEIGHT, WHITE, YELLOW, PURPLE,
    FLY_RADIUS, FLY_SPEED, NEIGHBOR_RADIUS,
    ANCHOR_WEIGHT, FROG_SPEED
)
from utils import limit, draw_debug_overlay
import debug_state
from steering import (
    boids_separation, boids_cohesion, boids_alignment,
    flee, evade, wander_force, seek
)

class FlyState(Enum):
    Flock   = auto()
    Fleeing = auto()
    Idle    = auto()

class Fly:
    def __init__(self, pos):
        self.pos = V2(pos)
        self.vel = V2(random.uniform(-1, 1), random.uniform(-1, 1))
        if self.vel.length_squared() == 0:
            self.vel = V2(1, 0)
        self.vel.scale_to_length(FLY_SPEED * 0.5)

        self.radius = FLY_RADIUS
        self.state = FlyState.Flock

        # Timers and cached values
        self.scare_timer = 0.0   # counts down while nervous before calming
        self.idle_timer  = 0.0   # time spent far from frog
        self._catching_up = False  # True while hurrying to merge into a bigger flock
        self._rng_seed   = random.randint(0, 999999)
        self._debug_neighbors = []   # cached neighbor list for debug neighbor-link drawing

    def sense_bubbles_close(self, bubbles, r):
        """Return True if any bubble is within range r of the fly."""
        for b in bubbles:
            if (b.pos - self.pos).length_squared() <= r * r:
                return True
        return False

    def _set_state(self, new_state):
        """Switch FSM state and log the transition when it actually changes."""
        if new_state != self.state:
            debug_state.log_transition("Fly", id(self) % 1000, self.state.name, new_state.name)
        self.state = new_state

    def update(self, dt, flies, frog, bounds_rect, bubbles, neighbor_counts=None, neighbors=None, neighbor_ids=None):
        """
        Update FSM and behavior. Flies use perception to switch states.
        Parameters
          flies: list of all flies for neighborhood queries
          frog:  player agent used as a threat source
          bounds_rect: world rectangle for anchor force and containment
          bubbles: list of active bubbles to trigger panic
        """

        # Perception radii and timers for the FSM
        BubbleFleeRange  = settings.FLY_BUBBLE_FLEE_RANGE
        StopFleeingRange = settings.FLY_CALM_RANGE
        IdleDistance     = settings.FLY_IDLE_DISTANCE
        IdleDelay        = settings.FLY_IDLE_DELAY

        # Triggers based on the frog and bubbles
        dist_to_frog = (frog.pos - self.pos).length()
        scared_by_frog   = dist_to_frog < settings.FLY_SCARED_RANGE
        scared_by_bubble = self.sense_bubbles_close(bubbles, BubbleFleeRange)

        # Cheap neighbor-presence check: true if any other fly is within NEIGHBOR_RADIUS
        has_nearby_flockmate = bool(neighbors)

        # ---------------- FSM transitions ----------------
        if self.state == FlyState.Flock:
            if scared_by_frog or scared_by_bubble:
                self._set_state(FlyState.Fleeing)
                self.scare_timer = settings.FLY_SCARE_TIMER
                # One-time velocity kick directly away from threat
                burst_dir = self.pos - frog.pos
                if burst_dir.length_squared() > 0:
                    burst_dir = burst_dir.normalize()
                else:
                    burst_dir = V2(0, -1)
                self.vel += burst_dir * settings.FLEE_BURST_STRENGTH
            else:
                if dist_to_frog > IdleDistance:
                    self.idle_timer += dt
                    if self.idle_timer >= IdleDelay:
                        self._set_state(FlyState.Idle)
                else:
                    self.idle_timer = 0.0

        elif self.state == FlyState.Fleeing:
            calm = dist_to_frog > StopFleeingRange and not self.sense_bubbles_close(bubbles, StopFleeingRange)
            if calm:
                self.scare_timer -= dt
                if self.scare_timer <= 0:
                    self._set_state(FlyState.Flock)
                    self.idle_timer = 0.0
            else:
                self.scare_timer = settings.FLY_SCARE_TIMER

        elif self.state == FlyState.Idle:
            if scared_by_frog or scared_by_bubble:
                self._set_state(FlyState.Fleeing)
                self.scare_timer = settings.FLY_SCARE_TIMER
                burst_dir = self.pos - frog.pos
                if burst_dir.length_squared() > 0:
                    burst_dir = burst_dir.normalize()
                else:
                    burst_dir = V2(0, -1)
                self.vel += burst_dir * settings.FLEE_BURST_STRENGTH
            elif dist_to_frog <= IdleDistance:
                self._set_state(FlyState.Flock)
                self.idle_timer = 0.0

        # ---------------- State behaviours ----------------
        if self.state == FlyState.Flock:
            # Neighbor list and neighbor-id set are precomputed once per frame in main.py
            # (single O(N^2) pass shared by every fly) and passed in here — no need to
            # rebuild them per-fly anymore.
            neighbors = neighbors if neighbors is not None else []
            neighbor_ids = neighbor_ids if neighbor_ids is not None else set()
            self._debug_neighbors = neighbors   # cache for debug drawing

            self._catching_up = False  # will be set True only if we decide to catch up below

            my_group_size = len(neighbors)
            best_bigger = None
            best_bigger_size = my_group_size

            # Only genuinely small/isolated groups should ever consider catching up —
            # density variation inside an already-joined flock should not re-trigger this
            # Only a genuinely small-but-real flock (not a lone straggler or a pair) should
            # actively hurry toward a meaningfully bigger one nearby. A lone fly or pair just
            # flocks normally and merges naturally whenever it happens to encounter a group —
            # no active cross-map hunting for those.
            if (neighbor_counts is not None
                    and settings.CATCHUP_MIN_OWN_GROUP <= my_group_size <= settings.CATCHUP_MAX_OWN_GROUP):
                for f in flies:
                    if f is self:
                        continue
                    # Skip flies already in my own neighbor set — cohesion handles them
                    if id(f) in neighbor_ids:
                        continue
                    d = (f.pos - self.pos).length()
                    if d <= settings.CATCHUP_SEARCH_RADIUS:
                        f_count = neighbor_counts.get(id(f), 0)
                        if f_count > best_bigger_size + settings.CATCHUP_GROUP_DELTA:
                            best_bigger_size = f_count
                            best_bigger = f

            if best_bigger is not None:
                # A meaningfully bigger flock is nearby — hurry to join it
                self._catching_up = True
                force = seek(
                    self.pos, self.vel, best_bigger.pos, FLY_SPEED * settings.CATCHUP_SPEED_MULT
                ) * settings.CATCHUP_WEIGHT
            elif len(neighbors) == 0:
                nearest = None
                min_dist = settings.REGROUP_RADIUS
                for f in flies:
                    if f is self:
                        continue
                    d = (f.pos - self.pos).length()
                    if d < min_dist:
                        min_dist = d
                        nearest = f

                if nearest is not None:
                    force = seek(self.pos, self.vel, nearest.pos, FLY_SPEED) * settings.REGROUP_WEIGHT
                else:
                    force = V2()
            else:
                sep = boids_separation(self.pos, self.vel, neighbors, settings.SEP_RADIUS, FLY_SPEED)
                coh = boids_cohesion(self.pos, self.vel, neighbors, FLY_SPEED)
                ali = boids_alignment(self.vel, neighbors, FLY_SPEED)
                force = sep * settings.SEP_WEIGHT + coh * settings.COH_WEIGHT + ali * settings.ALI_WEIGHT

            # Gentle anchor toward arena center to avoid drifting out of bounds
            center = V2(bounds_rect.centerx, bounds_rect.centery)
            force += (center - self.pos) * ANCHOR_WEIGHT * 0.002

            # Integrate velocity
            self.vel += limit(force, 240.0) * dt

        elif self.state == FlyState.Fleeing:
            force = evade(self.pos, self.vel, frog.pos, frog.vel, FLY_SPEED, predict_speed=FROG_SPEED)

            # Scale evade force by proximity — the closer the frog, the sharper the panic
            closeness = 1.0 - min(dist_to_frog, settings.FLEE_PANIC_RANGE) / settings.FLEE_PANIC_RANGE
            panic_mult = 1.0 + (settings.FLEE_PANIC_MAX_MULT - 1.0) * (closeness ** settings.FLEE_PANIC_EXPONENT)
            force *= panic_mult

            # Mild separation so panicking flies scatter apart instead of overlapping each
            # other — reuse the neighbor list precomputed once per frame in main.py instead
            # of rebuilding it here.
            neighbors = neighbors if neighbors is not None else []
            self._debug_neighbors = neighbors
            if neighbors:
                sep = boids_separation(self.pos, self.vel, neighbors, settings.SEP_RADIUS, FLY_SPEED)
                force += sep * settings.SEP_WEIGHT * 0.6

            # Anchor blend so the group does not disappear off screen
            center = V2(bounds_rect.centerx, bounds_rect.centery)
            force += (center - self.pos) * ANCHOR_WEIGHT * 0.002

            self.vel += limit(force, 420.0) * dt

        elif self.state == FlyState.Idle:
            force = wander_force(self.vel, FLY_SPEED, rng_seed=self._rng_seed)
            self.vel += limit(force, 120.0) * dt
            self.vel *= 0.98  # mild damping so idle feels soft

        # Speed clamp and position integrate — allow a temporary higher cap while catching up
        if self.state == FlyState.Fleeing:
            effective_max_speed = FLY_SPEED * settings.FLEE_PANIC_MAX_MULT
        elif self._catching_up:
            effective_max_speed = FLY_SPEED * settings.CATCHUP_SPEED_MULT
        else:
            effective_max_speed = FLY_SPEED

        if self.vel.length() > effective_max_speed:
            self.vel.scale_to_length(effective_max_speed)
        self.pos += self.vel * dt

        # Soft containment inside arena
        if self.pos.x < self.radius:
            self.pos.x = self.radius; self.vel.x *= -0.4
        if self.pos.x > WIDTH - self.radius:
            self.pos.x = WIDTH - self.radius; self.vel.x *= -0.4
        if self.pos.y < self.radius:
            self.pos.y = self.radius; self.vel.y *= -0.4
        if self.pos.y > HEIGHT - self.radius:
            self.pos.y = HEIGHT - self.radius; self.vel.y *= -0.4

    def draw(self, surf):
        color = YELLOW if self.state in (FlyState.Flock, FlyState.Idle) else PURPLE
        pygame.draw.circle(surf, color, self.pos, self.radius)
        
        # Debug overlay when enabled
        if debug_state.DEBUG:
            # Draw faint lines to each boid neighbor
            for n_pos, n_vel in self._debug_neighbors:
                pygame.draw.line(surf, (60, 90, 110), self.pos, n_pos, 1)
            # Draw velocity vector, NEIGHBOR_RADIUS perception, and state name
            perception_radii = [(NEIGHBOR_RADIUS, (100, 200, 255))]
            draw_debug_overlay(surf, self.pos, self.vel, perception_radii, self.state.name, vel_color=(230, 220, 100))
