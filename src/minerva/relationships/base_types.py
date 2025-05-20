"""Relationship System Components.

The relationship system tracks feelings of one character toward another character.
Relationships are represented as independent entities. Together they form a directed
graph.

"""

from __future__ import annotations

from typing import Any, Iterable, Iterator, Literal, Protocol

from minerva.ecs import Component, Entity
from minerva.stats.base_types import Stat

# Opinion Threshold Constants
OPINION_TERRIBLE = -100
OPINION_POOR = -75
OPINION_NEUTRAL = -25
OPINION_GOOD = 25
OPINION_EXCELLENT = 75

# Attraction Threshold Constants
ATTRACTION_TERRIBLE = -100
ATTRACTION_POOR = -75
ATTRACTION_NEUTRAL = -25
ATTRACTION_GOOD = 25
ATTRACTION_EXCELLENT = 75


class Relationship(Component):
    """Tags an entity as a relationship and tracks the owner and target."""

    __slots__ = ("_target", "_owner")

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
        return f"Relationship(owner={self.owner.name}, target={self.target.name})"


class Opinion(Stat):
    """Tracks a character's opinion of another."""

    def __init__(self, base_value: int = 0) -> None:
        super().__init__(base_value, min_value=-100, max_value=100)


class Attraction(Stat):
    """Tracks a character's romantic attraction to another."""

    def __init__(self, base_value: int = 0) -> None:
        super().__init__(base_value, min_value=-100, max_value=100)


class RelationshipManager(Component):
    """Tracks relationships for an entity and modifiers for those relationships."""

    __slots__ = (
        "incoming_relationships",
        "outgoing_relationships",
        "incoming_opinion_mods",
        "outgoing_opinion_mods",
        "incoming_attraction_mods",
        "outgoing_attraction_mods",
    )

    incoming_relationships: dict[Entity, Entity]
    """Relationship owners mapped to the Relationship entities."""
    outgoing_relationships: dict[Entity, Entity]
    """Relationship targets mapped to the Relationship entities."""
    incoming_opinion_mods: list[RelationshipModifier]
    """Opinion modifiers applied to incoming relationships."""
    outgoing_opinion_mods: list[RelationshipModifier]
    """Opinion modifiers applied to outgoing relationships."""
    incoming_attraction_mods: list[RelationshipModifier]
    """Attraction modifiers applied to incoming relationships."""
    outgoing_attraction_mods: list[RelationshipModifier]
    """Attraction modifiers applied to outgoing relationships."""

    def __init__(self) -> None:
        super().__init__()
        self.incoming_relationships = {}
        self.outgoing_relationships = {}
        self.incoming_opinion_mods = []
        self.outgoing_opinion_mods = []
        self.incoming_attraction_mods = []
        self.outgoing_attraction_mods = []

    def add_opinion_modifier(self, modifier: RelationshipModifier) -> None:
        """Add an opinion modifier."""
        if modifier.direction == "incoming":
            self.incoming_opinion_mods.append(modifier)
        else:
            self.outgoing_opinion_mods.append(modifier)

    def remove_opinion_modifier(self, modifier: RelationshipModifier) -> None:
        """Remove an opinion modifier."""
        try:
            if modifier.direction == "incoming":
                self.incoming_opinion_mods.remove(modifier)
            else:
                self.outgoing_opinion_mods.remove(modifier)

        except ValueError:
            pass

    def add_opinion_modifiers(self, modifiers: Iterable[RelationshipModifier]) -> None:
        """Add a collection of opinion modifiers."""
        for modifier in modifiers:
            self.add_opinion_modifier(modifier)

    def add_attraction_modifier(self, modifier: RelationshipModifier) -> None:
        """Add an attraction modifier."""
        if modifier.direction == "incoming":
            self.incoming_attraction_mods.append(modifier)
        else:
            self.outgoing_attraction_mods.append(modifier)

    def remove_attraction_modifier(self, modifier: RelationshipModifier) -> None:
        """Remove an attraction modifier."""
        try:
            if modifier.direction == "incoming":
                self.incoming_attraction_mods.remove(modifier)
            else:
                self.outgoing_attraction_mods.remove(modifier)

        except ValueError:
            pass

    def add_attraction_modifiers(
        self, modifiers: Iterable[RelationshipModifier]
    ) -> None:
        """Add a collection of attraction modifiers."""
        for modifier in modifiers:
            self.add_attraction_modifier(modifier)

    def iter_opinion_modifiers(
        self, direction: RelationshipModifierDirection
    ) -> Iterator[RelationshipModifier]:
        """Get an iterator for the opinion modifiers."""
        if direction == "incoming":
            return iter(self.incoming_opinion_mods)
        else:
            return iter(self.outgoing_opinion_mods)

    def iter_attraction_modifiers(
        self, direction: RelationshipModifierDirection
    ) -> Iterator[RelationshipModifier]:
        """Get an iterator for the attraction modifiers."""
        if direction == "incoming":
            return iter(self.incoming_attraction_mods)
        else:
            return iter(self.outgoing_attraction_mods)


