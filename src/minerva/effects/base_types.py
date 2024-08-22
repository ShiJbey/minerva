"""Core classes and abstract base types for implementing effects."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from minerva.ecs import GameObject, World


class Effect(ABC):
    """Abstract base class for all effect objects."""

    @abstractmethod
    def get_description(self) -> str:
        """Get a string description of the effect."""
        raise NotImplementedError()

    @abstractmethod
    def apply(self, target: GameObject) -> None:
        """Apply the effects of this effect."""
        raise NotImplementedError()

    @abstractmethod
    def remove(self, target: GameObject) -> None:
        """Remove the effects of this effect."""
        raise NotImplementedError()

    def __str__(self) -> str:
        return self.get_description()


class EffectFactory(ABC):
    """Creates instances of effects."""

    __slots__ = ("effect_name",)

    effect_name: str

    def __init__(self, effect_name: str) -> None:
        super().__init__()
        self.effect_name = effect_name

    @abstractmethod
    def instantiate(self, world: World, params: dict[str, Any]) -> Effect:
        """Construct a new instance of the effect type using a data dict."""
        raise NotImplementedError()


class EffectLibrary:
    """Manages factories used to construct effects from data files."""

    _slots__ = ("_factories",)

    _factories: dict[str, EffectFactory]

    def __init__(self) -> None:
        self._factories = {}

    def get_factory(self, effect_name: str) -> EffectFactory:
        """Get an effect factory."""
        return self._factories[effect_name]

    def add_factory(self, factory: EffectFactory) -> None:
        """Add an effect factory."""
        self._factories[factory.effect_name] = factory

    def create_from_obj(self, world: World, obj: dict[str, Any]) -> Effect:
        """Parse a definition from a dict and add to the library."""
        params = {**obj}
        effect_name: str = params["type"]
        del params["type"]

        factory = self.get_factory(effect_name)
        effect = factory.instantiate(world, params)

        return effect
