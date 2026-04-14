"""Ball entity with physics, trail, and collision helpers."""
import math
import pygame

from ..config import BALL_SIZE, SCREEN_HEIGHT, MAX_BALL_SPEED


class Ball:
    def __init__(self, x, y, speed_x, speed_y):
        self.rect = pygame.Rect(
            int(x - BALL_SIZE // 2), int(y - BALL_SIZE // 2), BALL_SIZE, BALL_SIZE
        )
        self.speed_x = float(speed_x)
        self.speed_y = float(speed_y)
        self.spin = 0.0
        self.trail = []

    def update(self, time_factor=1.0):
        """Advance physics. Returns 'wall' if wall hit this frame."""
        self.speed_y += self.spin * 0.1 * time_factor
        self.rect.x += int(self.speed_x * time_factor)
        self.rect.y += int(self.speed_y * time_factor)

        self.trail.append((self.rect.centerx, self.rect.centery))
        if len(self.trail) > 15:
            self.trail.pop(0)

        wall = None
        if self.rect.top <= 0:
            self.rect.top = 0
            self.speed_y = abs(self.speed_y)
            self.spin *= -0.8
            wall = "wall"
        elif self.rect.bottom >= SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
            self.speed_y = -abs(self.speed_y)
            self.spin *= -0.8
            wall = "wall"
        return wall

    def clamp_speed(self):
        if abs(self.speed_x) > MAX_BALL_SPEED:
            self.speed_x = MAX_BALL_SPEED if self.speed_x > 0 else -MAX_BALL_SPEED
        if abs(self.speed_y) > MAX_BALL_SPEED:
            self.speed_y = MAX_BALL_SPEED if self.speed_y > 0 else -MAX_BALL_SPEED

    @property
    def speed(self):
        return math.hypot(self.speed_x, self.speed_y)
