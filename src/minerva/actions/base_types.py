"""Character action/behaviors.

Actions are operations performed by agents. Each action has two probability scores.
The first how likely it is an agent will attempt the action, and the second describes
how likely the action is to succeed if it is attempted.

"""

from __future__ import annotations

import enum
import random
from abc import ABC, abstractmethod
from typing import Any, Iterable, Iterator, Optional

from ordered_set import OrderedSet

from minerva.characters.motive_helpers import MotiveVector
from minerva.datetime import SimDate
from minerva.ecs import Component, GameObject, World


class ActionSelectionStrategy(ABC):
    """A utility object that helps AIBrains choose an action to execute."""

    @abstractmethod
    def choose_action(self, actions: Iterable[AIAction]) -> AIAction:
        """Select an action from the given collection of actions."""
        raise NotImplementedError()


class BehaviorSelectionStrategy(ABC):
    """A utility object that helps AIBrains choose a behavior to execute."""

    @abstractmethod
    def choose_behavior(
        self, character: GameObject, behaviors: Iterable[AIBehavior]
    ) -> AIBehavior:
        """Select a behavior from the given collection of behaviors."""
        raise NotImplementedError()


class AIBrain(Component):
    """A brain used to make choices for a character."""

    __slots__ = ("context", "action_selection_strategy", "behavior_selection_strategy")

    context: AIContext
    action_selection_strategy: ActionSelectionStrategy
    behavior_selection_strategy: BehaviorSelectionStrategy

    def __init__(
        self,
        context: AIContext,
        action_selection_strategy: ActionSelectionStrategy,
        behavior_selection_strategy: BehaviorSelectionStrategy,
    ) -> None:
        super().__init__()
        self.context = context
        self.action_selection_strategy = action_selection_strategy
        self.behavior_selection_strategy = behavior_selection_strategy


class AISensor(ABC):
    """An object that retrieves some world state to help fill AI blackboard."""

    @abstractmethod
    def evaluate(self, context: AIContext) -> None:
        """Run the sensor and write to the context's blackboard."""
        raise NotImplementedError()

    @abstractmethod
    def clear_output(self, context: AIContext) -> None:
        """Clear the output from the sensor."""
        raise NotImplementedError()


class AIContext:
    """A context of information used for AI decision making."""

    __slots__ = ("blackboard", "world", "character", "sensors")

    blackboard: dict[str, Any]
    world: World
    character: GameObject
    sensors: list[AISensor]

    def __init__(
        self, world: World, character: GameObject, sensors: list[AISensor]
    ) -> None:
        self.blackboard = {}
        self.world = world
        self.character = character
        self.sensors = [*sensors]

    def update_sensors(self) -> None:
        """Run all the sensors."""
        for sensor in self.sensors:
            sensor.evaluate(self)

    def clear_sensors(self) -> None:
        """Clear the output from all sensors."""
        for sensor in self.sensors:
            sensor.clear_output(self)

    def copy(self) -> AIContext:
        """Create a copy of the context."""
        context_copy = AIContext(self.world, self.character, self.sensors)
        context_copy.blackboard = self.blackboard.copy()
        return context_copy


class AIPrecondition(ABC):
    """A precondition required for an action to be executed."""

    @abstractmethod
    def evaluate(self, context: AIContext) -> bool:
        """Evaluate the precondition."""
        raise NotImplementedError()


class AIUtilityConsideration(ABC):
    """A consideration of the utility of taking an action."""

    @abstractmethod
    def evaluate(self, context: AIContext) -> float:
        """Evaluate the consideration."""
        raise NotImplementedError()


class AISuccessConsideration(ABC):
    """A consideration of the chance of success for an action."""

    @abstractmethod
    def evaluate(self, context: AIContext) -> float:
        """Evaluate the consideration."""
        raise NotImplementedError()


class ConstantUtilityConsideration(AIUtilityConsideration):
    """A utility consideration that is a constant value."""

    __slots__ = ("value",)

    value: float

    def __init__(self, value: float) -> None:
        super().__init__()
        self.value = value

    def evaluate(self, context: AIContext) -> float:
        return self.value


class ConstantSuccessConsideration(AISuccessConsideration):
    """A success consideration that is a constant value."""

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

    GEOMETRIC_MEAN = 0
    MIN = enum.auto()
    MAX = enum.auto()


