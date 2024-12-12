"""Classes and components for implementing wars and alliances between families.

"""

import enum
from typing import Iterable, Optional

from ordered_set import OrderedSet

from minerva.datetime import SimDate
from minerva.ecs import Component, Entity


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
        "contested_territory",
        "_start_date",
        "_end_date",
    )

    contested_territory: Entity
    """The land they are fighting over."""
    aggressor: Entity
    """The family that started the war by attacking the defender."""
    defender: Entity
    """The family fighting off the aggressor and their allies."""
    aggressor_allies: OrderedSet[Entity]
    """Families allied with the aggressor in this war."""
    defender_allies: OrderedSet[Entity]
    """Families allied with the defender in this war."""
    _start_date: SimDate
    """The date the war started"""
    _end_date: Optional[SimDate]
    """The date the war ended."""

    def __init__(
        self,
        aggressor: Entity,
        defender: Entity,
        contested_territory: Entity,
        start_date: SimDate,
    ) -> None:
        super().__init__()
        self.contested_territory = contested_territory
        self.aggressor = aggressor
        self.defender = defender
        self.start_date = start_date
        self.aggressor_allies = OrderedSet([])
        self.defender_allies = OrderedSet([])
        self.end_date = None

    @property
    def start_date(self) -> SimDate:
        """The date the war started."""
        return self._start_date

    @start_date.setter
    def start_date(self, value: SimDate) -> None:
        """Set the start date."""
        self._start_date = value.copy()

    @property
    def end_date(self) -> Optional[SimDate]:
        """The date the war started."""
        return self._end_date

    @end_date.setter
    def end_date(self, value: Optional[SimDate]) -> None:
        """Set the end date."""
        if value is not None:
            self._end_date = value.copy()
        else:
            self._end_date = None


class WarTracker(Component):
    """Tracks references to all wars the family is currently engaged in."""

    __slots__ = ("offensive_wars", "defensive_wars")

    offensive_wars: OrderedSet[Entity]
    """Wars this family started or is allied with the aggressor."""
    defensive_wars: OrderedSet[Entity]
    """Wars where this family was attacked or is allied with the defender."""

    def __init__(self) -> None:
        super().__init__()
        self.offensive_wars = OrderedSet([])
        self.defensive_wars = OrderedSet([])


class Alliance(Component):
    """Tracks an alliance among a group of families."""

    __slots__ = (
        "founder",
        "founder_family",
        "member_families",
        "_start_date",
        "_end_date",
    )

    founder: Entity
    """The family head that founded the alliance."""
    founder_family: Entity
    """The family the alliance's founder was the head of."""
    member_families: OrderedSet[Entity]
    """All families that belong to the alliance."""
    _start_date: SimDate
    """The date the alliance started."""
    _end_date: Optional[SimDate]
    """The date the alliance ended."""

    def __init__(
        self,
        founder: Entity,
        founder_family: Entity,
        member_families: Iterable[Entity],
        start_date: SimDate,
    ) -> None:
        super().__init__()
        self.founder = founder
        self.founder_family = founder_family
        self.member_families = OrderedSet(member_families)
        self.start_date = start_date
        self.end_date = None

    @property
    def start_date(self) -> SimDate:
        """The date the war started."""
        return self._start_date

    @start_date.setter
    def start_date(self, value: SimDate) -> None:
        """Set the start date."""
        self._start_date = value.copy()

    @property
    def end_date(self) -> Optional[SimDate]:
        """The date the war started."""
        return self._end_date

    @end_date.setter
    def end_date(self, value: Optional[SimDate]) -> None:
        """Set the end date."""
        if value is not None:
            self._end_date = value.copy()
        else:
            self._end_date = None
