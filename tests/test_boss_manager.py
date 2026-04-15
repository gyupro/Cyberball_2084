import unittest
import pygame
pygame.init()

from cyberball.systems.boss_manager import BossManager
from cyberball.entities.boss import Titan, Barrage, Split


class BossManagerTest(unittest.TestCase):
    def setUp(self):
        self.mgr = BossManager(boss_x=80)

    def test_triggers_boss_at_score_5(self):
        boss = self.mgr.on_player_score(new_player_score=5)
        self.assertIsInstance(boss, Titan)
        self.assertTrue(self.mgr.active)

    def test_no_trigger_off_multiple(self):
        self.assertIsNone(self.mgr.on_player_score(new_player_score=3))
        self.assertFalse(self.mgr.active)

    def test_rotation_advances_on_defeat(self):
        b1 = self.mgr.on_player_score(5)
        self.mgr.on_boss_defeated()
        b2 = self.mgr.on_player_score(10)
        self.assertIsInstance(b1, Titan)
        self.assertIsInstance(b2, Barrage)
        self.mgr.on_boss_defeated()
        b3 = self.mgr.on_player_score(15)
        self.assertIsInstance(b3, Split)

    def test_rotation_preserved_on_player_loss(self):
        self.mgr.on_player_score(5)
        self.mgr.on_player_lost_point()
        b = self.mgr.on_player_score(10)
        self.assertIsInstance(b, Titan)

    def test_defeat_reward(self):
        self.mgr.on_player_score(5)
        reward = self.mgr.on_boss_defeated()
        # Titan hp_max=5 → 5 match points
        self.assertEqual(reward['score_bonus'], 5)
        self.assertEqual(reward['boss_type'], 'titan')
        self.assertIn(reward['powerup_type'],
                      ['speed', 'size', 'multi', 'shield', 'gravity', 'slow_time', 'laser'])

    def test_no_double_trigger_while_active(self):
        self.mgr.on_player_score(5)
        # Even if we call again with the same score, no new boss spawns
        self.assertIsNone(self.mgr.on_player_score(5))

    def test_titan_kill_at_5_advances_score_and_triggers_barrage(self):
        """Regression for I1/I2: bonus from Titan kill (5pts) at score 5
        pushes player to score 10, which must immediately trigger Barrage."""
        boss = self.mgr.on_player_score(5)
        self.assertIsInstance(boss, Titan)
        for _ in range(5):
            boss.take_damage()
        reward = self.mgr.on_boss_defeated()
        self.assertEqual(reward['score_bonus'], 5)
        # Caller adds bonus: 5 + 5 = 10. on_player_score(10) should trigger Barrage.
        next_boss = self.mgr.on_player_score(10)
        self.assertIsInstance(next_boss, Barrage)


if __name__ == '__main__':
    unittest.main()
