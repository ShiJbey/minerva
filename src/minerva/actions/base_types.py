"""Character action/behaviors.

Actions are operations performed by agents. Each action has two probability scores.
The first how likely it is an agent will attempt the action, and the second describes
how likely the action is to succeed if it is attempted.

"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Callable, ClassVar, DefaultDict, Iterable, Iterator, Optional

from ordered_set import OrderedSet

from minerva.ecs import Component, Entity, World
from minerva.game_state import GameState
from minerva.pcg.text_gen import render_string
from minerva.sim_db import SimDB

_logger = logging.getLogger(__name__)

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
    def choose_action(self, action_scores: ProclivityScores) -> AIAction:
        """Select an action from the given collection of actions."""
        raise NotImplementedError()


class Proclivity:
    """A consideration function for characters taking actions."""

    __slots__ = ("score", "conditions")

    score: int
    """The score to return if the proclivity applies."""
    conditions: list[Callable[[AIAction], bool]]
    """Conditions that must pass for the score to be returned."""

    def __init__(self, score: int) -> None:
        self.score = score
        self.conditions = []

    def where(self, condition: Callable[[AIAction], bool]) -> Proclivity:
        """Add a condition to a proclivity."""
        self.conditions.append(condition)
        return self

    def check_preconditions(self, ctx: AIAction) -> bool:
        """Check if the preconditions pass."""
        return all(cond(ctx) for cond in self.conditions)


class ProclivityTracker(Component):
    """Tracks all the action proclivities for an entity."""

    __slots__ = ("proclivities", "target_proclivities")

    proclivities: list[Proclivity]
    """Proclivities evaluated when a character is initiates an action."""
    target_proclivities: list[Proclivity]
    """Proclivities evaluated when a character is the recipient of an action."""

    def __init__(self) -> None:
        super().__init__()
        self.proclivities = []
        self.target_proclivities = []


class GlobalProclivities:
    """A collection of proclivities evaluated against every action."""

    __slots__ = ("proclivities",)

    proclivities: list[Proclivity]
    """Proclivities to evaluate."""

    def __init__(self) -> None:
        self.proclivities = []


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

    proclivity_tracker = action.initiator.get_component(ProclivityTracker)

    pos_score: float = 0
    abs_total_score: float = 0

    for proclivity in proclivity_tracker.proclivities:
        if proclivity.check_preconditions(action):
            if proclivity.score <= P_NEVER:
                return 0.0

            if proclivity.score > 0:
                pos_score += proclivity.score

            abs_total_score += abs(proclivity.score)

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
    """Function called to choose from a collection of sorted actions
    """

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


class AIPrecondition(ABC):
    """A precondition required for a behavior to be available."""

    @abstractmethod
    def evaluate(self, entity: Entity) -> bool:
        """Evaluate the precondition."""
        raise NotImplementedError()


class AIPreconditionGroup(AIPrecondition):
    """A composite group of preconditions."""

    __slots__ = ("preconditions",)

    preconditions: list[AIPrecondition]

    def __init__(self, *preconditions: AIPrecondition) -> None:
        super().__init__()
        self.preconditions = list(preconditions)

    def evaluate(self, entity: Entity) -> bool:
        return all(p.evaluate(entity) for p in self.preconditions)


class CharacterController(Component):
    """Manages character-specific AI information."""

    __slots__ = ("brain", "blackboard", "action_cooldowns")

    brain: AIBrain
    blackboard: dict[str, Any]
    action_cooldowns: DefaultDict[str, int]

    def __init__(self, brain: AIBrain) -> None:
        super().__init__()
        self.brain = brain
        self.blackboard = {}
        self.action_cooldowns = defaultdict(lambda: 0)


class AIActionType:
    """An abstract base class for all actions."""

    __slots__ = (
        "name",
        "display_name",
        "description",
        "cost",
        "cooldown",
        "tags",
    )

    name: str
    """The name of this action type."""
    display_name: str
    """The name of the event when displayed in a GUI."""
    description: str
    """A text template used to generate a textual description of this event type."""
    cost: int
    """The number of influence points required to execute this action."""
    cooldown: int
    """Number of months between recurred uses of this action by the same character."""
    tags: set[str]
    """Tags associated with this action (used for action selection)."""

    def __init__(
        self,
        name: str,
        display_name: str,
        description: str,
        cost: int = 0,
        cooldown: int = 0,
        tags: Optional[Iterable[str]] = None,
    ) -> None:
        super().__init__()
        self.name = name
        self.display_name = display_name
        self.description = description
        self.cost = cost
        self.cooldown = cooldown
        self.tags = set(tags if tags else [])


class AIAction(ABC):
    """An action that a character can take."""

    __slots__ = (
        "uid",
        "world",
        "action_type",
        "initiator",
        "recipient",
        "target",
        "timestamp",
        "context",
    )

    _next_uid: ClassVar[int] = 1

    uid: int
    """The unique ID for this event."""
    world: World
    """The simulation's world instance."""
    action_type: AIActionType
    """A reference to the action this is an instantiation of."""
    initiator: Entity
    """The UID of the entity that is performing the action."""
    recipient: Optional[Entity]
    """The UID of the entity the action is directed toward."""
    target: Optional[Entity]
    """The UID of the entity being acted upon."""
    timestamp: int
    """The timestamp of the event."""
    context: dict[str, str]
    """Arguments passed to the database."""

    def __init__(
        self,
        name: str,
        initiator: Entity,
        recipient: Optional[Entity] = None,
        target: Optional[Entity] = None,
        context: Optional[dict[str, str]] = None,
    ) -> None:
        super().__init__()
        super().__init__()
        self.uid = -1
        self.world = initiator.world
        self.initiator = initiator
        self.timestamp = self.world.get_resource(GameState).year
        self.action_type = initiator.world.get_resource(
            ActionTypeDatabase
        ).get_action_with_name(name)
        self.recipient = recipient
        self.target = target
        self.context = {
            "initiator": initiator.name_with_uid,
        }

        if self.recipient:
            self.context["recipient"] = self.recipient.name_with_uid

        if self.target:
            self.context["target"] = self.target.name_with_uid

        if context:
            self.context.update(context)

    @abstractmethod
    def execute(self) -> None:
        """Execute the action using the instance information."""
        raise NotImplementedError()

    def log_event(self, *entities: Entity) -> int:
        """Dispatches the event to the proper listeners."""
        self.uid = AIAction._next_uid
        AIAction._next_uid += 1

        _logger.info(
            "[%04d]: %s",
            self.timestamp,
            render_string(
                self.action_type.description,
                {
                    "initiator": self.initiator.name_with_uid,
                    "subject": self.initiator.name_with_uid,
                    "target": self.target.name_with_uid if self.target else "",
                    "recipient": self.recipient.name_with_uid if self.recipient else "",
                    **self.context,
                },
            ),
        )

        db = self.world.get_resource(SimDB).conn
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO events
                (uid, event_type, initiator, recipient, target, timestamp)
            VALUES
                (?, ?, ?, ?, ?, ?);
            """,
            (
                self.uid,
                self.action_type.name,
                self.initiator.uid,
                self.recipient.uid if self.recipient else None,
                self.target.uid if self.target else None,
                self.timestamp,
            ),
        )

        cursor.executemany(
            """
            INSERT INTO event_args (uid, name, value)
            VALUES (?, ?, ?);
            """,
            [(self.uid, k, v) for k, v in self.context.items()],
        )

        db.commit()
        cursor.close()

        for entity in entities:
            entity.get_component(EventHistory).append(self.uid)

        return 0

    def get_name(self) -> str:
        """Get the name of the action."""
        return self.action_type.name

    def get_cost(self) -> int:
        """Get the influence point cost of this action."""
        return self.action_type.cost

    def get_cooldown_time(self) -> int:
        """Get the cooldown time for this action."""
        return self.action_type.cooldown


class ActionTypeDatabase:
    """The Database of AI action types."""

    __slots__ = ("_action_types",)

    _action_types: dict[str, AIActionType]

    def __init__(self) -> None:
        self._action_types = {}

    def add_action(self, action_type: AIActionType) -> None:
        """Add an action type to the database."""
        self._action_types[action_type.name] = action_type

    def get_actions(self) -> list[AIActionType]:
        """Get all actions in the database."""
        return list(self._action_types.values())

    def get_action_with_name(self, name: str) -> AIActionType:
        """Get an action using its name."""
        return self._action_types[name]


class AIBehavior(ABC):
    """A behavior that can be performed by a character."""

    __slots__ = ("name",)

    name: str
    """The name of the behavior."""

    def __init__(self, name: str) -> None:
        self.name = name

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

    event_type: str = cursor.execute(
        """
        SELECT
            event_type
        FROM events
        WHERE uid=?;
        """,
        (event_id,),
    ).fetchone()[0]

    action_database = world.get_resource(ActionTypeDatabase)
    action_type = action_database.get_action_with_name(event_type)

    # First get the event information

    event_args: list[tuple[str, str]] = cursor.execute(
        """
        SELECT
            name,
            value
        FROM event_args
        WHERE uid=?;
        """,
        (event_id,),
    ).fetchall()

    final_description = action_type.description
    for k, v in event_args:
        final_description = final_description.replace("[" + k + "]", v)

    return final_description


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
    start_date: int
    """The date the scheme was started."""
    initiator: Entity
    """The character that initiated the scheme."""
    members: OrderedSet[Entity]
    """All characters involved in planning the scheme."""
    data: SchemeData
    """Context-specific data about this scheme."""
    is_valid: bool
    """Is the scheme still valid."""

    def __init__(
        self,
        scheme_type: str,
        required_time: int,
        date_started: int,
        initiator: Entity,
        data: SchemeData,
    ) -> None:
        super().__init__()
        self.scheme_type = scheme_type
        self.required_time = required_time
        self.start_date = date_started
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

    initiated_schemes: list[Entity]
    """All active schemes that a character initiated."""
    schemes: list[Entity]
    """All active schemes that a character is part of (including those initiated)."""

    def __init__(self) -> None:
        super().__init__()
        self.initiated_schemes = []
        self.schemes = []

    def add_scheme(self, scheme: Entity) -> None:
        """Add a scheme to the manager."""
        self.schemes.append(scheme)
        if scheme.get_component(Scheme).initiator == self.entity:
            self.initiated_schemes.append(scheme)

    def remove_scheme(self, scheme: Entity) -> None:
        """Remove a scheme from the manager."""
        self.schemes.remove(scheme)
        if scheme.get_component(Scheme).initiator == self.entity:
            self.initiated_schemes.remove(scheme)

    def get_initiated_schemes(self) -> Iterable[Entity]:
        """Get all schemes initiated by this character."""
        return self.initiated_schemes

    def get_schemes(self) -> Iterable[Entity]:
        """Get all the schemes the character is a member of."""
        return self.schemes
