from typing import Optional, List, Tuple
import math
import pygame
from settings import (
    PATH_RADIUS,
    WAYPOINT_ARRIVAL_RADIUS,
    FROG_MAX_SPEED,
    FROG_MAX_FORCE,
    FROG_SLOW_RADIUS,
    FROG_PREDICT_DIST,
)

def project_point_on_segment(p: pygame.Vector2, a: pygame.Vector2, b: pygame.Vector2) -> pygame.Vector2:
    """Projects point P onto segment AB, clamping scalar t to [0, 1]."""
    ab = b - a
    if ab.length_squared() == 0:
        return pygame.Vector2(a)
    t = (p - a).dot(ab) / ab.length_squared()
    t = max(0.0, min(1.0, t))
    return a + ab * t

class Frog:
    def __init__(self, x: float, y: float, sprite_path: Optional[str] = None):
        self.pos = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0.0, 0.0)
        self.path: List[pygame.Vector2] = []
        self.path_index = 0
        self.angle = 0.0
        
        self.sprite = None
        if sprite_path:
            try:
                raw_sprite = pygame.image.load(str(sprite_path)).convert_alpha()
                self.sprite = pygame.transform.scale(raw_sprite, (36, 36))
            except Exception:
                self.sprite = None

    def set_path(self, world_points: List[Tuple[float, float]]):
        self.path = [pygame.Vector2(pt[0], pt[1]) for pt in world_points]
        self.path_index = 0

    def is_path_complete(self) -> bool:
        if not self.path:
            return True
        final_target = self.path[-1]
        is_last_index = (self.path_index >= len(self.path) - 1)
        is_close = (self.pos.distance_to(final_target) < WAYPOINT_ARRIVAL_RADIUS)
        return is_last_index and is_close

    def follow_path(self, dt: float):
        if not self.path:
            return

        target = self.path[self.path_index]
        
        # 1. Advance waypoint index if arrived at current target
        if self.pos.distance_to(target) < WAYPOINT_ARRIVAL_RADIUS and self.path_index < len(self.path) - 1:
            self.path_index += 1
            target = self.path[self.path_index]

        # 2. Predict future position (Reynolds' look ahead)
        if self.velocity.length() > 0:
            future_pos = self.pos + self.velocity.normalize() * FROG_PREDICT_DIST
        else:
            future_pos = pygame.Vector2(self.pos)

        # 3. Project future position onto active path segment
        seg_start = self.path[max(self.path_index - 1, 0)]
        seg_end = target
        projected = project_point_on_segment(future_pos, seg_start, seg_end)

        # 4. Steering decision: seek onto line if off-track, else arrive at target
        distance_off_line = future_pos.distance_to(projected)
        seg_dir = (seg_end - seg_start)
        if seg_dir.length() > 0:
            seg_dir = seg_dir.normalize()
        else:
            seg_dir = pygame.Vector2(1, 0)

        if distance_off_line > PATH_RADIUS:
            seek_target = projected + seg_dir * FROG_PREDICT_DIST
            steering = self._seek(seek_target)
        else:
            # Arrive behavior towards current target segment endpoint
            steering = self._arrive(target)

        self._apply_steering(steering, dt)
        self._update_facing_angle()

    def _seek(self, target: pygame.Vector2) -> pygame.Vector2:
        desired = (target - self.pos)
        if desired.length() > 0:
            desired = desired.normalize() * FROG_MAX_SPEED
        else:
            desired = pygame.Vector2(0, 0)
        
        steering = desired - self.velocity
        if steering.length() > FROG_MAX_FORCE:
            steering = steering.normalize() * FROG_MAX_FORCE
        return steering

    def _arrive(self, target: pygame.Vector2) -> pygame.Vector2:
        to_target = target - self.pos
        dist = to_target.length()

        if dist < 0.001:
            desired = pygame.Vector2(0, 0)
        else:
            if dist < FROG_SLOW_RADIUS:
                speed = FROG_MAX_SPEED * (dist / FROG_SLOW_RADIUS)
            else:
                speed = FROG_MAX_SPEED
            desired = to_target.normalize() * speed

        steering = desired - self.velocity
        if steering.length() > FROG_MAX_FORCE:
            steering = steering.normalize() * FROG_MAX_FORCE
        return steering

    def _apply_steering(self, force: pygame.Vector2, dt: float):
        self.velocity += force * dt
        if self.velocity.length() > FROG_MAX_SPEED:
            self.velocity = self.velocity.normalize() * FROG_MAX_SPEED
        
        self.pos += self.velocity * dt

    def _update_facing_angle(self):
        if self.velocity.length() > 5.0:
            # Angle relative to positive X-axis in degrees
            self.angle = math.degrees(math.atan2(-self.velocity.y, self.velocity.x))

    def draw(self, surface: pygame.Surface):
        if self.sprite:
            rotated_sprite = pygame.transform.rotate(self.sprite, self.angle)
            rect = rotated_sprite.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            surface.blit(rotated_sprite, rect)
        else:
            # Vector fallback: Green circle with direction indicator line
            center = (int(self.pos.x), int(self.pos.y))
            pygame.draw.circle(surface, (40, 200, 40), center, 14)
            pygame.draw.circle(surface, (255, 255, 255), center, 14, 2)
            
            rad = math.radians(self.angle)
            end_x = self.pos.x + 18 * math.cos(rad)
            end_y = self.pos.y - 18 * math.sin(rad)
            pygame.draw.line(surface, (255, 255, 0), center, (end_x, end_y), 3)
