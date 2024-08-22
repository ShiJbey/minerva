"""Classes and Abstract base classes for implementing preconditions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from minerva.ecs import GameObject, World


class Precondition(ABC):
    """Abstract base class for all precondition objects."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Get a string description of the precondition."""
        raise NotImplementedError()

    @abstractmethod
    def check(self, gameobject: GameObject) -> bool:
        """Check if a gameobject passes this precondition.

        Parameters
        ----------
        gameobject
            A GameObject to check..

        Returns
        -------
        bool
            True if the gameobject passes the precondition, False otherwise.
        """
        raise NotImplementedError()

    def __str__(self) -> str:
        return self.description


class PreconditionFactory(ABC):
    """Creates instances of preconditions."""

    __slots__ = ("precondition_name",)

    precondition_name: str

    def __init__(self, precondition_name: str) -> None:
        super().__init__()
        self.precondition_name = precondition_name

    @abstractmethod
    def instantiate(self, world: World, params: dict[str, Any]) -> Precondition:
        """Construct a new instance of the precondition using a data dict.

        Parameters
        ----------
        world
            The simulation's world instance
        params
            Keyword parameters to pass to the precondition.
        """
        raise NotImplementedError()


class PreconditionLibrary:
    """Manages effect precondition types and constructs them when needed."""

    _slots__ = ("_factories",)

    _factories: dict[str, PreconditionFactory]
    """Precondition types for loading data from config files."""

    def __init__(self) -> None:
        self._factories = {}

    def get_factory(self, precondition_name: str) -> PreconditionFactory:
        """Get a definition type."""
        return self._factories[precondition_name]

    def add_factory(self, factory: PreconditionFactory) -> None:
        """Add a definition type for loading objs."""
        self._factories[factory.precondition_name] = factory

    def create_from_obj(self, world: World, obj: dict[str, Any]) -> Precondition:
        """Parse a definition from a dict and add to the library."""
        params = {**obj}
        precondition_name: str = params["type"]
        del params["type"]

        factory = self.get_factory(precondition_name)
        precondition = factory.instantiate(world, params)

        return precondition
