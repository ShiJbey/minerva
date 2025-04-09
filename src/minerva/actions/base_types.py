"""Character action/behaviors.

Actions are operations performed by agents. Each action has two probability scores.
The first how likely it is an agent will attempt the action, and the second describes
how likely the action is to succeed if it is attempted.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import (
    Any,
    Callable,
    ClassVar,
    DefaultDict,
    Generic,
    Iterable,
    Iterator,
    Optional,
    Protocol,
    Type,
    TypeVar,
    cast,
)

from minerva.characters.components import Character
from minerva.ecs import Component, Entity, World
from minerva.game_action import GameAction
from minerva.game_state import GameState
from minerva.sim_db import SimDB

P_ALWAYS = 999
P_USUALLY = 7
P_FREQUENTLY = 3
P_LIKELY = 1
P_UNLIKELY = -1
P_INFREQUENTLY = -3
P_RARELY = -7
P_NEVER = -999


class ActionSelectionStrategy(ABC):
    """A utility object that helps AIBrains choose an action to execute."""

    @abstractmethod
    def choose_action(self, action_scores: ProclivityScores) -> Optional[AIAction]:
        """Select an action from the given collection of actions."""
        raise NotImplementedError()


class AIBrain:
    """A brain used to make choices for a character."""

    __slots__ = (
        "uid",
        "name",
        "action_selection_strategy",
        "sensors",
    )

    uid: int
    """A unique ID assigned to this brain."""
    name: str
    """A unique name assigned to this brain."""
    sensors: list[AISensor]
    """Sensors used to fill the blackboard with information about the world/action."""
    action_selection_strategy: ActionSelectionStrategy
    """Function called to choose from a collection of sorted actions."""

    def __init__(
        self,
        name: str,
        sensors: list[AISensor],
        action_selection_strategy: ActionSelectionStrategy,
    ) -> None:
        self.uid = -1
        self.name = name
        self.sensors = sensors
        self.action_selection_strategy = action_selection_strategy


class AIBrainDatabase:
    """A database for all the brains that control characters."""

    __slots__ = ("_uid_to_brain_map", "_name_to_uid_map", "_next_brain_uid")

    _next_brain_uid: int
    """The UID assigned to the next brain in the database."""
    _uid_to_brain_map: dict[int, AIBrain]
    """Trait UIDs mapped to brain instances."""
    _name_to_uid_map: dict[str, int]
    """Trait names mapped to UIDs."""

    def __init__(self) -> None:
        self._next_brain_uid = 1
        self._uid_to_brain_map = {}
        self._name_to_uid_map = {}

    def get_brains(self) -> list[AIBrain]:
        """Get all brains in the database."""
        return list(self._uid_to_brain_map.values())

    def get_brain_by_name(self, name: str) -> AIBrain:
        """Get a brain using it's name."""
        uid = self._name_to_uid_map[name]
        return self._uid_to_brain_map[uid]

    def get_brain_by_uid(self, uid: int) -> AIBrain:
        """Get a brain using its UID."""
        return self._uid_to_brain_map[uid]

    def add_brain(self, brain: AIBrain) -> None:
        """Add a brain to the database."""
        brain.uid = self._next_brain_uid
        self._next_brain_uid += 1
        self._uid_to_brain_map[brain.uid] = brain
        self._name_to_uid_map[brain.name] = brain.uid


class AISensor(ABC):
    """An object that retrieves some world state to help fill AI blackboard."""

    @abstractmethod
    def evaluate(self, entity: Entity, blackboard: dict[str, Any]) -> None:
        """Run the sensor and write to the context's blackboard."""
        raise NotImplementedError()


class AIPrecondition(Protocol):
    """A precondition required for a behavior to be available."""

    @abstractmethod
    def __call__(self, entity: Entity) -> bool:
        """Evaluate the precondition."""
        raise NotImplementedError()


class AIPreconditionGroup(AIPrecondition):
    """A composite group of preconditions."""

    __slots__ = ("preconditions",)

    preconditions: list[AIPrecondition]

    def __init__(self, *preconditions: AIPrecondition) -> None:
        super().__init__()
        self.preconditions = list(preconditions)

    def __call__(self, entity: Entity) -> bool:
        return all(p(entity) for p in self.preconditions)


