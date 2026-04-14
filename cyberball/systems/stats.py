"""Persistent stats + high scores."""
import json
import os

from ..config import SAVE_FILE, SAVE_DIR, DIFFICULTIES


DEFAULT_STATS = {
    'games_played': 0,
    'total_hits': 0,
    'max_combo': 0,
    'powerups_collected': 0,
    'high_scores': {d: 0 for d in DIFFICULTIES},
}


class StatsManager:
    def __init__(self, path=SAVE_FILE):
        self.path = path
        self.data = self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            # Merge with defaults to tolerate new keys
            merged = {**DEFAULT_STATS, **loaded}
            merged['high_scores'] = {
                **DEFAULT_STATS['high_scores'],
                **loaded.get('high_scores', {}),
            }
            return merged
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {
                'games_played': 0,
                'total_hits': 0,
                'max_combo': 0,
                'powerups_collected': 0,
                'high_scores': dict(DEFAULT_STATS['high_scores']),
            }

    def save(self):
        try:
            os.makedirs(SAVE_DIR, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except OSError:
            pass

    # Convenience accessors
    def record_hit(self, combo):
        self.data['total_hits'] += 1
        if combo > self.data['max_combo']:
            self.data['max_combo'] = combo

    def record_powerup(self):
        self.data['powerups_collected'] += 1

    def record_game_end(self, difficulty, score):
        self.data['games_played'] += 1
        if score > self.data['high_scores'].get(difficulty, 0):
            self.data['high_scores'][difficulty] = score
        self.save()

    def high_score(self, difficulty):
        return self.data['high_scores'].get(difficulty, 0)
