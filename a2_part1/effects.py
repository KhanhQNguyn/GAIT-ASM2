from __future__ import annotations
import random
import math
import pygame


class Particle:
    __slots__ = ("pos", "vel", "life", "max_life", "color", "size", "gravity", "fade")

    def __init__(self, pos, vel, life, color, size, gravity=0.0, fade=True):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.gravity = gravity
        self.fade = fade

    def update(self, dt: float) -> bool:
        self.vel.y += self.gravity * dt
        self.pos += self.vel * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surface: pygame.Surface) -> None:
        t = max(0.0, self.life / self.max_life)
        alpha = int(255 * t) if self.fade else 255
        size = max(1, int(self.size * t))
        s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (size, size), size)
        surface.blit(s, (self.pos.x - size, self.pos.y - size))


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def update(self, dt: float) -> None:
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface: pygame.Surface) -> None:
        for p in self.particles:
            p.draw(surface)

    def emit_trail(self, pos, color=(210, 255, 210), count=1) -> None:
        for _ in range(count):
            vel = (random.uniform(-12, 12), random.uniform(-12, 12))
            self.particles.append(Particle(pos, vel, life=random.uniform(0.25, 0.4),
                                            color=color, size=random.uniform(2, 4), gravity=6))

    def emit_burst(self, pos, color=(255, 240, 140), count=14, speed=140) -> None:
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            spd = random.uniform(speed * 0.3, speed)
            vel = pygame.Vector2(spd, 0).rotate_rad(angle)
            self.particles.append(Particle(pos, vel, life=random.uniform(0.35, 0.6),
                                            color=color, size=random.uniform(3, 6), gravity=90))

    def emit_terrain_splash(self, pos, terrain_color, count=8) -> None:
        for _ in range(count):
            vel = (random.uniform(-40, 40), random.uniform(-70, -10))
            self.particles.append(Particle(pos, vel, life=random.uniform(0.3, 0.5),
                                            color=terrain_color, size=random.uniform(2, 5), gravity=160))
