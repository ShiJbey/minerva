"""Trait system

This module contains class definitions for implementing the trait system.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from minerva.actions.base_types import Proclivity
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


class CharacterTrait:
    """Additional state associated with characters and other entities."""

    __slots__ = (
        "uid",
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
        "proclivities",
        "target_proclivities",
    )

    uid: int
    """A numerical ID assigned to this trait."""
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
    """The relative frequency of an agent spawning with this trait."""
    is_inheritable: bool
    """Is the trait inheritable."""
    inheritance_chance_single: float
    """The probability of inheriting this trait if one parent has it."""
    inheritance_chance_both: float
    """The probability of inheriting this trait if both parents have it."""
    tags: set[str]
    """Tags describing this definition."""
    proclivities: list[Proclivity]
    """Proclivities added to the character when this trait is attached."""
    target_proclivities: list[Proclivity]
    """Proclivities evaluated when the character is the target of an action."""

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
        proclivities: Optional[Iterable[Proclivity]] = None,
        target_proclivities: Optional[Iterable[Proclivity]] = None,
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
        self.proclivities = list(proclivities if proclivities else [])
        self.target_proclivities = list(
            target_proclivities if target_proclivities else []
        )

    def __hash__(self) -> int:
        return self.uid

    def __str__(self) -> str:
        return self.name


class RelationshipTrait:
    """A permanent tag associated with a relationship that affects behavior."""

    __slots__ = (
        "uid",
        "trait_id",
        "name",
        "description",
        "effects",
        "tags",
        "proclivities",
    )

    uid: int
    """A numerical ID assigned to this trait."""
    trait_id: str
    """The ID of this tag definition."""
    name: str
    """The name of this tag printed."""
    description: str
    """A short description of the tag."""
    effects: list[TraitEffect]
    """Effects to apply when the tag is added."""
    proclivities: list[Proclivity]
    """Proclivities added to the character when this trait is attached."""

    def __init__(
        self,
        trait_id: str,
        name: str,
        description: str = "",
        effects: Optional[list[TraitEffect]] = None,
        proclivities: Optional[Iterable[Proclivity]] = None,
    ) -> None:
        self.trait_id = trait_id
        self.name = name
        self.description = description
        self.effects = list(effects) if effects else []
        self.proclivities = list(proclivities) if proclivities else []

    def __hash__(self) -> int:
        return self.uid

    def __str__(self) -> str:
        return self.name


class Traits(Component):
    """Tracks traits attached to an entity."""

    __slots__ = ("traits",)

    traits: set[int]
    """UIDs of attached traits.."""

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self.traits = set()

    def __str__(self) -> str:
        return f"Traits(traits={self.traits})"

    def __repr__(self) -> str:
        return f"Traits(traits={self.traits})"


class CharacterTraitDatabase:
    """A database of static character trait data."""

    __slots__ = ("_uid_to_trait_map", "_name_to_uid_map", "_next_trait_uid")

    _next_trait_uid: int
    """The UID assigned to the next trait in the database."""
    _uid_to_trait_map: dict[int, CharacterTrait]
    """Trait UIDs mapped to trait instances."""
    _name_to_uid_map: dict[str, int]
    """Trait names mapped to UIDs."""

    def __init__(self) -> None:
        self._next_trait_uid = 1
        self._uid_to_trait_map = {}
        self._name_to_uid_map = {}

    def get_traits(self) -> list[CharacterTrait]:
        """Get all traits in the database."""
        return list(self._uid_to_trait_map.values())

    def get_trait_by_name(self, name: str) -> CharacterTrait:
        """Get a trait using it's name."""
        uid = self._name_to_uid_map[name]
        return self._uid_to_trait_map[uid]

    def get_trait_by_uid(self, uid: int) -> CharacterTrait:
        """Get a trait using its UID."""
        return self._uid_to_trait_map[uid]

    def add_trait(self, trait: CharacterTrait) -> None:
        """Add a trait to the database."""
        trait.uid = self._next_trait_uid
        self._next_trait_uid += 1
        self._uid_to_trait_map[trait.uid] = trait
        self._name_to_uid_map[trait.trait_id] = trait.uid

    def get_trait(self, trait_id: str) -> CharacterTrait:
        """Get a trait instance."""
        return self.get_trait_by_name(trait_id)

    def get_traits_with_tags(self, tags: list[str]) -> list[CharacterTrait]:
        """Get a trait instance from the library with the given tags."""

        return get_with_tags(
            options=[(d, d.tags) for d in self._uid_to_trait_map.values()], tags=tags
        )


class RelationshipTraitDatabase:
    """A database of static relationship trait data."""

    __slots__ = ("_uid_to_trait_map", "_name_to_uid_map", "_next_trait_uid")

    _next_trait_uid: int
    """The UID assigned to the next trait in the database."""
    _uid_to_trait_map: dict[int, RelationshipTrait]
    """Trait UIDs mapped to trait instances."""
    _name_to_uid_map: dict[str, int]
    """Trait names mapped to UIDs."""

    def __init__(self) -> None:
        self._next_trait_uid = 1
        self._uid_to_trait_map = {}
        self._name_to_uid_map = {}

    def get_traits(self) -> list[RelationshipTrait]:
        """Get all traits in the database."""
        return list(self._uid_to_trait_map.values())

    def get_trait_by_name(self, name: str) -> RelationshipTrait:
        """Get a trait using it's name."""
        uid = self._name_to_uid_map[name]
        return self._uid_to_trait_map[uid]

    def get_trait_by_uid(self, uid: int) -> RelationshipTrait:
        """Get a trait using its UID."""
        return self._uid_to_trait_map[uid]

    def add_trait(self, trait: RelationshipTrait) -> None:
        """Add a trait to the database."""
        trait.uid = self._next_trait_uid
        self._next_trait_uid += 1
        self._uid_to_trait_map[trait.uid] = trait
        self._name_to_uid_map[trait.name] = trait.uid

    def get_trait(self, trait_id: str) -> RelationshipTrait:
        """Get a trait instance."""
        return self.get_trait_by_name(trait_id)

    def get_traits_with_tags(self, tags: list[str]) -> list[RelationshipTrait]:
        """Get a trait instance from the library with the given tags."""

        return get_with_tags(
            options=[(d, d.tags) for d in self._uid_to_trait_map.values()], tags=tags
        )
