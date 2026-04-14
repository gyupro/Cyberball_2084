"""Capture highlight screenshots for README (headless)."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import random
import pygame

from cyberball.game import Game, _apply_powerup

OUT = "docs/screenshots"
os.makedirs(OUT, exist_ok=True)


def save(screen, name):
    pygame.image.save(screen, os.path.join(OUT, name))
    print(f"saved {name}")


def warm(g, frames):
    for _ in range(frames):
        pygame.event.get()
        g._update_playing()
        g._draw()


def main():
    random.seed(7)
    g = Game(headless=True)

    # 1. Menu
    g.state.state = "menu"
    for _ in range(30):
        pygame.event.get()
        g._draw()
    save(g.screen, "01_menu.png")

    # 2. Gameplay (combo + particles)
    g.state.state = "playing"
    g.state.reset_match()
    # Force some combo
    g.state.combo_counter = 7
    g.state.last_hit_time = pygame.time.get_ticks()
    g.state.score_multiplier = 2.0
    g.state.left_score = 5
    g.state.right_score = 8
    warm(g, 30)
    save(g.screen, "02_gameplay_combo.png")

    # 3. All powerups active + gravity well + multi-ball
    for pt in ["speed", "size", "shield", "slow_time", "laser"]:
        _apply_powerup(g.state, pt)
    _apply_powerup(g.state, "multi")
    _apply_powerup(g.state, "gravity")
    warm(g, 60)
    save(g.screen, "03_powerups_chaos.png")

    # 4. Pause overlay
    g.state.state = "paused"
    g._draw()
    save(g.screen, "04_pause.png")

    pygame.quit()


if __name__ == "__main__":
    main()
