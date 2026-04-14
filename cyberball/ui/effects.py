"""Glow effects and drawing helpers."""
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
