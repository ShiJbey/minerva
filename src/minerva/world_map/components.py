"""World Map Components and Classes."""

from __future__ import annotations

import enum
import itertools
from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, Iterator, Optional, TypeVar

from ordered_set import OrderedSet

from minerva.datetime import SimDate
from minerva.ecs import Component, Entity
from minerva.stats.base_types import IStatCalculationStrategy, StatComponent

_GT = TypeVar("_GT")  # Generic Grid Type variable


class GridBase(ABC, Generic[_GT]):
    """An abstract base class for a grid of values."""

    @abstractmethod
    def get_size(self) -> tuple[int, int]:
        """The size of the grid."""
        raise NotImplementedError()

    @abstractmethod
    def get(self, coord: tuple[int, int]) -> _GT:
        """Get the value at the coordinates or None if out of bounds."""
        raise NotImplementedError()

    @abstractmethod
    def set(self, coord: tuple[int, int], value: _GT) -> None:
        """Set a value in the grid."""
        raise NotImplementedError()

    @abstractmethod
    def in_bounds(self, coord: tuple[int, int]) -> bool:
        """Check if a position is within the bounds of the grid."""
        raise NotImplementedError()

    @abstractmethod
    def get_neighbors(
        self, coord: tuple[int, int], **kwargs: Any
    ) -> list[tuple[int, int]]:
        """Get all the adjacent grid cells."""
        raise NotImplementedError()

    @abstractmethod
    def iter_cells(self) -> Iterator[_GT]:
        """Iterate the cells of the grid."""
        raise NotImplementedError()

    @abstractmethod
    def enumerate(self) -> Iterator[tuple[tuple[int, int], _GT]]:
        """Enumerate the coordinates and cell values."""
        raise NotImplementedError()

    def __iter__(self) -> Iterator[_GT]:
        return self.iter_cells()

    @abstractmethod
    def copy(self) -> GridBase[_GT]:
        """Make a copy of the grid."""
        raise NotImplementedError()


class CartesianNeighborhoodCache:
    """A cache entry for a cartesian grid."""

    __slots__ = ("coord", "neighbors", "includes_diagonals")

    coord: tuple[int, int]
    neighbors: list[tuple[int, int]]
    includes_diagonals: bool

    def __init__(
        self,
        coord: tuple[int, int],
        neighbors: list[tuple[int, int]],
        includes_diagonals: bool,
    ) -> None:
        self.coord = coord
        self.neighbors = neighbors
        self.includes_diagonals = includes_diagonals


class CartesianGrid(GridBase[_GT]):
    """A cartesian grid of values."""

    __slots__ = ("_size", "_cells", "_neighbor_cache", "_default_factory")

    _size: tuple[int, int]
    _cells: list[list[_GT]]
    _neighbor_cache: dict[tuple[int, int], CartesianNeighborhoodCache]
    _default_factory: Callable[[], _GT]

    def __init__(
        self, size: tuple[int, int], default_factory: Callable[[], _GT]
    ) -> None:
        super().__init__()
        self._size = size
        self._cells = []
        self._neighbor_cache = {}
        self._default_factory = default_factory

        for _ in range(size[1]):
            row: list[_GT] = []

            for _ in range(size[0]):
                row.append(default_factory())

            self._cells.append(row)

    def get_size(self) -> tuple[int, int]:
        """The size of the grid."""
        return self._size

    def get(self, coord: tuple[int, int]) -> _GT:
        if self.in_bounds(coord):
            return self._cells[coord[1]][coord[0]]

        raise ValueError(f"{coord} is not within the bound of the grid.")

    def set(self, coord: tuple[int, int], value: _GT) -> None:
        if not self.in_bounds(coord):
            raise ValueError(f"{coord} is not within the bound of the grid.")

        self._cells[coord[1]][coord[0]] = value

    def in_bounds(self, coord: tuple[int, int]) -> bool:
        return 0 <= coord[0] < self._size[0] and 0 <= coord[1] < self._size[1]

    def get_neighbors(
        self, coord: tuple[int, int], include_diagonals: bool = False, **kwargs: Any
    ) -> list[tuple[int, int]]:

        if cache_entry := self._neighbor_cache.get(coord):
            if cache_entry.includes_diagonals == include_diagonals:
                return cache_entry.neighbors

        x, y = coord
        neighbors: list[tuple[int, int]] = []

        # North
        if self.in_bounds((x, y - 1)) and self._cells[y - 1][x] == -1:
            neighbors.append((x, y - 1))

        # North-East
        if (
            self.in_bounds((x + 1, y - 1))
            and self._cells[y - 1][x + 1] == -1
            and include_diagonals
        ):
            neighbors.append((x + 1, y - 1))

        # East
        if self.in_bounds((x + 1, y)) and self._cells[y][x + 1] == -1:
            neighbors.append((x + 1, y))

        # South-East
        if (
            self.in_bounds((x + 1, y + 1))
            and self._cells[y + 1][x + 1] == -1
            and include_diagonals
        ):
            neighbors.append((x + 1, y + 1))

        # South
        if self.in_bounds((x, y + 1)) and self._cells[y + 1][x] == -1:
            neighbors.append((x, y + 1))

        # South-West
        if (
            self.in_bounds((x - 1, y + 1))
            and self._cells[y + 1][x - 1] == -1
            and include_diagonals
        ):
            neighbors.append((x - 1, y + 1))

        # West
        if self.in_bounds((x - 1, y)) and self._cells[y][x - 1] == -1:
            neighbors.append((x - 1, y))

        # North-West
        if (
            self.in_bounds((x - 1, y - 1))
            and self._cells[y - 1][x - 1] == -1
            and include_diagonals
        ):
            neighbors.append((x - 1, y - 1))

        self._neighbor_cache[coord] = CartesianNeighborhoodCache(
            coord=coord, neighbors=[*neighbors], includes_diagonals=include_diagonals
        )

        return neighbors

    def iter_cells(self) -> Iterator[_GT]:
        return itertools.chain(*self._cells)

    def enumerate(self) -> Iterator[tuple[tuple[int, int], _GT]]:
        for y in range(self._size[1]):
            for x in range(self._size[0]):
                yield (x, y), self._cells[y][x]

    def copy(self) -> CartesianGrid[_GT]:
        new_grid = CartesianGrid(self._size, default_factory=self._default_factory)

        for coord, value in self.enumerate():
            new_grid.set(coord, value)

        return new_grid


