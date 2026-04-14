# Boss Battles + UI/UX Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 3-boss rotating battle system (Titan/Barrage/Split) triggered every 5 points, plus UI/UX upgrades across menu, HUD, effects, gameover, settings, and typography.

**Architecture:** New `entities/boss.py` + `systems/boss_manager.py` bolted onto existing `GameState` flow; UI rewrites in `ui/` directory with new `backgrounds.py`, `gameover.py`, `settings.py`, `typography.py`. Match end condition added (first to 11). Save schema extended with `boss_kills` and `settings`.

**Tech Stack:** Python 3, pygame, unittest.

**Spec:** `docs/superpowers/specs/2026-04-14-boss-battles-and-ui-upgrade-design.md`

---

## Task 1: Extend config with palette + match constants

**Files:**
- Modify: `cyberball/config.py`

- [ ] **Step 1: Add match and boss constants**

Append to `cyberball/config.py`:
```python
# Match rules
MATCH_POINT_LIMIT = 11
BOSS_TRIGGER_INTERVAL = 5

# Boss defaults
BOSS_TITAN_HP = 5
BOSS_BARRAGE_HP = 3
BOSS_SPLIT_HP = 2  # per sub-paddle
BOSS_ROTATION = ['titan', 'barrage', 'split']
BOSS_POWERUP_SPAWN_MULTIPLIER = 2.0

# Screen effects
SCREEN_FLASH_MS = 150
SLOWMO_FACTOR = 0.3
SLOWMO_MS = 150
BOSS_BANNER_MS = 500
BOSS_DEFEAT_SLOWMO_MS = 2000

# Palette namespace (tuples re-exported for semantic use)
GOLD = POWERUP_GOLD
ALERT_RED = (220, 40, 40)
VOID_BLACK = BLACK
ACID_GREEN = NEON_GREEN
```

- [ ] **Step 2: Commit**
```bash
git add cyberball/config.py
git commit -m "feat(config): add boss and match constants"
```

---

## Task 2: Extend StatsManager schema for boss_kills and settings

**Files:**
- Modify: `cyberball/systems/stats.py`
- Create: `tests/test_stats_schema.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_stats_schema.py`:
```python
import json
import os
import tempfile
import unittest

from cyberball.systems.stats import StatsManager, DEFAULT_STATS, DEFAULT_SETTINGS


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
```

- [ ] **Step 2: Run test to verify failure**

Run: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest tests.test_stats_schema -v`
Expected: ImportError on `DEFAULT_SETTINGS`.

- [ ] **Step 3: Replace `cyberball/systems/stats.py` with:**

```python
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
        merged = {
            'games_played': loaded.get('games_played', 0),
            'total_hits': loaded.get('total_hits', 0),
            'max_combo': loaded.get('max_combo', 0),
            'powerups_collected': loaded.get('powerups_collected', 0),
            'high_scores': {**DEFAULT_STATS['high_scores'], **loaded.get('high_scores', {})},
            'boss_kills': {**DEFAULT_STATS['boss_kills'], **loaded.get('boss_kills', {})},
            'settings': {**DEFAULT_SETTINGS, **loaded.get('settings', {})},
        }
        return merged

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path) or SAVE_DIR, exist_ok=True)
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
```

- [ ] **Step 4: Run test to verify pass**
Run: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest tests.test_stats_schema -v`
Expected: 5 tests pass.

- [ ] **Step 5: Run full suite to check for regressions**
Run: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest discover tests -v`
Expected: all pass.

- [ ] **Step 6: Commit**
```bash
git add cyberball/systems/stats.py tests/test_stats_schema.py
git commit -m "feat(stats): add boss_kills and settings schema"
```

---

## Task 3: Boss entity classes (Titan/Barrage/Split)

**Files:**
- Create: `cyberball/entities/boss.py`
- Create: `tests/test_boss.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_boss.py`:
```python
import unittest
import pygame
pygame.init()

from cyberball.entities.boss import Boss, Titan, Barrage, Split, BossProjectile


class BossBaseTest(unittest.TestCase):
    def test_titan_initial_hp(self):
        b = Titan(x=900)
        self.assertEqual(b.hp, 5)
        self.assertEqual(b.hp_max, 5)
        self.assertEqual(b.boss_type, 'titan')

    def test_barrage_initial_hp(self):
        b = Barrage(x=900)
        self.assertEqual(b.hp, 3)
        self.assertEqual(b.boss_type, 'barrage')

    def test_split_initial_hp(self):
        b = Split(x=900)
        # Split stores per-paddle HP, total = 4
        self.assertEqual(b.hp, 4)
        self.assertEqual(b.hp_max, 4)
        self.assertEqual(len(b.segments), 2)

    def test_titan_takes_damage(self):
        b = Titan(x=900)
        b.take_damage()
        self.assertEqual(b.hp, 4)
        self.assertFalse(b.is_defeated())

    def test_titan_defeat(self):
        b = Titan(x=900)
        for _ in range(5):
            b.take_damage()
        self.assertTrue(b.is_defeated())

    def test_split_damage_per_segment(self):
        b = Split(x=900)
        b.take_damage_at(0)  # top segment
        b.take_damage_at(0)
        self.assertEqual(b.segments[0].hp, 0)
        self.assertEqual(b.segments[1].hp, 2)
        self.assertFalse(b.is_defeated())
        b.take_damage_at(1)
        b.take_damage_at(1)
        self.assertTrue(b.is_defeated())

    def test_barrage_fires_projectile(self):
        b = Barrage(x=900)
        target_y = 400
        # Advance enough frames to trigger a volley (2.0s = 120 frames at 60fps)
        projectiles = []
        for _ in range(125):
            new = b.update(target_y=target_y)
            projectiles.extend(new)
        self.assertGreaterEqual(len(projectiles), 1)
        self.assertIsInstance(projectiles[0], BossProjectile)


class BossProjectileTest(unittest.TestCase):
    def test_projectile_moves_left(self):
        p = BossProjectile(x=800, y=400, vx=-4, vy=0)
        p.update()
        self.assertLess(p.rect.centerx, 800)


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**
Run: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest tests.test_boss -v`
Expected: ImportError (module doesn't exist).

- [ ] **Step 3: Create `cyberball/entities/boss.py`:**

```python
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
        self.rect = pygame.Rect(int(x) - self.RADIUS, int(y) - self.RADIUS,
                                self.RADIUS * 2, self.RADIUS * 2)
        self.vx = vx
        self.vy = vy

    def update(self):
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)

    def off_screen(self, width):
        return self.rect.right < 0 or self.rect.left > width


