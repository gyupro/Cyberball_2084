"""Boss entities: Titan (tanker), Barrage (ranged), Split (dual-paddle)."""
from dataclasses import dataclass
import pygame

from ..config import (
    PADDLE_WIDTH,
    PADDLE_HEIGHT,
    SCREEN_HEIGHT,
    BOSS_TITAN_HP,
    BOSS_BARRAGE_HP,
    BOSS_SPLIT_HP,
)


class BossProjectile:
    RADIUS = 8

    def __init__(self, x, y, vx, vy):
        self.rect = pygame.Rect(
            int(x) - self.RADIUS, int(y) - self.RADIUS,
            self.RADIUS * 2, self.RADIUS * 2,
        )
        self.vx = vx
        self.vy = vy

    def update(self):
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)

    def off_screen(self, width):
        return self.rect.right < 0 or self.rect.left > width


class Boss:
    """Base paddle boss."""
    boss_type = 'generic'
    hp_max = 1
    speed_multiplier = 1.0

    def __init__(self, x):
        self.hp = self.hp_max
        self.rect = pygame.Rect(
            x, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2,
            PADDLE_WIDTH, PADDLE_HEIGHT,
        )

    def take_damage(self):
        self.hp = max(0, self.hp - 1)

    def is_defeated(self):
        return self.hp <= 0

    def update(self, target_y=None):
        if target_y is not None:
            diff = target_y - self.rect.centery
            step = max(-8, min(8, diff)) * self.speed_multiplier
            self.rect.y += int(step)
            self.rect.clamp_ip(pygame.Rect(0, 0, 10_000, SCREEN_HEIGHT))
        return []


class Titan(Boss):
    boss_type = 'titan'
    hp_max = BOSS_TITAN_HP
    speed_multiplier = 0.55

    def __init__(self, x):
        super().__init__(x)
        height = int(PADDLE_HEIGHT * 2.5)
        self.rect = pygame.Rect(
            x, SCREEN_HEIGHT // 2 - height // 2, PADDLE_WIDTH, height,
        )


class Barrage(Boss):
    boss_type = 'barrage'
    hp_max = BOSS_BARRAGE_HP
    speed_multiplier = 1.0
    FIRE_INTERVAL_FRAMES = 120

    def __init__(self, x):
        super().__init__(x)
        self.fire_cooldown = self.FIRE_INTERVAL_FRAMES

    def update(self, target_y=None):
        super().update(target_y=target_y)
        self.fire_cooldown -= 1
        if self.fire_cooldown <= 0:
            self.fire_cooldown = self.FIRE_INTERVAL_FRAMES
            return self._fire_volley(target_y)
        return []

    def _fire_volley(self, target_y):
        projectiles = []
        # Fire from right edge of boss rect (boss is on left side of screen)
        for offset in (-20, 20):
            px = self.rect.right
            py = self.rect.centery + offset
            projectiles.append(BossProjectile(px, py, vx=4, vy=0))
        return projectiles


@dataclass
class SplitSegment:
    rect: pygame.Rect
    hp: int


class Split(Boss):
    boss_type = 'split'
    speed_multiplier = 1.1

    def __init__(self, x):
        self.hp_max = BOSS_SPLIT_HP * 2
        self.hp = self.hp_max
        seg_height = int(PADDLE_HEIGHT * 0.6)
        gap = 40
        total = seg_height * 2 + gap
        top_y = SCREEN_HEIGHT // 2 - total // 2
        self.segments = [
            SplitSegment(
                rect=pygame.Rect(x, top_y, PADDLE_WIDTH, seg_height),
                hp=BOSS_SPLIT_HP,
            ),
            SplitSegment(
                rect=pygame.Rect(x, top_y + seg_height + gap, PADDLE_WIDTH, seg_height),
                hp=BOSS_SPLIT_HP,
            ),
        ]
        self.rect = self.segments[0].rect.union(self.segments[1].rect)

    def take_damage_at(self, index):
        if 0 <= index < len(self.segments) and self.segments[index].hp > 0:
            self.segments[index].hp -= 1
            self.hp = sum(s.hp for s in self.segments)

    def take_damage(self):
        for i, seg in enumerate(self.segments):
            if seg.hp > 0:
                self.take_damage_at(i)
                return

    def update(self, target_y=None):
        if target_y is None:
            return []
        for i, seg in enumerate(self.segments):
            if seg.hp <= 0:
                continue
            tgt = target_y + (-120 if i == 0 else 120)
            diff = tgt - seg.rect.centery
            step = max(-8, min(8, diff)) * self.speed_multiplier
            seg.rect.y += int(step)
            seg.rect.clamp_ip(pygame.Rect(0, 0, 10_000, SCREEN_HEIGHT))
        self.rect = self.segments[0].rect.union(self.segments[1].rect)
        return []
