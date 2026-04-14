"""Persistent stats + high scores + settings."""
import json
import os

from ..config import SAVE_FILE, SAVE_DIR, DIFFICULTIES


DEFAULT_STATS = {
    'games_played': 0,
    'total_hits': 0,
    'max_combo': 0,
    'powerups_collected': 0,
    'high_scores': {d: 0 for d in DIFFICULTIES},
    'boss_kills': {'titan': 0, 'barrage': 0, 'split': 0},
}

DEFAULT_SETTINGS = {
    'volume': 70,
    'colorblind': False,
    'mode': '1P',
    'slowmo_enabled': True,
    'shake_intensity': 'medium',
}


class StatsManager:
    def __init__(self, path=SAVE_FILE):
        self.path = path
        self.data = self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            loaded = {}
        return {
            'games_played': loaded.get('games_played', 0),
            'total_hits': loaded.get('total_hits', 0),
            'max_combo': loaded.get('max_combo', 0),
            'powerups_collected': loaded.get('powerups_collected', 0),
            'high_scores': {**DEFAULT_STATS['high_scores'], **loaded.get('high_scores', {})},
            'boss_kills': {**DEFAULT_STATS['boss_kills'], **loaded.get('boss_kills', {})},
            'settings': {**DEFAULT_SETTINGS, **loaded.get('settings', {})},
        }

    def save(self):
        try:
            target_dir = os.path.dirname(self.path) or SAVE_DIR
            os.makedirs(target_dir, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except OSError:
            pass

    def record_hit(self, combo):
        self.data['total_hits'] += 1
        if combo > self.data['max_combo']:
            self.data['max_combo'] = combo

    def record_powerup(self):
        self.data['powerups_collected'] += 1

    def record_boss_kill(self, boss_type):
        if boss_type in self.data['boss_kills']:
            self.data['boss_kills'][boss_type] += 1

    def record_game_end(self, difficulty, score):
        self.data['games_played'] += 1
        if score > self.data['high_scores'].get(difficulty, 0):
            self.data['high_scores'][difficulty] = score
        self.save()

    def high_score(self, difficulty):
        return self.data['high_scores'].get(difficulty, 0)

    def update_setting(self, key, value):
        if key in DEFAULT_SETTINGS:
            self.data['settings'][key] = value

    def get_setting(self, key):
        return self.data['settings'].get(key, DEFAULT_SETTINGS.get(key))