class AIUtilityConsiderationGroup(AIUtilityConsideration):
    """A composite group of utility considerations."""

    __slots__ = ("op", "considerations")

    op: AIConsiderationGroupOp
    considerations: list[AIUtilityConsideration]

    def __init__(
        self,
        op: AIConsiderationGroupOp,
        considerations: Iterable[AIUtilityConsideration],
    ) -> None:
        super().__init__()
        self.op = op
        self.considerations = list(considerations)

    def evaluate(self, context: AIContext) -> float:
        if self.op == AIConsiderationGroupOp.GEOMETRIC_MEAN:
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


class AISuccessConsiderationGroup(AISuccessConsideration):
    """A composite group of success considerations."""

    __slots__ = ("op", "considerations")

    op: AIConsiderationGroupOp
    considerations: list[AISuccessConsideration]

    def __init__(
        self,
        op: AIConsiderationGroupOp,
        considerations: Iterable[AISuccessConsideration],
    ) -> None:
        super().__init__()
        self.op = op
        self.considerations = list(considerations)

    def evaluate(self, context: AIContext) -> float:
        if self.op == AIConsiderationGroupOp.GEOMETRIC_MEAN:
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


class AIActionType(ABC):
    """An abstract base class for all actions."""

    __slots__ = (
        "success_consideration",
        "utility_consideration",
        "precondition",
    )

    success_consideration: AISuccessConsideration
    utility_consideration: AIUtilityConsideration
    precondition: AIPrecondition

    def __init__(
        self,
        success_consideration: AISuccessConsideration,
        utility_consideration: AIUtilityConsideration,
        precondition: AIPrecondition,
    ) -> None:
        super().__init__()
        self.success_consideration = success_consideration
        self.utility_consideration = utility_consideration
        self.precondition = precondition

    def can_execute(self, context: AIContext) -> bool:
        """Check if the action can be executed."""
        return self.precondition.evaluate(context)

    def calculate_utility(self, context: AIContext) -> float:
        """Get the utility of this action."""
        return self.utility_consideration.evaluate(context)

    def calculate_success_probability(self, context: AIContext) -> float:
        """Get probability of the action being successful."""
        return self.success_consideration.evaluate(context)

    @abstractmethod
    def execute(self, context: AIContext) -> bool:
        """Execute the action."""
        raise NotImplementedError()


class AIAction(ABC):
    """An action that a character can take."""

    __slots__ = ("context", "action")

    context: AIContext
    action: AIActionType

    def __init__(self, context: AIContext, action: AIActionType) -> None:
        super().__init__()
        self.context = context.copy()
        self.action = action

    def can_execute(self) -> bool:
        """Check if the action can be executed."""
        return self.action.can_execute(self.context)

    def calculate_utility(self) -> float:
        """Get the utility of this action."""
        return self.action.calculate_utility(self.context)

    def calculate_success_probability(self) -> float:
        """Get probability of the action being successful."""
        return self.action.calculate_success_probability(self.context)

    def execute(self) -> bool:
        """Execute the action type."""
        return self.action.execute(self.context)


class AIActionLibrary:
    """The library of AI actions."""

    __slots__ = ("actions",)

    actions: dict[str, AIActionType]

    def __init__(self) -> None:
        self.actions = {}

    def add_action(self, action: AIActionType) -> None:
        """Add an action to the library."""
        self.actions[action.__class__.__name__] = action

    def iter_actions(self) -> Iterator[AIActionType]:
        """Return iterator for the library."""
        return iter(self.actions.values())

    def get_action_with_name(self, name: str) -> AIActionType:
        """Get an action using its name."""
        return self.actions[name]


