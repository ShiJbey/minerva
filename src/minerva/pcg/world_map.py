"""World Map Generation."""

from __future__ import annotations

import random
from itertools import product
from typing import Any, Generator

from minerva.config import Config
from minerva.ecs import GameObject, World
from minerva.pcg.base_types import PCGFactories
from minerva.world_map.components import (
    CartesianGrid,
    CompassDir,
    Territory,
    TerritoryInfo,
    WorldMap,
)

TERRITORY_GENERATION_DEBUG_COLORS = [
    "#e90000",  # red
    "#31d5c8",  # light blue
    "#a538c6",  # violet
    "#cccccc",  # grey
    "#33a7c8",  # darker blue
    "#FF5733",  # (Bright Orange)
    "#33FF57",  # (Lime Green)
    "#FF338C",  # (Crimson)
    "#FFD733",  # (Bright Yellow)
    "#33FFF3",  # (Cyan)
    "#8C33FF",  # (Purple)
    "#FFB833",  # (Amber)
    "#05fb00",  # green
    "#001eba",  # royal blue
    "#fff500",  # yellow
    "#33FF8C",  # (Mint Green)
    "#FF3333",  # (Bright Red)
    "#33A6FF",  # (Sky Blue)
    "#FF3380",  # (Magenta)
    "#FFC733",  # (Gold)
    "#3380FF",  # (Royal Blue)
    "#FF8333",  # (Coral)
    "#33FF33",  # (Neon Green)
    "#33FFB8",  # (Light Green)
]


class TerritoryGenerator:
    """Subdivides a rectangular world map into various territories.

    This generator uses an iterative fill algorithm that starts territories
    as 3x3 squares and fills the space outward until it reaches the border
    of another territory or the edge of the map.

    """

    __slots__ = (
        "territory_grid",
        "borders",
        "n_territories",
        "territories",
        "rng",
        "frontier",
        "is_complete",
    )

    territory_grid: CartesianGrid[int]
    borders: CartesianGrid[CompassDir]
    n_territories: int
    territories: list[TerritoryInfo]
    rng: random.Random
    frontier: list[tuple[int, int]]

    def __init__(
        self,
        size: tuple[int, int],
        n_territories: int,
        seed: int | str | None = None,
    ) -> None:
        if n_territories <= 1:
            raise ValueError("n_territories must be greater than 1")

        self.territory_grid = CartesianGrid(size, lambda: -1)
        self.borders = CartesianGrid(size, lambda: CompassDir.NONE)
        self.n_territories = n_territories
        self.territories: list[TerritoryInfo] = []
        self.rng: random.Random = random.Random(seed)
        self.is_complete: bool = False
        self.frontier = []

    def generate_territories(self) -> None:
        """Generates the territory information and borders in a single calls."""
        for _ in self.step():
            pass

    def step(self) -> Generator[Any, Any, None]:
        """Step through the generation process."""
        if self.is_complete:
            return

        self._generate_centroids()
        yield

        for _ in self._fill_regions():
            yield

        self._determine_borders()
        self.is_complete = True

    def _fill_regions(self) -> Generator[Any, Any, None]:
        """Pop a single position from the frontier and fill the adjacent free space."""

        while self.frontier:

            target_coord = self.frontier.pop(0)
            target_territory_id = self.territory_grid.get(target_coord)
            empty_neighbors = self._get_unclaimed_neighbors(target_coord)

            for neighbor_coord in empty_neighbors:
                self.territory_grid.set(neighbor_coord, target_territory_id)
                self.frontier.append(neighbor_coord)

            yield

    def _get_unclaimed_neighbors(self, coord: tuple[int, int]) -> list[tuple[int, int]]:
        empty_neighbors: list[tuple[int, int]] = []

        for neighbor_coord in self.territory_grid.get_neighbors(coord):
            if self.territory_grid.get(neighbor_coord) == -1:
                empty_neighbors.append(neighbor_coord)

        return empty_neighbors

    def _generate_centroids(self) -> None:
        """Generate starting castle positions to fill territories."""

        # This function samples positions from the world grid to generate territories
        # Each starting point (centroid) is the center of a 3x3 free space in the grid.
        # To ensure there is no overlapping or territories too close to the border,
        # We take the original width & height of the world, subtract 2 to allow for
        # padding on the top/bottom (height) or left/right (width). Then we make
        # the final width and height of the sample area multiples of 3. This allows
        # us to bin the sample space into non-overlapping 3x3 chunks and ensure that
        # no two territories can use the same chunk.

        w = self.territory_grid.get_size()[0] - 2
        r = w % 3
        w_final = w - r

        h = self.territory_grid.get_size()[1] - 2
        r = h % 3
        h_final = h - r

        xs = list(range(int(w_final / 3)))
        ys = list(range(int(h_final / 3)))

        centroid_pos: list[tuple[int, int]] = self.rng.sample(
            list(product(xs, ys)), k=self.n_territories
        )

        for i in range(self.n_territories):

            # Below we reverse the math done above and convert the 3x3 bin coordinate
            # back to world grid coordinates by multiplying by three, adding 1 for the
            # left/top padding, and adding an additional 1 to place the centroid at the
            # middle of the 3x3 block.

            x = (centroid_pos[i][0] * 3) + 2
            y = (centroid_pos[i][1] * 3) + 2

            self.territories.append(
                TerritoryInfo(
                    uid=i,
                    castle_pos=(x, y),
                    color_primary=TERRITORY_GENERATION_DEBUG_COLORS[
                        i % len(TERRITORY_GENERATION_DEBUG_COLORS)
                    ],
                    color_secondary=self.rng.choice(TERRITORY_GENERATION_DEBUG_COLORS),
                )
            )

            self.territory_grid.set((x, y), i)
            self.frontier.append((x, y))

    def _determine_borders(self) -> None:
        for (x, y), territory_id in self.territory_grid.enumerate():
            wall_flags = CompassDir.NONE

            # North
            if (
                self.territory_grid.in_bounds((x, y - 1))
                and self.territory_grid.get((x, y - 1)) != territory_id
            ):
                wall_flags |= CompassDir.NORTH
                self.territories[territory_id].neighbors.append(
                    self.territory_grid.get((x, y - 1))
                )

            # East
            if (
                self.territory_grid.in_bounds((x + 1, y))
                and self.territory_grid.get((x + 1, y)) != territory_id
            ):
                wall_flags |= CompassDir.EAST
                self.territories[territory_id].neighbors.append(
                    self.territory_grid.get((x + 1, y))
                )

            # South
            if (
                self.territory_grid.in_bounds((x, y + 1))
                and self.territory_grid.get((x, y + 1)) != territory_id
            ):
                wall_flags |= CompassDir.SOUTH
                self.territories[territory_id].neighbors.append(
                    self.territory_grid.get((x, y + 1))
                )

            # West
            if (
                self.territory_grid.in_bounds((x - 1, y))
                and self.territory_grid.get((x - 1, y)) != territory_id
            ):
                wall_flags |= CompassDir.WEST
                self.territories[territory_id].neighbors.append(
                    self.territory_grid.get((x - 1, y))
                )

            self.borders.set((x, y), wall_flags)


