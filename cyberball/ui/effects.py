"""Glow effects and screen-level effects (flash/slowmo/shake/vignette/banner)."""
import random
import pygame


def draw_glow_rect(surface, color, rect, glow_size=5):
    if rect.width <= 0 or rect.height <= 0:
        return
    glow_surf = pygame.Surface(
        (rect.width + glow_size * 2, rect.height + glow_size * 2), pygame.SRCALPHA
    )
    for i in range(glow_size):
        alpha = 255 // (glow_size + 1) * (glow_size - i)
        glow_color = (*color, alpha)
        pygame.draw.rect(
            glow_surf, glow_color,
            (i, i, rect.width + (glow_size - i) * 2, rect.height + (glow_size - i) * 2),
        )
    surface.blit(glow_surf, (rect.x - glow_size, rect.y - glow_size))


def draw_glow_circle(surface, color, center, radius, glow_size=8):
    if radius <= 0:
        return
    size = (radius + glow_size) * 2
    glow_surf = pygame.Surface((size, size), pygame.SRCALPHA)
    for i in range(glow_size):
        alpha = 255 // (glow_size + 1) * (glow_size - i)
        glow_color = (*color, alpha)
        pygame.draw.circle(
            glow_surf, glow_color, (radius + glow_size, radius + glow_size), radius + i,
        )
    surface.blit(glow_surf, (center[0] - radius - glow_size, center[1] - radius - glow_size))


class ScreenEffect:
    """Manages flash, slow-mo, shake, vignette, and banner effects."""

    def __init__(self):
        self._flash_color = None
        self._flash_remaining_ms = 0
        self._flash_total_ms = 0

        self._slowmo_factor = 1.0
        self._slowmo_remaining_ms = 0

        self._shake_intensity = 0
        self._shake_remaining_ms = 0

        self._vignette_color = None
        self._vignette_intensity = 0.0

        self._banner_text = None
        self._banner_remaining_ms = 0
        self._banner_total_ms = 0

    def flash(self, color, duration_ms):
        self._flash_color = color
        self._flash_remaining_ms = duration_ms
        self._flash_total_ms = max(1, duration_ms)

    def slowmo(self, factor, duration_ms):
        if self._slowmo_remaining_ms > 0:
            self._slowmo_factor = min(self._slowmo_factor, factor)
        else:
            self._slowmo_factor = factor
        self._slowmo_remaining_ms = max(self._slowmo_remaining_ms, duration_ms)

    def shake(self, intensity, duration_ms):
        self._shake_intensity = max(self._shake_intensity, intensity)
        self._shake_remaining_ms = max(self._shake_remaining_ms, duration_ms)

    def vignette(self, color, intensity):
        self._vignette_color = color
        self._vignette_intensity = intensity

    def clear_vignette(self):
        self._vignette_color = None
        self._vignette_intensity = 0.0

    def banner(self, text, duration_ms):
        self._banner_text = text
        self._banner_remaining_ms = duration_ms
        self._banner_total_ms = max(1, duration_ms)

    def time_scale(self):
        return self._slowmo_factor if self._slowmo_remaining_ms > 0 else 1.0

    def flash_active(self):
        return self._flash_remaining_ms > 0

    def flash_alpha(self):
        if not self.flash_active():
            return 0
        return int(180 * (self._flash_remaining_ms / self._flash_total_ms))

    def flash_color(self):
        return self._flash_color

    def shake_offset(self):
        if self._shake_remaining_ms <= 0 or self._shake_intensity <= 0:
            return (0, 0)
        return (
            random.randint(-self._shake_intensity, self._shake_intensity),
            random.randint(-self._shake_intensity, self._shake_intensity),
        )

    def vignette_active(self):
        return self._vignette_color is not None

    def vignette_params(self):
        return self._vignette_color, self._vignette_intensity

    def active_banner(self):
        return self._banner_text if self._banner_remaining_ms > 0 else None

    def tick(self, dt_ms):
        self._flash_remaining_ms = max(0, self._flash_remaining_ms - dt_ms)
        self._slowmo_remaining_ms = max(0, self._slowmo_remaining_ms - dt_ms)
        if self._slowmo_remaining_ms == 0:
            self._slowmo_factor = 1.0
        self._shake_remaining_ms = max(0, self._shake_remaining_ms - dt_ms)
        if self._shake_remaining_ms == 0:
            self._shake_intensity = 0
        self._banner_remaining_ms = max(0, self._banner_remaining_ms - dt_ms)
        if self._banner_remaining_ms == 0:
            self._banner_text = None

    def render_overlays(self, surface):
        if self.flash_active() and self._flash_color is not None:
            alpha = self.flash_alpha()
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((*self._flash_color, alpha))
            surface.blit(overlay, (0, 0))
        if self.vignette_active():
            color, intensity = self.vignette_params()
            w, h = surface.get_size()
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            alpha = int(180 * intensity)
            border = 80
            pygame.draw.rect(overlay, (*color, alpha), (0, 0, w, border))
            pygame.draw.rect(overlay, (*color, alpha), (0, h - border, w, border))
            pygame.draw.rect(overlay, (*color, alpha), (0, 0, border, h))
            pygame.draw.rect(overlay, (*color, alpha), (w - border, 0, border, h))
            surface.blit(overlay, (0, 0))
        banner = self.active_banner()
        if banner:
            font = pygame.font.Font(None, 72)
            text_surf = font.render(banner, True, (255, 40, 80))
            rect = text_surf.get_rect(center=(surface.get_width() // 2, 120))
            pygame.draw.rect(surface, (0, 0, 0), rect.inflate(40, 20))
            surface.blit(text_surf, rect)