class AIBehavior(ABC):
    """A behavior that can be performed by a character."""

    __slots__ = (
        "motives",
        "cost",
        "precondition",
        "utility_consideration",
    )

    precondition: AIPrecondition
    """Calculates if the action can be performed."""
    utility_consideration: AIUtilityConsideration
    """Calculates the utility of the behavior."""
    motives: MotiveVector
    """The motives satisfied by this behavior."""
    cost: int
    """The number of influence point required to execute this behavior."""

    def __init__(
        self,
        motives: MotiveVector,
        cost: int,
        precondition: AIPrecondition,
        utility_consideration: AIUtilityConsideration,
    ) -> None:
        self.utility_consideration = utility_consideration
        self.precondition = precondition
        self.motives = motives
        self.cost = cost

    def can_execute(self, gameobject: GameObject) -> bool:
        """Check if the action can be executed."""
        context = gameobject.get_component(AIBrain).context.copy()
        context.blackboard["behavior_cost"] = self.cost
        context.blackboard["behavior_motives"] = self.motives
        return self.precondition.evaluate(context)

    def calculate_utility(self, gameobject: GameObject) -> float:
        """Get the utility of this action."""
        context = gameobject.get_component(AIBrain).context.copy()
        context.blackboard["behavior_cost"] = self.cost
        context.blackboard["behavior_motives"] = self.motives
        return self.utility_consideration.evaluate(context)

    def passes_preconditions(self, gameobject: GameObject) -> bool:
        """check if the given character passes all the preconditions."""
        context = gameobject.get_component(AIBrain).context.copy()
        context.blackboard["behavior_cost"] = self.cost
        context.blackboard["behavior_motives"] = self.motives
        return self.precondition.evaluate(context)

    @abstractmethod
    def execute(self, character: GameObject) -> bool:
        """Execute the behavior with the given character."""
        raise NotImplementedError()


class AIBehaviorLibrary:
    """The library of AI behaviors."""

    __slots__ = ("behaviors",)

    behaviors: dict[str, AIBehavior]

    def __init__(self) -> None:
        self.behaviors = {}

    def add_behavior(self, behavior: AIBehavior) -> None:
        """Add behavior to the library."""
        self.behaviors[behavior.__class__.__name__] = behavior

    def iter_behaviors(self) -> Iterator[AIBehavior]:
        """Return iterator to behaviors."""
        return iter(self.behaviors.values())

    def get_behavior(self, name: str) -> AIBehavior:
        """Get a behavior by name."""
        return self.behaviors[name]


class AIActionCollection:
    """A collection of actions to select from."""

    __slots__ = ("actions", "utilities")

    actions: list[AIAction]
    utilities: list[float]

    def __init__(self) -> None:
        self.actions = []
        self.utilities = []

    def add(self, action: AIAction, utility: float) -> None:
        """Add an action to the collection."""
        self.actions.append(action)
        self.utilities.append(utility)

    def select_max(self) -> AIAction:
        """Select the action with the highest utility"""
        max_utility: float = -999_999
        best_action: Optional[AIAction] = None

        for i, action in enumerate(self.actions):
            utility = self.utilities[i]
            if utility > max_utility:
                best_action = action

        if best_action is None:
            raise ValueError("No actions found in list with utility greater than 0.")

        return best_action

    def select_any(self, rng: Optional[random.Random] = None) -> AIAction:
        """Randomly select any action from the collection."""
        if len(self.actions) == 0:
            raise ValueError("No actions found in list.")

        if rng is not None:
            return rng.choice(self.actions)
        else:
            return random.choice(self.actions)

    def select_weighted_random(self, rng: Optional[random.Random] = None) -> AIAction:
        """Perform weighted random selection over the actions."""
        if len(self.actions) == 0:
            raise ValueError("No actions found in list.")

        # Filter those with weights less than or equal to zero
        filtered_actions: list[AIAction] = []
        filtered_utilities: list[float] = []
        for i, utility in enumerate(self.utilities):
            if utility > 0:
                filtered_actions.append(self.actions[i])
                filtered_utilities.append(utility)

        if len(filtered_actions) == 0:
            raise ValueError("No actions found in list after filtering.")

        if rng is not None:
            return rng.choices(filtered_actions, filtered_utilities, k=1)[0]
        else:
            return random.choices(filtered_actions, filtered_utilities, k=1)[0]

    def __len__(self) -> int:
        return len(self.actions)

    def __bool__(self) -> bool:
        return bool(self.actions)


