"""Menu, pause, and HUD rendering."""
import math
import random
import pygame

from ..config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, CYBER_BLUE, NEON_PINK, NEON_GREEN,
    ELECTRIC_PURPLE, BRIGHT_WHITE, GLOW_WHITE, DIM_GRAY, DARK_CYAN,
    DIFFICULTIES, POWERUP_GOLD, MENU_ANIMATION_SPEED,
)
from ..entities.particle import Particle


class MenuRenderer:
    def __init__(self, fonts):
        self.title_font = fonts['title']
        self.menu_font = fonts['menu']
        self.ui_font = fonts['ui']
        self.small_font = fonts['small']
        self.particles = []

    def _spawn_bg_particle(self):
        if len(self.particles) < 20:
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            color = random.choice([CYBER_BLUE, NEON_PINK, ELECTRIC_PURPLE, NEON_GREEN])
            self.particles.append(Particle(x, y, color))

    def draw_menu(self, surface, state):
        surface.fill(BLACK)
        self._spawn_bg_particle()
        self.particles[:] = [p for p in self.particles if p.update()]
        for p in self.particles:
            p.draw(surface)

        t = pygame.time.get_ticks() * MENU_ANIMATION_SPEED

        for i in range(0, SCREEN_WIDTH, 50):
            alpha = int(50 + 30 * math.sin(t + i * 0.1))
            s = pygame.Surface((2, SCREEN_HEIGHT), pygame.SRCALPHA)
            s.fill((*DARK_CYAN, max(0, alpha)))
            surface.blit(s, (i, 0))

        # Title
        title = self.title_font.render("CYBERBALL 2084", True, CYBER_BLUE)
        tx = SCREEN_WIDTH // 2 - title.get_width() // 2
        ty = 100 + int(8 * math.sin(t))
        for off in [(4, 4), (-4, -4), (4, -4), (-4, 4)]:
            glow = self.title_font.render("CYBERBALL 2084", True, BRIGHT_WHITE)
            glow.set_alpha(60)
            surface.blit(glow, (tx + off[0], ty + off[1]))
        surface.blit(title, (tx, ty))

        subtitle = self.ui_font.render("NEON WARS — v2.0", True, NEON_PINK)
        surface.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, ty + 80))

        # Main menu
        items = [
            ("SPACE", "START GAME"),
            ("1 / 2 / 3 / 4", f"DIFFICULTY: {state.difficulty.upper()}"),
            ("M", f"MODE: {state.mode.upper()}  (1P vs AI / 2P local)"),
            ("V / B", f"VOLUME: {int(state.audio.volume * 100)}%"),
            ("C", f"COLORBLIND: {'ON' if state.colorblind else 'OFF'}"),
            ("ESC", "EXIT"),
        ]
        y = 300
        for key, desc in items:
            key_surf = self.menu_font.render(key, True, NEON_GREEN)
            desc_surf = self.menu_font.render(desc, True, GLOW_WHITE)
            total_w = key_surf.get_width() + 30 + desc_surf.get_width()
            x = SCREEN_WIDTH // 2 - total_w // 2
            surface.blit(key_surf, (x, y))
            surface.blit(desc_surf, (x + key_surf.get_width() + 30, y))
            y += 50

        # Stats footer
        hs = state.stats.high_score(state.difficulty)
        foot1 = self.small_font.render(
            f"Games: {state.stats.data['games_played']}  |  High Score ({state.difficulty}): {hs}",
            True, DIM_GRAY,
        )
        surface.blit(foot1, (SCREEN_WIDTH // 2 - foot1.get_width() // 2, SCREEN_HEIGHT - 60))
        foot2 = self.small_font.render(
            f"Total Hits: {state.stats.data['total_hits']}  |  Max Combo: {state.stats.data['max_combo']}  |  "
            f"Powerups: {state.stats.data['powerups_collected']}",
            True, DIM_GRAY,
        )
        surface.blit(foot2, (SCREEN_WIDTH // 2 - foot2.get_width() // 2, SCREEN_HEIGHT - 35))

    def draw_pause(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        title = self.title_font.render("PAUSED", True, NEON_GREEN)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 120))

        lines = [
            "P — Resume",
            "ESC — Back to Menu",
            "R — Reset Match",
            "V / B — Volume  -  /  +",
            "M — Toggle Mute",
        ]
        y = SCREEN_HEIGHT // 2 - 20
        for line in lines:
            s = self.menu_font.render(line, True, GLOW_WHITE)
            surface.blit(s, (SCREEN_WIDTH // 2 - s.get_width() // 2, y))
            y += 45