def get_next_event_uid(world: World) -> int:
    """Get next UID for event."""

    game_state = world.get_resource(GameState)
    uid = game_state.next_event_uid
    game_state.next_event_uid += 1
    return uid


class CharacterController(Component):
    """Manages character-specific AI information."""

    __slots__ = ("brain", "blackboard", "action_cooldowns", "action_counts")

    brain: AIBrain
    blackboard: dict[str, Any]
    action_cooldowns: DefaultDict[Type[AIAction], int]
    action_counts: DefaultDict[Type[AIAction], int]

    def __init__(self, brain: AIBrain) -> None:
        super().__init__()
        self.brain = brain
        self.blackboard = {}
        self.action_cooldowns = defaultdict(lambda: 0)
        self.action_counts = defaultdict(lambda: 0)


class AIAction(GameAction):
    """An action that a character can take."""

    __action_cost__: ClassVar[int] = 0
    """The number of influence points required to execute this action."""
    __action_cooldown__: ClassVar[int] = 0
    """Number of months between recurred uses of this action by the same character."""
    __action_tags__: Iterable[str] = ()
    """Tags associated with this action (used for action selection)."""

    __slots__ = ("initiator", "context")

    initiator: Entity
    """The UID of the entity that is performing the action."""
    context: dict[str, Any]
    """General backboard values."""

    def __init__(self, initiator: Entity) -> None:
        super().__init__(initiator.world)
        self.initiator = initiator
        self.context = {"initiator": initiator}

    @property
    def tags(self) -> Iterable[str]:
        """The tags associated with this action."""
        return set(self.__action_tags__)

    def can_perform(self) -> int:
        """Check if requirements are met to perform the action."""
        character_controller = self.initiator.get_component(CharacterController)
        cooldown_time = character_controller.action_cooldowns[type(self)]
        character_component = self.initiator.get_component(Character)

        return (
            cooldown_time <= 0
            and character_component.influence_points >= self.get_cost()
        )

    def get_cost(self) -> int:
        """Get the influence point cost of this action."""
        return self.__action_cost__

    def get_cooldown_time(self) -> int:
        """Get the cooldown time for this action."""
        return self.__action_cooldown__

    def execute(self) -> None:
        self.initiator.get_component(CharacterController).action_cooldowns[
            type(self)
        ] = self.get_cooldown_time()
        self.initiator.get_component(Character).influence_points -= self.get_cost()
        return super().execute()


_T = TypeVar("_T", bound=AIAction)
_T_co = TypeVar("_T_co", covariant=True, bound=AIAction)


class IProclivity(Protocol):
    """A function that scores a character's desire to perform an action."""

    def __call__(self, action: AIAction) -> int:
        """Evaluate the action."""
        raise NotImplementedError()


class Proclivity(Generic[_T]):
    """A consideration function for characters taking actions."""

    __slots__ = ("action_type", "score", "conditions")

    action_type: Type[_T]
    """The action type this is mapped to."""
    score: int
    """The score to return if the proclivity applies."""
    conditions: list[Callable[[_T], bool]]
    """Conditions that must pass for the score to be returned."""

    def __init__(self, score: int, action_type: Type[_T] = AIAction) -> None:
        self.action_type = action_type
        self.score = score
        self.conditions = []

    def where(self, condition: Callable[[_T], bool]) -> Proclivity[_T]:
        """Add a condition to a proclivity."""
        self.conditions.append(condition)
        return self

    def __call__(self, action: _T) -> int:
        """Check if the preconditions pass."""
        if all(cond(action) for cond in self.conditions):
            return self.score

        return 0


