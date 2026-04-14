"""Settings screen: volume, colorblind, mode, slowmo, shake intensity."""
import pygame

from . import typography
from ..config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    CYBER_BLUE, NEON_PINK, BRIGHT_WHITE, DIM_GRAY,
)


SHAKE_OPTIONS = ['off', 'low', 'medium', 'high']
MODE_OPTIONS = ['1P', '2P']


class SettingsScreen:
    ITEMS = [
        ('volume', 'Volume', 'int'),
        ('colorblind', 'Colorblind palette', 'bool'),
        ('mode', 'Mode', 'mode'),
        ('slowmo_enabled', 'Slow-mo FX', 'bool'),
        ('shake_intensity', 'Shake intensity', 'shake'),
    ]

    def __init__(self, stats):
        self.stats = stats
        self.cursor = 0

    def handle_key(self, key):
        if key == pygame.K_ESCAPE:
            self.stats.save()
            return True
        if key in (pygame.K_UP, pygame.K_w):
            self.cursor = (self.cursor - 1) % len(self.ITEMS)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.cursor = (self.cursor + 1) % len(self.ITEMS)
        elif key in (pygame.K_LEFT, pygame.K_a):
            self._adjust(-1)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self._adjust(+1)
        return False

    def _adjust(self, direction):
        key, _, kind = self.ITEMS[self.cursor]
        current = self.stats.get_setting(key)
        if kind == 'int':
            new = max(0, min(100, current + direction * 5))
            self.stats.update_setting(key, new)
        elif kind == 'bool':
            self.stats.update_setting(key, not current)
        elif kind == 'mode':
            idx = (MODE_OPTIONS.index(current) + direction) % len(MODE_OPTIONS)
            self.stats.update_setting(key, MODE_OPTIONS[idx])
        elif kind == 'shake':
            idx = (SHAKE_OPTIONS.index(current) + direction) % len(SHAKE_OPTIONS)
            self.stats.update_setting(key, SHAKE_OPTIONS[idx])

    def draw(self, surface):
        surface.fill((0, 0, 0))
        title = typography.title().render("SETTINGS", True, CYBER_BLUE)
        surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 100)))

        body = typography.body()
        y = 220
        for i, (key, label, _kind) in enumerate(self.ITEMS):
            value = self.stats.get_setting(key)
            color = NEON_PINK if i == self.cursor else BRIGHT_WHITE
            label_surf = body.render(label, True, color)
            value_surf = body.render(f"< {value} >", True, color)
            surface.blit(label_surf, (SCREEN_WIDTH // 2 - 260, y))
            surface.blit(value_surf, (SCREEN_WIDTH // 2 + 80, y))
            y += 50

        hint = body.render("UP/DOWN select · LEFT/RIGHT adjust · ESC save & exit", True, DIM_GRAY)
        surface.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60)))
