"""Relationship System Components.

The relationship system tracks feelings of one character toward another character.
Relationships are represented as independent GameObjects. Together they form a directed
graph.

"""

from __future__ import annotations

from typing import Any, Optional

import attrs
import pydantic

from minerva.ecs import Component, Event, GameObject
from minerva.preconditions.base_types import Precondition
from minerva.stats.base_types import (
    StatComponent,
    StatManager,
    StatModifierData,
    StatusEffectManager,
)
from minerva.traits.base_types import TraitManager


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
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (-100, 100), True)


class Romance(StatComponent):
    """Tracks a relationship's romance stat."""

    __stat_name__ = "Romance"

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (-100, 100), True)


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


def add_relationship(owner: GameObject, target: GameObject) -> GameObject:
    """
    Creates a new relationship from the subject to the target

    Parameters
    ----------
    owner
        The GameObject that owns the relationship
    target
        The GameObject that the Relationship is directed toward

    Returns
    -------
    GameObject
        The new relationship instance
    """
    if has_relationship(owner, target):
        return get_relationship(owner, target)

    relationship = owner.world.gameobjects.spawn_gameobject()

    relationship.add_component(Relationship(owner=owner, target=target))
    relationship.add_component(StatManager())
    relationship.add_component(StatusEffectManager())
    relationship.add_component(TraitManager())
    relationship.add_component(Reputation())
    relationship.add_component(Romance())

    relationship.name = f"[{owner.name} -> {target.name}]"

    owner.get_component(RelationshipManager).add_outgoing_relationship(
        target, relationship
    )
    target.get_component(RelationshipManager).add_incoming_relationship(
        owner, relationship
    )

    relationship.world.events.dispatch_event(
        Event("relationship-added", world=relationship.world, relationship=relationship)
    )

    return relationship


def get_relationship(
    owner: GameObject,
    target: GameObject,
) -> GameObject:
    """Get a relationship from one GameObject to another.

    This function will create a new instance of a relationship if one does not exist.

    Parameters
    ----------
    owner
        The owner of the relationship.
    target
        The target of the relationship.

    Returns
    -------
    GameObject
        A relationship instance.
    """
    relationships = owner.get_component(RelationshipManager)
    if target in relationships.outgoing:
        return relationships.outgoing[target]

    return add_relationship(owner, target)


def has_relationship(owner: GameObject, target: GameObject) -> bool:
    """Check if there is an existing relationship from the owner to the target.

    Parameters
    ----------
    owner
        The owner of the relationship.
    target
        The target of the relationship.

    Returns
    -------
    bool
        True if there is an existing Relationship between the GameObjects,
        False otherwise.
    """
    relationships = owner.get_component(RelationshipManager)
    return target in relationships.outgoing


def destroy_relationship(owner: GameObject, target: GameObject) -> bool:
    """Destroy the relationship GameObject to the target.

    Parameters
    ----------
    owner
        The owner of the relationship
    target
        The target of the relationship

    Returns
    -------
    bool
        Returns True if a relationship was removed. False otherwise.
    """
    if has_relationship(owner, target):
        relationship = get_relationship(owner, target)
        owner.get_component(RelationshipManager).remove_outgoing_relationship(target)
        target.get_component(RelationshipManager).remove_incoming_relationship(owner)
        relationship.destroy()
        return True

    return False


def deactivate_relationships(gameobject: GameObject) -> None:
    """Deactivates all an objects incoming and outgoing relationships."""

    relationships = gameobject.get_component(RelationshipManager)

    for _, relationship in relationships.outgoing.items():
        relationship.deactivate()

    for _, relationship in relationships.incoming.items():
        relationship.deactivate()


def remove_relationship_modifiers_from_source(
    relationship: GameObject, source: Optional[object]
) -> None:
    """Remove all modifiers from a given source."""
    relationship_manager = relationship.get_component(RelationshipManager)

    relationship_manager.incoming_modifiers = [
        m for m in relationship_manager.incoming_modifiers if m.source != source
    ]

    relationship_manager.outgoing_modifiers = [
        m for m in relationship_manager.outgoing_modifiers if m.source != source
    ]


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
