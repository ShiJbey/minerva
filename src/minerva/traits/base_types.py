"""Trait system

This module contains class definitions for implementing the trait system.

"""

from __future__ import annotations

from typing import Any

import attrs
import pydantic

from minerva.content_selection import get_with_tags
from minerva.ecs import Component
from minerva.effects.base_types import Effect


class TraitDef(pydantic.BaseModel):
    """A definition for a trait."""

    trait_id: str
    """The ID of this tag definition."""
    name: str
    """The name of this trait."""
    description: str = ""
    """A short description of the trait."""
    effects: list[dict[str, Any]] = pydantic.Field(default_factory=list)
    """Effects applied when a GameObject has this trait."""
    conflicts_with: set[str] = pydantic.Field(default_factory=set)
    """IDs of traits that this trait conflicts with."""
    spawn_frequency: int = 0
    """(Characters only) The relative frequency of an agent spawning with this trait."""
    is_inheritable: bool = False
    """(Characters only) Is the trait inheritable."""
    inheritance_chance_single: float = 0.0
    """(Characters only) The probability of inheriting this trait if one parent has it."""
    inheritance_chance_both: float = 0.0
    """(Characters only) The probability of inheriting this trait if both parents have it."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""


@attrs.define
class Trait:
    """Additional state associated with characters, businesses, and other GameObjects."""

    trait_id: str
    """The ID of this tag definition."""
    name: str
    """The name of this tag printed."""
    description: str = ""
    """A short description of the tag."""
    effects: list[Effect] = attrs.field(factory=list)
    """Effects to apply when the tag is added."""
    conflicting_traits: set[str] = attrs.field(factory=set)
    """traits that this trait conflicts with."""
    spawn_frequency: int = 0
    """(Agents only) The relative frequency of an agent spawning with this trait."""
    is_inheritable: bool = False
    """(Agents only) Is the trait inheritable."""
    inheritance_chance_single: float = 0.0
    """(Agents only) The probability of inheriting this trait if one parent has it."""
    inheritance_chance_both: float = 0.0
    """(Agents only) The probability of inheriting this trait if both parents have it."""
    tags: set[str] = attrs.field(factory=set)
    """Tags describing this definition."""

    def __str__(self) -> str:
        return self.name


class TraitManager(Component):
    """Tracks the traits attached to a GameObject."""

    __slots__ = ("traits",)

    traits: dict[str, Trait]
    """References to traits attached to the GameObject."""

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
    """Manages trait definitions and instances."""

    _slots__ = (
        "definitions",
        "instances",
    )

    definitions: dict[str, TraitDef]
    """IDs mapped to definition instances."""
    instances: dict[str, Trait]
    """Trait instances."""

    def __init__(self) -> None:
        self.definitions = {}
        self.instances = {}

    def add_trait(self, trait: Trait) -> None:
        """Add trait to the library."""
        self.instances[trait.trait_id] = trait

    def get_trait(self, trait_id: str) -> Trait:
        """Get a trait instance."""
        return self.instances[trait_id]

    def get_definition(self, trait_id: str) -> TraitDef:
        """Get a definition from the library."""

        return self.definitions[trait_id]

    def add_definition(self, definition: TraitDef) -> None:
        """Add a definition to the library."""

        self.definitions[definition.trait_id] = definition

    def get_definition_with_tags(self, tags: list[str]) -> list[TraitDef]:
        """Get a definition from the library with the given tags."""

        return get_with_tags(
            options=[(d, d.tags) for d in self.definitions.values()], tags=tags
        )
