"""Game state machine and main loop."""
import math
import random
import sys
import pygame

from .config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS_TARGET, BLACK, CYBER_BLUE, NEON_PINK,
    NEON_GREEN, DIM_GRAY, POWERUP_GOLD, BRIGHT_WHITE, BALL_SIZE, BALL_START_SPEED,
    PADDLE_WIDTH, PADDLE_SPEED, POWERUP_DURATION, POWERUP_SPAWN_CHANCE, POWERUP_SIZE,
    POWERUP_TYPES, SCREEN_SHAKE_DURATION, SCREEN_SHAKE_INTENSITY, MAX_PARTICLES,
    DIFFICULTIES, SPEED_INCREMENT,
    MATCH_POINT_LIMIT, BOSS_POWERUP_SPAWN_MULTIPLIER,
    SCREEN_FLASH_MS, SLOWMO_FACTOR, SLOWMO_MS,
    BOSS_BANNER_MS, BOSS_DEFEAT_SLOWMO_MS, ALERT_RED,
)
from .entities import Ball, Paddle, PowerUp, GravityWell, Laser, Particle
from .entities.boss import Split
from .systems import AudioSystem, StatsManager, move_ai_paddle
from .systems.boss_manager import BossManager
from .ui.effects import draw_glow_rect, draw_glow_circle, ScreenEffect
from .ui.menu import MenuRenderer
from .ui.hud import HUD, draw_boss_hp_bar
from .ui.gameover import MatchStats, draw_game_over
from .ui.settings import SettingsScreen


class GameState:
    """Holds all runtime state. Avoids module-level globals."""

    def __init__(self, audio, stats):
        self.audio = audio
        self.stats = stats

        self.state = "menu"  # menu, playing, paused
        self.difficulty = "medium"
        self.mode = "1p"  # 1p or 2p
        self.colorblind = False

        self.left_paddle = Paddle(0, "left")
        self.right_paddle = Paddle(SCREEN_WIDTH - PADDLE_WIDTH, "right")
        self.ball = self._new_ball()
        self.multi_balls = []

        self.particles = []
        self.powerups = []
        self.active_powerups = []
        self.gravity_wells = []
        self.lasers = []
        self.laser_cooldown = {'left': 0, 'right': 0}
        self.shield_active = {'left': False, 'right': False}
        self.time_slow_factor = 1.0

        self.left_score = 0
        self.right_score = 0
        self.score_flash = {'left': 0, 'right': 0}
        self.screen_shake = 0

        self.combo_counter = 0
        self.last_hit_time = 0
        self.score_multiplier = 1.0

        # v4: boss + UI upgrades
        self.boss_manager = BossManager(boss_x=0)  # AI is on the left (x=0)
        self.boss_projectiles = []
        self.screen_effect = ScreenEffect()
        self.match_stats = MatchStats()
        self.match_stats.start(0)
        self.game_over_winner = None
        self.settings_screen = None

    def _new_ball(self):
        angle = random.uniform(-math.pi / 4, math.pi / 4)
        if random.choice([True, False]):
            angle += math.pi
        speed = random.uniform(BALL_START_SPEED - 1, BALL_START_SPEED + 1)
        return Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                    speed * math.cos(angle), speed * math.sin(angle))

    def reset_round(self):
        self.ball = self._new_ball()
        self.particles.clear()
        self.powerups.clear()
        self.multi_balls.clear()
        self.gravity_wells.clear()
        self.lasers.clear()
        self.active_powerups.clear()
        self.shield_active = {'left': False, 'right': False}
        self.time_slow_factor = 1.0
        self.left_paddle.reset_position()
        self.right_paddle.reset_position()
        self._spawn_particles(self.ball.rect.centerx, self.ball.rect.centery, CYBER_BLUE, 20)

    def reset_match(self):
        self.left_score = 0
        self.right_score = 0
        self.combo_counter = 0
        self.score_multiplier = 1.0
        self.boss_manager = BossManager(boss_x=0)
        self.boss_projectiles.clear()
        self.screen_effect = ScreenEffect()
        self.match_stats = MatchStats()
        self.match_stats.start(pygame.time.get_ticks())
        self.game_over_winner = None
        self.reset_round()

    # Particle helpers
    def _spawn_particles(self, x, y, color, count=10):
        if len(self.particles) + count > MAX_PARTICLES:
            del self.particles[:count]
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def spawn_impact(self, x, y, color, intensity=1.0):
        count = int(15 * intensity)
        spread = 50 * intensity
        if len(self.particles) + count > MAX_PARTICLES:
            del self.particles[:count]
        for _ in range(count):
            p = Particle(x, y, color)
            p.vx = random.uniform(-spread / 10, spread / 10)
            p.vy = random.uniform(-spread / 10, spread / 10)
            p.life = random.uniform(30, 80)
            p.max_life = p.life
            p.size = random.uniform(3, 8)
            self.particles.append(p)


