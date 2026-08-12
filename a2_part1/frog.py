from __future__ import annotations

import math
from pathlib import Path

import pygame

from settings import FROG_SPEED, TILE_SIZE


class Frog:
    def __init__(self, x, y, sprite_path=None):
        self.pos = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.path: list[pygame.Vector2] = []
        self.path_index = 0
        self.angle = 0.0
        self.sprite = self._load_sprite(sprite_path)
        self._cached_rotated_sprite = self.sprite
        self._cached_rotation_angle = None

    def _load_sprite(self, sprite_path):
        if sprite_path is None:
            return None
        try:
            path = Path(sprite_path)
            if not path.exists():
                return None
            sprite = pygame.image.load(str(path)).convert_alpha()
            max_size = int(TILE_SIZE * 0.72)
            sprite = pygame.transform.smoothscale(sprite, (max_size, max_size))
            return sprite
        except Exception:
            return None

    def set_path(self, world_points: list[tuple[float, float]]) -> None:
        self.path = [pygame.Vector2(point) for point in world_points]
        self.path_index = 0
        self.velocity = pygame.Vector2(0, 0)

    def follow_path(self, dt: float) -> None:
        if not self.path or self.is_path_complete():
            self.velocity.update(0, 0)
            return

        remaining_distance = max(0.0, FROG_SPEED * dt)
        if remaining_distance == 0.0:
            return

        for _ in range(len(self.path) + 1):
            if self.path_index >= len(self.path):
                self.velocity.update(0, 0)
                return

            target = self.path[self.path_index]
            offset = target - self.pos
            dist_to_target = offset.length()

            if dist_to_target > 0.0:
                desired_velocity = offset.normalize() * FROG_SPEED
                self.velocity = desired_velocity
                self.angle = math.degrees(math.atan2(-self.velocity.y, self.velocity.x))
            else:
                self.velocity.update(0, 0)

            if dist_to_target <= remaining_distance:
                self.pos = target.copy()
                remaining_distance -= dist_to_target
                if self.path_index < len(self.path) - 1:
                    self.path_index += 1
                    continue
                self.velocity.update(0, 0)
                remaining_distance = 0.0
                return

            if dist_to_target > 0.0:
                self.pos += self.velocity.normalize() * remaining_distance
            remaining_distance = 0.0
            return

        self.velocity.update(0, 0)

    def is_path_complete(self) -> bool:
        if not self.path:
            return True
        if self.path_index < len(self.path) - 1:
            return False
        return self.pos.distance_to(self.path[-1]) <= 0.5

    def draw(self, surface) -> None:
        center = (int(self.pos.x), int(self.pos.y))
        
        shadow_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        shadow_rect = pygame.Rect(0, 0, int(TILE_SIZE * 0.8), int(TILE_SIZE * 0.5))
        shadow_rect.center = (TILE_SIZE // 2, TILE_SIZE // 2)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 130), shadow_rect)
        surface.blit(shadow_surf, (center[0] - TILE_SIZE // 2, center[1] - TILE_SIZE // 2))

        if self.sprite is not None:
            angle_key = round(self.angle, 1)
            if self._cached_rotated_sprite is None or self._cached_rotation_angle != angle_key:
                self._cached_rotated_sprite = pygame.transform.rotate(self.sprite, self.angle)
                self._cached_rotation_angle = angle_key
            rotated = self._cached_rotated_sprite
            rect = rotated.get_rect(center=center)
            surface.blit(rotated, rect)
            return

        pygame.draw.circle(surface, (73, 190, 80), center, int(TILE_SIZE * 0.22))
        if self.velocity.length_squared() > 0.0:
            direction = self.velocity.normalize() * (TILE_SIZE * 0.28)
            end_point = (int(self.pos.x + direction.x), int(self.pos.y + direction.y))
            pygame.draw.line(surface, (220, 255, 220), center, end_point, 3)
