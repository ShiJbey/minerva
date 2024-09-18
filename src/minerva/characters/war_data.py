"""Classes and components for implementing wars and alliances between families.

"""

import enum

from ordered_set import OrderedSet

from minerva.datetime import SimDate
from minerva.ecs import Component, GameObject


class WarRole(enum.IntEnum):
    """Roles embodied by families within a war."""

    AGGRESSOR = enum.auto()
    """The family that started the war."""
    DEFENDER = enum.auto()
    """The family under attack."""
    AGGRESSOR_ALLY = enum.auto()
    """A family allied with the aggressor."""
    DEFENDER_ALLY = enum.auto()
    """A family allied with the defender."""


class War(Component):
    """Tracks information about a war between families."""

    __slots__ = (
        "aggressor",
        "defender",
        "aggressor_allies",
        "defender_allies",
        "start_date",
    )

    aggressor: GameObject
    """The family that started the war by attacking the defender."""
    defender: GameObject
    """The family fighting off the aggressor and their allies."""
    aggressor_allies: OrderedSet[GameObject]
    """Families allied with the aggressor in this war."""
    defender_allies: OrderedSet[GameObject]
    """Families allied with the defender in this war."""
    start_date: SimDate
    """The date the war started"""

    def __init__(
        self, aggressor: GameObject, defender: GameObject, start_date: SimDate
    ) -> None:
        super().__init__()
        self.aggressor = aggressor
        self.defender = defender
        self.start_date = start_date.copy()
        self.aggressor_allies = OrderedSet([])
        self.defender_allies = OrderedSet([])


class WarTracker(Component):
    """Tracks references to all wars the family is currently engaged in."""

    __slots__ = ("offensive_wars", "defensive_wars")

    offensive_wars: OrderedSet[GameObject]
    """Wars this family started or is allied with the aggressor."""
    defensive_wars: OrderedSet[GameObject]
    """Wars where this family was attacked or is allied with the defender."""

    def __init__(self) -> None:
        super().__init__()
        self.offensive_wars = OrderedSet([])
        self.defensive_wars = OrderedSet([])


class Alliance(Component):
    """Tracks an alliance from one family to another."""

    __slots__ = ("family", "ally", "start_date")

    family: GameObject
    """The subject of the alliance."""
    ally: GameObject
    """The other family the subject is allied with."""
    start_date: SimDate
    """The date the alliance started."""

    def __init__(
        self, family: GameObject, ally: GameObject, start_date: SimDate
    ) -> None:
        super().__init__()
        self.family = family
        self.ally = ally
        self.start_date = start_date


class AllianceTracker(Component):
    """Tracks references to all alliances a character belongs to."""

    __slots__ = ("alliances",)

    alliances: dict[int, GameObject]
    """References to all current alliances. (Ally ID mapped to alliance)"""

    def __init__(self) -> None:
        super().__init__()
        self.alliances = {}