class WorldMap:
    """Singleton that tracks world map information."""

    __slots__ = ("_size", "territory_grid", "borders", "territories")

    _size: tuple[int, int]
    """The width (x) and height (y) of the world map."""
    territory_grid: CartesianGrid[int]
    """A grid where each cell contains the ID of the territory it belongs to."""
    borders: CartesianGrid[CompassDir]
    """Border walls."""
    territories: list[Entity]
    """Information about territories."""

    def __init__(self, size: tuple[int, int]) -> None:
        self._size = size
        self.territory_grid = CartesianGrid(size, lambda: -1)
        self.borders = CartesianGrid(size, lambda: CompassDir.NONE)
        self.territories: list[Entity] = []

    @property
    def size(self) -> tuple[int, int]:
        """The size of the world map."""
        return self._size


class TerritoryInfo:
    """Information about a territory."""

    __slots__ = ("uid", "castle_pos", "color_primary", "color_secondary", "neighbors")

    uid: int
    castle_pos: tuple[int, int]
    color_primary: str
    color_secondary: str
    neighbors: OrderedSet[int]

    def __init__(
        self,
        uid: int,
        castle_pos: tuple[int, int],
        color_primary: str,
        color_secondary: str,
    ) -> None:
        self.uid = uid
        self.castle_pos = castle_pos
        self.color_primary = color_primary
        self.color_secondary = color_secondary
        self.neighbors = OrderedSet([])


class CompassDir(enum.IntFlag):
    """Compass directions."""

    NONE = 0
    SOUTH = enum.auto()
    WEST = enum.auto()
    EAST = enum.auto()
    NORTH = enum.auto()


class Territory(Component):
    """A territory of the map, controlled by a family."""

    __slots__ = (
        "name",
        "controlling_family",
        "territory_id",
        "neighbors",
        "castle_position",
        "political_influence",
        "families",
    )

    name: str
    """The territory's name."""
    controlling_family: Optional[Entity]
    """ID of the family that controls this territory."""
    neighbors: OrderedSet[Entity]
    """Neighboring territories."""
    castle_position: tuple[int, int]
    """The position of the castle on the screen."""
    political_influence: dict[Entity, int]
    """The Political influence held by all families in the territory."""
    families: OrderedSet[Entity]
    """The families that reside at this territory."""

    def __init__(
        self,
        name: str,
        controlling_family: Optional[Entity] = None,
    ) -> None:
        super().__init__()
        self.name = name
        self.controlling_family = controlling_family
        self.neighbors = OrderedSet([])
        self.castle_position: tuple[int, int] = (0, 0)
        self.political_influence = {}
        self.families = OrderedSet([])


class PopulationHappiness(StatComponent):
    """Tracks the happiness of general population (small folk) of a territory."""

    def __init__(
        self,
        base_value: float,
        max_value: float,
        calculation_strategy: IStatCalculationStrategy,
    ) -> None:
        super().__init__(
            calculation_strategy,
            base_value=base_value,
            bounds=(0, max_value),
            is_discrete=True,
        )


class InRevolt(Component):
    """Tags a territory as being in revolt."""

    __slots__ = ("_start_date",)

    def __init__(self, start_date: SimDate) -> None:
        super().__init__()
        self.start_date = start_date

    @property
    def start_date(self) -> SimDate:
        """The date the revolt start."""
        return self._start_date

    @start_date.setter
    def start_date(self, value: SimDate) -> None:
        """Set the date the revolt started."""
        self._start_date = value.copy()
