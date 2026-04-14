import unittest

from cyberball.ui.effects import ScreenEffect


class ScreenEffectTest(unittest.TestCase):
    def test_flash_timer_decrements(self):
        fx = ScreenEffect()
        fx.flash((255, 0, 0), duration_ms=150)
        self.assertTrue(fx.flash_active())
        fx.tick(dt_ms=100)
        self.assertTrue(fx.flash_active())
        fx.tick(dt_ms=100)
        self.assertFalse(fx.flash_active())

    def test_slowmo_factor(self):
        fx = ScreenEffect()
        self.assertEqual(fx.time_scale(), 1.0)
        fx.slowmo(0.3, duration_ms=200)
        self.assertAlmostEqual(fx.time_scale(), 0.3)
        fx.tick(dt_ms=250)
        self.assertEqual(fx.time_scale(), 1.0)

    def test_slowmo_uses_min_factor(self):
        fx = ScreenEffect()
        fx.slowmo(0.5, duration_ms=200)
        fx.slowmo(0.3, duration_ms=200)
        self.assertAlmostEqual(fx.time_scale(), 0.3)

    def test_shake_offset(self):
        fx = ScreenEffect()
        fx.shake(intensity=10, duration_ms=100)
        ox, oy = fx.shake_offset()
        self.assertTrue(-10 <= ox <= 10)
        self.assertTrue(-10 <= oy <= 10)
        fx.tick(dt_ms=150)
        self.assertEqual(fx.shake_offset(), (0, 0))

    def test_vignette_persistent(self):
        fx = ScreenEffect()
        fx.vignette((220, 40, 40), intensity=0.3)
        self.assertTrue(fx.vignette_active())
        fx.tick(dt_ms=10_000)
        self.assertTrue(fx.vignette_active())
        fx.clear_vignette()
        self.assertFalse(fx.vignette_active())

    def test_banner_timer(self):
        fx = ScreenEffect()
        fx.banner("TEST", duration_ms=500)
        self.assertEqual(fx.active_banner(), "TEST")
        fx.tick(dt_ms=600)
        self.assertIsNone(fx.active_banner())


if __name__ == '__main__':
    unittest.main()
