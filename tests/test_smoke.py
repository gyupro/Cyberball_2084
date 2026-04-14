"""Headless smoke test: boot the game and run frames without crashing."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import tempfile
import unittest


class TestSmoke(unittest.TestCase):
    def test_boot_and_frames(self):
        # Redirect save file into tempdir
        from cyberball import config
        tmp = tempfile.mkdtemp()
        config.SAVE_DIR = tmp
        config.SAVE_FILE = os.path.join(tmp, "save.json")

        from cyberball.game import Game
        g = Game(headless=True)
        # Start a match and run 180 frames (~3s of game logic)
        g.state.state = "playing"
        g.state.reset_match()
        # Do not use g.run() to avoid sys.exit; drive loop manually
        import pygame
        for _ in range(180):
            for e in pygame.event.get():
                pass
            g._update_playing()
            g._draw()
            g.clock.tick(0)  # uncapped
        pygame.quit()

    def test_stats_persist(self):
        from cyberball import config
        tmp = tempfile.mkdtemp()
        config.SAVE_DIR = tmp
        config.SAVE_FILE = os.path.join(tmp, "save.json")
        from cyberball.systems.stats import StatsManager
        s = StatsManager(path=config.SAVE_FILE)
        s.record_game_end("hard", 42)
        s2 = StatsManager(path=config.SAVE_FILE)
        self.assertEqual(s2.high_score("hard"), 42)


if __name__ == "__main__":
    unittest.main()
