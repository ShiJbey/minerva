"""Minerva Settlement System."""

from typing import Optional

from minerva.ecs import Component, GameObject
from minerva.stats.base_types import IStatCalculationStrategy, StatComponent


class WorldGrid:
    """Manages a cartesian grid of cells where each cell contains a settlement."""

    __slots__ = ("_grid", "_size")

    _grid: list[list[Optional[GameObject]]]
    _size: tuple[int, int]

    def __init__(self, size: tuple[int, int]) -> None:
        self._grid = []
        self._size = size

        for _ in range(size[1]):
            self._grid.append([None for _ in range(size[0])])

    @property
    def n_rows(self) -> int:
        """Get num rows in grid."""
        return self._size[1]

    @property
    def n_cols(self) -> int:
        """Get num cols in grid."""
        return self._size[0]

    def set(self, x: int, y: int, settlement: GameObject) -> None:
        """Set what settlement is at a position."""
        self._grid[y][x] = settlement

    def get(self, x: int, y: int) -> Optional[GameObject]:
        """Get settlement at the given position."""

        if 0 <= x < self._size[0] and 0 <= y < self._size[1]:
            return self._grid[y][x]

        return None

    def get_neighbors(self, x: int, y: int) -> list[GameObject]:
        """Get all settlements that neighbor the given position."""
        neighbors: list[GameObject] = []

        if top_neighbor := self.get(x, y - 1):
            neighbors.append(top_neighbor)

        if right_neighbor := self.get(x + 1, y):
            neighbors.append(right_neighbor)

        if bottom_neighbor := self.get(x, y + 1):
            neighbors.append(bottom_neighbor)

        if left_neighbor := self.get(x - 1, y):
            neighbors.append(left_neighbor)

        return neighbors


class Settlement(Component):
    """A settlement where character's live."""

    __slots__ = (
        "name",
        "controlling_clan",
        "business_types",
    )

    name: str
    """The settlement's name."""
    controlling_clan: Optional[GameObject]
    """ID of the clan that controls this settlement."""
    business_types: list[str]
    """Types of businesses that exist in this settlement."""

    def __init__(
        self,
        name: str,
        controlling_clan: Optional[GameObject] = None,
        business_types: Optional[list[str]] = None,
    ) -> None:
        super().__init__()
        self.name = name
        self.controlling_clan = controlling_clan
        self.business_types = business_types if business_types else []


class PopulationHappiness(StatComponent):
    """A settlement where character's live."""

    __stat_name__ = "PopulationHappiness"

    def __init__(self, calculation_strategy: IStatCalculationStrategy) -> None:
        super().__init__(calculation_strategy, 0, bounds=(-100, 100))
