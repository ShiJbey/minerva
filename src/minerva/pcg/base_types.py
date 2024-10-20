"""Abstract base types for procedural content generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from minerva.characters.components import LifeStage, Sex, SexualOrientation
from minerva.ecs import GameObject, World


class NameFactory(ABC):
    """Generates a name for a GameObject."""

    @abstractmethod
    def generate_name(self, gameobject: GameObject) -> str:
        """Generate a name for the given game object."""
        raise NotImplementedError()


class CharacterFactory(ABC):
    """Generates Character GameObjects."""

    @abstractmethod
    def generate_character(
        self,
        world: World,
        *,
        first_name: str = "",
        surname: str = "",
        species: str = "",
        sex: Optional[Sex] = None,
        sexual_orientation: Optional[SexualOrientation] = None,
        life_stage: Optional[LifeStage] = None,
        age: Optional[int] = None,
        n_max_personality_traits: int = 0,
        randomize_stats: bool = True,
    ) -> GameObject:
        """Generate a new character."""
        raise NotImplementedError()


class BabyFactory(ABC):
    """Generates baby characters from parents."""

    @abstractmethod
    def generate_child(self, mother: GameObject, father: GameObject) -> GameObject:
        """Generate a new child from the given parents."""
        raise NotImplementedError()


class FamilyFactory(ABC):
    """Generates family GameObjects."""

    @abstractmethod
    def generate_family(self, world: World, name: str = "") -> GameObject:
        """Generate a new family."""
        raise NotImplementedError()


class TerritoryFactory(ABC):
    """Generates territory GameObjects."""

    @abstractmethod
    def generate_territory(self, world: World, name: str = "") -> GameObject:
        """Generate a new territory."""
        raise NotImplementedError()


class PCGFactories:
    """A shared resource that manages reference to various factory objects for PCG."""

    __slots__ = (
        "character_factory",
        "baby_factory",
        "family_factory",
        "territory_factory",
    )

    character_factory: CharacterFactory
    baby_factory: BabyFactory
    family_factory: FamilyFactory
    territory_factory: TerritoryFactory

    def __init__(
        self,
        character_factory: CharacterFactory,
        baby_factory: BabyFactory,
        family_factory: FamilyFactory,
        territory_factory: TerritoryFactory,
    ) -> None:
        self.character_factory = character_factory
        self.baby_factory = baby_factory
        self.family_factory = family_factory
        self.territory_factory = territory_factory
