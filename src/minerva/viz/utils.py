"""Minerva Visualization Utility Functions."""

import pygame


def draw_text(
    display: pygame.Surface,
    text: str,
    x: int,
    y: int,
    font: pygame.font.Font,
    color: tuple[int, int, int] = (255, 255, 255),
) -> None:
    """Draw text to the screen."""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.center = (x, y)
    display.blit(text_surface, text_rect)