class ProclivityTracker(Component):
    """Tracks all the action proclivities for an entity."""

    __slots__ = ("_proclivities",)

    _proclivities: dict[Type[AIAction], list[IProclivity]]

    def __init__(self) -> None:
        self._proclivities = {}

    def add_proclivity(
        self, action_type: Type[_T_co], proclivity: Callable[[_T_co], int]
    ) -> None:
        """Add a proclivity to the database."""
        if action_type not in self._proclivities:
            self._proclivities[action_type] = []

        self._proclivities[action_type].append(cast(IProclivity, proclivity))

    def remove_proclivity(
        self, action_type: Type[_T_co], proclivity: Callable[[_T_co], int]
    ) -> None:
        """Remove a proclivity from the database."""
        if action_type not in self._proclivities:
            return

        try:
            self._proclivities[action_type].remove(cast(IProclivity, proclivity))

        except ValueError:
            pass

        finally:
            if len(self._proclivities[action_type]) == 0:
                del self._proclivities[action_type]

    def get_proclivities(self, action: AIAction) -> list[IProclivity]:
        """Get all the proclivities for an action."""
        # Combine proclivities that are not associated with a specific type
        # with the proclivities specific to this action type.
        proclivities = [
            *self._proclivities.get(AIAction, []),
            *self._proclivities.get(type(action), []),
        ]
        return proclivities


class ActionTagDatabase:
    """Manages all valid tags for actions."""

    __slots__ = ("_uid_to_tag_map", "_tag_to_uid_map", "_next_tag_uid")

    _next_tag_uid: int
    """The UID associated with the next tag added to the database."""
    _uid_to_tag_map: dict[int, str]
    """Maps UIDs to text tags."""
    _tag_to_uid_map: dict[str, int]
    """Maps tags to UIDs."""

    def __init__(self) -> None:
        self._next_tag_uid = 1
        self._uid_to_tag_map = {}
        self._tag_to_uid_map = {}

    def get_tags(self) -> list[str]:
        """List all the tags in the database."""
        return list(self._uid_to_tag_map.values())

    def get_tag_by_uid(self, uid: int):
        """Get a tag using its UID."""
        return self._uid_to_tag_map[uid]

    def tag_exists(self, tag: str) -> bool:
        """Check if the given tag is in the database."""
        return tag in self._tag_to_uid_map

    def get_tag_uid(self, tag: str) -> int:
        """Get the UID for a given tag."""
        return self._tag_to_uid_map[tag]

    def add_tag(self, tag: str) -> None:
        """Add a new tag to the database."""
        self._uid_to_tag_map[self._next_tag_uid] = tag
        self._tag_to_uid_map[tag] = self._next_tag_uid
        self._next_tag_uid += 1


def get_proclivity_score(action: AIAction) -> float:
    """Calculate the proclivity of a single action on a scale [0.0, 1.0]"""

    # This method calculates proclivities using a method described
    # in a Jon Ingold presentation that I cannot seem to find. Essentially,
    # the final score = (total positive scores) / (total pos) + abs(total negative)
    # This calculation ensures that:
    # 1. There is always a chance of something happening (even if it's super small)
    # 2. The scores will always be between 0.0 and 1.0

    pos_score: float = 0
    abs_total_score: float = 0

    proclivity_tracker = action.initiator.get_component(ProclivityTracker)
    action_proclivities = proclivity_tracker.get_proclivities(action)
    for proclivity in action_proclivities:
        score = proclivity(action)

        if score <= P_NEVER:
            return 0.0

        if score > 0:
            pos_score += score

        abs_total_score += abs(score)

    proclivity_db = action.world.get_resource(ProclivityDatabase)
    action_proclivities = proclivity_db.get_proclivities(action)
    for proclivity in action_proclivities:
        score = proclivity(action)

        if score <= P_NEVER:
            return 0.0

        if score > 0:
            pos_score += score

        abs_total_score += abs(score)

    # If we have no proclivities for this action, just assume that
    # there is a 50/50 chance that the character would want to
    # perform the action. This helps prevent division by zero errors.
    if abs_total_score == 0:
        return 0.5

    return pos_score / abs_total_score


