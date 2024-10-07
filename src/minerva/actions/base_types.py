"""Character action/behaviors.

Actions are operations performed by agents. Each action has two probability scores.
The first how likely it is an agent will attempt the action, and the second describes
how likely the action is to succeed if it is attempted.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, ClassVar, Generic, Iterator, TypeVar, cast

from minerva.characters.motive_helpers import MotiveVector
from minerva.ecs import GameObject, World
from minerva.preconditions.base_types import Precondition


class IAIBehavior(ABC):
    """Abstract interface implemented by all AI behaviors."""

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of the behavior."""
        raise NotImplementedError()

    @abstractmethod
    def get_motive_vect(self) -> MotiveVector:
        """Get the motive vector for this behavior."""
        raise NotImplementedError()

    @abstractmethod
    def get_cost(self) -> int:
        """Get the influence point cost of the behavior."""
        raise NotImplementedError()

    @abstractmethod
    def passes_preconditions(self, character: GameObject) -> bool:
        """check if the given character passes all the preconditions."""
        raise NotImplementedError()

    @abstractmethod
    def execute(self, character: GameObject) -> bool:
        """Execute the behavior with the given character."""
        raise NotImplementedError()


class AIBehavior(IAIBehavior):
    """A behavior that can be performed by a character."""

    __slots__ = ("name", "motives", "preconditions", "execution_strategy", "cost")

    name: str
    """The nme if the behavior."""
    motives: MotiveVector
    """The motives satisfied by this behavior."""
    preconditions: list[Precondition]
    """Preconditions required for the behavior to be available."""
    execution_strategy: Callable[[GameObject], bool]
    """A function that executes the behavior."""
    cost: int
    """The number of influence point required to execute this behavior."""

    def __init__(
        self,
        name: str,
        motives: MotiveVector,
        preconditions: list[Precondition],
        execution_strategy: Callable[[GameObject], bool],
        cost: int = 0,
    ) -> None:
        super().__init__()
        self.name = name
        self.motives = motives
        self.preconditions = preconditions
        self.execution_strategy = execution_strategy
        self.cost = cost

    def get_name(self) -> str:
        """Get the name of the behavior."""
        return self.name

    def get_cost(self) -> int:
        """Get the influence point cost of the behavior."""
        return self.cost

    def get_motive_vect(self) -> MotiveVector:
        """Get the motive vector for this behavior."""
        return self.motives

    def passes_preconditions(self, character: GameObject) -> bool:
        """check if the given character passes all the preconditions."""
        return all(p.check(character) for p in self.preconditions)

    def execute(self, character: GameObject) -> bool:
        """Execute the behavior with the given character."""
        return self.execution_strategy(character)


class AIBehaviorLibrary:
    """The library of AI behaviors."""

    __slots__ = ("behaviors",)

    behaviors: dict[str, IAIBehavior]

    def __init__(self) -> None:
        self.behaviors = {}

    def add_behavior(self, behavior: IAIBehavior) -> None:
        """Add behavior to the library."""
        self.behaviors[behavior.get_name()] = behavior

    def iter_behaviors(self) -> Iterator[IAIBehavior]:
        """Return iterator to behaviors."""
        return iter(self.behaviors.values())

    def get_behavior(self, name: str) -> IAIBehavior:
        """Get a behavior by name."""
        return self.behaviors[name]


class IAIAction(ABC):
    """An abstract interface for all actions executed by behaviors."""

    @abstractmethod
    def get_probability_success(self) -> float:
        """Get probability of the action being successful."""
        raise NotImplementedError()

    @abstractmethod
    def execute(self) -> bool:
        """Execute the action and return true if successful."""
        raise NotImplementedError()


_AD = TypeVar("_AD", bound="IAIAction")


class Action(IAIAction, Generic[_AD]):
    """An action that a character can take."""

    __slots__ = ("world", "data")

    considerations: ClassVar[list[Callable[[Action[IAIAction]], float]]] = []

    world: World
    data: _AD

    def __init__(self, world: World) -> None:
        self.world = world
        self.data = cast(_AD, self)

    def get_probability_success(self) -> float:
        """Get probability success of an action."""
        # We set the starting score to 1 since we are multiplying probabilities
        score: float = 1
        consideration_count: int = 0

        for consideration in self.considerations:
            utility_score = consideration(cast(Action[IAIAction], self))

            if utility_score < 0.0:
                continue

            elif utility_score == 0.0:
                return 0.0

            # Update the current score and counts
            score = score * utility_score
            consideration_count += 1

        if consideration_count == 0:
            return 0.5
        else:
            return score ** (1 / consideration_count)

    @abstractmethod
    def execute(self) -> bool:
        """Execute the action type."""
        raise NotImplementedError

    @classmethod
    def consideration(
        cls, fn: Callable[[Action[_AD]], float]
    ) -> Callable[[Action[_AD]], float]:
        """A decorator function for considerations."""
        cls.considerations.append(cast(Callable[[Action[IAIAction]], float], fn))
        return fn
