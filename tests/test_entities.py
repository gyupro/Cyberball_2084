"""Unit tests for entity logic (headless)."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

import math
import unittest

from cyberball.entities import Ball, Paddle, PowerUp, GravityWell, Laser
from cyberball.config import SCREEN_HEIGHT, SCREEN_WIDTH, PADDLE_HEIGHT, MAX_BALL_SPEED


class TestBall(unittest.TestCase):
    def test_wall_bounce_top(self):
        b = Ball(100, 0, 5, -10)
        result = b.update()
        self.assertEqual(result, "wall")
        self.assertGreater(b.speed_y, 0)
        self.assertGreaterEqual(b.rect.top, 0)

    def test_wall_bounce_bottom(self):
        b = Ball(100, SCREEN_HEIGHT - 10, 5, 10)
        result = b.update()
        self.assertEqual(result, "wall")
        self.assertLess(b.speed_y, 0)

    def test_clamp_speed(self):
        b = Ball(100, 100, 100, -100)
        b.clamp_speed()
        self.assertLessEqual(abs(b.speed_x), MAX_BALL_SPEED)
        self.assertLessEqual(abs(b.speed_y), MAX_BALL_SPEED)

    def test_trail_capped(self):
        b = Ball(100, 100, 1, 1)
        for _ in range(30):
            b.update()
        self.assertLessEqual(len(b.trail), 15)


class TestPaddle(unittest.TestCase):
    def test_clamp_top(self):
        p = Paddle(0, "left")
        p.move(-10000)
        self.assertGreaterEqual(p.rect.top, 0)

    def test_clamp_bottom(self):
        p = Paddle(0, "left")
        p.move(10000)
        self.assertLessEqual(p.rect.bottom, SCREEN_HEIGHT)

    def test_grow_and_reset(self):
        p = Paddle(0, "left")
        original = p.rect.height
        p.grow(50, SCREEN_HEIGHT // 3)
        self.assertGreater(p.rect.height, original)
        p.reset_size()
        self.assertEqual(p.rect.height, PADDLE_HEIGHT)


class TestGravityWell(unittest.TestCase):
    def test_attracts_within_radius(self):
        gw = GravityWell(100, 100)
        b = Ball(150, 100, 0, 0)
        gw.attract(b)
        self.assertLess(b.speed_x, 0)  # pulled toward x=100 (left)

    def test_ignores_far_ball(self):
        gw = GravityWell(100, 100)
        b = Ball(500, 500, 0, 0)
        gw.attract(b)
        self.assertEqual(b.speed_x, 0)
        self.assertEqual(b.speed_y, 0)


class TestLaser(unittest.TestCase):
    def test_leaves_screen(self):
        l = Laser(SCREEN_WIDTH - 5, 100, "right")
        for _ in range(5):
            alive = l.update()
        self.assertFalse(alive)


if __name__ == "__main__":
    unittest.main()
