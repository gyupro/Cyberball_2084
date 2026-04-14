"""Collectible power-up."""
import math
import pygame

from ..config import (
    POWERUP_SIZE, POWERUP_GOLD, POWERUP_RED, POWERUP_BLUE,
    NEON_GREEN, ELECTRIC_PURPLE, CYBER_BLUE, NEON_PINK, BLACK,
)
from ..ui.effects import draw_glow_rect


COLORS = {
    'speed': POWERUP_GOLD,
    'size': POWERUP_RED,
    'multi': POWERUP_BLUE,
    'shield': NEON_GREEN,
    'gravity': ELECTRIC_PURPLE,
    'slow_time': CYBER_BLUE,
    'laser': NEON_PINK,
}

LABELS = {
    'speed': 'SPD',
    'size': 'BIG',
    'multi': 'MLT',
    'shield': 'SHD',
    'gravity': 'GRV',
    'slow_time': 'SLO',
    'laser': 'LZR',
}


class PowerUp:
    def __init__(self, x, y, type_name):
        self.x = x
        self.y = y
        self.type = type_name
        self.rect = pygame.Rect(x - POWERUP_SIZE // 2, y - POWERUP_SIZE // 2, POWERUP_SIZE, POWERUP_SIZE)
        self.pulse = 0.0

    def update(self):
        self.pulse += 0.1

    def draw(self, surface):
        pulse_size = int(POWERUP_SIZE + 5 * math.sin(self.pulse))
        color = COLORS.get(self.type, POWERUP_GOLD)
        rect = pygame.Rect(self.x - pulse_size // 2, self.y - pulse_size // 2, pulse_size, pulse_size)
        draw_glow_rect(surface, color, rect, 5)
        pygame.draw.rect(surface, color, rect)
        self._draw_symbol(surface)

    def _draw_symbol(self, surface):
        t = self.type
        x, y = self.x, self.y
        if t == 'speed':
            pygame.draw.polygon(surface, BLACK, [(x - 8, y - 8), (x + 8, y), (x - 8, y + 8)])
        elif t == 'size':
            pygame.draw.rect(surface, BLACK, (x - 6, y - 6, 12, 12))
        elif t == 'multi':
            pygame.draw.circle(surface, BLACK, (x - 4, y), 3)
            pygame.draw.circle(surface, BLACK, (x + 4, y), 3)
        elif t == 'shield':
            pygame.draw.polygon(surface, BLACK, [
                (x, y - 8), (x - 6, y - 4), (x - 6, y + 4),
                (x, y + 8), (x + 6, y + 4), (x + 6, y - 4),
            ])
        elif t == 'gravity':
            pygame.draw.circle(surface, BLACK, (x, y), 8, 2)
            pygame.draw.circle(surface, BLACK, (x, y), 4, 1)
        elif t == 'slow_time':
            pygame.draw.circle(surface, BLACK, (x, y), 8, 2)
            pygame.draw.line(surface, BLACK, (x, y), (x, y - 5), 2)
            pygame.draw.line(surface, BLACK, (x, y), (x + 4, y), 2)
        elif t == 'laser':
            pygame.draw.line(surface, BLACK, (x - 8, y), (x + 8, y), 3)
