"""Gravity well — pulls balls toward its center."""
import math
import pygame
from ..config import ELECTRIC_PURPLE


class GravityWell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.strength = 150
        self.radius = 100
        self.life = 300
        self.pulse = 0.0

    def update(self):
        self.life -= 1
        self.pulse += 0.1
        return self.life > 0

    def attract(self, ball):
        dx = self.x - ball.rect.centerx
        dy = self.y - ball.rect.centery
        dist = math.hypot(dx, dy)
        if 10 < dist < self.radius:
            force = self.strength / (dist ** 2)
            ball.speed_x += (dx / dist) * force * 0.1
            ball.speed_y += (dy / dist) * force * 0.1

    def draw(self, surface):
        alpha = int(100 * (self.life / 300))
        for i in range(3):
            radius = int(self.radius * (1 - i * 0.3) + 10 * math.sin(self.pulse + i))
            if radius <= 0:
                continue
            color = (*ELECTRIC_PURPLE, max(0, alpha - i * 30))
            s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (radius, radius), radius, 2)
            surface.blit(s, (self.x - radius, self.y - radius))
