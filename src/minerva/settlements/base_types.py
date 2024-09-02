"""Minerva Settlement System."""

from typing import Optional

from ordered_set import OrderedSet

from minerva.ecs import Component, GameObject
from minerva.stats.base_types import IStatCalculationStrategy, StatComponent


class Settlement(Component):
    """A settlement where character's live."""

    __slots__ = (
        "name",
        "controlling_family",
        "business_types",
        "territory_id",
        "neighbors",
        "castle_position",
    )

    name: str
    """The settlement's name."""
    controlling_family: Optional[GameObject]
    """ID of the family that controls this settlement."""
    business_types: list[str]
    """Types of businesses that exist in this settlement."""
    neighbors: OrderedSet[GameObject]
    """Neighboring settlements."""
    castle_position: tuple[int, int]
    """The position of the castle on the screen."""

    def __init__(
        self,
        name: str,
        controlling_family: Optional[GameObject] = None,
        business_types: Optional[list[str]] = None,
    ) -> None:
        super().__init__()
        self.name = name
        self.controlling_family = controlling_family
        self.business_types = business_types if business_types else []
        self.neighbors = OrderedSet([])
        self.castle_position: tuple[int, int] = (0, 0)


class PopulationHappiness(StatComponent):
    """A settlement where character's live."""

    __stat_name__ = "PopulationHappiness"

    def __init__(self, calculation_strategy: IStatCalculationStrategy) -> None:
        super().__init__(calculation_strategy, 0, bounds=(-100, 100))
