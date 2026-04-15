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
        if not isinstance(loaded, dict):
            loaded = {}

        def _safe_int(key):
            v = loaded.get(key, 0)
            return v if isinstance(v, int) else 0

        def _safe_dict(key):
            v = loaded.get(key, {})
            return v if isinstance(v, dict) else {}

        return {
            'games_played': _safe_int('games_played'),
            'total_hits': _safe_int('total_hits'),
            'max_combo': _safe_int('max_combo'),
            'powerups_collected': _safe_int('powerups_collected'),
            'high_scores': {**DEFAULT_STATS['high_scores'], **_safe_dict('high_scores')},
            'boss_kills': {**DEFAULT_STATS['boss_kills'], **_safe_dict('boss_kills')},
            'settings': {**DEFAULT_SETTINGS, **_safe_dict('settings')},
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
