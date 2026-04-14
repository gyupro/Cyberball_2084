"""Particle visual effect."""
import random
import pygame


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size")

    def __init__(self, x, y, color):
        self.x = float(x)
        self.y = float(y)
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.life = random.uniform(20, 60)
        self.max_life = self.life
        self.color = color
        self.size = random.uniform(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.vx *= 0.98
        self.vy *= 0.98
        return self.life > 0

    def draw(self, surface):
        if self.max_life <= 0:
            return
        ratio = max(0.0, self.life / self.max_life)
        alpha = int(255 * ratio)
        size = int(self.size * ratio)
        if size <= 0:
            return
        s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (size, size), size)
        surface.blit(s, (int(self.x) - size, int(self.y) - size))
