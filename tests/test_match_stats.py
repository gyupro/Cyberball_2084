import unittest

from cyberball.ui.gameover import MatchStats


class MatchStatsTest(unittest.TestCase):
    def test_initial_zero(self):
        m = MatchStats()
        self.assertEqual(m.max_combo, 0)
        self.assertEqual(m.boss_kills, 0)
        self.assertEqual(m.powerups_picked, 0)
        self.assertEqual(m.hits, 0)

    def test_record_hit_updates_combo(self):
        m = MatchStats()
        m.record_hit(combo=3)
        m.record_hit(combo=7)
        m.record_hit(combo=5)
        self.assertEqual(m.hits, 3)
        self.assertEqual(m.max_combo, 7)

    def test_record_boss_and_powerup(self):
        m = MatchStats()
        m.record_boss_kill()
        m.record_boss_kill()
        m.record_powerup()
        self.assertEqual(m.boss_kills, 2)
        self.assertEqual(m.powerups_picked, 1)

    def test_duration_seconds(self):
        m = MatchStats()
        m.start_ms = 1_000
        self.assertEqual(m.duration_seconds(now_ms=6_500), 5)

    def test_start_resets(self):
        m = MatchStats()
        m.record_hit(combo=10)
        m.record_boss_kill()
        m.start(now_ms=0)
        self.assertEqual(m.hits, 0)
        self.assertEqual(m.max_combo, 0)
        self.assertEqual(m.boss_kills, 0)


if __name__ == '__main__':
    unittest.main()