class Boss:
    """Base class. Subclasses set hp_max, boss_type, size, and movement."""
    boss_type = 'generic'
    hp_max = 1
    speed_multiplier = 1.0

    def __init__(self, x):
        self.hp = self.hp_max
        self.rect = pygame.Rect(x, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2,
                                PADDLE_WIDTH, PADDLE_HEIGHT)

    def take_damage(self):
        self.hp = max(0, self.hp - 1)

    def is_defeated(self):
        return self.hp <= 0

    def update(self, target_y=None):
        """Return list of new projectiles (empty by default)."""
        if target_y is not None:
            center = self.rect.centery
            diff = target_y - center
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
        self.rect = pygame.Rect(x, SCREEN_HEIGHT // 2 - height // 2,
                                PADDLE_WIDTH, height)


class Barrage(Boss):
    boss_type = 'barrage'
    hp_max = BOSS_BARRAGE_HP
    speed_multiplier = 1.0
    FIRE_INTERVAL_FRAMES = 120  # ~2.0s at 60fps

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
        if target_y is None:
            target_y = self.rect.centery
        projectiles = []
        for offset in (-20, 20):
            px = self.rect.left
            py = self.rect.centery + offset
            projectiles.append(BossProjectile(px, py, vx=-4, vy=0))
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
            SplitSegment(rect=pygame.Rect(x, top_y, PADDLE_WIDTH, seg_height), hp=BOSS_SPLIT_HP),
            SplitSegment(rect=pygame.Rect(x, top_y + seg_height + gap, PADDLE_WIDTH, seg_height), hp=BOSS_SPLIT_HP),
        ]
        # Keep rect pointing at bounding box for collision convenience
        self.rect = self.segments[0].rect.union(self.segments[1].rect)

    def take_damage_at(self, index):
        if 0 <= index < len(self.segments) and self.segments[index].hp > 0:
            self.segments[index].hp -= 1
            self.hp = sum(s.hp for s in self.segments)

    def take_damage(self):
        # Fallback: damage the first alive segment
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
```

- [ ] **Step 4: Run tests to verify pass**
Run: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest tests.test_boss -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**
```bash
git add cyberball/entities/boss.py tests/test_boss.py
git commit -m "feat(boss): add Titan/Barrage/Split boss entities"
```

---

## Task 4: BossManager system

**Files:**
- Create: `cyberball/systems/boss_manager.py`
- Create: `tests/test_boss_manager.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_boss_manager.py`:
```python
import unittest
import pygame
pygame.init()

from cyberball.systems.boss_manager import BossManager
from cyberball.entities.boss import Titan, Barrage, Split


class BossManagerTest(unittest.TestCase):
    def setUp(self):
        self.mgr = BossManager(boss_x=900)

    def test_triggers_boss_at_score_5(self):
        boss = self.mgr.on_player_score(new_player_score=5)
        self.assertIsNotNone(boss)
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
        self.mgr.on_player_score(5)  # Titan
        self.mgr.on_player_lost_point()
        b = self.mgr.on_player_score(10)
        self.assertIsInstance(b, Titan)  # same boss returns

    def test_defeat_reward_score(self):
        self.mgr.on_player_score(5)
        reward = self.mgr.on_boss_defeated()
        self.assertEqual(reward['score_bonus'], 5 * 100)  # Titan hp_max=5
        self.assertIn(reward['powerup_type'], [
            'speed', 'size', 'multi', 'shield', 'gravity', 'slow_time', 'laser'
        ])
        self.assertEqual(reward['boss_type'], 'titan')

    def test_active_flag_lifecycle(self):
        self.assertFalse(self.mgr.active)
        self.mgr.on_player_score(5)
        self.assertTrue(self.mgr.active)
        self.mgr.on_boss_defeated()
        self.assertFalse(self.mgr.active)
        self.mgr.on_player_score(10)
        self.assertTrue(self.mgr.active)
        self.mgr.on_player_lost_point()
        self.assertFalse(self.mgr.active)


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run to verify failure**
Run: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest tests.test_boss_manager -v`
Expected: ImportError.

- [ ] **Step 3: Create `cyberball/systems/boss_manager.py`:**

```python
"""Boss rotation, triggering, defeat rewards."""
import random

from ..config import BOSS_ROTATION, BOSS_TRIGGER_INTERVAL, POWERUP_TYPES
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
        """Call after player scores. Returns boss instance if triggered, else None."""
        if self.active:
            return None
        if new_player_score <= 0:
            return None
        if new_player_score % BOSS_TRIGGER_INTERVAL != 0:
            return None
        boss_type = BOSS_ROTATION[self.rotation_index % len(BOSS_ROTATION)]
        cls = BOSS_CLASSES[boss_type]
        self.current_boss = cls(x=self.boss_x)
        self.active = True
        return self.current_boss

    def on_boss_defeated(self):
        """Returns reward dict. Advances rotation."""
        boss = self.current_boss
        if boss is None:
            return None
        reward = {
            'boss_type': boss.boss_type,
            'score_bonus': boss.hp_max * 100,
            'powerup_type': self.rng.choice(POWERUP_TYPES),
        }
        self.rotation_index = (self.rotation_index + 1) % len(BOSS_ROTATION)
        self.current_boss = None
        self.active = False
        return reward

    def on_player_lost_point(self):
        """Call when AI/boss scores on player. Keeps rotation index."""
        self.current_boss = None
        self.active = False
```

- [ ] **Step 4: Run tests**
Run: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest tests.test_boss_manager -v`
Expected: all pass.

- [ ] **Step 5: Commit**
```bash
git add cyberball/systems/boss_manager.py tests/test_boss_manager.py
git commit -m "feat(boss): add BossManager rotation and rewards"
```

---

## Task 5: ScreenEffect system

**Files:**
- Modify: `cyberball/ui/effects.py`
- Create: `tests/test_screen_effect.py`

