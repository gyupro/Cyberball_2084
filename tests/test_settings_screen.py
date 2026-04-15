"""Settings screen behavior — handle key + enum guard."""
import os
import tempfile
import unittest
import pygame
pygame.init()

from cyberball.systems.stats import StatsManager
from cyberball.ui.settings import SettingsScreen, MODE_OPTIONS, SHAKE_OPTIONS


class SettingsScreenTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.tmp.close()
        os.unlink(self.tmp.name)
        self.stats = StatsManager(path=self.tmp.name)
        self.screen = SettingsScreen(self.stats)

    def tearDown(self):
        if os.path.exists(self.tmp.name):
            os.unlink(self.tmp.name)

    def test_volume_adjusts(self):
        self.stats.update_setting('volume', 50)
        self.screen.cursor = 0  # 'volume'
        self.screen.handle_key(pygame.K_RIGHT)
        self.assertEqual(self.stats.get_setting('volume'), 55)
        self.screen.handle_key(pygame.K_LEFT)
        self.assertEqual(self.stats.get_setting('volume'), 50)

    def test_volume_clamps(self):
        self.stats.update_setting('volume', 0)
        self.screen.cursor = 0
        self.screen.handle_key(pygame.K_LEFT)
        self.assertEqual(self.stats.get_setting('volume'), 0)

    def test_mode_unknown_value_resets_safely(self):
        """Reviewer I4: corrupted enum value must not crash on adjust."""
        self.stats.data['settings']['mode'] = "3P"  # invalid
        self.screen.cursor = 2  # 'mode'
        # Should not raise
        self.screen.handle_key(pygame.K_RIGHT)
        # Should snap to a valid option
        self.assertIn(self.stats.get_setting('mode'), MODE_OPTIONS)

    def test_shake_unknown_value_resets_safely(self):
        self.stats.data['settings']['shake_intensity'] = "potato"
        self.screen.cursor = 4  # 'shake_intensity'
        self.screen.handle_key(pygame.K_LEFT)
        self.assertIn(self.stats.get_setting('shake_intensity'), SHAKE_OPTIONS)

    def test_escape_returns_true(self):
        self.assertTrue(self.screen.handle_key(pygame.K_ESCAPE))


if __name__ == '__main__':
    unittest.main()
