import unittest
import pygame
pygame.init()

from cyberball.entities.boss import Boss, Titan, Barrage, Split, BossProjectile


class BossBaseTest(unittest.TestCase):
    def test_titan_initial_hp(self):
        b = Titan(x=80)
        self.assertEqual(b.hp, 5)
        self.assertEqual(b.hp_max, 5)
        self.assertEqual(b.boss_type, 'titan')

    def test_barrage_initial_hp(self):
        b = Barrage(x=80)
        self.assertEqual(b.hp, 3)
        self.assertEqual(b.boss_type, 'barrage')

    def test_split_initial_hp(self):
        b = Split(x=80)
        self.assertEqual(b.hp, 4)
        self.assertEqual(b.hp_max, 4)
        self.assertEqual(len(b.segments), 2)

    def test_titan_takes_damage(self):
        b = Titan(x=80)
        b.take_damage()
        self.assertEqual(b.hp, 4)
        self.assertFalse(b.is_defeated())

    def test_titan_defeat(self):
        b = Titan(x=80)
        for _ in range(5):
            b.take_damage()
        self.assertTrue(b.is_defeated())

    def test_split_damage_per_segment(self):
        b = Split(x=80)
        b.take_damage_at(0)
        b.take_damage_at(0)
        self.assertEqual(b.segments[0].hp, 0)
        self.assertEqual(b.segments[1].hp, 2)
        self.assertFalse(b.is_defeated())
        b.take_damage_at(1)
        b.take_damage_at(1)
        self.assertTrue(b.is_defeated())

    def test_barrage_fires_projectile(self):
        b = Barrage(x=80)
        projectiles = []
        for _ in range(125):
            new = b.update(target_y=400)
            projectiles.extend(new)
        self.assertGreaterEqual(len(projectiles), 1)
        self.assertIsInstance(projectiles[0], BossProjectile)


class BossProjectileTest(unittest.TestCase):
    def test_projectile_moves(self):
        p = BossProjectile(x=100, y=400, vx=4, vy=0)
        start = p.rect.centerx
        p.update()
        self.assertGreater(p.rect.centerx, start)

    def test_off_screen(self):
        p = BossProjectile(x=2000, y=400, vx=4, vy=0)
        self.assertTrue(p.off_screen(1024))


if __name__ == '__main__':
    unittest.main()