def score_actions(potential_actions: Iterable[AIAction]) -> ProclivityScores:
    """Calculate the proclivity of each action."""

    scores: list[float] = []
    actions: list[AIAction] = []

    for action_instance in potential_actions:
        score = get_proclivity_score(action_instance)

        scores.append(score)
        actions.append(action_instance)

    return ProclivityScores(actions=actions, weights=scores)


class ProclivityDatabase:
    """Manages type-specific proclivities for AI Actions."""

    __slots__ = ("_proclivities",)

    _proclivities: dict[Type[AIAction], list[IProclivity]]

    def __init__(self) -> None:
        self._proclivities = {}

    def add_proclivity(
        self, action_type: Type[_T_co], proclivity: Callable[[_T_co], int]
    ) -> None:
        """Add a proclivity to the database."""
        if action_type not in self._proclivities:
            self._proclivities[action_type] = []

        self._proclivities[action_type].append(cast(IProclivity, proclivity))

    def remove_proclivity(
        self, action_type: Type[_T_co], proclivity: Callable[[_T_co], int]
    ) -> None:
        """Remove a proclivity from the database."""
        if action_type not in self._proclivities:
            return

        try:
            self._proclivities[action_type].remove(cast(IProclivity, proclivity))

        except ValueError:
            pass

        finally:
            if len(self._proclivities[action_type]) == 0:
                del self._proclivities[action_type]

    def get_proclivities(self, action: AIAction) -> list[IProclivity]:
        """Get all the proclivities for an action."""
        # Combine proclivities that are not associated with a specific type
        # with the proclivities specific to this action type.
        proclivities = [
            *self._proclivities.get(AIAction, []),
            *self._proclivities.get(type(action), []),
        ]
        return proclivities


class AIBehavior(ABC):
    """A behavior that can be performed by a character."""

    __slots__ = ("name", "precondition")

    name: str
    """The name of the behavior."""
    precondition: Callable[[Entity], bool]
    """Calculates if the action can be performed."""

    def __init__(
        self, name: str, precondition: Optional[AIPrecondition] = None
    ) -> None:
        self.name = name
        self.precondition = lambda _: True
        if precondition is not None:
            self.precondition = precondition

    def passes_preconditions(self, entity: Entity) -> bool:
        """Check if the given character passes all the preconditions."""
        return self.precondition(entity)

    @abstractmethod
    def get_actions(self, character: Entity) -> list[AIAction]:
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
        self.behaviors[behavior.name] = behavior

    def iter_behaviors(self) -> Iterator[AIBehavior]:
        """Return iterator to behaviors."""
        return iter(self.behaviors.values())

    def get_behavior(self, name: str) -> AIBehavior:
        """Get a behavior by name."""
        return self.behaviors[name]


class ProclivityScores:
    """Results of a proclivity calculation."""

    __slots__ = ("actions", "scores")

    actions: list[AIAction]
    scores: list[float]

    def __init__(self, actions: list[AIAction], weights: list[float]) -> None:
        self.actions = actions
        self.scores = weights


class EventHistory(Component):
    """Tracks events associated with this entity."""

    __slots__ = ("_event_ids",)

    _event_ids: list[int]

    def __init__(self) -> None:
        super().__init__()
        self._event_ids = []

    def append(self, event_id: int) -> None:
        """Add an event ID to the history."""
        self._event_ids.append(event_id)

    def get_events(self) -> list[int]:
        """Get all events in the history."""
        return self._event_ids


def get_event_timestamp(world: World, event_id: int) -> int:
    """Get the timestamp for the event with the given event ID."""

    db = world.get_resource(SimDB).conn
    cursor = db.cursor()

    # First get the event information
    timestamp: int = cursor.execute(
        """
        SELECT
            timestamp
        FROM events
        WHERE uid=?;
        """,
        (event_id,),
    ).fetchone()[0]

    return int(timestamp)


def get_event_description(world: World, event_id: int) -> str:
    """Get the description for the life event with the given event ID."""

    db = world.get_resource(SimDB).conn
    cursor = db.cursor()

    description: str = cursor.execute(
        """
        SELECT
            description
        FROM events
        WHERE uid=?;
        """,
        (event_id,),
    ).fetchone()[0]

    return description
