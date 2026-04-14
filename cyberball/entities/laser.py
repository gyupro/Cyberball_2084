"""Laser projectile."""
import random
import pygame
from ..config import SCREEN_WIDTH, NEON_PINK, CYBER_BLUE, BRIGHT_WHITE
from ..ui.effects import draw_glow_rect


class Laser:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction  # 'left' or 'right'
        self.speed = 15
        self.width = 60
        self.height = 4
        self.rect = pygame.Rect(x - self.width // 2, y - self.height // 2, self.width, self.height)

    def update(self):
        self.x += -self.speed if self.direction == 'left' else self.speed
        self.rect.x = self.x - self.width // 2
        return 0 < self.x < SCREEN_WIDTH

    def draw(self, surface):
        color = NEON_PINK if self.direction == 'right' else CYBER_BLUE
        draw_glow_rect(surface, color, self.rect, 8)
        pygame.draw.rect(surface, BRIGHT_WHITE, self.rect)
        for i in range(0, self.width, 4):
            spark_x = self.rect.x + i
            spark_y = self.rect.centery + random.randint(-2, 2)
            pygame.draw.circle(surface, color, (spark_x, spark_y), 1)