class RelationshipPrecondition(Protocol):
    """A condition evaluated against a social relationship."""

    def __call__(self, relationship: Entity) -> Any:
        """Evaluate the precondition."""
        raise NotImplementedError()


RelationshipModifierDirection = Literal["incoming", "outgoing"]


class RelationshipModifier:
    """A callable that returns a modifier for a opinion/attraction stat."""

    __slots__ = ("score", "conditions", "direction")

    score: int
    """The score to return if the proclivity applies."""
    conditions: list[RelationshipPrecondition]
    """Conditions that must pass for the score to be returned."""
    direction: RelationshipModifierDirection
    """The direction of the modifier."""

    def __init__(
        self,
        score: int,
        direction: RelationshipModifierDirection = "outgoing",
    ) -> None:
        self.score = score
        self.conditions = []
        self.direction = direction

    def where(self, condition: RelationshipPrecondition) -> RelationshipModifier:
        """Add a condition to a proclivity."""
        self.conditions.append(condition)
        return self

    def __call__(self, relationship: Entity) -> int:
        """Check if the preconditions pass."""
        if all(cond(relationship) for cond in self.conditions):
            return self.score

        return 0


class RelationshipModifierDatabase:
    """Collection of global modifiers for relationships."""

    __slots__ = (
        "_incoming_opinion_mods",
        "_outgoing_opinion_mods",
        "_incoming_attraction_mods",
        "_outgoing_attraction_mods",
    )

    _incoming_opinion_mods: list[RelationshipModifier]
    _outgoing_opinion_mods: list[RelationshipModifier]
    _incoming_attraction_mods: list[RelationshipModifier]
    _outgoing_attraction_mods: list[RelationshipModifier]

    def __init__(self) -> None:
        self._incoming_opinion_mods = []
        self._outgoing_opinion_mods = []
        self._incoming_attraction_mods = []
        self._outgoing_attraction_mods = []

    def add_opinion_modifier(self, modifier: RelationshipModifier) -> None:
        """Add an opinion modifier to the database."""
        if modifier.direction == "incoming":
            self._incoming_opinion_mods.append(modifier)
        else:
            self._outgoing_opinion_mods.append(modifier)

    def add_opinion_modifiers(self, modifiers: Iterable[RelationshipModifier]) -> None:
        """Add a collection of opinion modifiers to the database."""
        for modifier in modifiers:
            self.add_opinion_modifier(modifier)

    def add_attraction_modifier(self, modifier: RelationshipModifier) -> None:
        """Add an attraction modifier to the database."""
        if modifier.direction == "incoming":
            self._incoming_attraction_mods.append(modifier)
        else:
            self._outgoing_attraction_mods.append(modifier)

    def add_attraction_modifiers(
        self, modifiers: Iterable[RelationshipModifier]
    ) -> None:
        """Add a collection of attraction modifiers to the database."""
        for modifier in modifiers:
            self.add_attraction_modifier(modifier)

    def iter_opinion_modifiers(
        self, direction: RelationshipModifierDirection
    ) -> Iterator[RelationshipModifier]:
        """Get an iterator for the opinion modifiers."""
        if direction == "incoming":
            return iter(self._incoming_opinion_mods)
        else:
            return iter(self._outgoing_opinion_mods)

    def iter_attraction_modifiers(
        self, direction: RelationshipModifierDirection
    ) -> Iterator[RelationshipModifier]:
        """Get an iterator for the attraction modifiers."""
        if direction == "incoming":
            return iter(self._incoming_attraction_mods)
        else:
            return iter(self._outgoing_attraction_mods)
