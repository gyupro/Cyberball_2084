# Dead Code Analysis — 2026-04-15

**Tool:** vulture 2.16 (Python equivalent of knip/depcheck/ts-prune)
**Scope:** `cyberball/`, `main.py`
**Baseline:** 44/44 tests pass

## Findings (confidence ≥ 60%)

| File:Line | Symbol | Confidence | Verdict |
|-----------|--------|-----------:|---------|
| config.py:16 | `PARTICLE_COUNT` | 60% | **SAFE — remove** (no references) |
| config.py:79 | `VOID_BLACK` | 60% | **SAFE — remove** (added in v4 prep, never used) |
| config.py:80 | `ACID_GREEN` | 60% | **SAFE — remove** (same) |
| entities/boss.py:30 | `BossProjectile.off_screen` | 60% | **CAUTION — keep + refactor** (used in tests; game.py duplicates logic inline) |
| ui/effects.py:55,84 | `_banner_total_ms` | 60% | **SAFE — remove** (vestige of dropped `banner_progress`) |
| ui/effects.py:86 | `time_scale` | 60% | **KEEP** (false positive — used in tests + game loop) |
| ui/effects.py:97 | `flash_color` | 60% | **SAFE — remove** (render_overlays reads `_flash_color` directly) |
| ui/effects.py:100 | `shake_offset` | 60% | **KEEP** (false positive — used in tests) |
| ui/typography.py:34 | `small()` | 60% | **SAFE — remove** (no callers; remove `'small': 14` from SIZES too) |

## Action Plan

1. **SAFE deletions** (run tests after each):
   - `PARTICLE_COUNT`, `VOID_BLACK`, `ACID_GREEN` from `config.py`
   - `_banner_total_ms` field + assignments from `effects.py`
   - `flash_color()` method from `effects.py`
   - `small()` + `'small': 14` from `typography.py`

2. **CAUTION refactor**: replace inline `p.rect.right < 0 or p.rect.left > SCREEN_WIDTH` in `game.py` with `p.off_screen(SCREEN_WIDTH)` to justify keeping the method.

3. No DANGER-level findings. No file removals.
