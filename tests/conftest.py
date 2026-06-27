"""Shared pytest fixtures – sets up pygame headless before any test."""
import os
import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


@pytest.fixture(scope="session", autouse=True)
def pygame_init():
    import pygame
    pygame.init()
    pygame.display.set_mode((800, 600))
    yield
    pygame.quit()
