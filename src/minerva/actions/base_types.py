"""Character action/behaviors.

Actions are operations performed by agents. Each action has two probability scores.
The first how likely it is an agent will attempt the action, and the second describes
how likely the action is to succeed if it is attempted.

"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, DefaultDict, Iterable, Iterator, Literal, Optional, TypeVar

from ordered_set import OrderedSet

from minerva.datetime import SimDate
from minerva.ecs import Component, GameObject, World


class ActionSelectionStrategy(ABC):
    """A utility object that helps AIBrains choose an action to execute."""

    @abstractmethod
    def choose_action(self, actions: Iterable[AIAction]) -> AIAction:
        """Select an action from the given collection of actions."""
        raise NotImplementedError()


class AIBrain(Component):
    """A brain used to make choices for a character."""

    __slots__ = (
        "context",
        "action_selection_strategy",
        "action_cooldowns",
    )

    context: AIContext
    action_selection_strategy: ActionSelectionStrategy
    action_cooldowns: DefaultDict[str, int]

    def __init__(
        self,
        context: AIContext,
        action_selection_strategy: ActionSelectionStrategy,
    ) -> None:
        super().__init__()
        self.context = context
        self.action_selection_strategy = action_selection_strategy
        self.action_cooldowns = defaultdict(lambda: 0)


class AISensor(ABC):
    """An object that retrieves some world state to help fill AI blackboard."""

    @abstractmethod
    def evaluate(self, context: AIContext) -> None:
        """Run the sensor and write to the context's blackboard."""
        raise NotImplementedError()


_RT = TypeVar("_RT")


