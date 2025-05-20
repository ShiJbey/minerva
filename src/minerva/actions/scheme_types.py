"""Class definitions for various scheme variations."""

from __future__ import annotations

import dataclasses
from typing import Optional

from minerva.ecs import Component, Entity


class WarScheme(Component):
    """Create a new war scheme"""

    __slots__ = (
        "initiator",
        "start_year",
        "members",
        "aggressor",
        "defender",
        "territory",
        "is_valid",
    )

    aggressor: Entity
    defender: Entity
    territory: Entity
    start_year: int
    """The date the scheme was started."""
    initiator: Entity
    """The character that initiated the scheme."""
    members: list[Entity]
    """All characters involved in planning the scheme."""
    is_valid: bool
    """Is the scheme still valid."""

    def __init__(
        self,
        initiator: Entity,
        aggressor: Entity,
        defender: Entity,
        territory: Entity,
        start_year: int,
    ) -> None:
        super().__init__()
        self.aggressor = aggressor
        self.defender = defender
        self.territory = territory
        self.start_year = start_year
        self.initiator = initiator
        self.members = []
        self.is_valid = True


class CoupScheme(Component):
    """A scheme to overthrow the royal family and establish the coup organizer."""

    __slots__ = ("initiator", "members", "start_year", "is_valid", "target")

    target: Entity
    start_year: int
    """The date the scheme was started."""
    initiator: Entity
    """The character that initiated the scheme."""
    members: list[Entity]
    """All characters involved in planning the scheme."""
    is_valid: bool
    """Is the scheme still valid."""

    def __init__(self, initiator: Entity, target: Entity, start_year: int) -> None:
        super().__init__()
        self.target = target
        self.start_year = start_year
        self.initiator = initiator
        self.members = []
        self.is_valid = True

    def has_character(self, character: Entity) -> bool:
        """Check if a character belongs to this scheme."""
        for entry in self.members:
            if entry == character:
                return True

        return False

    def remove_character(self, character: Entity) -> None:
        """Remove a character from the member list."""
        self.members = [m for m in self.members if m != character]


@dataclasses.dataclass()
class AllianceSchemeMember:
    """An entry in an AllianceScheme member list."""

    character: Entity
    family: Entity


class AllianceScheme(Component):
    """Create a new alliance scheme"""

    __slots__ = ("initiator", "initiator_family", "members", "start_year", "is_valid")

    start_year: int
    """The date the scheme was started."""
    initiator: Entity
    """The character that initiated the scheme."""
    initiator_family: Entity
    """The family the initiator belongs to."""
    members: list[AllianceSchemeMember]
    """All characters involved in planning the scheme."""
    is_valid: bool
    """Is the scheme still valid."""

    def __init__(
        self, initiator: Entity, initiator_family: Entity, start_year: int
    ) -> None:
        super().__init__()
        self.start_year = start_year
        self.initiator = initiator
        self.initiator_family = initiator_family
        self.members = []
        self.is_valid = True

    def has_character(self, character: Entity) -> bool:
        """Check if a character belongs to this scheme."""
        for entry in self.members:
            if entry.character == character:
                return True

        return False

    def remove_character(self, character: Entity) -> None:
        """Remove a character from the member list."""
        self.members = [m for m in self.members if m.character != character]


class SchemeManager(Component):
    """Tracks all schemes that a character has initiated and is a member of."""

    __slots__ = ("alliance_scheme", "war_scheme", "coup_scheme")

    alliance_scheme: Optional[Entity]
    war_scheme: Optional[Entity]
    coup_scheme: Optional[Entity]

    def __init__(self) -> None:
        super().__init__()
        self.alliance_scheme = None
        self.war_scheme = None
        self.coup_scheme = None
