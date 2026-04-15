"""Game constants and configuration."""

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS_TARGET = 60

PADDLE_SPEED = 8
PADDLE_HEIGHT = 120
PADDLE_WIDTH = 20

BALL_SIZE = 24
BALL_START_SPEED = 7.0
SPEED_INCREMENT = 0.3
MAX_BALL_SPEED = 15

MAX_PARTICLES = 500

POWERUP_SPAWN_CHANCE = 0.005
POWERUP_SIZE = 30
POWERUP_DURATION = 300  # frames @ 60fps ~= 5s

SCREEN_SHAKE_DURATION = 15
SCREEN_SHAKE_INTENSITY = 8

MENU_ANIMATION_SPEED = 0.02

# Cyberpunk palette
BLACK = (0, 0, 0)
CYBER_BLUE = (0, 255, 255)
NEON_PINK = (255, 20, 147)
ELECTRIC_PURPLE = (138, 43, 226)
NEON_GREEN = (57, 255, 20)
DARK_CYAN = (0, 139, 139)
BRIGHT_WHITE = (255, 255, 255)
DIM_GRAY = (64, 64, 64)
GLOW_WHITE = (200, 200, 255)
POWERUP_GOLD = (255, 215, 0)
POWERUP_RED = (255, 69, 0)
POWERUP_BLUE = (30, 144, 255)

POWERUP_TYPES = ['speed', 'size', 'multi', 'shield', 'gravity', 'slow_time', 'laser']

DIFFICULTIES = ['easy', 'medium', 'hard', 'extreme']

AI_SPEED_MULTIPLIER = {
    'easy': 0.6,
    'medium': 0.9,
    'hard': 1.2,
    'extreme': 1.5,
}

# Persistent save path
import os
SAVE_DIR = os.path.join(os.path.expanduser("~"), ".cyberball2084")
SAVE_FILE = os.path.join(SAVE_DIR, "save.json")

# Match rules
MATCH_POINT_LIMIT = 11
BOSS_TRIGGER_INTERVAL = 5

# Boss defaults
BOSS_TITAN_HP = 5
BOSS_BARRAGE_HP = 3
BOSS_SPLIT_HP = 2  # per sub-paddle
BOSS_ROTATION = ['titan', 'barrage', 'split']
BOSS_POWERUP_SPAWN_MULTIPLIER = 2.0
# Match points awarded per boss HP defeated (Titan=5pts, Barrage=3pts, Split=4pts)
BOSS_SCORE_BONUS_PER_HP = 1

# Screen effects
SCREEN_FLASH_MS = 150
SLOWMO_FACTOR = 0.3
SLOWMO_MS = 150
BOSS_BANNER_MS = 500
BOSS_DEFEAT_SLOWMO_MS = 2000

# Palette semantic aliases
GOLD = POWERUP_GOLD
ALERT_RED = (220, 40, 40)