def _fonts():
    return {
        'title': pygame.font.Font(None, 80),
        'menu': pygame.font.Font(None, 36),
        'ui': pygame.font.Font(None, 32),
        'score': pygame.font.Font(None, 64),
        'small': pygame.font.Font(None, 24),
    }


def _handle_paddle_hit(state, ball_obj, paddle, color):
    hit_pos = (ball_obj.rect.centery - paddle.rect.centery) / max(paddle.rect.height, 1)
    ball_obj.speed_x = -ball_obj.speed_x
    # Push out of paddle to avoid tunneling/sticking
    if paddle.side == 'left':
        ball_obj.rect.left = paddle.rect.right + 1
        ball_obj.speed_x = abs(ball_obj.speed_x) + SPEED_INCREMENT
    else:
        ball_obj.rect.right = paddle.rect.left - 1
        ball_obj.speed_x = -(abs(ball_obj.speed_x) + SPEED_INCREMENT)
    ball_obj.speed_y += hit_pos * 3
    ball_obj.spin = hit_pos * 0.5
    ball_obj.clamp_speed()

    state.screen_shake = max(state.screen_shake, SCREEN_SHAKE_DURATION // 2)
    state.combo_counter += 1
    state.last_hit_time = pygame.time.get_ticks()
    intensity = min(state.combo_counter / 5, 2.0)
    state.spawn_impact(ball_obj.rect.centerx, ball_obj.rect.centery, color, intensity)
    state.audio.play('paddle_hit')
    state.stats.record_hit(state.combo_counter)


def _spawn_powerup(state):
    chance = POWERUP_SPAWN_CHANCE
    if state.boss_manager.active:
        chance *= BOSS_POWERUP_SPAWN_MULTIPLIER
    if random.random() < chance:
        x = random.randint(SCREEN_WIDTH // 4, 3 * SCREEN_WIDTH // 4)
        y = random.randint(POWERUP_SIZE, SCREEN_HEIGHT - POWERUP_SIZE)
        t = random.choice(POWERUP_TYPES)
        state.powerups.append(PowerUp(x, y, t))


def _apply_powerup(state, p_type):
    state.active_powerups.append({'type': p_type, 'duration': POWERUP_DURATION})
    state.screen_shake = max(state.screen_shake, SCREEN_SHAKE_DURATION)
    state._spawn_particles(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, POWERUP_GOLD, 20)
    state.stats.record_powerup()
    state.match_stats.record_powerup()

    if p_type == 'speed':
        state.ball.speed_x *= 1.3
        state.ball.speed_y *= 1.3
        state.ball.clamp_speed()
    elif p_type == 'size':
        state.left_paddle.grow(30, SCREEN_HEIGHT // 3)
        state.right_paddle.grow(30, SCREEN_HEIGHT // 3)
    elif p_type == 'multi':
        for _ in range(2):
            angle = random.uniform(-math.pi / 3, math.pi / 3)
            speed = random.uniform(6, 9)
            state.multi_balls.append(Ball(state.ball.rect.centerx, state.ball.rect.centery,
                                          speed * math.cos(angle), speed * math.sin(angle)))
    elif p_type == 'shield':
        state.shield_active['right'] = True
    elif p_type == 'gravity':
        state.gravity_wells.append(GravityWell(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    elif p_type == 'slow_time':
        state.time_slow_factor = 0.3
    elif p_type == 'laser':
        state.laser_cooldown['right'] = 0


def _update_active_powerups(state):
    for p in state.active_powerups[:]:
        p['duration'] -= 1
        if p['duration'] <= 0:
            if p['type'] == 'size':
                state.left_paddle.reset_size()
                state.right_paddle.reset_size()
            elif p['type'] == 'shield':
                state.shield_active['right'] = False
            elif p['type'] == 'slow_time':
                state.time_slow_factor = 1.0
            state.active_powerups.remove(p)


def _update_combo(state):
    now = pygame.time.get_ticks()
    if now - state.last_hit_time > 2000:
        state.combo_counter = 0
        state.score_multiplier = 1.0
    else:
        c = state.combo_counter
        state.score_multiplier = 3.0 if c >= 10 else 2.0 if c >= 5 else 1.5 if c >= 3 else 1.0


def _handle_ball_vs_boss(state, ball_obj):
    """Returns True if the ball hit the boss this frame."""
    boss = state.boss_manager.current_boss
    if boss is None or ball_obj.speed_x >= 0:
        return False
    hit = False
    if isinstance(boss, Split):
        for i, seg in enumerate(boss.segments):
            if seg.hp > 0 and ball_obj.rect.colliderect(seg.rect):
                ball_obj.speed_x = abs(ball_obj.speed_x) + SPEED_INCREMENT
                ball_obj.rect.left = seg.rect.right + 1
                boss.take_damage_at(i)
                state.spawn_impact(ball_obj.rect.centerx, ball_obj.rect.centery, ALERT_RED, 2.0)
                state.audio.play('paddle_hit')
                hit = True
                break
    else:
        if ball_obj.rect.colliderect(boss.rect):
            ball_obj.speed_x = abs(ball_obj.speed_x) + SPEED_INCREMENT
            ball_obj.rect.left = boss.rect.right + 1
            boss.take_damage()
            state.spawn_impact(ball_obj.rect.centerx, ball_obj.rect.centery, ALERT_RED, 2.0)
            state.audio.play('paddle_hit')
            hit = True
    ball_obj.clamp_speed()
    return hit


def _handle_ball_vs_paddles(state, ball_obj):
    # If boss active, left paddle is replaced by boss for collision
    if state.boss_manager.active:
        _handle_ball_vs_boss(state, ball_obj)
    elif ball_obj.rect.colliderect(state.left_paddle.rect) and ball_obj.speed_x < 0:
        _handle_paddle_hit(state, ball_obj, state.left_paddle, CYBER_BLUE)
    if ball_obj.rect.colliderect(state.right_paddle.rect) and ball_obj.speed_x > 0:
        _handle_paddle_hit(state, ball_obj, state.right_paddle, NEON_PINK)

    # Shields
    if (state.shield_active['left'] and ball_obj.speed_x < 0
            and ball_obj.rect.left <= state.left_paddle.rect.right + 20):
        ball_obj.speed_x = abs(ball_obj.speed_x)
        state.spawn_impact(state.left_paddle.rect.right + 10, ball_obj.rect.centery, NEON_GREEN, 2.0)
        state.audio.play('paddle_hit')
    if (state.shield_active['right'] and ball_obj.speed_x > 0
            and ball_obj.rect.right >= state.right_paddle.rect.left - 20):
        ball_obj.speed_x = -abs(ball_obj.speed_x)
        state.spawn_impact(state.right_paddle.rect.left - 10, ball_obj.rect.centery, NEON_GREEN, 2.0)
        state.audio.play('paddle_hit')

    ball_obj.clamp_speed()


def _handle_scoring(state):
    """Returns True if a score happened this frame."""
    if state.ball.rect.left <= 0:
        # Player (right) scored
        pts = int(1 * state.score_multiplier)
        state.right_score += pts
        state.score_flash['right'] = 30
        state.spawn_impact(state.ball.rect.centerx, state.ball.rect.centery, NEON_GREEN, 3.0)
        state.screen_shake = SCREEN_SHAKE_DURATION * 2
        state.screen_effect.flash(BRIGHT_WHITE, SCREEN_FLASH_MS)
        state.screen_effect.slowmo(SLOWMO_FACTOR, SLOWMO_MS)
        state.combo_counter = 0
        state.score_multiplier = 1.0
        state.audio.play('score')
        _check_boss_trigger(state)
        _check_match_end(state)
        if state.state != "gameover":
            state.reset_round()
        return True
    elif state.ball.rect.right >= SCREEN_WIDTH:
        # AI/boss scored on player
        pts = int(1 * state.score_multiplier)
        state.left_score += pts
        state.score_flash['left'] = 30
        state.spawn_impact(state.ball.rect.centerx, state.ball.rect.centery, NEON_GREEN, 3.0)
        state.screen_shake = SCREEN_SHAKE_DURATION * 2
        state.screen_effect.flash((255, 60, 60), SCREEN_FLASH_MS)
        state.screen_effect.slowmo(SLOWMO_FACTOR, SLOWMO_MS)
        state.combo_counter = 0
        state.score_multiplier = 1.0
        state.audio.play('score')
        if state.boss_manager.active:
            state.boss_manager.on_player_lost_point()
            state.boss_projectiles.clear()
            state.screen_effect.clear_vignette()
        _check_match_end(state)
        if state.state != "gameover":
            state.reset_round()
        return True
    return False


def _check_boss_trigger(state):
    boss = state.boss_manager.on_player_score(state.right_score)
    if boss is not None:
        state.screen_effect.banner("BOSS INCOMING", BOSS_BANNER_MS)
        state.screen_effect.vignette(ALERT_RED, 0.3)
        # Boss replaces the left side; clear any state attached to the hidden paddle.
        state.shield_active['left'] = False
        state.score_flash['left'] = 0


def _check_match_end(state):
    if state.right_score >= MATCH_POINT_LIMIT:
        _finish_match(state, winner="PLAYER")
    elif state.left_score >= MATCH_POINT_LIMIT:
        _finish_match(state, winner="AI")


def _finish_match(state, winner):
    state.game_over_winner = winner
    state.state = "gameover"
    state.match_stats.stop(pygame.time.get_ticks())
    _maybe_save_high(state)


def _maybe_save_high(state):
    player_score = state.right_score
    state.stats.record_game_end(state.difficulty, player_score)


def _screen_shake_offset(state):
    if state.screen_shake <= 0:
        return 0, 0
    sx = random.randint(-SCREEN_SHAKE_INTENSITY, SCREEN_SHAKE_INTENSITY)
    sy = random.randint(-SCREEN_SHAKE_INTENSITY, SCREEN_SHAKE_INTENSITY)
    state.screen_shake -= 1
    return sx, sy


def _draw_playfield(surface, state, shake):
    sx, sy = shake
    surface.fill(BLACK)

    # Grid background
    t = pygame.time.get_ticks() * 0.001
    for i in range(0, SCREEN_WIDTH, 80):
        alpha = int(30 + 20 * math.sin(t + i * 0.05))
        s = pygame.Surface((1, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((*DIM_GRAY, alpha))
        surface.blit(s, (i, 0))
    for i in range(0, SCREEN_HEIGHT, 80):
        alpha = int(30 + 20 * math.sin(t + i * 0.05))
        s = pygame.Surface((SCREEN_WIDTH, 1), pygame.SRCALPHA)
        s.fill((*DIM_GRAY, alpha))
        surface.blit(s, (0, i))

    # Center line
    cx = SCREEN_WIDTH // 2
    for i in range(0, SCREEN_HEIGHT, 30):
        alpha = int(100 + 50 * math.sin(t * 2 + i * 0.1))
        s = pygame.Surface((4, 20), pygame.SRCALPHA)
        s.fill((*CYBER_BLUE, alpha))
        surface.blit(s, (cx - 2, i))

    for p in state.powerups:
        p.draw(surface)
    for gw in state.gravity_wells:
        gw.draw(surface)

    # Paddles (left hidden during boss fight)
    rp = state.right_paddle.rect.move(sx, sy)
    if not state.boss_manager.active:
        lp = state.left_paddle.rect.move(sx, sy)
        draw_glow_rect(surface, CYBER_BLUE, lp, 3)
        pygame.draw.rect(surface, CYBER_BLUE, lp)
    draw_glow_rect(surface, NEON_PINK, rp, 3)
    pygame.draw.rect(surface, NEON_PINK, rp)

    # Shields
    if state.shield_active['left']:
        x = state.left_paddle.rect.right + 10
        r = pygame.Rect(x - 2, state.left_paddle.rect.top - 10, 4, state.left_paddle.rect.height + 20)
        draw_glow_rect(surface, NEON_GREEN, r, 10)
        pygame.draw.rect(surface, NEON_GREEN, r)
    if state.shield_active['right']:
        x = state.right_paddle.rect.left - 10
        r = pygame.Rect(x - 2, state.right_paddle.rect.top - 10, 4, state.right_paddle.rect.height + 20)
        draw_glow_rect(surface, NEON_GREEN, r, 10)
        pygame.draw.rect(surface, NEON_GREEN, r)

    # Balls with trail + glow
    for b in [state.ball, *state.multi_balls]:
        for i, (tx, ty) in enumerate(b.trail):
            ratio = i / max(len(b.trail), 1)
            size = int(BALL_SIZE * ratio * 0.3)
            if size > 0:
                ts = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(ts, (*CYBER_BLUE, int(128 * ratio)), (size, size), size)
                surface.blit(ts, (tx - size, ty - size))
        draw_glow_circle(surface, BRIGHT_WHITE, b.rect.center, BALL_SIZE // 2, 10)
        pygame.draw.circle(surface, BRIGHT_WHITE, b.rect.center, BALL_SIZE // 2)

    for laser in state.lasers:
        laser.draw(surface)
    for p in state.particles:
        p.draw(surface)


def _draw_boss(surface, state, shake):
    if not state.boss_manager.active:
        return
    sx, sy = shake
    boss = state.boss_manager.current_boss
    if isinstance(boss, Split):
        for seg in boss.segments:
            if seg.hp <= 0:
                continue
            r = seg.rect.move(sx, sy)
            draw_glow_rect(surface, ALERT_RED, r, 4)
            pygame.draw.rect(surface, ALERT_RED, r)
    else:
        r = boss.rect.move(sx, sy)
        draw_glow_rect(surface, ALERT_RED, r, 4)
        pygame.draw.rect(surface, ALERT_RED, r)


def _draw_boss_projectiles(surface, state, shake):
    sx, sy = shake
    for p in state.boss_projectiles:
        r = p.rect.move(sx, sy)
        draw_glow_rect(surface, ALERT_RED, r, 6)
        pygame.draw.rect(surface, ALERT_RED, r)


class Game:
    def __init__(self, headless=False):
        pygame.init()
        flags = pygame.HIDDEN if headless else 0
        try:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        except pygame.error:
            # Some builds don't support HIDDEN; fall back
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('CYBERBALL 2084 — NEON WARS')
        self.clock = pygame.time.Clock()
        self.fonts = _fonts()

        self.audio = AudioSystem()
        self.stats = StatsManager()
        self.state = GameState(self.audio, self.stats)
        self.menu = MenuRenderer(self.fonts)
        self.hud = HUD(self.fonts)

    # ----- Input -----
    def _handle_event(self, event):
        if event.type == pygame.QUIT:
            self._shutdown()
        if event.type != pygame.KEYDOWN:
            return

        s = self.state
        k = event.key

        if s.state == "menu":
            if k == pygame.K_SPACE:
                s.reset_match()
                s.state = "playing"
            elif k == pygame.K_1:
                s.difficulty = "easy"
            elif k == pygame.K_2:
                s.difficulty = "medium"
            elif k == pygame.K_3:
                s.difficulty = "hard"
            elif k == pygame.K_4:
                s.difficulty = "extreme"
            elif k == pygame.K_m:
                s.mode = "2p" if s.mode == "1p" else "1p"
            elif k == pygame.K_c:
                s.colorblind = not s.colorblind
            elif k == pygame.K_v:
                self.audio.set_volume(self.audio.volume - 0.1)
            elif k == pygame.K_b:
                self.audio.set_volume(self.audio.volume + 0.1)
            elif k == pygame.K_o:
                s.settings_screen = SettingsScreen(s.stats)
                s.state = "settings"
            elif k == pygame.K_ESCAPE:
                self._shutdown()
        elif s.state == "settings":
            if s.settings_screen and s.settings_screen.handle_key(k):
                s.state = "menu"
        elif s.state == "playing":
            if k == pygame.K_p:
                s.state = "paused"
            elif k == pygame.K_ESCAPE:
                s.state = "menu"
            elif k == pygame.K_r:
                s.reset_match()
            elif k == pygame.K_f:
                # Fire laser if active
                if any(p['type'] == 'laser' for p in s.active_powerups) and s.laser_cooldown['right'] == 0:
                    s.lasers.append(Laser(s.right_paddle.rect.centerx - 20,
                                          s.right_paddle.rect.centery, 'left'))
                    s.laser_cooldown['right'] = 30
                    self.audio.play('powerup')
        elif s.state == "gameover":
            if k == pygame.K_r:
                s.reset_match()
                s.state = "playing"
            elif k == pygame.K_ESCAPE:
                s.state = "menu"
        elif s.state == "paused":
            if k in (pygame.K_p, pygame.K_SPACE):
                s.state = "playing"
            elif k == pygame.K_ESCAPE:
                s.state = "menu"
            elif k == pygame.K_r:
                s.reset_match()
                s.state = "playing"
            elif k == pygame.K_v:
                self.audio.set_volume(self.audio.volume - 0.1)
            elif k == pygame.K_b:
                self.audio.set_volume(self.audio.volume + 0.1)
            elif k == pygame.K_m:
                self.audio.toggle_mute()

    def _shutdown(self):
        self.stats.save()
        pygame.quit()
        sys.exit()

    # ----- Update -----
    def _update_playing(self):
        s = self.state
        keys = pygame.key.get_pressed()

        # Tick screen effects (approx dt from clock)
        dt_ms = max(1, self.clock.get_time() or 16)
        s.screen_effect.tick(dt_ms)

        # Right paddle: player 1
        if keys[pygame.K_UP]:
            s.right_paddle.move(-PADDLE_SPEED)
        if keys[pygame.K_DOWN]:
            s.right_paddle.move(PADDLE_SPEED)

        # Boss or AI or Player 2 controls the left side
        if s.boss_manager.active:
            new_proj = s.boss_manager.current_boss.update(target_y=s.ball.rect.centery)
            room = max(0, 4 - len(s.boss_projectiles))
            s.boss_projectiles.extend(new_proj[:room])
        elif s.mode == "2p":
            if keys[pygame.K_w]:
                s.left_paddle.move(-PADDLE_SPEED)
            if keys[pygame.K_s]:
                s.left_paddle.move(PADDLE_SPEED)
        else:
            move_ai_paddle(s.left_paddle, s.ball, s.difficulty)

        # Boss projectiles
        alive = []
        for p in s.boss_projectiles:
            p.update()
            if p.off_screen(SCREEN_WIDTH):
                continue
            if p.rect.colliderect(s.right_paddle.rect):
                s.combo_counter = 0
                s.score_multiplier = 1.0
                s.spawn_impact(p.rect.centerx, p.rect.centery, ALERT_RED, 1.0)
                continue
            alive.append(p)
        s.boss_projectiles = alive

        _spawn_powerup(s)
        for p in s.powerups:
            p.update()
        _update_active_powerups(s)
        _update_combo(s)

        # Gravity wells
        s.gravity_wells[:] = [gw for gw in s.gravity_wells if gw.update()]
        for gw in s.gravity_wells:
            gw.attract(s.ball)
            for mb in s.multi_balls:
                gw.attract(mb)

        # Lasers
        s.lasers[:] = [l for l in s.lasers if l.update()]
        if s.laser_cooldown['left'] > 0:
            s.laser_cooldown['left'] -= 1
        if s.laser_cooldown['right'] > 0:
            s.laser_cooldown['right'] -= 1

        # Ball physics
        if s.ball.update(s.time_slow_factor) == 'wall':
            s._spawn_particles(s.ball.rect.centerx, s.ball.rect.centery, NEON_PINK, 5)
            self.audio.play('wall_hit')
        for mb in s.multi_balls[:]:
            mb.update(s.time_slow_factor)
            if mb.rect.left <= 0 or mb.rect.right >= SCREEN_WIDTH:
                s.multi_balls.remove(mb)

        prev_combo = s.combo_counter
        _handle_ball_vs_paddles(s, s.ball)
        for mb in s.multi_balls:
            _handle_ball_vs_paddles(s, mb)
        if s.combo_counter > prev_combo:
            s.match_stats.record_hit(s.combo_counter)

        # Boss defeat check
        if s.boss_manager.active and s.boss_manager.current_boss.is_defeated():
            reward = s.boss_manager.on_boss_defeated()
            if reward:
                s.right_score += reward['score_bonus']
                s.stats.record_boss_kill(reward['boss_type'])
                s.match_stats.record_boss_kill()
                _apply_powerup(s, reward['powerup_type'])
                s.screen_effect.slowmo(0.4, BOSS_DEFEAT_SLOWMO_MS)
                s.screen_effect.clear_vignette()
                s.boss_projectiles.clear()
                s.spawn_impact(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, POWERUP_GOLD, 3.0)
                _check_match_end(s)
                # Bonus may have crossed the next 5-point threshold — re-check trigger
                if s.state == "playing":
                    _check_boss_trigger(s)

        # Laser collisions
        for laser in s.lasers[:]:
            if laser.rect.colliderect(s.ball.rect):
                s.ball.speed_x = -abs(s.ball.speed_x) if laser.direction == 'right' else abs(s.ball.speed_x)
                s.ball.speed_y += random.uniform(-3, 3)
                if laser in s.lasers:
                    s.lasers.remove(laser)
                s.spawn_impact(s.ball.rect.centerx, s.ball.rect.centery, BRIGHT_WHITE, 2.0)
                s.screen_shake = max(s.screen_shake, SCREEN_SHAKE_DURATION)
                self.audio.play('paddle_hit')
                continue
            for mb in s.multi_balls[:]:
                if laser.rect.colliderect(mb.rect):
                    s.multi_balls.remove(mb)
                    if laser in s.lasers:
                        s.lasers.remove(laser)
                    s.spawn_impact(mb.rect.centerx, mb.rect.centery, BRIGHT_WHITE, 1.5)
                    self.audio.play('paddle_hit')
                    break

        # Powerup pickups
        for p in s.powerups[:]:
            if s.ball.rect.colliderect(p.rect):
                s.powerups.remove(p)
                _apply_powerup(s, p.type)
                self.audio.play('powerup')

        _handle_scoring(s)
        s.particles[:] = [p for p in s.particles if p.update()]

    # ----- Draw -----
    def _draw(self):
        s = self.state
        if s.state == "menu":
            self.menu.draw_menu(self.screen, s)
        elif s.state == "settings":
            if s.settings_screen:
                s.settings_screen.draw(self.screen)
        else:
            shake = _screen_shake_offset(s) if s.state == "playing" else (0, 0)
            _draw_playfield(self.screen, s, shake)
            _draw_boss(self.screen, s, shake)
            _draw_boss_projectiles(self.screen, s, shake)
            self.hud.draw(self.screen, s, shake)
            if s.boss_manager.active:
                draw_boss_hp_bar(self.screen, s.boss_manager.current_boss, self.fonts['ui'])
            s.screen_effect.render_overlays(self.screen)
            if s.state == "paused":
                self.menu.draw_pause(self.screen)
            elif s.state == "gameover":
                draw_game_over(self.screen, s.game_over_winner,
                               s.right_score, s.left_score,
                               s.match_stats, now_ms=pygame.time.get_ticks())
        pygame.display.flip()

    # ----- Main loop -----
    def run(self, max_frames=None):
        frame = 0
        while True:
            for event in pygame.event.get():
                self._handle_event(event)
            if self.state.state == "playing":
                self._update_playing()
            self._draw()
            if max_frames is None:
                self.clock.tick(FPS_TARGET)
            frame += 1
            if max_frames is not None and frame >= max_frames:
                self.stats.save()
                pygame.quit()
                return


def main():
    Game().run()
