# Boss Battles + UI/UX Upgrade — Design Spec

**Date:** 2026-04-14
**Status:** Approved, pending implementation plan

## Goals

1. Add boss encounters triggered every 5 player points, with 3 rotating boss types.
2. Upgrade UI/UX across menu, HUD, feedback, game over, settings, and typography.
3. Preserve existing gameplay (7 powerups, combos, 4 AI difficulties, 2P mode, persistent stats).

## Non-Goals

- Online leaderboards / replays
- Achievement system (reserved for a later spec)
- VR / external integrations

---

## Part A — Boss Battles

### A.1 Trigger

- Trigger condition: player score reaches a multiple of 5 (5, 10, 15, ...).
- On trigger, the AI paddle is replaced by a `Boss` entity until the boss is defeated or the player loses a point.
- 2P mode: boss system is **disabled** (bosses replace the AI paddle, which doesn't exist in 2P).

### A.2 Boss Rotation

Three boss types rotate in fixed order: `Titan → Barrage → Split → Titan → ...`

A `boss_rotation_index` is stored in `GameState` and advanced **only on successful defeat**. If the player loses a point while a boss is active, the boss exits and the **same** boss returns at the next 5-point threshold.

| Index | Type    | Role         | HP | Paddle Size | Speed (vs default) | Ability |
|-------|---------|--------------|----|-------------|--------------------|---------|
| 0     | Titan   | Tank         | 5  | 2.5× height | 0.55×              | None |
| 1     | Barrage | Ranged       | 3  | 1.0×        | 1.0×               | Fires 2 slow projectiles every 2.0s toward player paddle; projectiles cost 1 combo on hit |
| 2     | Split   | Dual-entity  | 2+2 | 0.6× each  | 1.1× each          | Two independent paddles stacked vertically, each with own HP; must destroy both |

### A.3 Boss Combat Rules

- Ball hitting the boss paddle → boss HP -1 + ball reflects normally.
- `Split` boss: each sub-paddle tracks its own HP; destroying one leaves the other active.
- `Barrage` projectiles: if they hit the player paddle, combo resets (no life loss); if player paddle misses them, they pass through (no effect).
- Powerup spawn rate doubles during boss fight (`PowerUp.SPAWN_INTERVAL` × 0.5).
- Combo chain persists and accumulates normally; multipliers apply to boss damage score.

### A.4 Defeat Reward

On boss HP reaching 0:

1. Score += `hp_max × 100` (Titan=500, Barrage=300, Split=400).
2. A random powerup is auto-activated on the player for 3 seconds (chosen uniformly from the 7 types).
3. `boss_rotation_index` advances (mod 3).
4. Normal AI paddle restored.
5. Stats: `stats.boss_kills[boss_type]` incremented in `save.json`.

### A.5 Boss Defeat by Player Point Loss

If the AI boss (or Barrage projectile) scores against the player:

- Boss exits immediately, AI paddle restored.
- `boss_rotation_index` **unchanged**.
- Same boss returns at next multiple-of-5 threshold.

### A.6 Files

- `cyberball/entities/boss.py` — `Boss` base + `Titan`, `Barrage`, `Split` subclasses. Includes `Projectile` helper for Barrage.
- `cyberball/systems/boss_manager.py` — `BossManager` class: handles trigger detection, spawning, defeat events, rotation advancement.
- `cyberball/game.py` — `GameState` gains `current_boss`, `boss_rotation_index`, `boss_manager` fields; scoring code dispatches to `BossManager.on_player_score()`.
- `cyberball/systems/stats.py` — extended schema: `boss_kills: {titan: int, barrage: int, split: int}`.

---

## Part B — UI/UX Upgrade

### B.1 Main Menu (`ui/menu.py` + `ui/backgrounds.py` [new])

- **Card layout:** 4 difficulty cards arranged horizontally, each with title, flavor tagline, difficulty color bar, hint text ("Press 1/2/3/4"). Selected card highlighted with glow.
- **Animated background:** demo rally — 2 auto-playing paddles + 1 ball behind a 50% dim overlay. Runs in `backgrounds.MenuDemo` module.
- **Glitch title:** "CYBERBALL 2084" with 1Hz micro-displacement (±2px random) every 1s.
- **Key hints:** bottom strip, separated visually from cards.
- **New keys:** `O` opens Settings screen; existing `M`, `C` moved into Settings.

### B.2 In-Game HUD (`ui/hud.py` extended)

- **Combo gauge:** number + circular progress ring around it; ring depletes over the 2s timeout window. Ring color: white → gold as multiplier tier rises.
- **Powerup timer bars:** vertical stack on left edge. Each row: icon (16×16) + bar (60px wide) + seconds remaining (number). Consistent spacing and styling.
- **Boss HP bar:** top-center during boss fight only. Shows boss name, icon, segmented HP (one segment per HP point). For `Split`, two stacked bars.
- **Score:** glow strengthened; when multiplier ≥ 1.5×, score text uses gold gradient (via vertical linear blend).

### B.3 Screen Effects (`ui/effects.py` extended)

New class `ScreenEffect` with methods:

- `flash(color, duration_ms)` — full-screen alpha-decaying overlay.
- `shake(intensity, duration_ms)` — camera offset (existing, unified under this API).
- `slowmo(factor, duration_ms)` — global `dt *= factor` during active window.
- `vignette(color, intensity)` — persistent until cleared (used for boss fight).
- `banner(text, duration_ms)` — sweep-in banner overlay.

Triggers:

- Point scored: `flash(side_color, 150ms)` + `slowmo(0.3, 150ms)` + existing shake.
- Boss incoming: `banner("⚠ BOSS INCOMING", 500ms)` + `vignette(red, 0.3)` until boss exits.
- Boss defeated: radial particle burst + `slowmo(0.4, 2000ms)` + clear vignette.

### B.4 Game Over / Victory (`ui/gameover.py` [new])

- Match end condition: **first to 11 points** (new rule; previously unlimited).
- Result screen shows: winner, final score, max combo, boss kills this match, powerups collected this match, match duration.
- Keys: `R` restart, `ESC` menu. Same-session stats merged into `save.json` on exit.

### B.5 Settings Screen (`ui/settings.py` [new])

- Entered from menu via `O`.
- Items (navigated by up/down, adjusted by left/right):
  - Volume (0–100)
  - Colorblind palette (on/off)
  - Mode (1P / 2P)
  - Slowmo effect (on/off) — accessibility toggle
  - Shake intensity (0 / low / medium / high)
- Persisted in `save.json` under `settings` key.
- `ESC` returns to menu.

### B.6 Typography & Palette (`ui/typography.py` [new], `config.py` extended)

- `typography.FONT_TITLE` (72), `FONT_HEADING` (36), `FONT_BODY` (20), `FONT_SMALL` (14). Single source of truth; all UI files import from here.
- `config.palette` namespace: `NEON_PINK`, `CYBER_CYAN`, `ACID_GREEN`, `GOLD`, `VOID_BLACK`, `ALERT_RED`, etc. Replace raw RGB tuples throughout.
- `effects.draw_glow(surface, color, intensity)` helper unifies glow rendering.

---

## Data / State Changes

### `GameState` new fields
```python
current_boss: Optional[Boss] = None
boss_rotation_index: int = 0
boss_manager: BossManager
screen_effect: ScreenEffect
match_stats: MatchStats  # per-match counters for game over screen
```

### `save.json` schema additions
```json
{
  "stats": {
    "boss_kills": {"titan": 0, "barrage": 0, "split": 0}
  },
  "settings": {
    "volume": 70,
    "colorblind": false,
    "mode": "1P",
    "slowmo_enabled": true,
    "shake_intensity": "medium"
  }
}
```

Backward compat: missing keys default via `.get()` on load.

---

## Architecture Overview

```
cyberball/
├── config.py                  # palette namespace added
├── game.py                    # GameState extended; scoring routes through BossManager
├── entities/
│   ├── ball.py                # unchanged
│   ├── paddle.py              # unchanged
│   ├── powerup.py             # unchanged (spawn rate param externalized)
│   ├── gravity_well.py        # unchanged
│   ├── laser.py               # unchanged
│   ├── particle.py            # unchanged
│   └── boss.py                # NEW: Boss, Titan, Barrage, Split, Projectile
├── systems/
│   ├── audio.py               # unchanged
│   ├── stats.py               # extended schema
│   ├── ai.py                  # unchanged
│   └── boss_manager.py        # NEW
└── ui/
    ├── menu.py                # rewritten: cards, demo background
    ├── hud.py                 # extended: combo ring, boss HP, powerup bars
    ├── effects.py             # extended: ScreenEffect class
    ├── backgrounds.py         # NEW: MenuDemo
    ├── gameover.py            # NEW
    ├── settings.py            # NEW
    └── typography.py          # NEW
```

## Testing Strategy

Existing 12 tests must continue to pass. Add ~15 new tests:

**Unit (boss logic):**
- `Titan` takes 5 hits to defeat
- `Barrage` spawns projectile every 2.0s
- `Split` tracks two independent HP pools; defeat requires both
- `BossManager.on_player_score` triggers boss at 5, 10, 15
- `BossManager` advances rotation on defeat, preserves on player loss
- Defeat reward: score +hp_max×100, random powerup activated

**Unit (UI state):**
- `ScreenEffect.flash/slowmo/shake/vignette/banner` timers decrement and clear correctly
- `MatchStats` accumulates hits, combo max, boss kills, powerup pickups
- `Settings` load/save round-trip preserves all fields
- `save.json` backward-compat: old file missing `boss_kills` / `settings` loads with defaults

**Smoke (headless):**
- Menu → start game → trigger boss at score 5 → defeat boss → continue: no crash
- Game over at 11 points displays result screen without crash

Run with: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest discover tests`

## Risks & Mitigations

- **Boss paddle collision edge cases** (Titan 2.5× size may tunnel): reuse existing paddle tunneling fix in `ball.py`.
- **Barrage projectile clutter**: cap projectile count at 4 on screen.
- **Slowmo stacking**: `ScreenEffect.slowmo` uses max-active factor, not multiplied; prevents near-freeze from overlapping triggers.
- **Settings migration**: old `save.json` without `settings` key uses defaults; no destructive migration.

## Out of Scope

- Boss-specific music cues
- Difficulty-scaled boss HP (all difficulties use same HP)
- Achievement unlocks from boss kills (data captured, UI later)