- [ ] **Step 1: Read current `cyberball/ui/effects.py` to preserve existing helpers**
Run: `cat cyberball/ui/effects.py`

- [ ] **Step 2: Write failing tests**

Create `tests/test_screen_effect.py`:
```python
import unittest

from cyberball.ui.effects import ScreenEffect


class ScreenEffectTest(unittest.TestCase):
    def test_flash_timer_decrements(self):
        fx = ScreenEffect()
        fx.flash((255, 0, 0), duration_ms=150)
        self.assertTrue(fx.flash_active())
        fx.tick(dt_ms=100)
        self.assertTrue(fx.flash_active())
        fx.tick(dt_ms=100)
        self.assertFalse(fx.flash_active())

    def test_slowmo_factor(self):
        fx = ScreenEffect()
        self.assertEqual(fx.time_scale(), 1.0)
        fx.slowmo(0.3, duration_ms=200)
        self.assertAlmostEqual(fx.time_scale(), 0.3)
        fx.tick(dt_ms=250)
        self.assertEqual(fx.time_scale(), 1.0)

    def test_slowmo_uses_min_factor(self):
        fx = ScreenEffect()
        fx.slowmo(0.5, duration_ms=200)
        fx.slowmo(0.3, duration_ms=200)
        self.assertAlmostEqual(fx.time_scale(), 0.3)

    def test_shake_offset(self):
        fx = ScreenEffect()
        fx.shake(intensity=10, duration_ms=100)
        ox, oy = fx.shake_offset()
        self.assertTrue(-10 <= ox <= 10)
        self.assertTrue(-10 <= oy <= 10)
        fx.tick(dt_ms=150)
        self.assertEqual(fx.shake_offset(), (0, 0))

    def test_vignette_persistent(self):
        fx = ScreenEffect()
        fx.vignette((220, 40, 40), intensity=0.3)
        self.assertTrue(fx.vignette_active())
        fx.tick(dt_ms=10_000)
        self.assertTrue(fx.vignette_active())
        fx.clear_vignette()
        self.assertFalse(fx.vignette_active())

    def test_banner_timer(self):
        fx = ScreenEffect()
        fx.banner("TEST", duration_ms=500)
        self.assertEqual(fx.active_banner(), "TEST")
        fx.tick(dt_ms=600)
        self.assertIsNone(fx.active_banner())


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 3: Run tests to verify failure**
Run: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest tests.test_screen_effect -v`
Expected: ImportError on ScreenEffect.

- [ ] **Step 4: Overwrite `cyberball/ui/effects.py`:**

```python
"""Screen effects: flash, shake, slowmo, vignette, banner + glow helper."""
import random
import pygame


def draw_glow(surface, color, center, radius, intensity=3):
    """Draw radial glow at center. Preserves legacy helper."""
    for i in range(intensity, 0, -1):
        alpha = max(20, 80 // i)
        size = radius + i * 4
        glow = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, alpha), (size, size), size)
        surface.blit(glow, (center[0] - size, center[1] - size))


class ScreenEffect:
    def __init__(self):
        self._flash_color = None
        self._flash_remaining_ms = 0
        self._flash_total_ms = 0

        self._slowmo_factor = 1.0
        self._slowmo_remaining_ms = 0

        self._shake_intensity = 0
        self._shake_remaining_ms = 0

        self._vignette_color = None
        self._vignette_intensity = 0.0

        self._banner_text = None
        self._banner_remaining_ms = 0
        self._banner_total_ms = 0

    # Public API
    def flash(self, color, duration_ms):
        self._flash_color = color
        self._flash_remaining_ms = duration_ms
        self._flash_total_ms = max(1, duration_ms)

    def slowmo(self, factor, duration_ms):
        # Minimum of currently active factor and new factor
        if self._slowmo_remaining_ms > 0:
            self._slowmo_factor = min(self._slowmo_factor, factor)
        else:
            self._slowmo_factor = factor
        self._slowmo_remaining_ms = max(self._slowmo_remaining_ms, duration_ms)

    def shake(self, intensity, duration_ms):
        self._shake_intensity = max(self._shake_intensity, intensity)
        self._shake_remaining_ms = max(self._shake_remaining_ms, duration_ms)

    def vignette(self, color, intensity):
        self._vignette_color = color
        self._vignette_intensity = intensity

    def clear_vignette(self):
        self._vignette_color = None
        self._vignette_intensity = 0.0

    def banner(self, text, duration_ms):
        self._banner_text = text
        self._banner_remaining_ms = duration_ms
        self._banner_total_ms = max(1, duration_ms)

    # Queries
    def time_scale(self):
        return self._slowmo_factor if self._slowmo_remaining_ms > 0 else 1.0

    def flash_active(self):
        return self._flash_remaining_ms > 0

    def flash_alpha(self):
        if not self.flash_active():
            return 0
        return int(180 * (self._flash_remaining_ms / self._flash_total_ms))

    def flash_color(self):
        return self._flash_color

    def shake_offset(self):
        if self._shake_remaining_ms <= 0 or self._shake_intensity <= 0:
            return (0, 0)
        return (
            random.randint(-self._shake_intensity, self._shake_intensity),
            random.randint(-self._shake_intensity, self._shake_intensity),
        )

    def vignette_active(self):
        return self._vignette_color is not None

    def vignette_params(self):
        return self._vignette_color, self._vignette_intensity

    def active_banner(self):
        return self._banner_text if self._banner_remaining_ms > 0 else None

    def banner_progress(self):
        if self._banner_remaining_ms <= 0:
            return 1.0
        return 1.0 - (self._banner_remaining_ms / self._banner_total_ms)

    # Tick
    def tick(self, dt_ms):
        self._flash_remaining_ms = max(0, self._flash_remaining_ms - dt_ms)
        self._slowmo_remaining_ms = max(0, self._slowmo_remaining_ms - dt_ms)
        if self._slowmo_remaining_ms == 0:
            self._slowmo_factor = 1.0
        self._shake_remaining_ms = max(0, self._shake_remaining_ms - dt_ms)
        if self._shake_remaining_ms == 0:
            self._shake_intensity = 0
        self._banner_remaining_ms = max(0, self._banner_remaining_ms - dt_ms)
        if self._banner_remaining_ms == 0:
            self._banner_text = None

    # Rendering helpers
    def render_overlays(self, surface):
        if self.flash_active():
            alpha = self.flash_alpha()
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((*self._flash_color, alpha))
            surface.blit(overlay, (0, 0))
        if self.vignette_active():
            color, intensity = self.vignette_params()
            w, h = surface.get_size()
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            alpha = int(180 * intensity)
            border = 80
            pygame.draw.rect(overlay, (*color, alpha), (0, 0, w, border))
            pygame.draw.rect(overlay, (*color, alpha), (0, h - border, w, border))
            pygame.draw.rect(overlay, (*color, alpha), (0, 0, border, h))
            pygame.draw.rect(overlay, (*color, alpha), (w - border, 0, border, h))
            surface.blit(overlay, (0, 0))
        banner = self.active_banner()
        if banner:
            font = pygame.font.Font(None, 72)
            text_surf = font.render(banner, True, (255, 40, 80))
            rect = text_surf.get_rect(center=(surface.get_width() // 2, 120))
            pygame.draw.rect(surface, (0, 0, 0),
                             rect.inflate(40, 20))
            surface.blit(text_surf, rect)
```

