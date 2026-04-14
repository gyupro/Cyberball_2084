"""Per-match stats tracking and game over screen."""
import pygame

from . import typography
from ..config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    CYBER_BLUE, NEON_PINK, BRIGHT_WHITE, GOLD,
)


class MatchStats:
    def __init__(self):
        self.hits = 0
        self.max_combo = 0
        self.boss_kills = 0
        self.powerups_picked = 0
        self.start_ms = 0
        self.end_ms = 0

    def start(self, now_ms):
        self.start_ms = now_ms
        self.end_ms = 0
        self.hits = 0
        self.max_combo = 0
        self.boss_kills = 0
        self.powerups_picked = 0

    def stop(self, now_ms):
        self.end_ms = now_ms

    def record_hit(self, combo):
        self.hits += 1
        if combo > self.max_combo:
            self.max_combo = combo

    def record_boss_kill(self):
        self.boss_kills += 1

    def record_powerup(self):
        self.powerups_picked += 1

    def duration_seconds(self, now_ms=None):
        end = self.end_ms or now_ms or 0
        return max(0, (end - self.start_ms) // 1000)


def draw_game_over(surface, winner_label, player_score, ai_score, stats, now_ms=None):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 210))
    surface.blit(overlay, (0, 0))

    title_font = typography.title()
    body_font = typography.body()
    heading_font = typography.heading()

    title = title_font.render(f"{winner_label} WINS", True, GOLD)
    surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 140)))

    score_text = heading_font.render(f"{player_score}  :  {ai_score}", True, BRIGHT_WHITE)
    surface.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH // 2, 230)))

    lines = [
        f"Max Combo:        {stats.max_combo}",
        f"Boss Kills:       {stats.boss_kills}",
        f"Powerups Picked:  {stats.powerups_picked}",
        f"Total Hits:       {stats.hits}",
        f"Match Time:       {stats.duration_seconds(now_ms)}s",
    ]
    y = 310
    for line in lines:
        surf = body_font.render(line, True, CYBER_BLUE)
        surface.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, y)))
        y += 36

    hint = body_font.render("Press R to restart  /  ESC for menu", True, NEON_PINK)
    surface.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)))