class AIBehaviorCollection:
    """A collection of behaviors to select from."""

    __slots__ = ("behaviors", "utilities", "rng")

    behaviors: list[AIBehavior]
    utilities: list[float]
    rng: Optional[random.Random]

    def __init__(self, rng: Optional[random.Random] = None) -> None:
        self.behaviors = []
        self.utilities = []
        self.rng = rng

    def add(self, behavior: AIBehavior, utility: float) -> None:
        """Add an action to the collection."""
        self.behaviors.append(behavior)
        self.utilities.append(utility)

    def select_max(self) -> AIBehavior:
        """Select the behavior with the highest utility"""
        max_utility: float = -999_999
        best_behavior: Optional[AIBehavior] = None

        for i, behavior in enumerate(self.behaviors):
            utility = self.utilities[i]
            if utility > max_utility:
                best_behavior = behavior

        if best_behavior is None:
            raise ValueError("No behaviors found in list with utility greater than 0.")

        return best_behavior

    def select_any(self) -> AIBehavior:
        """Randomly select any behavior from the collection."""
        if len(self.behaviors) == 0:
            raise ValueError("No behavior found in list.")

        if self.rng is not None:
            return self.rng.choice(self.behaviors)
        else:
            return random.choice(self.behaviors)

    def select_weighted_random(self) -> AIBehavior:
        """Perform weighted random selection over the behaviors."""
        if len(self.behaviors) == 0:
            raise ValueError("No behaviors found in list.")

        # Filter those with weights less than or equal to zero
        filtered_behaviors: list[AIBehavior] = []
        filtered_utilities: list[float] = []
        for i, utility in enumerate(self.utilities):
            if utility > 0:
                filtered_behaviors.append(self.behaviors[i])
                filtered_utilities.append(utility)

        if len(filtered_behaviors) == 0:
            raise ValueError("No actions found in list after filtering.")

        if self.rng is not None:
            return self.rng.choices(filtered_behaviors, filtered_utilities, k=1)[0]
        else:
            return random.choices(filtered_behaviors, filtered_utilities, k=1)[0]

    def __len__(self) -> int:
        return len(self.behaviors)

    def __bool__(self) -> bool:
        return bool(self.behaviors)


class SchemeStrategy(ABC):
    """An plan that takes has a delay before execution that others can join."""

    __slots__ = ("required_time",)

    required_time: int
    """Amount of time required for this scheme to mature."""

    def __init__(self, required_time: int) -> None:
        super().__init__()
        self.required_time = required_time

    @abstractmethod
    def get_description(self, scheme: Scheme) -> str:
        """Get a string description of the scheme."""
        raise NotImplementedError()

    @abstractmethod
    def update(self, scheme: Scheme) -> None:
        """Update the scheme and execute any code."""
        raise NotImplementedError()


class Scheme(Component):
    """Encapsulates a SchemeState object within the ECS."""

    __slots__ = (
        "scheme_type",
        "start_date",
        "initiator",
        "members",
        "targets",
        "strategy",
        "is_valid",
    )

    scheme_type: str
    """The name of this scheme type."""
    start_date: SimDate
    """The date the scheme was started."""
    initiator: GameObject
    """The character that initiated the scheme."""
    members: OrderedSet[GameObject]
    """All characters involved in planning the scheme."""
    targets: OrderedSet[GameObject]
    """All characters who are targets of the scheme."""
    strategy: SchemeStrategy
    """The strategy used to update and and check the validity of a scheme."""
    is_valid: bool
    """Is the scheme still valid."""

    def __init__(
        self,
        scheme_type: str,
        date_started: SimDate,
        initiator: GameObject,
        strategy: SchemeStrategy,
    ) -> None:
        super().__init__()
        self.scheme_type = scheme_type
        self.start_date = date_started.copy()
        self.initiator = initiator
        self.members = OrderedSet([])
        self.targets = OrderedSet([])
        self.strategy = strategy
        self.is_valid = True

    def get_type(self) -> str:
        """Get a type name for this Scheme."""
        return self.scheme_type

    def get_description(self) -> str:
        """Get a string description of the scheme."""
        return self.strategy.get_description(self)

    def update(self) -> None:
        """Update the scheme and execute any code."""
        self.strategy.update(self)

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


class SchemeStrategyLibrary:
    """Manages a repository of scheme strategies."""

    strategies: dict[str, SchemeStrategy]

    def __init__(self) -> None:
        self.strategies = {}

    def add_strategy(self, key: str, strategy: SchemeStrategy) -> None:
        """Add a strategy to the library."""
        self.strategies[key] = strategy

    def get_strategy(self, key: str) -> SchemeStrategy:
        """Retrieve a strategy using a key."""
        return self.strategies[key]

    def has_strategy(self, key: str) -> bool:
        """Check if a strategy exists for the given key."""
        return key in self.strategies