- [ ] **Step 5: Run tests**
Run: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest tests.test_screen_effect -v`
Expected: all pass.

- [ ] **Step 6: Run full suite**
Run: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest discover tests -v`
Expected: all pass (legacy `draw_glow` preserved).

- [ ] **Step 7: Commit**
```bash
git add cyberball/ui/effects.py tests/test_screen_effect.py
git commit -m "feat(ui): add ScreenEffect system (flash/slowmo/shake/vignette/banner)"
```

---

## Task 6: Typography module + palette refs

**Files:**
- Create: `cyberball/ui/typography.py`

- [ ] **Step 1: Create `cyberball/ui/typography.py`:**

```python
"""Centralized font sizes for UI consistency."""
import pygame

_cached = {}

SIZES = {
    'title': 72,
    'heading': 36,
    'body': 20,
    'small': 14,
}


def get(name):
    if not pygame.font.get_init():
        pygame.font.init()
    size = SIZES.get(name, SIZES['body'])
    if name not in _cached:
        _cached[name] = pygame.font.Font(None, size)
    return _cached[name]


def title():
    return get('title')


def heading():
    return get('heading')


def body():
    return get('body')


def small():
    return get('small')
```

- [ ] **Step 2: Commit**
```bash
git add cyberball/ui/typography.py
git commit -m "feat(ui): add typography module"
```

---

## Task 7: MatchStats for per-match tracking + GameOver screen

**Files:**
- Create: `cyberball/ui/gameover.py`
- Create: `tests/test_match_stats.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_match_stats.py`:
```python
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

    def test_duration_seconds_rounds(self):
        m = MatchStats()
        m.start_ms = 1_000
        self.assertEqual(m.duration_seconds(now_ms=6_500), 5)


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run to verify failure**
Run: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest tests.test_match_stats -v`
Expected: ImportError.

- [ ] **Step 3: Create `cyberball/ui/gameover.py`:**

```python
"""Per-match stats tracking and game over screen."""
import pygame

from . import typography
from ..config import SCREEN_WIDTH, SCREEN_HEIGHT, CYBER_BLUE, NEON_PINK, BRIGHT_WHITE, GOLD


class MatchStats:
    def __init__(self):
        self.hits = 0
        self.max_combo = 0
        self.boss_kills = 0
        self.powerups_picked = 0
        self.start_ms = 0
        self.end_ms = 0

    def start(self, now_ms):
        self.start_ms = now_ms

    def stop(self, now_ms):
        self.end_ms = now_ms

    def record_hit(self, combo):
        self.hits += 1
        if combo > self.max_combo:
            self.max_combo = combo

    def record_boss_kill(self):
        self.boss_kills += 1

    def record_powerup(self):
        self.powerups_picked += 1

    def duration_seconds(self, now_ms=None):
        end = self.end_ms or now_ms or 0
        return max(0, (end - self.start_ms) // 1000)


def draw_game_over(surface, winner_label, player_score, ai_score, stats: MatchStats, now_ms=None):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    surface.blit(overlay, (0, 0))

    title_font = typography.title()
    body_font = typography.body()
    heading_font = typography.heading()

    title = title_font.render(f"{winner_label} WINS", True, GOLD)
    surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 140)))

    score_text = heading_font.render(f"{player_score}  :  {ai_score}", True, BRIGHT_WHITE)
    surface.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH // 2, 230)))

    lines = [
        f"Max Combo:       {stats.max_combo}",
        f"Boss Kills:      {stats.boss_kills}",
        f"Powerups Picked: {stats.powerups_picked}",
        f"Total Hits:      {stats.hits}",
        f"Match Time:      {stats.duration_seconds(now_ms)}s",
    ]
    y = 310
    for line in lines:
        surf = body_font.render(line, True, CYBER_BLUE)
        surface.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, y)))
        y += 36

    hint = body_font.render("Press R to restart   /   ESC for menu", True, NEON_PINK)
    surface.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)))
```

- [ ] **Step 4: Run tests**
Run: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest tests.test_match_stats -v`
Expected: pass.

- [ ] **Step 5: Commit**
```bash
git add cyberball/ui/gameover.py tests/test_match_stats.py
git commit -m "feat(ui): add MatchStats and game over screen"
```

---

## Task 8: Settings screen

**Files:**
- Create: `cyberball/ui/settings.py`

- [ ] **Step 1: Create `cyberball/ui/settings.py`:**

```python
"""Settings screen: adjust volume, colorblind, mode, slowmo, shake intensity."""
import pygame

from . import typography
from ..config import SCREEN_WIDTH, SCREEN_HEIGHT, CYBER_BLUE, NEON_PINK, BRIGHT_WHITE, DIM_GRAY


SHAKE_OPTIONS = ['off', 'low', 'medium', 'high']
MODE_OPTIONS = ['1P', '2P']


