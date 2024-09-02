"""Various Tile Sprites."""

import enum
import pathlib
from typing import Any, Optional

import pygame
from pygame.sprite import Sprite

from minerva.constants import TILE_SIZE
from minerva.ecs import GameObject
from minerva.settlements.base_types import Settlement
from minerva.world_map.components import CompassDir


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
        self.rect = self.image.get_rect()
        settlement_component = settlement.get_component(Settlement)
        pos_x, pos_y = settlement_component.castle_position
        self.rect.topleft = (pos_x * TILE_SIZE, pos_y * TILE_SIZE)


class WallTileSprite(Sprite):
    """Spite for a wall tile."""

    def __init__(
        self, position: tuple[int, int], image_path: str, *groups: Any
    ) -> None:
        super().__init__(*groups)
        self.image = pygame.transform.scale(
            pygame.image.load(image_path).convert_alpha(), (32, 32)
        )
        self.rect = self.image.get_rect()
        self.rect.topleft = position


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


def get_wall_spite(
    position: tuple[int, int], wall_flags: CompassDir
) -> Optional[WallTileSprite]:
    """Create a new wall sprite given the flags."""
    if wall_flags == CompassDir.SOUTH:
        return WallTileSprite(
            position,
            str(
                pathlib.Path(__file__).parent / "resources/images/WallTiles/Wall_B.png"
            ),
        )

    if wall_flags == CompassDir.WEST:
        return WallTileSprite(
            position,
            str(
                pathlib.Path(__file__).parent / "resources/images/WallTiles/Wall_L.png"
            ),
        )

    if wall_flags == CompassDir.NORTH:
        return WallTileSprite(
            position,
            str(
                pathlib.Path(__file__).parent / "resources/images/WallTiles/Wall_T.png"
            ),
        )

    if wall_flags == CompassDir.EAST:
        return WallTileSprite(
            position,
            str(
                pathlib.Path(__file__).parent / "resources/images/WallTiles/Wall_R.png"
            ),
        )

    if wall_flags == CompassDir.SOUTH | CompassDir.WEST:
        return WallTileSprite(
            position,
            str(
                pathlib.Path(__file__).parent / "resources/images/WallTiles/Wall_BL.png"
            ),
        )

    if wall_flags == CompassDir.SOUTH | CompassDir.EAST:
        return WallTileSprite(
            position,
            str(
                pathlib.Path(__file__).parent / "resources/images/WallTiles/Wall_BR.png"
            ),
        )

    if wall_flags == CompassDir.WEST | CompassDir.EAST:
        return WallTileSprite(
            position,
            str(
                pathlib.Path(__file__).parent / "resources/images/WallTiles/Wall_LR.png"
            ),
        )

    if wall_flags == CompassDir.NORTH | CompassDir.SOUTH:
        return WallTileSprite(
            position,
            str(
                pathlib.Path(__file__).parent / "resources/images/WallTiles/Wall_TB.png"
            ),
        )

    if wall_flags == CompassDir.NORTH | CompassDir.WEST:
        return WallTileSprite(
            position,
            str(
                pathlib.Path(__file__).parent / "resources/images/WallTiles/Wall_TL.png"
            ),
        )

    if wall_flags == CompassDir.NORTH | CompassDir.EAST:
        return WallTileSprite(
            position,
            str(
                pathlib.Path(__file__).parent / "resources/images/WallTiles/Wall_TR.png"
            ),
        )

    if wall_flags == CompassDir.NORTH | CompassDir.EAST | CompassDir.WEST:
        return WallTileSprite(
            position,
            str(
                pathlib.Path(__file__).parent
                / "resources/images/WallTiles/Wall_TRL.png"
            ),
        )

    if wall_flags == CompassDir.NORTH | CompassDir.EAST | CompassDir.SOUTH:
        return WallTileSprite(
            position,
            str(
                pathlib.Path(__file__).parent
                / "resources/images/WallTiles/Wall_TRB.png"
            ),
        )

    if wall_flags == CompassDir.EAST | CompassDir.SOUTH | CompassDir.WEST:
        return WallTileSprite(
            position,
            str(
                pathlib.Path(__file__).parent
                / "resources/images/WallTiles/Wall_RBL.png"
            ),
        )

    if wall_flags == CompassDir.NORTH | CompassDir.SOUTH | CompassDir.WEST:
        return WallTileSprite(
            position,
            str(
                pathlib.Path(__file__).parent
                / "resources/images/WallTiles/Wall_TBL.png"
            ),
        )

    return None
