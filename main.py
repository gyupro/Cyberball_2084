import pygame
import sys
import random
import math
from pygame.locals import QUIT, KEYDOWN, K_UP, K_DOWN, K_r, K_ESCAPE, K_SPACE, K_1, K_2, K_3, K_4

pygame.init()
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
except pygame.error:
    print("Warning: Audio initialization failed. Running without sound.")
    SOUND_ENABLED = False

# Constants
SOUND_ENABLED = True
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
PADDLE_SPEED = 8
BALL_SPEED = [7, 7]
PADDLE_HEIGHT = 120
PADDLE_WIDTH = 20
BALL_SIZE = 24
SPEED_INCREMENT = 0.3
MAX_BALL_SPEED = 15
PARTICLE_COUNT = 50
MAX_PARTICLES = 500
POWERUP_SPAWN_CHANCE = 0.005
POWERUP_SIZE = 30
POWERUP_DURATION = 300  # frames
SCREEN_SHAKE_DURATION = 15
SCREEN_SHAKE_INTENSITY = 8
FPS_TARGET = 60
MENU_ANIMATION_SPEED = 0.02
SOUND_ENABLED = True

# Cyberpunk Colors
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

# Game state
left_score = 0
right_score = 0
game_state = "menu"  # menu, playing, paused
difficulty = "medium"  # easy, medium, hard, extreme
ai_speed_multiplier = 1.0
particles = []
trail_points = []
ball_glow = 0
glow_direction = 1
powerups = []
active_powerups = []
screen_shake = 0
ball_spin = 0.0
multi_balls = []
menu_particles = []
score_flash = {'left': 0, 'right': 0}
combo_counter = 0
last_hit_time = 0
sounds = {}
score_multiplier = 1.0
consecutive_hits = 0
shield_active = {'left': False, 'right': False}
gravity_wells = []
time_slow_factor = 1.0
lasers = []
laser_cooldown = {'left': 0, 'right': 0}

# Sound system
def init_sounds():
    global sounds
    try:
        # Create simple beep sounds using pygame
        sounds['paddle_hit'] = pygame.mixer.Sound(buffer=b'\x00\x80' * 1000)
        sounds['wall_hit'] = pygame.mixer.Sound(buffer=b'\x00\x60' * 800)
        sounds['powerup'] = pygame.mixer.Sound(buffer=b'\x00\xa0' * 1200)
        sounds['score'] = pygame.mixer.Sound(buffer=b'\x00\xff' * 2000)
        
        # Set volumes
        for sound in sounds.values():
            sound.set_volume(0.3)
    except:
        # Disable sounds if initialization fails
        global SOUND_ENABLED
        SOUND_ENABLED = False
        sounds = {}

def play_sound(sound_name):
    if SOUND_ENABLED and sound_name in sounds:
        try:
            sounds[sound_name].play()
        except:
            pass

init_sounds()

# Statistics system
game_stats = {
    'games_played': 0,
    'total_hits': 0,
    'max_combo': 0,
    'powerups_collected': 0,
    'high_scores': {'easy': 0, 'medium': 0, 'hard': 0, 'extreme': 0}
}

def update_stats():
    global game_stats, combo_counter
    game_stats['total_hits'] += 1
    if combo_counter > game_stats['max_combo']:
        game_stats['max_combo'] = combo_counter

def end_game_stats():
    global game_stats, left_score, right_score, difficulty
    game_stats['games_played'] += 1
    player_score = right_score  # Assuming player is on the right
    if player_score > game_stats['high_scores'][difficulty]:
        game_stats['high_scores'][difficulty] = player_score