class AIContext:
    """A context of information used for AI decision making.

    AIContexts can be hierarchical and use information from a parent context
    to prevent from duplicating data.
    """

    __slots__ = ("_blackboard", "world", "character", "sensors", "_parent")

    _blackboard: dict[str, Any]
    """A key-value store of variables used for decision-making."""
    world: World
    """The simulation's World instance."""
    character: GameObject
    """The character this context is in reference to."""
    sensors: list[AISensor]
    """Sensors used to fill the blackboard with information about the world/action."""
    _parent: Optional[AIContext]
    """The context this context is derived from."""

    def __init__(
        self,
        world: World,
        character: GameObject,
        sensors: list[AISensor],
        *,
        parent: Optional[AIContext] = None,
    ) -> None:
        self._blackboard = {}
        self.world = world
        self.character = character
        self.sensors = [*sensors]
        self._parent = parent

    def update_sensors(self) -> None:
        """Run all the sensors."""
        for sensor in self.sensors:
            sensor.evaluate(self)

    def create_child(self) -> AIContext:
        """Create a child of the context."""
        return AIContext(self.world, self.character, self.sensors, parent=self)

    def set_value(self, key: str, value: Any) -> None:
        """Set a value."""
        self._blackboard[key] = value

    def get_value(self, key: str, default_value: _RT = None) -> _RT:
        """Get a value."""
        try:
            return self._blackboard[key]
        except KeyError:
            if self._parent:
                return self._parent.get_value(key, default_value)
            else:
                return default_value

    def clear_blackboard(self) -> None:
        """Clear all key-value entries."""
        self._blackboard.clear()

    def __getitem__(self, key: str) -> Any:
        return self.get_value(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.set_value(key, value)


class AIPrecondition(ABC):
    """A precondition required for an action to be executed."""

    @abstractmethod
    def evaluate(self, context: AIContext) -> bool:
        """Evaluate the precondition."""
        raise NotImplementedError()


class AIUtilityConsideration(ABC):
    """A consideration of the utility of taking an action."""

    def invert(self) -> AIUtilityConsideration:
        """Invert the consideration."""
        return _InvertedConsideration(self)

    def pow(self, exponent: int) -> AIUtilityConsideration:
        """Raise the utility value to a given exponent."""
        return _ExponentialConsideration(self, exponent)

    @abstractmethod
    def evaluate(self, context: AIContext) -> float:
        """Evaluate the consideration."""
        raise NotImplementedError()


class _InvertedConsideration(AIUtilityConsideration):
    """Inverts a consideration score."""

    __slots__ = ("consideration",)

    consideration: AIUtilityConsideration

    def __init__(self, consideration: AIUtilityConsideration) -> None:
        super().__init__()
        self.consideration = consideration

    def evaluate(self, context: AIContext) -> float:
        return 1 - self.consideration.evaluate(context)


class _ExponentialConsideration(AIUtilityConsideration):
    """Inverts a consideration score."""

    __slots__ = ("consideration", "exponent")

    consideration: AIUtilityConsideration
    exponent: int

    def __init__(self, consideration: AIUtilityConsideration, exponent: int) -> None:
        super().__init__()
        self.consideration = consideration
        self.exponent = exponent

    def evaluate(self, context: AIContext) -> float:
        return self.consideration.evaluate(context) ** self.exponent


class ConstantUtilityConsideration(AIUtilityConsideration):
    """A utility consideration that is a constant value."""

    __slots__ = ("value",)

    value: float

    def __init__(self, value: float) -> None:
        super().__init__()
        self.value = value

    def evaluate(self, context: AIContext) -> float:
        return self.value


class ConstantPrecondition(AIPrecondition):
    """A precondition that is always true."""

    __slots__ = ("value",)

    value: bool

    def __init__(self, value: bool) -> None:
        super().__init__()
        self.value = value

    def evaluate(self, context: AIContext) -> bool:
        return self.value


class AIPreconditionGroup(AIPrecondition):
    """A composite group of preconditions."""

    __slots__ = ("preconditions",)

    preconditions: list[AIPrecondition]

    def __init__(self, *preconditions: AIPrecondition) -> None:
        super().__init__()
        self.preconditions = list(preconditions)

    def evaluate(self, context: AIContext) -> bool:
        return all(p.evaluate(context) for p in self.preconditions)


class AIConsiderationGroupOp(enum.IntEnum):
    """An operation to perform on a group of considerations."""

    MEAN = 0
    MIN = enum.auto()
    MAX = enum.auto()


class AIUtilityConsiderationGroup(AIUtilityConsideration):
    """A composite group of utility considerations."""

    __slots__ = ("op", "considerations")

    op: AIConsiderationGroupOp
    considerations: list[AIUtilityConsideration]

    def __init__(
        self,
        *considerations: AIUtilityConsideration,
        op: Literal["mean", "min", "max"] = "mean",
    ) -> None:
        super().__init__()
        self.op = AIConsiderationGroupOp[op.upper()]
        self.considerations = list(considerations)

    def evaluate(self, context: AIContext) -> float:
        if self.op == AIConsiderationGroupOp.MEAN:
            return self.get_geometric_mean_score(context)
        elif self.op == AIConsiderationGroupOp.MAX:
            return self.get_max_score(context)
        elif self.op == AIConsiderationGroupOp.MIN:
            return self.get_min_score(context)
        else:
            raise ValueError(f"Error: Unsupported op value: {self.op}")

    def get_geometric_mean_score(self, context: AIContext) -> float:
        """Calculate the geometric mean of the considerations."""
        score: float = 1
        consideration_count: int = 0

        for consideration in self.considerations:
            utility_score = consideration.evaluate(context)

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

    def get_min_score(self, context: AIContext) -> float:
        """Get the minimum score of the considerations."""

        min_score: float = 999_999.0

        for consideration in self.considerations:
            utility_score = consideration.evaluate(context)

            if utility_score < min_score:
                min_score = utility_score

        return min_score

    def get_max_score(self, context: AIContext) -> float:
        """Get the maximum score of the considerations."""

        max_score: float = -999_999.0

        for consideration in self.considerations:
            utility_score = consideration.evaluate(context)

            if utility_score > max_score:
                max_score = utility_score

        return max_score


class AIActionType:
    """An abstract base class for all actions."""

    __slots__ = (
        "name",
        "cost",
        "cooldown",
        "utility_consideration",
    )

    name: str
    """The name of this action type."""
    cost: int
    """The number of influence points required to execute this action."""
    cooldown: int
    """Number of months between recurred uses of this action by the same character."""
    utility_consideration: AIUtilityConsideration
    """Consideration(s) for how much a character wants to perform this action."""

    def __init__(
        self,
        name: str,
        cost: int,
        cooldown: int,
        utility_consideration: AIUtilityConsideration,
    ) -> None:
        super().__init__()
        self.name = name
        self.cost = cost
        self.cooldown = cooldown
        self.utility_consideration = utility_consideration


class AIAction(ABC):
    """An action that a character can take."""

    __slots__ = ("performer", "context", "action_type", "world")

    performer: GameObject
    context: AIContext
    action_type: AIActionType
    world: World

    def __init__(self, performer: GameObject, action_type: str) -> None:
        super().__init__()
        self.performer = performer
        self.context = performer.get_component(AIBrain).context.create_child()
        self.action_type = performer.world.resources.get_resource(
            AIActionLibrary
        ).get_action_with_name(action_type)
        self.context["performer"] = performer
        self.world = self.context.world

    def get_name(self) -> str:
        """Get the name of the behavior."""
        return self.action_type.name

    def get_cost(self) -> int:
        """Get the cost of the behavior."""
        return self.action_type.cost

    def get_cooldown_time(self) -> int:
        """Get the amount of time between repeat uses of this action type."""
        return self.action_type.cooldown

    def get_performer(self) -> GameObject:
        """Get the character performing the action."""
        return self.performer

    def calculate_utility(self) -> float:
        """Get the utility of this action."""
        return self.action_type.utility_consideration.evaluate(self.context)

    @abstractmethod
    def execute(self) -> bool:
        """Execute the action."""
        raise NotImplementedError()


class AIActionLibrary:
    """The library of AI actions."""

    __slots__ = ("actions",)

    actions: dict[str, AIActionType]

    def __init__(self) -> None:
        self.actions = {}

    def add_action(self, action: AIActionType) -> None:
        """Add an action to the library."""
        self.actions[action.name] = action

    def iter_actions(self) -> Iterator[AIActionType]:
        """Return iterator for the library."""
        return iter(self.actions.values())

    def get_action_with_name(self, name: str) -> AIActionType:
        """Get an action using its name."""
        return self.actions[name]


class AIBehavior(ABC):
    """A behavior that can be performed by a character."""

    __slots__ = (
        "name",
        "precondition",
    )

    name: str
    """The name of the behavior."""
    precondition: AIPrecondition
    """Calculates if the action can be performed."""

    def __init__(
        self,
        name: str,
        precondition: AIPrecondition,
    ) -> None:
        self.name = name
        self.precondition = precondition

    def get_name(self) -> str:
        """Get the name of the behavior."""
        return self.name

    def passes_preconditions(self, gameobject: GameObject) -> bool:
        """Check if the given character passes all the preconditions."""
        context = gameobject.get_component(AIBrain).context.create_child()
        return self.precondition.evaluate(context)

    @abstractmethod
    def get_actions(self, character: GameObject) -> list[AIAction]:
        """Get valid actions for performing this behavior."""
        raise NotImplementedError


class AIBehaviorLibrary:
    """The library of AI behaviors."""

    __slots__ = ("behaviors",)

    behaviors: dict[str, AIBehavior]

    def __init__(self) -> None:
        self.behaviors = {}

    def add_behavior(self, behavior: AIBehavior) -> None:
        """Add behavior to the library."""
        self.behaviors[behavior.get_name()] = behavior

    def iter_behaviors(self) -> Iterator[AIBehavior]:
        """Return iterator to behaviors."""
        return iter(self.behaviors.values())

    def get_behavior(self, name: str) -> AIBehavior:
        """Get a behavior by name."""
        return self.behaviors[name]


class SchemeData(Component, ABC):
    """Context-specific data for a scheme.

    This class should be derived from when creating new scheme types.
    """

    @abstractmethod
    def get_description(self, scheme: Scheme) -> str:
        """Get a string description of the scheme."""
        raise NotImplementedError()


class Scheme(Component):
    """Encapsulates a SchemeState object within the ECS."""

    __slots__ = (
        "required_time",
        "scheme_type",
        "start_date",
        "initiator",
        "members",
        "data",
        "is_valid",
    )

    required_time: int
    """Amount of time required for this scheme to mature."""
    scheme_type: str
    """The name of this scheme type."""
    start_date: SimDate
    """The date the scheme was started."""
    initiator: GameObject
    """The character that initiated the scheme."""
    members: OrderedSet[GameObject]
    """All characters involved in planning the scheme."""
    data: SchemeData
    """Context-specific data about this scheme."""
    is_valid: bool
    """Is the scheme still valid."""

    def __init__(
        self,
        scheme_type: str,
        required_time: int,
        date_started: SimDate,
        initiator: GameObject,
        data: SchemeData,
    ) -> None:
        super().__init__()
        self.scheme_type = scheme_type
        self.required_time = required_time
        self.start_date = date_started.copy()
        self.initiator = initiator
        self.members = OrderedSet([])
        self.data = data
        self.is_valid = True

    def get_type(self) -> str:
        """Get a type name for this Scheme."""
        return self.scheme_type

    def get_description(self) -> str:
        """Get a string description of the scheme."""
        return self.data.get_description(self)

    def __str__(self) -> str:
        return self.get_description()


class SchemeManager(Component):
    """Tracks all schemes that a character has initiated and is a member of."""

    __slots__ = (
        "initiated_schemes",
        "schemes",
    )

    initiated_schemes: list[GameObject]
    """All active schemes that a character initiated."""
    schemes: list[GameObject]
    """All active schemes that a character is part of (including those initiated)."""

    def __init__(self) -> None:
        super().__init__()
        self.initiated_schemes = []
        self.schemes = []

    def add_scheme(self, scheme: GameObject) -> None:
        """Add a scheme to the manager."""
        self.schemes.append(scheme)
        if scheme.get_component(Scheme).initiator == self.gameobject:
            self.initiated_schemes.append(scheme)

    def remove_scheme(self, scheme: GameObject) -> None:
        """Remove a scheme from the manager."""
        self.schemes.remove(scheme)
        if scheme.get_component(Scheme).initiator == self.gameobject:
            self.initiated_schemes.remove(scheme)

    def get_initiated_schemes(self) -> Iterable[GameObject]:
        """Get all schemes initiated by this character."""
        return self.initiated_schemes

    def get_schemes(self) -> Iterable[GameObject]:
        """Get all the schemes the character is a member of."""
        return self.schemes
