"""World Map Generation."""

from __future__ import annotations

import random
from itertools import product
from typing import Generator, Any

from minerva.config import Config
from minerva.constants import TERRITORY_GENERATION_DEBUG_COLORS
from minerva.ecs import GameObject, World
from minerva.pcg.settlement import generate_settlement
from minerva.world_map.components import (
    CartesianGrid,
    TerritoryInfo,
    CompassDir,
    WorldMap, Settlement,
)


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
    """Divide the world map into territories and instantiate settlements."""

    config = world.resources.get_resource(Config)

    world_map = WorldMap(config.world_size)

    world.resources.add_resource(world_map)

    territory_generator = TerritoryGenerator(
        config.world_size,
        config.n_territories,
    )

    territory_generator.generate_territories()

    world_map.territory_grid = territory_generator.territory_grid.copy()
    world_map.settlements = []
    world_map.borders = territory_generator.borders.copy()

    territory_id_to_settlement: dict[int, GameObject] = {}
    settlements: dict[int, GameObject] = {}

    for territory in territory_generator.territories:
        settlement = generate_settlement(world)
        territory_id_to_settlement[territory.uid] = settlement
        settlements[settlement.uid] = settlement
        world_map.settlements.append(settlement)

        settlement_component = settlement.get_component(Settlement)
        settlement_component.castle_position = territory.castle_pos

        # Convert the territory IDs to the UIDs of the settlement objects
        for coord, territory_id in world_map.territory_grid.enumerate():
            if territory_id == territory.uid:
                world_map.territory_grid.set(coord, settlement.uid)

    # Generate a the neighbor links
    for territory in territory_generator.territories:
        settlement = territory_id_to_settlement[territory.uid]
        settlement_component = settlement.get_component(Settlement)
        for neighbor in territory.neighbors:
            settlement_component.neighbors.append(territory_id_to_settlement[neighbor])