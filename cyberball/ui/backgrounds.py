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
        dim.fill((0, 0, 0, 140))
        surface.blit(dim, (0, 0))
