"""Various Tile Sprites."""

import enum
import pathlib
from typing import Any

import pygame
import pygame.gfxdraw
from pygame import SRCALPHA
from pygame.sprite import Sprite

from minerva.constants import (
    SETTLEMENT_BORDER_PADDING,
    SETTLEMENT_BORDER_WIDTH,
    TILE_SIZE,
)
from minerva.ecs import GameObject
from minerva.viz.game_events import gameobject_wiki_shown
from minerva.world_map.components import CompassDir, Settlement


class ClanFlagSprite(Sprite):
    """A sprite showing the flag of a clan."""

    def __init__(
        self,
        primary_color: pygame.color.Color,
        secondary_color: pygame.color.Color,
        parent: Sprite,
        *groups: Any,
    ) -> None:
        super().__init__(*groups)
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.parent = parent
        self.redraw_image()

    def set_primary_color(self, color: pygame.color.Color) -> None:
        """Set the primary color of the flag."""
        self.primary_color = color
        self.redraw_image()

    def set_secondary_color(self, color: pygame.color.Color) -> None:
        """Set the secondary color of the flag."""
        self.secondary_color = color
        self.redraw_image()

    def redraw_image(self) -> None:
        """Re-render the sprite image."""
        self.image = pygame.surface.Surface((TILE_SIZE, TILE_SIZE), SRCALPHA)
        self.rect = self.image.get_rect()

        # Draw the top bar
        pygame.gfxdraw.box(
            self.image,
            (0, 0, TILE_SIZE, 4),
            pygame.color.Color("#010101"),
        )

        # Draw the flag pole
        pygame.gfxdraw.box(
            self.image,
            (14, 0, 4, TILE_SIZE),
            pygame.color.Color("#010101"),
        )

        # Draw the flag secondary color outline
        pygame.gfxdraw.filled_polygon(
            self.image,
            [
                (28, 0),
                (28, 20),
                (18, 28),
                (14, 28),
                (4, 20),
                (4, 0),
            ],  # Counter clockwise
            self.secondary_color,
        )

        # Draw the flag primary color
        pygame.gfxdraw.filled_polygon(
            self.image,
            [
                (24, 4),
                (24, 20),
                (18, 24),
                (14, 24),
                (8, 20),
                (8, 4),
            ],  # Counter clockwise
            self.primary_color,
        )

        # Draw the flag black outline
        pygame.gfxdraw.polygon(
            self.image,
            [
                (28, 0),
                (28, 20),
                (18, 28),
                (14, 28),
                (4, 20),
                (4, 0),
            ],  # Counter clockwise
            pygame.color.Color("#010101"),
        )

        # Draw the flag symbol (secondary-colored circle)
        pygame.gfxdraw.filled_circle(self.image, 16, 12, 4, self.secondary_color)

        # Fix positioning
        assert self.parent.rect
        self.rect.centerx = self.parent.rect.centerx
        self.rect.top = self.parent.rect.top - TILE_SIZE


class LabelSprite(Sprite):
    """A string label associated with a sprite."""

    def __init__(
        self,
        text: str,
        font: pygame.font.Font,
        parent: Sprite,
        *groups: Any,
        text_color: str = "#ffffff",
        bg_color: str = "#000000",
    ) -> None:
        super().__init__(*groups)
        self.parent = parent
        self.text = text
        self.image = font.render(f"   {text}   ", True, text_color, bgcolor=bg_color)
        self.rect = self.image.get_rect()
        assert self.parent.rect
        self.rect.centerx = self.parent.rect.centerx
        self.rect.centery = self.parent.rect.bottom + TILE_SIZE // 3

    # def update(self, *args, **kwargs):
    #     self.rect = self.image.get_rect()
    #     self.rect.centerx = self.parent.rect.centerx
    #     self.rect.centery = self.parent.rect.bottom + TILE_SIZE // 3


class CrownSprite(Sprite):
    """Crown sprite to denote location of royal family."""

    def __init__(self, parent: Sprite, *groups: Any) -> None:
        super().__init__(*groups)
        self.image = pygame.transform.scale(
            pygame.image.load(
                str(pathlib.Path(__file__).parent / "resources/images/crown.png"),
            ).convert_alpha(),
            (TILE_SIZE, TILE_SIZE),
        )
        self.rect = self.image.get_rect()
        self.parent = parent
        assert self.parent.rect
        parent_x, parent_y = self.parent.rect.topleft
        self.rect.topleft = (parent_x - TILE_SIZE, parent_y)


