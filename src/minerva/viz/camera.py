"""Minerva Visualization Camera."""

from __future__ import annotations

import pygame.math


class Camera:
    """A 2D PyGame Camera."""

    def __init__(self, width: int, height: int, speed: int = 3) -> None:
        self.width = width
        self.height = height
        self.scroll = pygame.math.Vector2(64, 64)
        self.speed = speed

    def update(self, delta: pygame.math.Vector2) -> None:
        """Update the position of the camera."""
        self.scroll += delta * self.speed
