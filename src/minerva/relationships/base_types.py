"""Relationship System Components.

The relationship system tracks feelings of one character toward another character.
Relationships are represented as independent entities. Together they form a directed
graph.

"""

from __future__ import annotations

from minerva.ecs import Component, Entity
from minerva.stats.base_types import Stat


class Relationship(Component):
    """Tags an entity as a relationship and tracks the owner and target."""

    __slots__ = "_target", "_owner"

    _owner: Entity
    """Who owns this relationship."""
    _target: Entity
    """Who is the relationship directed toward."""

    def __init__(
        self,
        owner: Entity,
        target: Entity,
    ) -> None:
        super().__init__()
        self._owner = owner
        self._target = target

    @property
    def owner(self) -> Entity:
        """Get the owner of the relationship."""
        return self._owner

    @property
    def target(self) -> Entity:
        """Get the target of the relationship."""
        return self._target

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(owner={self.owner.name}, "
            f"target={self.target.name})"
        )


class RelationshipManager(Component):
    """Tracks all relationships associated with an entity."""

    __slots__ = (
        "incoming_relationships",
        "outgoing_relationships",
    )

    incoming_relationships: dict[Entity, Entity]
    """Relationship owners mapped to the Relationship entities."""
    outgoing_relationships: dict[Entity, Entity]
    """Relationship targets mapped to the Relationship entities."""

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self.incoming_relationships = {}
        self.outgoing_relationships = {}


class Opinion(Stat):
    """Tracks a character's opinion of another."""


class Attraction(Stat):
    """Tracks a character's romantic attraction to another."""