def generate_world_map(world: World) -> None:
    """Divide the world map into territories and instantiate territories."""

    config = world.resources.get_resource(Config)

    world_map = WorldMap(config.world_size)

    world.resources.add_resource(world_map)

    territory_generator = TerritoryGenerator(
        config.world_size,
        config.n_territories,
    )

    territory_generator.generate_territories()

    world_map.territory_grid = territory_generator.territory_grid.copy()
    world_map.territories = []
    world_map.borders = territory_generator.borders.copy()

    territory_id_to_gameobject: dict[int, GameObject] = {}
    territories: dict[int, GameObject] = {}

    pcg_factories = world.resources.get_resource(PCGFactories)

    for territory_info in territory_generator.territories:
        territory = pcg_factories.territory_factory.generate_territory(world)
        territory_id_to_gameobject[territory_info.uid] = territory
        territories[territory_info.uid] = territory
        world_map.territories.append(territory)

        territory_component = territory.get_component(Territory)
        territory_component.castle_position = territory_info.castle_pos

        # Convert the territory IDs to the UIDs of the territory objects
        for coord, territory_id in world_map.territory_grid.enumerate():
            if territory_id == territory.uid:
                world_map.territory_grid.set(coord, territory.uid)

    # Generate a the neighbor links
    for territory_info in territory_generator.territories:
        territory = territory_id_to_gameobject[territory_info.uid]
        territory_component = territory.get_component(Territory)
        for neighbor in territory_info.neighbors:
            territory_component.neighbors.append(territory_id_to_gameobject[neighbor])
