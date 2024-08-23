"""Relationship System Components.

The relationship system tracks feelings of one character toward another character.
Relationships are represented as independent GameObjects. Together they form a directed
graph.

"""

from __future__ import annotations

from typing import Any, Optional

import attrs
import pydantic

from minerva.ecs import Component, GameObject
from minerva.preconditions.base_types import Precondition
from minerva.stats.base_types import (
    IStatCalculationStrategy,
    StatComponent,
    StatModifierData,
)


class Relationship(Component):
    """Tags a GameObject as a relationship and tracks the owner and target."""

    __slots__ = "_target", "_owner"

    _owner: GameObject
    """Who owns this relationship."""
    _target: GameObject
    """Who is the relationship directed toward."""

    def __init__(
        self,
        owner: GameObject,
        target: GameObject,
    ) -> None:
        super().__init__()
        self._owner = owner
        self._target = target

    @property
    def owner(self) -> GameObject:
        """Get the owner of the relationship."""
        return self._owner

    @property
    def target(self) -> GameObject:
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
    """Tracks all relationships associated with a GameObject."""

    __slots__ = (
        "incoming",
        "outgoing",
        "incoming_modifiers",
        "outgoing_modifiers",
    )

    incoming: dict[GameObject, GameObject]
    """Relationship owners mapped to the Relationship GameObjects."""
    outgoing: dict[GameObject, GameObject]
    """Relationship targets mapped to the Relationship GameObjects."""
    incoming_modifiers: list[RelationshipModifier]
    """Relationship modifiers for incoming relationships."""
    outgoing_modifiers: list[RelationshipModifier]
    """Relationship modifiers for outgoing relationships."""

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self.incoming = {}
        self.outgoing = {}
        self.incoming_modifiers = []
        self.outgoing_modifiers = []

    def add_outgoing_relationship(
        self, target: GameObject, relationship: GameObject
    ) -> None:
        """Add a new relationship to a target.

        Parameters
        ----------
        target
            The GameObject that the Relationship is directed toward.
        relationship
            The relationship.
        """
        if target in self.outgoing:
            raise ValueError(
                f"{self.gameobject.name} has existing outgoing relationship to "
                "target: {target.name}"
            )

        self.outgoing[target] = relationship

    def remove_outgoing_relationship(self, target: GameObject) -> bool:
        """Remove the relationship GameObject to the target.

        Parameters
        ----------
        target
            The target of the relationship

        Returns
        -------
        bool
            Returns True if a relationship was removed. False otherwise.
        """
        if target in self.outgoing:
            del self.outgoing[target]
            return True

        return False

    def add_incoming_relationship(
        self, owner: GameObject, relationship: GameObject
    ) -> None:
        """Add a new relationship to a target.

        Parameters
        ----------
        owner
            The GameObject owns the relationship.
        relationship
            The relationship.
        """
        if owner in self.incoming:
            raise ValueError(
                f"{self.gameobject.name} has existing incoming relationship from "
                "target: {target.name}"
            )

        self.incoming[owner] = relationship

    def remove_incoming_relationship(self, owner: GameObject) -> bool:
        """Remove the relationship GameObject to the owner.

        Parameters
        ----------
        owner
            The owner of the relationship

        Returns
        -------
        bool
            Returns True if a relationship was removed. False otherwise.
        """
        if owner in self.incoming:
            del self.incoming[owner]
            return True

        return False

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(outgoing={self.outgoing}, "
            f"incoming={self.incoming})"
        )


class Reputation(StatComponent):
    """Tracks a relationship's reputations stat."""

    __stat_name__ = "Reputation"

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (-100, 100), True)


class Romance(StatComponent):
    """Tracks a relationship's romance stat."""

    __stat_name__ = "Romance"

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (-100, 100), True)


class RelationshipModifier:
    """Conditionally modifies a GameObject's relationships."""

    __slots__ = (
        "description",
        "preconditions",
        "modifiers",
        "source",
    )

    description: str
    """A text description of this belief."""
    preconditions: list[Precondition]
    """Preconditions checked against a relationship GameObject."""
    modifiers: dict[str, StatModifierData]
    """Effects to apply to a relationship GameObject."""
    source: Optional[object]
    """The source of the modifier."""

    def __init__(
        self,
        description: str,
        preconditions: list[Precondition],
        modifiers: dict[str, StatModifierData],
    ) -> None:
        self.description = description
        self.preconditions = preconditions
        self.modifiers = modifiers
        self.source = None

    def check_preconditions_for(self, relationship: GameObject) -> bool:
        """Check the preconditions against the given relationship."""

        return all(p.check(relationship) for p in self.preconditions)


class SocialRuleDef(pydantic.BaseModel):
    """A rule that modifies a relationship."""

    label: str = ""
    preconditions: list[dict[str, Any]] = pydantic.Field(default_factory=list)
    modifiers: dict[str, StatModifierData] = pydantic.Field(default_factory=dict)


@attrs.define
class SocialRule:
    """A rule that modifies a relationship."""

    label: str = ""
    preconditions: list[Precondition] = attrs.field(factory=list)
    modifiers: dict[str, StatModifierData] = attrs.field(factory=dict)

    def check_preconditions_for(self, relationship: GameObject) -> bool:
        """Check if a relationship passes the preconditions for this rule."""
        return all(p.check(relationship) for p in self.preconditions)


class SocialRuleLibrary:
    """Collection of all social rules that modify relationships."""

    __slots__ = ("definitions", "rules")

    definitions: list[SocialRuleDef]
    rules: list[SocialRule]

    def __init__(self) -> None:
        self.definitions = []
        self.rules = []
