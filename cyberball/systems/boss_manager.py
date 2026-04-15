"""Boss rotation, triggering, defeat rewards."""
import random

from ..config import (
    BOSS_ROTATION, BOSS_TRIGGER_INTERVAL, POWERUP_TYPES, BOSS_SCORE_BONUS_PER_HP,
)
from ..entities.boss import Titan, Barrage, Split


BOSS_CLASSES = {
    'titan': Titan,
    'barrage': Barrage,
    'split': Split,
}


class BossManager:
    def __init__(self, boss_x, rng=None):
        self.boss_x = boss_x
        self.rotation_index = 0
        self.current_boss = None
        self.active = False
        self.rng = rng or random.Random()

    def on_player_score(self, new_player_score):
        """Trigger boss if score is multiple of BOSS_TRIGGER_INTERVAL."""
        if self.active:
            return None
        if new_player_score <= 0:
            return None
        if new_player_score % BOSS_TRIGGER_INTERVAL != 0:
            return None
        boss_type = BOSS_ROTATION[self.rotation_index % len(BOSS_ROTATION)]
        self.current_boss = BOSS_CLASSES[boss_type](x=self.boss_x)
        self.active = True
        return self.current_boss

    def on_boss_defeated(self):
        boss = self.current_boss
        if boss is None:
            return None
        reward = {
            'boss_type': boss.boss_type,
            'score_bonus': boss.hp_max * BOSS_SCORE_BONUS_PER_HP,
            'powerup_type': self.rng.choice(POWERUP_TYPES),
        }
        self.rotation_index = (self.rotation_index + 1) % len(BOSS_ROTATION)
        self.current_boss = None
        self.active = False
        return reward

    def on_player_lost_point(self):
        """Called when AI/boss scores against the player."""
        self.current_boss = None
        self.active = False
