"""Paddle entity — thin wrapper around pygame.Rect with sizing helpers."""
import pygame
from ..config import PADDLE_WIDTH, PADDLE_HEIGHT, SCREEN_HEIGHT


class Paddle:
    def __init__(self, x, side):
        self.rect = pygame.Rect(x, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.side = side  # 'left' or 'right'

    def move(self, dy):
        self.rect.y += dy
        self.clamp()

    def clamp(self):
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

    def grow(self, delta, max_height):
        center = self.rect.centery
        new_h = min(self.rect.height + delta, max_height)
        self.rect.height = new_h
        self.rect.centery = center
        self.clamp()

    def reset_size(self):
        center = self.rect.centery
        self.rect.height = PADDLE_HEIGHT
        self.rect.centery = center
        self.clamp()

    def reset_position(self):
        self.rect.y = SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2
        self.rect.height = PADDLE_HEIGHT