class SettingsScreen:
    """Stateful settings UI. Uses StatsManager as backing store."""
    ITEMS = [
        ('volume', 'Volume', 'int'),
        ('colorblind', 'Colorblind palette', 'bool'),
        ('mode', 'Mode', 'mode'),
        ('slowmo_enabled', 'Slow-mo FX', 'bool'),
        ('shake_intensity', 'Shake intensity', 'shake'),
    ]

    def __init__(self, stats):
        self.stats = stats
        self.cursor = 0

    def handle_key(self, key):
        """Returns True if ESC pressed (exit signal)."""
        if key == pygame.K_ESCAPE:
            self.stats.save()
            return True
        if key in (pygame.K_UP, pygame.K_w):
            self.cursor = (self.cursor - 1) % len(self.ITEMS)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.cursor = (self.cursor + 1) % len(self.ITEMS)
        elif key in (pygame.K_LEFT, pygame.K_a):
            self._adjust(-1)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self._adjust(+1)
        return False

    def _adjust(self, direction):
        key, _label, kind = self.ITEMS[self.cursor]
        current = self.stats.get_setting(key)
        if kind == 'int':
            new = max(0, min(100, current + direction * 5))
            self.stats.update_setting(key, new)
        elif kind == 'bool':
            self.stats.update_setting(key, not current)
        elif kind == 'mode':
            idx = (MODE_OPTIONS.index(current) + direction) % len(MODE_OPTIONS)
            self.stats.update_setting(key, MODE_OPTIONS[idx])
        elif kind == 'shake':
            idx = (SHAKE_OPTIONS.index(current) + direction) % len(SHAKE_OPTIONS)
            self.stats.update_setting(key, SHAKE_OPTIONS[idx])

    def draw(self, surface):
        surface.fill((0, 0, 0))
        title = typography.title().render("SETTINGS", True, CYBER_BLUE)
        surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 100)))

        body = typography.body()
        y = 220
        for i, (key, label, _kind) in enumerate(self.ITEMS):
            value = self.stats.get_setting(key)
            color = NEON_PINK if i == self.cursor else BRIGHT_WHITE
            label_surf = body.render(f"{label}", True, color)
            value_surf = body.render(f"< {value} >", True, color)
            surface.blit(label_surf, (SCREEN_WIDTH // 2 - 260, y))
            surface.blit(value_surf, (SCREEN_WIDTH // 2 + 80, y))
            y += 50

        hint = body.render("UP/DOWN select · LEFT/RIGHT adjust · ESC save & exit", True, DIM_GRAY)
        surface.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60)))
```

- [ ] **Step 2: Commit**
```bash
git add cyberball/ui/settings.py
git commit -m "feat(ui): add settings screen"
```

---

## Task 9: Menu card layout + demo background

**Files:**
- Create: `cyberball/ui/backgrounds.py`
- Modify: `cyberball/ui/menu.py` (full rewrite)

- [ ] **Step 1: Read current `cyberball/ui/menu.py` to understand existing function signatures**
Run: `cat cyberball/ui/menu.py`

- [ ] **Step 2: Create `cyberball/ui/backgrounds.py`:**

```python
"""Animated background for menu — auto-rally demo."""
import random
import pygame

from ..config import SCREEN_WIDTH, SCREEN_HEIGHT, DIM_GRAY, CYBER_BLUE, NEON_PINK


class MenuDemo:
    def __init__(self):
        self.ball = pygame.Rect(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 18, 18)
        self.bvx = random.choice([-5, 5])
        self.bvy = random.choice([-3, 3])
        self.left = pygame.Rect(40, SCREEN_HEIGHT // 2 - 60, 16, 120)
        self.right = pygame.Rect(SCREEN_WIDTH - 56, SCREEN_HEIGHT // 2 - 60, 16, 120)

    def update(self):
        self.ball.x += self.bvx
        self.ball.y += self.bvy
        if self.ball.top <= 0 or self.ball.bottom >= SCREEN_HEIGHT:
            self.bvy = -self.bvy
        if self.ball.colliderect(self.left) or self.ball.colliderect(self.right):
            self.bvx = -self.bvx
        if self.ball.left < 0 or self.ball.right > SCREEN_WIDTH:
            self.ball.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            self.bvx = random.choice([-5, 5])
        # Track ball
        for paddle in (self.left, self.right):
            if paddle.centery < self.ball.centery:
                paddle.y += 3
            elif paddle.centery > self.ball.centery:
                paddle.y -= 3
            paddle.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

    def draw(self, surface):
        pygame.draw.rect(surface, CYBER_BLUE, self.left)
        pygame.draw.rect(surface, NEON_PINK, self.right)
        pygame.draw.rect(surface, DIM_GRAY, self.ball)
        dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 128))
        surface.blit(dim, (0, 0))
```

- [ ] **Step 3: Overwrite `cyberball/ui/menu.py`:**

```python
"""Main menu — card-based difficulty select with animated background."""
import random
import pygame

from . import typography
from .backgrounds import MenuDemo
from ..config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    DIFFICULTIES,
    CYBER_BLUE,
    NEON_PINK,
    NEON_GREEN,
    POWERUP_GOLD,
    ELECTRIC_PURPLE,
    BRIGHT_WHITE,
    DIM_GRAY,
)


DIFFICULTY_COLORS = {
    'easy': NEON_GREEN,
    'medium': CYBER_BLUE,
    'hard': NEON_PINK,
    'extreme': ELECTRIC_PURPLE,
}

DIFFICULTY_FLAVOR = {
    'easy': "Sleepy AI",
    'medium': "Awake AI",
    'hard': "Predicts future",
    'extreme': "Sentient AI",
}


