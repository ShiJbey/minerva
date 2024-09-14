"""Family Banner sprites and sprite generation.

Each family in the simulation gets a generated flag. There are over 500
flag combinations using the default configuration. This module contains
the implementation for the sprite class, and the factory method generating
the final banners.

"""

from typing import Any, Callable, ClassVar

import pygame
import pygame.gfxdraw
from pygame import SRCALPHA
from pygame.color import Color
from pygame.sprite import Sprite
from pygame.surface import Surface


class FamilyBannerFactory:
    """Creates instances of 32x32 family banners."""

    shape_fns: ClassVar[dict[str, Callable[[Surface, Color], None]]] = {}

    BANNER_POLE_COLOR: ClassVar[str] = "#010101"
    BANNER_OUTLINE_COLOR: ClassVar[str] = "#010101"
    BANNER_POLE_WIDTH: ClassVar[int] = 4
    BANNER_MARGIN: ClassVar[int] = 4
    BANNER_CENTER_SIZE: ClassVar[int] = 16
    TILE_SIZE: ClassVar[int] = 32

    def create_banner_image(
        self,
        color_primary: str,
        color_secondary: str,
        color_tertiary: str,
        shape: str,
    ) -> Surface:
        """Create a new banner image."""
        image = pygame.surface.Surface((self.TILE_SIZE, self.TILE_SIZE), SRCALPHA)

        # Draw the horizontal banner pole
        pygame.gfxdraw.box(
            image,
            (0, 0, self.TILE_SIZE, self.BANNER_POLE_WIDTH),
            Color(self.BANNER_POLE_COLOR),
        )

        # Draw the vertical banner pole
        pygame.gfxdraw.box(
            image,
            (
                (self.TILE_SIZE // 2) - (self.BANNER_POLE_WIDTH // 2),
                0,
                self.BANNER_POLE_WIDTH,
                self.TILE_SIZE,
            ),
            Color(self.BANNER_POLE_COLOR),
        )

        # Draw the flag secondary color outline
        pygame.gfxdraw.filled_polygon(
            image,
            [
                (self.TILE_SIZE - self.BANNER_MARGIN, 0),
                (
                    self.TILE_SIZE - self.BANNER_MARGIN,
                    self.BANNER_MARGIN + self.BANNER_CENTER_SIZE,
                ),
                (
                    (self.TILE_SIZE // 2) + (self.BANNER_POLE_WIDTH // 2),
                    self.TILE_SIZE - self.BANNER_MARGIN,
                ),
                (
                    (self.TILE_SIZE // 2) - (self.BANNER_POLE_WIDTH // 2),
                    self.TILE_SIZE - self.BANNER_MARGIN,
                ),
                (self.BANNER_MARGIN, self.BANNER_MARGIN + self.BANNER_CENTER_SIZE),
                (self.BANNER_MARGIN, 0),
            ],  # Counter clockwise
            Color(color_secondary),
        )

        # Draw the flag primary color
        pygame.gfxdraw.filled_polygon(
            image,
            [
                (24, 4),
                (24, 20),
                (18, 24),
                (14, 24),
                (8, 20),
                (8, 4),
            ],  # Counter clockwise
            Color(color_primary),
        )

        if shape_fn := self.shape_fns.get(shape):
            shape_fn(image, Color(color_tertiary))

        return image

    @classmethod
    def add_shape_fn(
        cls,
        shape_name: str,
        fn: Callable[[Surface, Color], None],
    ) -> None:
        """Add a shape function to the factory."""
        cls.shape_fns[shape_name] = fn

    @classmethod
    def shape_fn(cls, shape_name: str):
        """Decorator function to register a shape function."""

        def wrapper(fn: Callable[[Surface, Color], None]):
            cls.add_shape_fn(shape_name, fn)

        return wrapper


@FamilyBannerFactory.shape_fn("square")
def banner_square(surface: Surface, color: Color) -> None:
    """Draws a square at the center of the banner."""
    pygame.gfxdraw.box(surface, (12, 8, 8, 8), color)


@FamilyBannerFactory.shape_fn("circle")
def banner_circle(surface: Surface, color: Color) -> None:
    """Draws a circle at the center of the banner."""
    pygame.gfxdraw.filled_circle(surface, 16, 12, 4, color)


@FamilyBannerFactory.shape_fn("diamond")
def banner_diamond(surface: Surface, color: Color) -> None:
    """Draws a diamond at the center of the banner."""
    pygame.gfxdraw.filled_polygon(
        surface, [(16, 8), (20, 12), (16, 16), (12, 12)], color
    )


@FamilyBannerFactory.shape_fn("triangle_down")
def banner_triangle_down(surface: Surface, color: Color) -> None:
    """Draws an triangle pointing down at the center of the banner."""
    pygame.gfxdraw.filled_polygon(surface, [(12, 8), (20, 8), (16, 16)], color)


@FamilyBannerFactory.shape_fn("triangle_up")
def banner_triangle_up(surface: Surface, color: Color) -> None:
    """Draws a triangle pointing up at the center of the banner."""
    pygame.gfxdraw.filled_polygon(surface, [(16, 8), (20, 16), (12, 16)], color)


class FamilyBannerSprite(Sprite):
    """A Sprite showing the banner for a family."""

    def __init__(
        self,
        x: int,
        y: int,
        color_primary: str,
        color_secondary: str,
        color_tertiary: str,
        shape: str,
        *groups: Any,
    ) -> None:
        super().__init__(*groups)
        self.image = FamilyBannerSprite._generate_image(
            color_primary, color_secondary, color_tertiary, shape
        )
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    @staticmethod
    def _generate_image(
        color_primary: str,
        color_secondary: str,
        color_tertiary: str,
        shape: str,
    ) -> Surface:

        return FamilyBannerFactory().create_banner_image(
            color_primary, color_secondary, color_tertiary, shape
        )
