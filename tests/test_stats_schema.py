import json
import os
import tempfile
import unittest

from cyberball.systems.stats import StatsManager, DEFAULT_SETTINGS


class StatsSchemaTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.tmp.close()
        os.unlink(self.tmp.name)

    def tearDown(self):
        if os.path.exists(self.tmp.name):
            os.unlink(self.tmp.name)

    def test_boss_kills_default(self):
        sm = StatsManager(path=self.tmp.name)
        self.assertEqual(sm.data['boss_kills'], {'titan': 0, 'barrage': 0, 'split': 0})

    def test_settings_default(self):
        sm = StatsManager(path=self.tmp.name)
        self.assertEqual(sm.data['settings'], DEFAULT_SETTINGS)

    def test_record_boss_kill(self):
        sm = StatsManager(path=self.tmp.name)
        sm.record_boss_kill('titan')
        sm.record_boss_kill('titan')
        sm.record_boss_kill('split')
        self.assertEqual(sm.data['boss_kills']['titan'], 2)
        self.assertEqual(sm.data['boss_kills']['split'], 1)

    def test_settings_roundtrip(self):
        sm = StatsManager(path=self.tmp.name)
        sm.update_setting('volume', 42)
        sm.update_setting('colorblind', True)
        sm.save()
        sm2 = StatsManager(path=self.tmp.name)
        self.assertEqual(sm2.data['settings']['volume'], 42)
        self.assertTrue(sm2.data['settings']['colorblind'])

    def test_malformed_subfields_dont_crash(self):
        """Non-dict shapes for sub-fields should not crash the loader."""
        broken = {
            'high_scores': [],
            'boss_kills': None,
            'settings': "garbage",
            'games_played': "not-a-number",
        }
        with open(self.tmp.name, 'w') as f:
            json.dump(broken, f)
        sm = StatsManager(path=self.tmp.name)
        self.assertEqual(sm.data['games_played'], 0)
        self.assertEqual(sm.data['high_scores'].get('easy'), 0)
        self.assertEqual(sm.data['boss_kills']['titan'], 0)
        self.assertEqual(sm.data['settings'], DEFAULT_SETTINGS)

    def test_root_not_dict_dont_crash(self):
        with open(self.tmp.name, 'w') as f:
            json.dump([1, 2, 3], f)
        sm = StatsManager(path=self.tmp.name)
        self.assertEqual(sm.data['settings'], DEFAULT_SETTINGS)

    def test_old_save_backward_compat(self):
        old = {
            'games_played': 3,
            'total_hits': 10,
            'max_combo': 5,
            'powerups_collected': 1,
            'high_scores': {'easy': 5},
        }
        with open(self.tmp.name, 'w') as f:
            json.dump(old, f)
        sm = StatsManager(path=self.tmp.name)
        self.assertEqual(sm.data['games_played'], 3)
        self.assertIn('boss_kills', sm.data)
        self.assertIn('settings', sm.data)


if __name__ == '__main__':
    unittest.main()
