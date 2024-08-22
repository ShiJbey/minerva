"""Character action/behaviors.

Actions are operations performed by agents. Each action has two probability scores.
The first how likely it is an agent will attempt the action, and the second describes
how likely the action is to succeed if it is attempted.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, ClassVar, Iterable, Protocol

from ordered_set import OrderedSet

from minerva.ecs import World


class ActionConsideration(Protocol):
    """A callable that accepts an action and returns a probability value."""

    def __call__(self, action: Action) -> float:
        """Calculate a probability for the action."""
        raise NotImplementedError()


def invert_cons(consideration: ActionConsideration) -> ActionConsideration:
    """Invert the probability by subtracting it from one."""

    def wrapped_fn(action: Action) -> float:
        return 1 - consideration(action)

    return wrapped_fn


def cons_pow(consideration: ActionConsideration, pow_exp: int) -> ActionConsideration:
    """Invert the probability by subtracting it from one."""

    def wrapped_fn(action: Action) -> float:
        return consideration(action) ** pow_exp

    return wrapped_fn


class Action(ABC):
    """An abstract base class for all actions that agents may perform."""

    __action_id__: ClassVar[str] = ""

    __slots__ = ("world", "is_silent", "data")

    world: World
    """The simulation's World instance."""
    is_silent: bool
    """Should this event or sub-events emit life events."""
    data: dict[str, Any]
    """General metadata."""

    def __init__(self, world: World, is_silent: bool = False, **kwargs: Any) -> None:
        super().__init__()
        self.world = world
        self.is_silent = is_silent
        self.data = {**kwargs}

        if not self.__action_id__:
            raise ValueError("Please specify the __action_id__ class variable.")

    @classmethod
    def action_id(cls) -> str:
        """The action's ID."""
        return cls.__action_id__

    @abstractmethod
    def execute(self) -> bool:
        """Executes the action.

        Returns
        -------
        bool
            True, if the action completed successfully.
        """

        raise NotImplementedError()


def get_action_probability(action: Action) -> float:
    """Calculate the probability of a given action being successful."""

    consideration_library = action.world.resources.get_resource(
        ActionConsiderationLibrary
    )

    considerations = consideration_library.get_success_considerations(
        action.action_id()
    )

    # We set the starting score to 1 since we are multiplying probabilities
    score: float = 1
    consideration_count: int = 0

    for consideration in considerations:
        utility_score = consideration(action)

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


class ActionConsiderationLibrary:
    """Manages all considerations that calculate the probability of a potential action.

    All considerations are grouped by action ID. End-users are responsible for casting
    the action instance if they care about type hints and such.
    """

    __slots__ = ("success_considerations",)

    success_considerations: defaultdict[str, OrderedSet[ActionConsideration]]
    """Considerations for calculating success probabilities."""

    def __init__(self) -> None:
        self.success_considerations = defaultdict(lambda: OrderedSet([]))

    def add_success_consideration(
        self, action_id: str, consideration: ActionConsideration
    ) -> None:
        """Add a success consideration to the library."""
        self.success_considerations[action_id].add(consideration)

    def remove_success_consideration(
        self, action_id: str, consideration: ActionConsideration
    ) -> None:
        """Remove a success consideration from the library."""
        self.success_considerations[action_id].remove(consideration)

    def remove_all_success_considerations(self, action_id: str) -> None:
        """Add a success consideration to the library."""
        del self.success_considerations[action_id]

    def get_success_considerations(
        self, action_id: str
    ) -> Iterable[ActionConsideration]:
        """Get all success considerations for an action."""
        return self.success_considerations[action_id]