# Create the ball and paddles
ball = pygame.Rect(SCREEN_WIDTH // 2 - BALL_SIZE // 2, SCREEN_HEIGHT // 2 - BALL_SIZE // 2, BALL_SIZE, BALL_SIZE)
left_paddle = pygame.Rect(0, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
right_paddle = pygame.Rect(SCREEN_WIDTH - PADDLE_WIDTH, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
# Set up the screen, clock, and font renderer
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('CYBERBALL 2084 - NEON WARS')
clock = pygame.time.Clock()
title_font = pygame.font.Font(None, 72)
menu_font = pygame.font.Font(None, 48)
score_font = pygame.font.Font(None, 56)
ui_font = pygame.font.Font(None, 32)

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.life = random.uniform(20, 60)
        self.max_life = self.life
        self.color = color
        self.size = random.uniform(2, 5)
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.vx *= 0.98
        self.vy *= 0.98
        return self.life > 0
    
    def draw(self, screen):
        alpha = int(255 * (self.life / self.max_life))
        size = int(self.size * (self.life / self.max_life))
        if size > 0:
            color_with_alpha = (*self.color, alpha)
            s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, color_with_alpha, (size, size), size)
            screen.blit(s, (self.x-size, self.y-size))

class PowerUp:
    def __init__(self, x, y, type_name):
        self.x = x
        self.y = y
        self.type = type_name
        self.rect = pygame.Rect(x - POWERUP_SIZE//2, y - POWERUP_SIZE//2, POWERUP_SIZE, POWERUP_SIZE)
        self.rotation = 0
        self.pulse = 0
        
    def update(self):
        self.rotation += 3
        self.pulse += 0.1
        
    def draw(self, screen):
        pulse_size = int(POWERUP_SIZE + 5 * math.sin(self.pulse))
        colors = {
            'speed': POWERUP_GOLD,
            'size': POWERUP_RED,
            'multi': POWERUP_BLUE,
            'shield': NEON_GREEN,
            'gravity': ELECTRIC_PURPLE,
            'slow_time': CYBER_BLUE,
            'laser': NEON_PINK
        }
        color = colors.get(self.type, POWERUP_GOLD)
        
        # Draw rotating square with glow
        draw_glow_rect(screen, color, 
                      pygame.Rect(self.x - pulse_size//2, self.y - pulse_size//2, pulse_size, pulse_size), 5)
        pygame.draw.rect(screen, color, 
                        pygame.Rect(self.x - pulse_size//2, self.y - pulse_size//2, pulse_size, pulse_size))
        
        # Draw symbol
        if self.type == 'speed':
            pygame.draw.polygon(screen, BLACK, [
                (self.x - 8, self.y - 8), (self.x + 8, self.y), (self.x - 8, self.y + 8)
            ])
        elif self.type == 'size':
            pygame.draw.rect(screen, BLACK, (self.x - 6, self.y - 6, 12, 12))
        elif self.type == 'multi':
            pygame.draw.circle(screen, BLACK, (self.x - 4, self.y), 3)
            pygame.draw.circle(screen, BLACK, (self.x + 4, self.y), 3)
        elif self.type == 'shield':
            # Draw shield icon
            pygame.draw.polygon(screen, BLACK, [
                (self.x, self.y - 8), (self.x - 6, self.y - 4),
                (self.x - 6, self.y + 4), (self.x, self.y + 8),
                (self.x + 6, self.y + 4), (self.x + 6, self.y - 4)
            ])
        elif self.type == 'gravity':
            # Draw gravity well
            pygame.draw.circle(screen, BLACK, (self.x, self.y), 8, 2)
            pygame.draw.circle(screen, BLACK, (self.x, self.y), 4, 1)
        elif self.type == 'slow_time':
            # Draw clock icon
            pygame.draw.circle(screen, BLACK, (self.x, self.y), 8, 2)
            pygame.draw.line(screen, BLACK, (self.x, self.y), (self.x, self.y - 5), 2)
            pygame.draw.line(screen, BLACK, (self.x, self.y), (self.x + 4, self.y), 2)
        elif self.type == 'laser':
            # Draw laser beam icon
            pygame.draw.line(screen, BLACK, (self.x - 8, self.y), (self.x + 8, self.y), 3)
            for i in range(-6, 7, 3):
                pygame.draw.line(screen, BLACK, (self.x + i, self.y - 2), (self.x + i, self.y + 2), 1)

class GravityWell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.strength = 150
        self.radius = 100
        self.life = 300
        self.pulse = 0
        
    def update(self):
        self.life -= 1
        self.pulse += 0.1
        return self.life > 0
        
    def attract_ball(self, ball):
        dx = self.x - ball.rect.centerx
        dy = self.y - ball.rect.centery
        dist = math.sqrt(dx**2 + dy**2)
        if dist < self.radius and dist > 10:
            force = self.strength / (dist**2)
            ball.speed_x += (dx / dist) * force * 0.1
            ball.speed_y += (dy / dist) * force * 0.1
            
    def draw(self, screen):
        # Draw gravity effect
        alpha = int(100 * (self.life / 300))
        for i in range(3):
            radius = int(self.radius * (1 - i * 0.3) + 10 * math.sin(self.pulse + i))
            color = (*ELECTRIC_PURPLE, max(0, alpha - i * 30))
            s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (radius, radius), radius, 2)
            screen.blit(s, (self.x - radius, self.y - radius))

class Laser:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction  # 'left' or 'right'
        self.speed = 15
        self.width = 60
        self.height = 4
        self.rect = pygame.Rect(x - self.width//2, y - self.height//2, self.width, self.height)
        
    def update(self):
        if self.direction == 'left':
            self.x -= self.speed
        else:
            self.x += self.speed
        self.rect.x = self.x - self.width//2
        return 0 < self.x < SCREEN_WIDTH
        
    def draw(self, screen):
        # Draw laser beam with glow
        color = NEON_PINK if self.direction == 'right' else CYBER_BLUE
        draw_glow_rect(screen, color, self.rect, 8)
        pygame.draw.rect(screen, BRIGHT_WHITE, self.rect)
        # Add energy effect
        for i in range(0, self.width, 4):
            spark_x = self.rect.x + i
            spark_y = self.rect.centery + random.randint(-2, 2)
            pygame.draw.circle(screen, color, (spark_x, spark_y), 1)

class Ball:
    def __init__(self, x, y, speed_x, speed_y):
        self.rect = pygame.Rect(x - BALL_SIZE//2, y - BALL_SIZE//2, BALL_SIZE, BALL_SIZE)
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.spin = 0.0
        self.trail = []
        
    def update(self):
        global time_slow_factor
        # Apply spin to movement
        self.speed_y += self.spin * 0.1 * time_slow_factor
        
        # Update position
        self.rect.x += self.speed_x * time_slow_factor
        self.rect.y += self.speed_y * time_slow_factor
        
        # Update trail
        self.trail.append((self.rect.centerx, self.rect.centery))
        if len(self.trail) > 15:
            self.trail.pop(0)
            
        # Wall collision
        if self.rect.top <= 0 or self.rect.bottom >= SCREEN_HEIGHT:
            self.speed_y = -self.speed_y
            self.spin *= -0.8
            create_particles(self.rect.centerx, self.rect.centery, NEON_PINK, 5)
            play_sound('wall_hit')
            return 'wall'
        return None
        
    def draw(self, screen):
        # Draw trail
        for i, (x, y) in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)) * 0.5)
            size = int(BALL_SIZE * (i / len(self.trail)) * 0.3)
            if size > 0:
                trail_surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                pygame.draw.circle(trail_surf, (*CYBER_BLUE, alpha), (size, size), size)
                screen.blit(trail_surf, (x - size, y - size))
        
        # Draw ball with glow
        global ball_glow, glow_direction
        ball_glow += glow_direction * 3
        if ball_glow >= 50 or ball_glow <= 0:
            glow_direction *= -1
            
        glow_intensity = 8 + int(ball_glow * 0.1)
        draw_glow_circle(screen, BRIGHT_WHITE, self.rect.center, BALL_SIZE//2, glow_intensity)
        pygame.draw.circle(screen, BRIGHT_WHITE, self.rect.center, BALL_SIZE//2)

def create_particles(x, y, color, count=10):
    # Limit total particles to prevent memory issues
    if len(particles) + count > MAX_PARTICLES:
        # Remove oldest particles
        particles[:count] = []
    for _ in range(count):
        particles.append(Particle(x, y, color))

def spawn_powerup():
    if random.random() < POWERUP_SPAWN_CHANCE:
        x = random.randint(SCREEN_WIDTH // 4, 3 * SCREEN_WIDTH // 4)
        y = random.randint(POWERUP_SIZE, SCREEN_HEIGHT - POWERUP_SIZE)
        powerup_type = random.choice(['speed', 'size', 'multi', 'shield', 'gravity', 'slow_time', 'laser'])
        powerups.append(PowerUp(x, y, powerup_type))

def apply_powerup(powerup_type):
    global active_powerups, screen_shake
    active_powerups.append({'type': powerup_type, 'duration': POWERUP_DURATION})
    screen_shake = SCREEN_SHAKE_DURATION
    create_particles(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, POWERUP_GOLD, 20)

def update_powerups():
    global active_powerups, left_paddle, right_paddle, shield_active, time_slow_factor
    for powerup in active_powerups[:]:
        powerup['duration'] -= 1
        if powerup['duration'] <= 0:
            active_powerups.remove(powerup)
            # Reset paddle sizes
            if powerup['type'] == 'size':
                # Store center position before resizing
                left_center = left_paddle.centery
                right_center = right_paddle.centery
                # Reset sizes
                left_paddle.height = PADDLE_HEIGHT
                right_paddle.height = PADDLE_HEIGHT
                # Restore center position
                left_paddle.centery = left_center
                right_paddle.centery = right_center
                # Keep paddles in bounds
                if left_paddle.top < 0:
                    left_paddle.top = 0
                if left_paddle.bottom > SCREEN_HEIGHT:
                    left_paddle.bottom = SCREEN_HEIGHT
                if right_paddle.top < 0:
                    right_paddle.top = 0
                if right_paddle.bottom > SCREEN_HEIGHT:
                    right_paddle.bottom = SCREEN_HEIGHT
            elif powerup['type'] == 'shield':
                shield_active['right'] = False
            elif powerup['type'] == 'slow_time':
                time_slow_factor = 1.0

def apply_screen_shake():
    global screen_shake
    if screen_shake > 0:
        shake_x = random.randint(-SCREEN_SHAKE_INTENSITY, SCREEN_SHAKE_INTENSITY)
        shake_y = random.randint(-SCREEN_SHAKE_INTENSITY, SCREEN_SHAKE_INTENSITY)
        screen_shake -= 1
        return shake_x, shake_y
    return 0, 0

def create_menu_particles():
    global menu_particles
    if len(menu_particles) < 20:
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        color = random.choice([CYBER_BLUE, NEON_PINK, ELECTRIC_PURPLE, NEON_GREEN])
        menu_particles.append(Particle(x, y, color))

def update_combo_system():
    global combo_counter, last_hit_time, score_multiplier, consecutive_hits
    current_time = pygame.time.get_ticks()
    if current_time - last_hit_time > 2000:  # Reset combo after 2 seconds
        combo_counter = 0
        consecutive_hits = 0
        score_multiplier = 1.0
    else:
        # Calculate score multiplier based on combo
        if combo_counter >= 10:
            score_multiplier = 3.0
        elif combo_counter >= 5:
            score_multiplier = 2.0
        elif combo_counter >= 3:
            score_multiplier = 1.5
        else:
            score_multiplier = 1.0

def create_impact_particles(x, y, color, intensity=1):
    count = int(15 * intensity)
    spread = int(50 * intensity)
    # Limit total particles
    if len(particles) + count > MAX_PARTICLES:
        particles[:count] = []
    for _ in range(count):
        particle = Particle(x, y, color)
        particle.vx = random.uniform(-spread/10, spread/10)
        particle.vy = random.uniform(-spread/10, spread/10) 
        particle.life = random.uniform(30, 80)
        particle.max_life = particle.life
        particle.size = random.uniform(3, 8)
        particles.append(particle)

def reset_game():
    global ball, BALL_SPEED, particles, trail_points, powerups, active_powerups, multi_balls
    global gravity_wells, lasers, shield_active, time_slow_factor
    # Reset ball
    speed = random.uniform(6, 8)
    angle = random.uniform(-math.pi/4, math.pi/4)
    if random.choice([True, False]):
        angle += math.pi
    
    ball = Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 
                speed * math.cos(angle), speed * math.sin(angle))
    
    # Clear game objects
    particles.clear()
    trail_points.clear()
    powerups.clear()
    multi_balls.clear()
    gravity_wells.clear()
    lasers.clear()
    
    # Reset powerup states
    shield_active['left'] = False
    shield_active['right'] = False
    time_slow_factor = 1.0
    
    # Reset paddle sizes if needed
    global left_paddle, right_paddle
    left_paddle.height = PADDLE_HEIGHT
    right_paddle.height = PADDLE_HEIGHT
    left_paddle.y = SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2
    right_paddle.y = SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2
    
    create_particles(ball.rect.centerx, ball.rect.centery, CYBER_BLUE, 20)

def move_left_paddle():
    global ai_speed_multiplier
    # Smarter AI based on difficulty
    if isinstance(ball, Ball):
        target_y = ball.rect.centery
    else:
        target_y = ball.centery
    paddle_center = left_paddle.centery
    
    # Enhanced AI for different difficulties
    if difficulty == "extreme":
        # Perfect prediction with adaptive strategies
        if isinstance(ball, Ball):
            if ball.speed_x < 0 and abs(ball.speed_x) > 0.1:  # Ball moving towards AI
                time_to_reach = abs(ball.rect.centerx - left_paddle.centerx) / abs(ball.speed_x)
                predicted_y = ball.rect.centery + (ball.speed_y + ball.spin * 0.1) * time_to_reach
                target_y = predicted_y
        elif BALL_SPEED[0] < 0 and abs(BALL_SPEED[0]) > 0.1:
            time_to_reach = abs(ball.centerx - left_paddle.centerx) / abs(BALL_SPEED[0])
            predicted_y = ball.centery + BALL_SPEED[1] * time_to_reach
            target_y = predicted_y
        ai_speed_multiplier = 1.5
        # Add strategic positioning
        if random.random() < 0.1:
            target_y += random.uniform(-20, 20)
    elif difficulty == "hard":
        if isinstance(ball, Ball):
            if ball.speed_x < 0 and abs(ball.speed_x) > 0.1:
                time_to_reach = abs(ball.rect.centerx - left_paddle.centerx) / abs(ball.speed_x)
                predicted_y = ball.rect.centery + ball.speed_y * time_to_reach
                target_y = predicted_y
        elif BALL_SPEED[0] < 0 and abs(BALL_SPEED[0]) > 0.1:
            time_to_reach = abs(ball.centerx - left_paddle.centerx) / abs(BALL_SPEED[0])
            predicted_y = ball.centery + BALL_SPEED[1] * time_to_reach
            target_y = predicted_y
        ai_speed_multiplier = 1.2
    elif difficulty == "medium":
        ai_speed_multiplier = 0.9
    else:  # easy
        ai_speed_multiplier = 0.6
        target_y += random.uniform(-30, 30)
    
    # Move towards target
    diff = target_y - paddle_center
    move_speed = PADDLE_SPEED * ai_speed_multiplier
    
    if abs(diff) > 10:
        if diff > 0 and left_paddle.bottom < SCREEN_HEIGHT - 10:
            left_paddle.move_ip(0, min(move_speed, abs(diff)))
        elif diff < 0 and left_paddle.top > 10:
            left_paddle.move_ip(0, -min(move_speed, abs(diff)))

def draw_glow_rect(surface, color, rect, glow_size=5):
    glow_surf = pygame.Surface((rect.width + glow_size*2, rect.height + glow_size*2), pygame.SRCALPHA)
    for i in range(glow_size):
        alpha = 255 // (glow_size + 1) * (glow_size - i)
        glow_color = (*color, alpha)
        pygame.draw.rect(glow_surf, glow_color, 
                        (i, i, rect.width + (glow_size-i)*2, rect.height + (glow_size-i)*2))
    surface.blit(glow_surf, (rect.x - glow_size, rect.y - glow_size))

def draw_glow_circle(surface, color, center, radius, glow_size=8):
    glow_surf = pygame.Surface((radius*2 + glow_size*2, radius*2 + glow_size*2), pygame.SRCALPHA)
    for i in range(glow_size):
        alpha = 255 // (glow_size + 1) * (glow_size - i)
        glow_color = (*color, alpha)
        pygame.draw.circle(glow_surf, glow_color, 
                          (radius + glow_size, radius + glow_size), radius + i)
    surface.blit(glow_surf, (center[0] - radius - glow_size, center[1] - radius - glow_size))

def draw_menu():
    screen.fill(BLACK)
    
    # Update and draw menu particles
    create_menu_particles()
    menu_particles[:] = [p for p in menu_particles if p.update()]
    for particle in menu_particles:
        particle.draw(screen)
    
    # Enhanced animated background with multiple layers
    time_offset = pygame.time.get_ticks() * MENU_ANIMATION_SPEED
    
    # Layer 1: Vertical lines
    for i in range(0, SCREEN_WIDTH, 50):
        alpha = int(50 + 30 * math.sin(time_offset + i * 0.1))
        color = (*DARK_CYAN, alpha)
        s = pygame.Surface((2, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill(color)
        screen.blit(s, (i, 0))
    
    # Layer 2: Moving diagonal lines
    for i in range(-SCREEN_HEIGHT, SCREEN_WIDTH + SCREEN_HEIGHT, 100):
        x1 = i + int(100 * math.sin(time_offset * 0.5))
        y1 = 0
        x2 = i + SCREEN_HEIGHT + int(100 * math.sin(time_offset * 0.5))
        y2 = SCREEN_HEIGHT
        alpha = int(20 + 15 * math.sin(time_offset + i * 0.02))
        if alpha > 0:
            color = (*ELECTRIC_PURPLE, alpha)
            s = pygame.Surface((SCREEN_WIDTH + SCREEN_HEIGHT, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(s, color, (0, 0), (SCREEN_WIDTH + SCREEN_HEIGHT, SCREEN_HEIGHT), 1)
            screen.blit(s, (x1 - SCREEN_HEIGHT, y1))
    
    # Title with enhanced glow effect and animation
    title_pulse = 1.0 + 0.1 * math.sin(time_offset * 3)
    title_text = title_font.render("CYBERBALL 2084", True, CYBER_BLUE)
    title_glow = title_font.render("CYBERBALL 2084", True, BRIGHT_WHITE)
    
    title_x = SCREEN_WIDTH // 2 - title_text.get_width() // 2
    title_y = 120 + int(10 * math.sin(time_offset))
    
    # Enhanced glow with multiple layers
    glow_offsets = [(4, 4), (-4, -4), (4, -4), (-4, 4), (0, 6), (0, -6), (6, 0), (-6, 0)]
    for i, offset in enumerate(glow_offsets):
        alpha = int(100 - i * 12)
        glow_surface = pygame.Surface(title_glow.get_size(), pygame.SRCALPHA)
        glow_surface.blit(title_glow, (0, 0))
        glow_surface.set_alpha(alpha)
        screen.blit(glow_surface, (title_x + offset[0], title_y + offset[1]))
    
    screen.blit(title_text, (title_x, title_y))
    
    # Animated subtitle
    subtitle_wave = int(5 * math.sin(time_offset * 2))
    subtitle = ui_font.render("NEON WARS", True, NEON_PINK)
    screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, title_y + 80 + subtitle_wave))
    
    # Menu options
    menu_items = [
        "PRESS SPACE TO START",
        "1 - EASY MODE",
        "2 - MEDIUM MODE", 
        "3 - HARD MODE",
        "4 - EXTREME MODE",
        "ESC - EXIT"
    ]
    
    for i, item in enumerate(menu_items):
        color = NEON_GREEN if i == 0 else GLOW_WHITE
        if i > 0 and i-1 == ["easy", "medium", "hard", "extreme"].index(difficulty):
            color = NEON_PINK
        
        text = menu_font.render(item, True, color)
        y_pos = 350 + i * 60
        screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y_pos))
    
    # Difficulty indicator
    diff_text = ui_font.render(f"Current Difficulty: {difficulty.upper()}", True, ELECTRIC_PURPLE)
    screen.blit(diff_text, (SCREEN_WIDTH // 2 - diff_text.get_width() // 2, 630))
    
    # Statistics display
    stats_y = 670
    stats_text = ui_font.render(f"Games: {game_stats['games_played']} | High Score ({difficulty}): {game_stats['high_scores'][difficulty]}", True, DIM_GRAY)
    screen.blit(stats_text, (SCREEN_WIDTH // 2 - stats_text.get_width() // 2, stats_y))
    
    stats2_text = ui_font.render(f"Total Hits: {game_stats['total_hits']} | Max Combo: {game_stats['max_combo']} | Powerups: {game_stats['powerups_collected']}", True, DIM_GRAY)
    screen.blit(stats2_text, (SCREEN_WIDTH // 2 - stats2_text.get_width() // 2, stats_y + 25))

def handle_menu_input(event):
    global game_state, difficulty
    if event.type == KEYDOWN:
        if event.key == K_SPACE:
            game_state = "playing"
            reset_game()
        elif event.key == K_1:
            difficulty = "easy"
        elif event.key == K_2:
            difficulty = "medium"
        elif event.key == K_3:
            difficulty = "hard"
        elif event.key == K_4:
            difficulty = "extreme"
        elif event.key == K_ESCAPE:
            pygame.quit()
            sys.exit()

# Main game loop
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        
        if game_state == "menu":
            handle_menu_input(event)
        elif game_state == "playing":
            if event.type == KEYDOWN:
                if event.key == K_r:
                    left_score = 0
                    right_score = 0
                    reset_game()
                elif event.key == K_ESCAPE:
                    game_state = "menu"
                elif event.key == K_SPACE:
                    game_state = "paused"
        elif game_state == "paused":
            if event.type == KEYDOWN:
                if event.key == K_SPACE:
                    game_state = "playing"
                elif event.key == K_ESCAPE:
                    game_state = "menu"

    if game_state == "menu":
        draw_menu()
    elif game_state == "playing":
        keys = pygame.key.get_pressed()
        
        # Update game logic
        move_left_paddle()
        
        # Move the right paddle with arrow keys
        if keys[K_UP] and right_paddle.top > 0:
            right_paddle.move_ip(0, -PADDLE_SPEED)
        if keys[K_DOWN] and right_paddle.bottom < SCREEN_HEIGHT:
            right_paddle.move_ip(0, PADDLE_SPEED)
        
        # Spawn powerups
        spawn_powerup()
        
        # Update powerups
        for powerup in powerups[:]:
            powerup.update()
        
        update_powerups()
        update_combo_system()
        
        # Update gravity wells
        gravity_wells[:] = [gw for gw in gravity_wells if gw.update()]
        for gw in gravity_wells:
            gw.attract_ball(ball)
            for mb in multi_balls:
                gw.attract_ball(mb)
        
        # Update lasers
        lasers[:] = [laser for laser in lasers if laser.update()]
        
        # Update laser cooldowns
        if laser_cooldown['left'] > 0:
            laser_cooldown['left'] -= 1
        if laser_cooldown['right'] > 0:
            laser_cooldown['right'] -= 1
        
        # Fire lasers with keyboard
        if keys[K_SPACE] and laser_cooldown['right'] == 0 and 'laser' in [p['type'] for p in active_powerups]:
            lasers.append(Laser(right_paddle.centerx - 20, right_paddle.centery, 'left'))
            laser_cooldown['right'] = 30
            play_sound('powerup')
        
        # Update ball
        ball.update()
        
        # Handle multi-balls
        for mb in multi_balls[:]:
            mb.update()
            if mb.rect.left <= 0 or mb.rect.right >= SCREEN_WIDTH:
                multi_balls.remove(mb)
        
        # Handle ball collisions
        def handle_ball_collision(ball_obj):
            global screen_shake, combo_counter, last_hit_time
            # Paddle collisions
            if ball_obj.rect.colliderect(left_paddle):
                if ball_obj.speed_x < 0:
                    hit_pos = (ball_obj.rect.centery - left_paddle.centery) / left_paddle.height
                    ball_obj.speed_x = abs(ball_obj.speed_x) + SPEED_INCREMENT
                    ball_obj.speed_y += hit_pos * 3
                    ball_obj.spin = hit_pos * 0.5
                    screen_shake = SCREEN_SHAKE_DURATION // 2
                    # Enhanced collision feedback with combo
                    combo_counter += 1
                    last_hit_time = pygame.time.get_ticks()
                    intensity = min(combo_counter / 5, 2.0)
                    create_impact_particles(ball_obj.rect.centerx, ball_obj.rect.centery, CYBER_BLUE, intensity)
                    play_sound('paddle_hit')
                    update_stats()
            
            elif ball_obj.rect.colliderect(right_paddle):
                if ball_obj.speed_x > 0:
                    hit_pos = (ball_obj.rect.centery - right_paddle.centery) / right_paddle.height
                    ball_obj.speed_x = -(abs(ball_obj.speed_x) + SPEED_INCREMENT)
                    ball_obj.speed_y += hit_pos * 3
                    ball_obj.spin = hit_pos * 0.5
                    screen_shake = SCREEN_SHAKE_DURATION // 2
                    # Enhanced collision feedback with combo
                    combo_counter += 1
                    last_hit_time = pygame.time.get_ticks()
                    intensity = min(combo_counter / 5, 2.0)
                    create_impact_particles(ball_obj.rect.centerx, ball_obj.rect.centery, NEON_PINK, intensity)
                    play_sound('paddle_hit')
                    update_stats()
            
            # Shield collision detection
            if shield_active['left'] and ball_obj.speed_x < 0 and ball_obj.rect.left <= left_paddle.right + 20:
                ball_obj.speed_x = abs(ball_obj.speed_x)
                create_impact_particles(left_paddle.right + 10, ball_obj.rect.centery, NEON_GREEN, 2.0)
                play_sound('paddle_hit')
            
            if shield_active['right'] and ball_obj.speed_x > 0 and ball_obj.rect.right >= right_paddle.left - 20:
                ball_obj.speed_x = -abs(ball_obj.speed_x)
                create_impact_particles(right_paddle.left - 10, ball_obj.rect.centery, NEON_GREEN, 2.0)
                play_sound('paddle_hit')
            
            # Limit ball speed
            if abs(ball_obj.speed_x) > MAX_BALL_SPEED:
                ball_obj.speed_x = MAX_BALL_SPEED if ball_obj.speed_x > 0 else -MAX_BALL_SPEED
            if abs(ball_obj.speed_y) > MAX_BALL_SPEED:
                ball_obj.speed_y = MAX_BALL_SPEED if ball_obj.speed_y > 0 else -MAX_BALL_SPEED
        
        handle_ball_collision(ball)
        for mb in multi_balls:
            handle_ball_collision(mb)
        
        # Laser-ball collision
        for laser in lasers[:]:
            if laser.rect.colliderect(ball.rect):
                # Deflect ball
                ball.speed_x = -abs(ball.speed_x) if laser.direction == 'right' else abs(ball.speed_x)
                ball.speed_y += random.uniform(-3, 3)
                lasers.remove(laser)
                create_impact_particles(ball.rect.centerx, ball.rect.centery, BRIGHT_WHITE, 2.0)
                screen_shake = SCREEN_SHAKE_DURATION
                play_sound('paddle_hit')
            else:
                # Check multi-balls
                for mb in multi_balls[:]:
                    if laser.rect.colliderect(mb.rect):
                        multi_balls.remove(mb)
                        lasers.remove(laser)
                        create_impact_particles(mb.rect.centerx, mb.rect.centery, BRIGHT_WHITE, 1.5)
                        play_sound('paddle_hit')
                        break
        
        # Check powerup collisions
        for powerup in powerups[:]:
            if ball.rect.colliderect(powerup.rect):
                powerups.remove(powerup)
                apply_powerup(powerup.type)
                play_sound('powerup')
                game_stats['powerups_collected'] += 1
                
                # Apply powerup effects
                if powerup.type == 'speed':
                    ball.speed_x *= 1.3
                    ball.speed_y *= 1.3
                elif powerup.type == 'size':
                    left_paddle.height = min(left_paddle.height + 30, SCREEN_HEIGHT // 3)
                    right_paddle.height = min(right_paddle.height + 30, SCREEN_HEIGHT // 3)
                elif powerup.type == 'multi':
                    for _ in range(2):
                        angle = random.uniform(-math.pi/3, math.pi/3)
                        speed = random.uniform(6, 9)
                        multi_balls.append(Ball(ball.rect.centerx, ball.rect.centery,
                                              speed * math.cos(angle), speed * math.sin(angle)))
                elif powerup.type == 'shield':
                    shield_active['right'] = True
                elif powerup.type == 'gravity':
                    # Create gravity well at center
                    gravity_wells.append(GravityWell(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                elif powerup.type == 'slow_time':
                    time_slow_factor = 0.3
                elif powerup.type == 'laser':
                    laser_cooldown['right'] = 0  # Reset cooldown to allow immediate shot
        
        # Scoring with enhanced effects
        if ball.rect.left <= 0:
            # Apply score multiplier
            points_earned = int(1 * score_multiplier)
            right_score += points_earned
            score_flash['right'] = 30
            create_impact_particles(ball.rect.centerx, ball.rect.centery, NEON_GREEN, 3.0)
            screen_shake = SCREEN_SHAKE_DURATION * 2
            
            # Show bonus points if multiplier active
            if score_multiplier > 1:
                bonus_particles = int(20 * score_multiplier)
                create_particles(SCREEN_WIDTH - 100, 100, POWERUP_GOLD, bonus_particles)
            
            combo_counter = 0
            consecutive_hits = 0
            score_multiplier = 1.0
            play_sound('score')
            end_game_stats()
            reset_game()
        elif ball.rect.right >= SCREEN_WIDTH:
            # Apply score multiplier
            points_earned = int(1 * score_multiplier)
            left_score += points_earned
            score_flash['left'] = 30
            create_impact_particles(ball.rect.centerx, ball.rect.centery, NEON_GREEN, 3.0)
            screen_shake = SCREEN_SHAKE_DURATION * 2
            
            # Show bonus points if multiplier active
            if score_multiplier > 1:
                bonus_particles = int(20 * score_multiplier)
                create_particles(100, 100, POWERUP_GOLD, bonus_particles)
            
            combo_counter = 0
            consecutive_hits = 0
            score_multiplier = 1.0
            play_sound('score')
            end_game_stats()
            reset_game()
        
        # Update particles
        particles[:] = [p for p in particles if p.update()]
        
        # Render game with screen shake
        shake_x, shake_y = apply_screen_shake()
        screen.fill(BLACK)
        
        # Draw animated background grid
        time_offset = pygame.time.get_ticks() * 0.001
        for i in range(0, SCREEN_WIDTH, 80):
            alpha = int(30 + 20 * math.sin(time_offset + i * 0.05))
            color = (*DIM_GRAY, alpha)
            s = pygame.Surface((1, SCREEN_HEIGHT), pygame.SRCALPHA)
            s.fill(color)
            screen.blit(s, (i, 0))
        
        for i in range(0, SCREEN_HEIGHT, 80):
            alpha = int(30 + 20 * math.sin(time_offset + i * 0.05))
            color = (*DIM_GRAY, alpha)
            s = pygame.Surface((SCREEN_WIDTH, 1), pygame.SRCALPHA)
            s.fill(color)
            screen.blit(s, (0, i))
        
        # Draw center line with glow
        center_x = SCREEN_WIDTH // 2
        for i in range(0, SCREEN_HEIGHT, 30):
            alpha = int(100 + 50 * math.sin(time_offset * 2 + i * 0.1))
            color = (*CYBER_BLUE, alpha)
            s = pygame.Surface((4, 20), pygame.SRCALPHA)
            s.fill(color)
            screen.blit(s, (center_x - 2, i))
        
        # Draw powerups
        for powerup in powerups:
            powerup.draw(screen)
        
        # Draw gravity wells
        for gw in gravity_wells:
            gw.draw(screen)
        
        # Apply screen shake offset to all drawing
        screen_offset = (shake_x, shake_y)
        
        # Draw paddles with glow
        left_paddle_shaken = left_paddle.move(shake_x, shake_y)
        right_paddle_shaken = right_paddle.move(shake_x, shake_y)
        draw_glow_rect(screen, CYBER_BLUE, left_paddle_shaken, 3)
        pygame.draw.rect(screen, CYBER_BLUE, left_paddle_shaken)
        
        draw_glow_rect(screen, NEON_PINK, right_paddle_shaken, 3)
        pygame.draw.rect(screen, NEON_PINK, right_paddle_shaken)
        
        # Draw shields if active
        if shield_active['left']:
            shield_x = left_paddle.right + 10
            shield_rect = pygame.Rect(shield_x - 2, left_paddle.top - 10, 4, left_paddle.height + 20)
            draw_glow_rect(screen, NEON_GREEN, shield_rect, 10)
            pygame.draw.rect(screen, NEON_GREEN, shield_rect)
        
        if shield_active['right']:
            shield_x = right_paddle.left - 10
            shield_rect = pygame.Rect(shield_x - 2, right_paddle.top - 10, 4, right_paddle.height + 20)
            draw_glow_rect(screen, NEON_GREEN, shield_rect, 10)
            pygame.draw.rect(screen, NEON_GREEN, shield_rect)
        
        # Draw main ball
        ball.draw(screen)
        
        # Draw multi-balls
        for mb in multi_balls:
            mb.draw(screen)
        
        # Draw lasers
        for laser in lasers:
            laser.draw(screen)
        
        # Draw particles
        for particle in particles:
            particle.draw(screen)
        
        # Display scores with enhanced effects
        # Left score with flash
        left_color = CYBER_BLUE
        if score_flash['left'] > 0:
            flash_intensity = score_flash['left'] / 30
            left_color = (min(255, int(CYBER_BLUE[0] + 100 * flash_intensity)),
                         min(255, int(CYBER_BLUE[1] + 100 * flash_intensity)),
                         min(255, int(CYBER_BLUE[2] + 100 * flash_intensity)))
            score_flash['left'] -= 1
        
        score_text = score_font.render(f"{left_score}", True, left_color)
        screen.blit(score_text, (SCREEN_WIDTH // 4 - score_text.get_width() // 2 + shake_x, 30 + shake_y))
        
        # Right score with flash
        right_color = NEON_PINK
        if score_flash['right'] > 0:
            flash_intensity = score_flash['right'] / 30
            right_color = (min(255, int(NEON_PINK[0] + 100 * flash_intensity)),
                          min(255, int(NEON_PINK[1] + 100 * flash_intensity)),
                          min(255, int(NEON_PINK[2] + 100 * flash_intensity)))
            score_flash['right'] -= 1
        
        score_text = score_font.render(f"{right_score}", True, right_color)
        screen.blit(score_text, (3 * SCREEN_WIDTH // 4 - score_text.get_width() // 2 + shake_x, 30 + shake_y))
        
        # Display combo counter and multiplier
        if combo_counter > 1:
            combo_text = ui_font.render(f"COMBO x{combo_counter}!", True, POWERUP_GOLD)
            combo_x = SCREEN_WIDTH // 2 - combo_text.get_width() // 2
            combo_y = 80 + int(5 * math.sin(pygame.time.get_ticks() * 0.01))
            screen.blit(combo_text, (combo_x + shake_x, combo_y + shake_y))
            
            # Show score multiplier
            if score_multiplier > 1:
                mult_text = ui_font.render(f"SCORE x{score_multiplier:.1f}", True, NEON_GREEN)
                mult_x = SCREEN_WIDTH // 2 - mult_text.get_width() // 2
                mult_y = combo_y + 30
                screen.blit(mult_text, (mult_x + shake_x, mult_y + shake_y))
        
        # Game info with powerup status
        speed_display = abs(ball.speed_x) if hasattr(ball, 'speed_x') else 7.0
        powerup_text = ""
        if active_powerups:
            powerup_types = [p['type'].upper() for p in active_powerups]
            powerup_text = f"  |  POWERUPS: {', '.join(powerup_types)}"
        
        info_text = ui_font.render(f"Difficulty: {difficulty.upper()}  |  Speed: {speed_display:.1f}{powerup_text}  |  ESC: Menu  |  R: Reset", True, DIM_GRAY)
        screen.blit(info_text, (10 + shake_x, SCREEN_HEIGHT - 30 + shake_y))
    
    elif game_state == "paused":
        # Draw game state but dimmed
        screen.fill(BLACK)
        pause_text = title_font.render("PAUSED", True, NEON_GREEN)
        screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        
        continue_text = menu_font.render("SPACE to Continue  |  ESC for Menu", True, GLOW_WHITE)
        screen.blit(continue_text, (SCREEN_WIDTH // 2 - continue_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))
    
    pygame.display.flip()
    clock.tick(60)
