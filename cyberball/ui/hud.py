"""In-game HUD: scores, combo, powerup timers."""
import math
import pygame

from ..config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CYBER_BLUE, NEON_PINK, POWERUP_GOLD,
    NEON_GREEN, DIM_GRAY, POWERUP_DURATION, BRIGHT_WHITE, ALERT_RED,
)
from ..entities.powerup import COLORS as POWERUP_COLORS, LABELS as POWERUP_LABELS


def draw_boss_hp_bar(surface, boss, font):
    if boss is None:
        return
    center_x = SCREEN_WIDTH // 2
    y = 15
    name = font.render(f"BOSS: {boss.boss_type.upper()}", True, ALERT_RED)
    surface.blit(name, name.get_rect(center=(center_x, y)))
    bar_w = 420
    bar_h = 16
    bar_x = center_x - bar_w // 2
    bar_y = y + 20
    pygame.draw.rect(surface, (40, 10, 10), (bar_x, bar_y, bar_w, bar_h))
    if hasattr(boss, 'segments'):
        total = boss.hp_max
        seg_w = bar_w // max(1, total)
        filled = sum(seg.hp for seg in boss.segments)
        for i in range(filled):
            pygame.draw.rect(surface, ALERT_RED,
                             (bar_x + i * seg_w + 1, bar_y + 1, seg_w - 2, bar_h - 2))
    else:
        frac = boss.hp / max(1, boss.hp_max)
        pygame.draw.rect(surface, ALERT_RED,
                         (bar_x + 1, bar_y + 1, int((bar_w - 2) * frac), bar_h - 2))
    pygame.draw.rect(surface, BRIGHT_WHITE, (bar_x, bar_y, bar_w, bar_h), 2)


class HUD:
    def __init__(self, fonts):
        self.score_font = fonts['score']
        self.ui_font = fonts['ui']
        self.small_font = fonts['small']

    def draw(self, surface, state, shake):
        shake_x, shake_y = shake
        self._draw_scores(surface, state, shake_x, shake_y)
        self._draw_combo(surface, state, shake_x, shake_y)
        self._draw_powerup_bars(surface, state)
        self._draw_footer(surface, state)

    def _draw_scores(self, surface, state, sx, sy):
        left_color = self._flash_color(CYBER_BLUE, state.score_flash['left'])
        right_color = self._flash_color(NEON_PINK, state.score_flash['right'])

        left = self.score_font.render(str(state.left_score), True, left_color)
        right = self.score_font.render(str(state.right_score), True, right_color)
        surface.blit(left, (SCREEN_WIDTH // 4 - left.get_width() // 2 + sx, 30 + sy))
        surface.blit(right, (3 * SCREEN_WIDTH // 4 - right.get_width() // 2 + sx, 30 + sy))

        if state.score_flash['left'] > 0:
            state.score_flash['left'] -= 1
        if state.score_flash['right'] > 0:
            state.score_flash['right'] -= 1

    @staticmethod
    def _flash_color(base, flash):
        if flash <= 0:
            return base
        f = flash / 30
        return tuple(min(255, int(c + 100 * f)) for c in base)

    def _draw_combo(self, surface, state, sx, sy):
        if state.combo_counter <= 1:
            return
        combo_txt = self.ui_font.render(f"COMBO x{state.combo_counter}", True, POWERUP_GOLD)
        y = 80 + int(5 * math.sin(pygame.time.get_ticks() * 0.01))
        surface.blit(combo_txt, (SCREEN_WIDTH // 2 - combo_txt.get_width() // 2 + sx, y + sy))
        if state.score_multiplier > 1:
            mult = self.ui_font.render(f"SCORE x{state.score_multiplier:.1f}", True, NEON_GREEN)
            surface.blit(mult, (SCREEN_WIDTH // 2 - mult.get_width() // 2 + sx, y + 30 + sy))

    def _draw_powerup_bars(self, surface, state):
        if not state.active_powerups:
            return
        x = 20
        y = 80
        bar_w = 140
        bar_h = 14
        for p in state.active_powerups:
            ratio = max(0.0, min(1.0, p['duration'] / POWERUP_DURATION))
            color = POWERUP_COLORS.get(p['type'], POWERUP_GOLD)
            label = POWERUP_LABELS.get(p['type'], p['type'][:3].upper())

            pygame.draw.rect(surface, DIM_GRAY, (x, y, bar_w, bar_h), 1)
            pygame.draw.rect(surface, color, (x + 1, y + 1, int((bar_w - 2) * ratio), bar_h - 2))
            txt = self.small_font.render(label, True, color)
            surface.blit(txt, (x + bar_w + 8, y - 2))
            y += bar_h + 6

    def _draw_footer(self, surface, state):
        speed = abs(state.ball.speed_x) if state.ball else 0.0
        mode = "1P" if state.mode == "1p" else "2P"
        txt = self.small_font.render(
            f"Difficulty: {state.difficulty.upper()}  |  Speed: {speed:.1f}  |  Mode: {mode}  |  "
            f"P: Pause  |  ESC: Menu  |  R: Reset",
            True, DIM_GRAY,
        )
        surface.blit(txt, (10, SCREEN_HEIGHT - 25))
