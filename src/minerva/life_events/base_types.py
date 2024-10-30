"""Life Event System.

Life events are the building block of story generation. We set them apart from the
ECS-related events by requiring that each have a timestamp of the in-simulation date
they were emitted.

"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from itertools import count
from typing import Callable, ClassVar, Iterable

from minerva.datetime import SimDate
from minerva.ecs import Component, GameObject, World
from minerva.sim_db import SimDB
from minerva.viz.game_events import EventEmitter

_logger = logging.getLogger(__name__)


class LifeEvent(ABC):
    """An event of significant importance in a GameObject's life"""

    _next_life_event_id: ClassVar[count[int]] = count()

    __slots__ = ("world", "subject", "event_id", "timestamp")

    world: World
    """The simulation's world instance."""
    subject: GameObject
    """What/Who is the event about."""
    event_id: int
    """Numerical ID of this life event."""
    timestamp: SimDate
    """The timestamp of the event"""

    def __init__(self, subject: GameObject) -> None:
        self.world = subject.world
        self.subject = subject
        self.event_id = next(self._next_life_event_id)
        self.timestamp = subject.world.resources.get_resource(SimDate).copy()

    @abstractmethod
    def get_event_type(self) -> str:
        """Get the name of this type of event."""
        raise NotImplementedError()

    def on_event_logged(self) -> None:
        """Called when logging the event."""
        return

    @abstractmethod
    def get_description(self) -> str:
        """Get a text description of the life event."""
        raise NotImplementedError()

    def log_event(self) -> None:
        """Dispatches the event to the proper listeners."""
        self.subject.get_component(LifeEventHistory).log_event(self)

        db = self.world.resources.get_resource(SimDB).db
        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO life_events (event_id, subject_id, event_type, timestamp, description)
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                self.event_id,
                self.subject.uid,
                self.get_event_type(),
                self.timestamp.to_iso_str(),
                self.get_description(),
            ),
        )
        db.commit()

        _logger.info("[%s]: %s", str(self.timestamp), self.get_description())

        self.on_event_logged()

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.event_id}, "
            f" timestamp={self.timestamp!r})"
        )

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.event_id}, "
            f" timestamp={self.timestamp!r})"
        )


class LifeEventHistory(Component):
    """Stores a record of all past life events for a specific GameObject."""

    __slots__ = ("_history", "_event_emitter")

    _history: list[LifeEvent]
    """A list of events in chronological-order."""
    _event_emitter: EventEmitter[LifeEvent]
    """Emitter invoked whenever a life event is logged."""

    def __init__(self) -> None:
        super().__init__()
        self._history = []
        self._event_emitter = EventEmitter()

    def log_event(self, life_event: LifeEvent) -> None:
        """Log an event to the event history."""
        self._history.append(life_event)
        self._event_emitter.emit(life_event)

    def add_listener(self, listener: Callable[[LifeEvent], None]) -> None:
        """Add a listener to this life event history."""
        self._event_emitter.add_listener(listener)

    def remove_listener(self, listener: Callable[[LifeEvent], None]) -> None:
        """Add a listener to this life event history."""
        self._event_emitter.remove_listener(listener)

    def remove_all_listeners(self) -> None:
        """Add a listener to this life event history."""
        self._event_emitter.remove_all_listeners()

    def get_history(self) -> Iterable[LifeEvent]:
        """Get all life events for this character."""
        return self._history

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._history})"
