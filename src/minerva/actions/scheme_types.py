"""Class definitions for various scheme variations."""

from __future__ import annotations

from minerva.actions.base_types import Scheme, SchemeData
from minerva.ecs import Entity


class WarScheme(SchemeData):
    """Create a new war scheme"""

    __slots__ = ("aggressor", "defender", "territory")

    aggressor: Entity
    defender: Entity
    territory: Entity

    def __init__(
        self,
        aggressor: Entity,
        defender: Entity,
        territory: Entity,
    ) -> None:
        super().__init__()
        self.aggressor = aggressor
        self.defender = defender
        self.territory = territory

    def get_description(self, scheme: Scheme) -> str:
        """Get a string description of the scheme."""
        return (
            f"{self.aggressor.name_with_uid} is planning to start an war against "
            f"{self.defender.name_with_uid} for the {self.territory.name_with_uid} "
            "territory."
        )


class CoupScheme(SchemeData):
    """A scheme to overthrow the royal family and establish the coup organizer."""

    __slots__ = ("target",)

    target: Entity

    def __init__(self, target: Entity) -> None:
        super().__init__()
        self.target = target

    def get_description(self, scheme: Scheme) -> str:
        """Get a string description of the scheme."""
        return (
            f"{scheme.initiator.name_with_uid} is planning a coup against "
            f"{self.target.name_with_uid}."
        )


class AllianceScheme(SchemeData):
    """Create a new alliance scheme"""

    def get_description(self, scheme: Scheme) -> str:
        """Get a string description of the scheme."""
        return f"{scheme.initiator.name_with_uid} is trying to start an alliance."


class CheatingScheme(SchemeData):
    """A scheme to cheat on ones spouse."""

    __slots__ = ("accomplice",)

    accomplice: Entity

    def __init__(self, accomplice: Entity) -> None:
        super().__init__()
        self.accomplice = accomplice

    def get_description(self, scheme: Scheme) -> str:
        """Get a string description of the scheme."""
        return (
            f"{scheme.initiator.name_with_uid} is planning cheat on their spouse with "
            f"{self.accomplice.name_with_uid}."
        )
