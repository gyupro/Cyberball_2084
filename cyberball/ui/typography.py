"""Centralized font sizes for UI consistency."""
import pygame

_cached = {}

SIZES = {
    'title': 72,
    'heading': 36,
    'body': 20,
    'small': 14,
}


def get(name):
    if not pygame.font.get_init():
        pygame.font.init()
    if name not in _cached:
        _cached[name] = pygame.font.Font(None, SIZES.get(name, SIZES['body']))
    return _cached[name]


def title():
    return get('title')


def heading():
    return get('heading')


def body():
    return get('body')


def small():
    return get('small')
