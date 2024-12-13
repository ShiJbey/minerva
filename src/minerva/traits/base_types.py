"""Trait system

This module contains class definitions for implementing the trait system.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from minerva.ecs import Component, Entity
from minerva.pcg.content_selection import get_with_tags


class TraitEffect(ABC):
    """Abstract base class for all effect objects."""

    @abstractmethod
    def apply(self, target: Entity) -> None:
        """Apply this effect."""
        raise NotImplementedError()

    @abstractmethod
    def remove(self, target: Entity) -> None:
        """Remove this effect."""
        raise NotImplementedError()


class Trait:
    """Additional state associated with characters and other entities."""

    __slots__ = (
        "trait_id",
        "name",
        "description",
        "effects",
        "conflicting_traits",
        "spawn_frequency",
        "is_inheritable",
        "inheritance_chance_single",
        "inheritance_chance_both",
        "tags",
    )

    trait_id: str
    """The ID of this tag definition."""
    name: str
    """The name of this tag printed."""
    description: str
    """A short description of the tag."""
    effects: list[TraitEffect]
    """Effects to apply when the tag is added."""
    conflicting_traits: set[str]
    """traits that this trait conflicts with."""
    spawn_frequency: int
    """(Agents only) The relative frequency of an agent spawning with this trait."""
    is_inheritable: bool
    """(Agents only) Is the trait inheritable."""
    inheritance_chance_single: float
    """(Agents only) The probability of inheriting this trait if one parent has it."""
    inheritance_chance_both: float
    """(Agents only) The probability of inheriting this trait if both parents have it."""
    tags: set[str]
    """Tags describing this definition."""

    def __init__(
        self,
        trait_id: str,
        name: str,
        description: str = "",
        effects: Optional[list[TraitEffect]] = None,
        conflicting_traits: Optional[list[str]] = None,
        spawn_frequency: int = 0,
        is_inheritable: bool = False,
        inheritance_chance_single: float = 0.0,
        inheritance_chance_both: float = 0.0,
        tags: Optional[list[str]] = None,
    ) -> None:
        self.trait_id = trait_id
        self.name = name
        self.description = description
        self.effects = list(effects) if effects else []
        self.conflicting_traits = (
            set(conflicting_traits) if conflicting_traits else set()
        )
        self.spawn_frequency = spawn_frequency
        self.is_inheritable = is_inheritable
        self.inheritance_chance_single = inheritance_chance_single
        self.inheritance_chance_both = inheritance_chance_both
        self.tags = set(tags) if tags else set()

    def __hash__(self) -> int:
        return hash(self.trait_id)

    def __str__(self) -> str:
        return self.name


class TraitManager(Component):
    """Tracks the traits attached to an entity."""

    __slots__ = ("traits",)

    traits: dict[str, Trait]
    """References to traits attached to the entity."""

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self.traits = {}

    def __str__(self) -> str:
        return f"Traits(traits={list(self.traits.keys())!r})"

    def __repr__(self) -> str:
        return f"Traits(traits={list(self.traits.keys())!r})"


class TraitLibrary:
    """Manages trait instances."""

    _slots__ = ("traits",)

    traits: dict[str, Trait]
    """Trait instances."""

    def __init__(self) -> None:
        self.traits = {}

    def add_trait(self, trait: Trait) -> None:
        """Add trait to the library."""
        self.traits[trait.trait_id] = trait

    def get_trait(self, trait_id: str) -> Trait:
        """Get a trait instance."""
        return self.traits[trait_id]

    def get_traits_with_tags(self, tags: list[str]) -> list[Trait]:
        """Get a trait instance from the library with the given tags."""

        return get_with_tags(
            options=[(d, d.tags) for d in self.traits.values()], tags=tags
        )