class CastleSprite(Sprite):
    """A sprite of a settlement castle."""

    def __init__(self, settlement: GameObject, *groups: Any) -> None:
        super().__init__(*groups)
        self.image = pygame.transform.scale(
            pygame.image.load(
                str(pathlib.Path(__file__).parent / "resources/images/castle.png"),
            ).convert_alpha(),
            (TILE_SIZE, TILE_SIZE),
        )
        self.settlement = settlement
        self.rect = self.image.get_rect()
        settlement_component = settlement.get_component(Settlement)
        pos_x, pos_y = settlement_component.castle_position
        self.rect.topleft = (pos_x * TILE_SIZE, pos_y * TILE_SIZE)

    def on_click(self) -> None:
        """Function called when this castle is clicked by the player."""
        gameobject_wiki_shown.emit(self.settlement.uid)


class BorderSprite(Sprite):
    """A sprite showing the flag of a clan."""

    def __init__(
        self,
        position: tuple[int, int],
        primary_color: pygame.color.Color,
        secondary_color: pygame.color.Color,
        border_flags: CompassDir,
        *groups: Any,
    ) -> None:
        super().__init__(*groups)
        self.position = position
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.border_flags = border_flags
        self.redraw_image()

    def set_primary_color(self, color: pygame.color.Color) -> None:
        """Set the primary color of the flag."""
        self.primary_color = color
        self.redraw_image()

    def set_secondary_color(self, color: pygame.color.Color) -> None:
        """Set the secondary color of the flag."""
        self.secondary_color = color
        self.redraw_image()

    def redraw_image(self) -> None:
        """Re-render the sprite image."""
        self.image = pygame.surface.Surface((TILE_SIZE, TILE_SIZE)).convert_alpha()
        self.image.set_colorkey((0, 0, 0))  # Some section will be transparent.
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.position[0], self.position[1])

        # Draw the primary color as a box
        pygame.gfxdraw.box(
            self.image,
            (
                SETTLEMENT_BORDER_PADDING,
                SETTLEMENT_BORDER_PADDING,
                TILE_SIZE - (2 * SETTLEMENT_BORDER_PADDING),
                TILE_SIZE - (2 * SETTLEMENT_BORDER_PADDING),
            ),
            self.primary_color,
        )

        # Draw the secondary vertical and horizontal boxes
        pygame.gfxdraw.box(
            self.image,
            (
                SETTLEMENT_BORDER_PADDING,
                SETTLEMENT_BORDER_PADDING + 11,
                TILE_SIZE - (2 * SETTLEMENT_BORDER_PADDING),
                TILE_SIZE // 3,
            ),
            self.secondary_color,
        )

        pygame.gfxdraw.box(
            self.image,
            (
                SETTLEMENT_BORDER_PADDING + 11,
                SETTLEMENT_BORDER_PADDING,
                TILE_SIZE // 3,
                TILE_SIZE - (2 * SETTLEMENT_BORDER_PADDING),
            ),
            self.secondary_color,
        )

        top_offset: int = (
            SETTLEMENT_BORDER_PADDING + SETTLEMENT_BORDER_WIDTH
            if CompassDir.NORTH in self.border_flags
            else 0
        )

        left_offset: int = (
            SETTLEMENT_BORDER_PADDING + SETTLEMENT_BORDER_WIDTH
            if CompassDir.WEST in self.border_flags
            else 0
        )

        width: int = (
            TILE_SIZE
            - left_offset
            - (
                SETTLEMENT_BORDER_PADDING + SETTLEMENT_BORDER_WIDTH
                if CompassDir.EAST in self.border_flags
                else 0
            )
        )

        height: int = (
            TILE_SIZE
            - top_offset
            - (
                SETTLEMENT_BORDER_PADDING + SETTLEMENT_BORDER_WIDTH
                if CompassDir.SOUTH in self.border_flags
                else 0
            )
        )

        pygame.gfxdraw.box(
            self.image,
            (left_offset, top_offset, width, height),
            pygame.color.Color("#000000"),
        )


class TerrainTileSprite(Sprite):
    """Sprite for terrain."""

    def __init__(
        self, position: tuple[int, int], image_path: str, *groups: Any
    ) -> None:
        super().__init__(*groups)
        self.image = pygame.transform.scale(
            pygame.image.load(image_path).convert_alpha(), (32, 32)
        )
        self.rect = self.image.get_rect()
        self.rect.topleft = position


class TerrainType(enum.Enum):
    """Wall tile types."""

    WATER_DEEP = enum.auto()
    WATER_SHALLOW = enum.auto()
    WATER_SHALLOWEST = enum.auto()
    SAND = enum.auto()
    GRASS = enum.auto()
    GRASS_LONG = enum.auto()


def get_terrain_tile(
    terrain_type: TerrainType, position: tuple[int, int]
) -> TerrainTileSprite:
    """Generate terrain tile."""

    if terrain_type == TerrainType.GRASS:
        return TerrainTileSprite(
            position, str(pathlib.Path(__file__).parent / "resources/images/grass.png")
        )

    raise ValueError(f"Unsupported terrain type: {terrain_type}")