class Menu:
    def __init__(self, stats):
        self.stats = stats
        self.demo = MenuDemo()
        self.glitch_frame = 0

    def update(self):
        self.demo.update()
        self.glitch_frame = (self.glitch_frame + 1) % 60

    def draw(self, surface):
        surface.fill((0, 0, 0))
        self.demo.draw(surface)

        title_font = typography.title()
        title_text = "CYBERBALL 2084"
        # Glitch offset
        ox = random.randint(-2, 2) if self.glitch_frame < 4 else 0
        title = title_font.render(title_text, True, NEON_PINK)
        surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2 + ox, 80)))

        subtitle = typography.body().render(
            "Choose your doom · Press 1 / 2 / 3 / 4", True, CYBER_BLUE
        )
        surface.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, 150)))

        self._draw_cards(surface)
        self._draw_hints(surface)

    def _draw_cards(self, surface):
        n = len(DIFFICULTIES)
        card_w = 180
        card_h = 240
        gap = 30
        total = n * card_w + (n - 1) * gap
        start_x = (SCREEN_WIDTH - total) // 2
        y = SCREEN_HEIGHT // 2 - card_h // 2 + 30
        body_font = typography.body()
        heading_font = typography.heading()
        small_font = typography.small()
        for i, diff in enumerate(DIFFICULTIES):
            x = start_x + i * (card_w + gap)
            color = DIFFICULTY_COLORS[diff]
            rect = pygame.Rect(x, y, card_w, card_h)
            pygame.draw.rect(surface, (10, 10, 20), rect)
            pygame.draw.rect(surface, color, rect, 3)
            num = heading_font.render(str(i + 1), True, color)
            surface.blit(num, (x + 16, y + 12))
            name = heading_font.render(diff.upper(), True, BRIGHT_WHITE)
            surface.blit(name, name.get_rect(center=(x + card_w // 2, y + 90)))
            flavor = body_font.render(DIFFICULTY_FLAVOR[diff], True, color)
            surface.blit(flavor, flavor.get_rect(center=(x + card_w // 2, y + 140)))
            high = self.stats.high_score(diff)
            hs = small_font.render(f"HIGH {high}", True, DIM_GRAY)
            surface.blit(hs, hs.get_rect(center=(x + card_w // 2, y + card_h - 30)))
            # Color bar
            pygame.draw.rect(surface, color, (x + 10, y + card_h - 14, card_w - 20, 4))

    def _draw_hints(self, surface):
        small = typography.small()
        hints = [
            "O: Settings",
            "SPACE: Start (currently selected difficulty)",
            "ESC: Quit",
        ]
        y = SCREEN_HEIGHT - 60
        for h in hints:
            surf = small.render(h, True, DIM_GRAY)
            surface.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, y)))
            y += 18
```

- [ ] **Step 4: Run full suite**
Run: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest discover tests -v`
Expected: all tests pass (menu has no tests, but import must not break).

- [ ] **Step 5: Commit**
```bash
git add cyberball/ui/menu.py cyberball/ui/backgrounds.py
git commit -m "feat(ui): redesign menu with cards and demo background"
```

---

## Task 10: HUD extension — combo ring + boss HP bar + powerup bars

**Files:**
- Modify: `cyberball/ui/hud.py` (full rewrite)

- [ ] **Step 1: Read current `cyberball/ui/hud.py` for signature reference**
Run: `cat cyberball/ui/hud.py`

- [ ] **Step 2: Overwrite `cyberball/ui/hud.py`:**

```python
"""In-game HUD: score, combo ring, powerup timer bars, boss HP."""
import math
import pygame

from . import typography
from ..config import (
    SCREEN_WIDTH,
    BRIGHT_WHITE,
    CYBER_BLUE,
    NEON_PINK,
    POWERUP_GOLD,
    DIM_GRAY,
    ALERT_RED,
)


POWERUP_ICON_COLORS = {
    'speed': POWERUP_GOLD,
    'size': (255, 80, 80),
    'multi': (80, 120, 255),
    'shield': (80, 255, 80),
    'gravity': (180, 80, 255),
    'slow_time': (80, 255, 255),
    'laser': (255, 80, 200),
}


def draw_score(surface, player_score, ai_score, multiplier=1.0):
    font = typography.title()
    color = POWERUP_GOLD if multiplier >= 1.5 else BRIGHT_WHITE
    p = font.render(str(player_score), True, color)
    a = font.render(str(ai_score), True, color)
    surface.blit(p, p.get_rect(center=(SCREEN_WIDTH // 4 * 3, 60)))
    surface.blit(a, a.get_rect(center=(SCREEN_WIDTH // 4, 60)))


def draw_combo_ring(surface, combo, time_since_hit_ms, timeout_ms=2000,
                    center=(SCREEN_WIDTH // 2, 80)):
    if combo < 2:
        return
    radius = 36
    width = 5
    fraction = max(0.0, 1.0 - (time_since_hit_ms / timeout_ms))
    tier_color = BRIGHT_WHITE
    multiplier = 1.0
    if combo >= 10:
        tier_color = POWERUP_GOLD
        multiplier = 3.0
    elif combo >= 5:
        tier_color = NEON_PINK
        multiplier = 2.0
    elif combo >= 3:
        tier_color = CYBER_BLUE
        multiplier = 1.5
    pygame.draw.circle(surface, DIM_GRAY, center, radius, width)
    end_angle = -math.pi / 2 + 2 * math.pi * fraction
    # Arc approximation via line segments
    segments = 48
    pts = []
    for i in range(segments + 1):
        t = i / segments
        if t > fraction:
            break
        ang = -math.pi / 2 + 2 * math.pi * t
        pts.append((center[0] + radius * math.cos(ang),
                    center[1] + radius * math.sin(ang)))
    if len(pts) >= 2:
        pygame.draw.lines(surface, tier_color, False, pts, width)
    body = typography.body()
    num = body.render(f"x{combo}", True, tier_color)
    surface.blit(num, num.get_rect(center=center))
    mlabel = typography.small().render(f"{multiplier:g}x", True, tier_color)
    surface.blit(mlabel, mlabel.get_rect(center=(center[0], center[1] + radius + 12)))


def draw_powerup_bars(surface, active_powerups, x=10, y=150):
    """active_powerups: list of dicts with keys: type, remaining_frames, total_frames."""
    body = typography.small()
    row_h = 22
    for i, pu in enumerate(active_powerups):
        yy = y + i * row_h
        color = POWERUP_ICON_COLORS.get(pu['type'], BRIGHT_WHITE)
        # Icon
        pygame.draw.rect(surface, color, (x, yy + 4, 14, 14))
        # Bar
        total = max(1, pu['total_frames'])
        frac = max(0.0, pu['remaining_frames'] / total)
        pygame.draw.rect(surface, DIM_GRAY, (x + 22, yy + 6, 60, 10))
        pygame.draw.rect(surface, color, (x + 22, yy + 6, int(60 * frac), 10))
        # Seconds
        secs = max(0, pu['remaining_frames'] // 60)
        label = body.render(f"{pu['type']} {secs}s", True, color)
        surface.blit(label, (x + 90, yy + 3))


def draw_boss_hp_bar(surface, boss):
    if boss is None:
        return
    center_x = SCREEN_WIDTH // 2
    y = 25
    body = typography.body()
    name = body.render(f"BOSS: {boss.boss_type.upper()}", True, ALERT_RED)
    surface.blit(name, name.get_rect(center=(center_x, y - 4)))
    bar_w = 420
    bar_h = 18
    bar_x = center_x - bar_w // 2
    bar_y = y + 20
    pygame.draw.rect(surface, (40, 10, 10), (bar_x, bar_y, bar_w, bar_h))
    if hasattr(boss, 'segments'):
        total = boss.hp_max
        seg_w = bar_w // max(1, total)
        filled = sum(seg.hp for seg in boss.segments)
        for i in range(filled):
            pygame.draw.rect(surface, ALERT_RED,
                             (bar_x + i * seg_w + 1, bar_y + 1, seg_w - 2, bar_h - 2))
    else:
        frac = boss.hp / max(1, boss.hp_max)
        pygame.draw.rect(surface, ALERT_RED,
                         (bar_x + 1, bar_y + 1, int((bar_w - 2) * frac), bar_h - 2))
    pygame.draw.rect(surface, BRIGHT_WHITE, (bar_x, bar_y, bar_w, bar_h), 2)
```

- [ ] **Step 3: Run full suite (HUD has no direct tests, ensure imports still work)**
Run: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest discover tests -v`
Expected: all pass.

- [ ] **Step 4: Commit**
```bash
git add cyberball/ui/hud.py
git commit -m "feat(ui): upgrade HUD with combo ring, powerup bars, boss HP"
```

---

## Task 11: Wire boss + screen effects + gameover + settings into GameState/main loop

**Files:**
- Modify: `cyberball/game.py` (significant)

- [ ] **Step 1: Read current `cyberball/game.py` in full**
Run: `cat cyberball/game.py`

- [ ] **Step 2: Modify `cyberball/game.py` to integrate all new systems**

Key integration points (apply these changes; preserve existing logic):

1. **Imports:** add
```python
from .systems.boss_manager import BossManager
from .entities.boss import Split, BossProjectile
from .ui.effects import ScreenEffect
from .ui.gameover import MatchStats, draw_game_over
from .ui.settings import SettingsScreen
from .ui import hud as hud_module
from .config import (
    MATCH_POINT_LIMIT,
    BOSS_POWERUP_SPAWN_MULTIPLIER,
    SCREEN_FLASH_MS,
    SLOWMO_FACTOR,
    SLOWMO_MS,
    BOSS_BANNER_MS,
    BOSS_DEFEAT_SLOWMO_MS,
    ALERT_RED,
    POWERUP_SPAWN_CHANCE,
)
```

2. **GameState __init__:** add fields
```python
self.boss_manager = BossManager(boss_x=80)  # AI is on the left side
self.boss_projectiles = []
self.screen_effect = ScreenEffect()
self.match_stats = MatchStats()
self.match_stats.start(pygame.time.get_ticks())
self.state = 'menu'   # 'menu', 'playing', 'settings', 'gameover', 'paused'
self.game_over_winner = None
self.settings_screen = None  # lazy-init with stats
self.time_since_hit_ms = 999_999
```

3. **Score handler (whatever function currently processes a score):** dispatch to boss manager
```python
def on_player_score(self):
    self.player_score += 1
    self.screen_effect.flash((255, 255, 255), SCREEN_FLASH_MS)
    self.screen_effect.slowmo(SLOWMO_FACTOR, SLOWMO_MS)
    if self.player_score >= MATCH_POINT_LIMIT:
        self._end_match(winner='PLAYER')
        return
    boss = self.boss_manager.on_player_score(self.player_score)
    if boss is not None:
        self.screen_effect.banner("⚠ BOSS INCOMING", BOSS_BANNER_MS)
        self.screen_effect.vignette(ALERT_RED, 0.3)

def on_ai_score(self):
    self.ai_score += 1
    self.screen_effect.flash((255, 60, 60), SCREEN_FLASH_MS)
    self.screen_effect.slowmo(SLOWMO_FACTOR, SLOWMO_MS)
    if self.boss_manager.active:
        self.boss_manager.on_player_lost_point()
        self.screen_effect.clear_vignette()
    if self.ai_score >= MATCH_POINT_LIMIT:
        self._end_match(winner='AI')

def _end_match(self, winner):
    self.game_over_winner = winner
    self.state = 'gameover'
    self.match_stats.stop(pygame.time.get_ticks())
    self.stats.record_game_end(self.difficulty,
                               max(self.player_score, self.ai_score))
```

4. **Collision — ball vs boss paddle:** replace AI paddle collision block with:
```python
if self.boss_manager.active:
    boss = self.boss_manager.current_boss
    if isinstance(boss, Split):
        for i, seg in enumerate(boss.segments):
            if seg.hp > 0 and ball.rect.colliderect(seg.rect):
                ball.reflect_x()
                boss.take_damage_at(i)
                self._on_boss_hit(boss)
                break
    else:
        if ball.rect.colliderect(boss.rect):
            ball.reflect_x()
            boss.take_damage()
            self._on_boss_hit(boss)
else:
    # existing AI paddle collision
    ...
```

5. **Boss defeat reward:**
```python
def _on_boss_hit(self, boss):
    if boss.is_defeated():
        reward = self.boss_manager.on_boss_defeated()
        if reward:
            self.player_score_bonus = reward['score_bonus']
            self.player_score += 0  # score bonus applied via match_stats display
            # Apply actual score bonus (not crossing 11-point limit check):
            self._add_score_bonus(reward['score_bonus'])
            self._activate_powerup_for_player(reward['powerup_type'], frames=180)
            self.stats.record_boss_kill(reward['boss_type'])
            self.match_stats.record_boss_kill()
            self.screen_effect.slowmo(0.4, BOSS_DEFEAT_SLOWMO_MS)
            self.screen_effect.clear_vignette()

def _add_score_bonus(self, bonus):
    # Bonus does not trigger additional boss spawn
    self.player_score += bonus
    if self.player_score >= MATCH_POINT_LIMIT:
        self._end_match('PLAYER')
```

Note: the `bonus` crossing the threshold still ends the match — desired behavior per spec.

**Adjustment:** because `_add_score_bonus` might push score past a boss-trigger multiple, skip further boss triggers (already handled since `boss_manager.active=False` after defeat, and bonus doesn't call `on_player_score`).

6. **Boss projectiles update:**
```python
def _update_boss(self):
    if not self.boss_manager.active:
        return
    boss = self.boss_manager.current_boss
    new_projectiles = boss.update(target_y=self.player_paddle.rect.centery)
    self.boss_projectiles.extend(new_projectiles[:4 - len(self.boss_projectiles)])
    alive = []
    for p in self.boss_projectiles:
        p.update()
        if p.off_screen(SCREEN_WIDTH):
            continue
        if p.rect.colliderect(self.player_paddle.rect):
            self.combo = 0
            continue
        alive.append(p)
    self.boss_projectiles = alive[:4]
```

7. **Powerup spawn rate:**
Where `POWERUP_SPAWN_CHANCE` is used in the random check:
```python
spawn_chance = POWERUP_SPAWN_CHANCE
if self.boss_manager.active:
    spawn_chance *= BOSS_POWERUP_SPAWN_MULTIPLIER
if random.random() < spawn_chance:
    ...
```

8. **Event handling (menu/settings/gameover branches):**
```python
# In menu event loop:
elif event.key == pygame.K_o:
    self.settings_screen = SettingsScreen(self.stats)
    self.state = 'settings'
# In settings:
if self.state == 'settings' and event.type == pygame.KEYDOWN:
    if self.settings_screen.handle_key(event.key):
        self.state = 'menu'
# In gameover:
if self.state == 'gameover' and event.type == pygame.KEYDOWN:
    if event.key == pygame.K_r:
        self._reset_match()
        self.state = 'playing'
    elif event.key == pygame.K_ESCAPE:
        self.state = 'menu'
```

9. **Draw dispatch:**
```python
if self.state == 'menu':
    self.menu.update()
    self.menu.draw(self.screen)
elif self.state == 'settings':
    self.settings_screen.draw(self.screen)
elif self.state == 'gameover':
    self._draw_play_frame()  # draw frozen game behind overlay
    draw_game_over(self.screen, self.game_over_winner,
                   self.player_score, self.ai_score,
                   self.match_stats, now_ms=pygame.time.get_ticks())
else:  # playing
    self._draw_play_frame()
    hud_module.draw_score(self.screen, self.player_score, self.ai_score,
                          multiplier=self._current_multiplier())
    hud_module.draw_combo_ring(self.screen, self.combo, self.time_since_hit_ms)
    hud_module.draw_powerup_bars(self.screen, self._active_powerups_for_hud())
    if self.boss_manager.active:
        hud_module.draw_boss_hp_bar(self.screen, self.boss_manager.current_boss)
    self.screen_effect.render_overlays(self.screen)
```

10. **Time scale for game updates (slowmo):**
Wrap physics update with:
```python
dt_ms = clock.get_time()
self.screen_effect.tick(dt_ms)
self.time_since_hit_ms += dt_ms
time_scale = self.screen_effect.time_scale()
# Use time_scale to scale ball movement, boss updates:
self._physics_step(time_scale)
```

11. **Reset match:** `_reset_match` should re-init `match_stats`, reset scores, reset `boss_manager = BossManager(...)`.

- [ ] **Step 3: Run full test suite**
Run: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest discover tests -v`
Expected: existing tests still pass.

- [ ] **Step 4: Smoke-test manually**
Run: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy timeout 3 python main.py || true`
Expected: no crash on init/menu; exits cleanly.

- [ ] **Step 5: Commit**
```bash
git add cyberball/game.py
git commit -m "feat(game): wire boss battles, screen effects, gameover, settings into main loop"
```

---

## Task 12: Smoke test — full flow

**Files:**
- Modify: `tests/test_smoke.py` (append new test)

- [ ] **Step 1: Append to `tests/test_smoke.py`:**

```python
class BossFlowSmokeTest(unittest.TestCase):
    def test_boss_trigger_and_defeat(self):
        from cyberball.systems.boss_manager import BossManager
        from cyberball.entities.boss import Titan
        mgr = BossManager(boss_x=80)
        boss = mgr.on_player_score(5)
        self.assertIsInstance(boss, Titan)
        for _ in range(5):
            boss.take_damage()
        self.assertTrue(boss.is_defeated())
        reward = mgr.on_boss_defeated()
        self.assertEqual(reward['boss_type'], 'titan')
        self.assertEqual(reward['score_bonus'], 500)
        # Next boss should be Barrage
        from cyberball.entities.boss import Barrage
        b2 = mgr.on_player_score(10)
        self.assertIsInstance(b2, Barrage)
```

- [ ] **Step 2: Run full suite**
Run: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest discover tests -v`
Expected: all pass.

- [ ] **Step 3: Commit**
```bash
git add tests/test_smoke.py
git commit -m "test: add boss flow smoke test"
```

---

## Task 13: Update README + push

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README — add v4 section describing boss battles + UI upgrade**

Insert a new section `## v4: Boss Battles + UI/UX Overhaul` after the v2 section (line ~15), summarizing:
- 3 rotating bosses triggered every 5 points
- Match-to-11 rule, game over screen with stats
- Settings screen (`O` from menu)
- New screen effects: slow-mo, flash, vignette, boss banner

Also append to "This is 2026-04-14 Claude" section a note: "v4 boss battles + UI overhaul".

- [ ] **Step 2: Commit and push**

```bash
git add README.md
git commit -m "docs: add v4 boss battles + UI overhaul notes"
git push origin main
```

---

## Self-Review Checklist

- [x] Every spec section has at least one task
- [x] No `TBD`/`TODO`/placeholder content
- [x] Type names consistent (`BossManager`, `ScreenEffect`, `MatchStats`, `SettingsScreen`)
- [x] Test files path-consistent (`tests/test_*.py`)
- [x] `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy` used for every test invocation
- [x] Backwards-compat covered (`StatsManager` old save load test)
- [x] Match end at 11 points, game over screen wired
