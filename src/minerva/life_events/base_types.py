"""Life Event System.

Life events are the building block of story generation. We set them apart from the
ECS-related events by requiring that each have a timestamp of the in-simulation date
they were emitted. Life events are tracked in two places -- the GlobalEventHistory and
in characters' PersonalEventHistories.

"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from itertools import count
from typing import Any, ClassVar, Iterable

from minerva.datetime import SimDate
from minerva.ecs import Component, Event, World

_logger = logging.getLogger(__name__)


class LifeEvent(Event, ABC):
    """An event of significant importance in a GameObject's life"""

    _next_life_event_id: ClassVar[count[int]] = count()

    __slots__ = ("event_id", "timestamp")

    event_id: int
    """Numerical ID of this life event."""
    timestamp: SimDate
    """The timestamp of the event"""

    def __init__(self, event_type: str, world: World, **kwargs: Any) -> None:
        super().__init__(event_type, world, **kwargs)
        self.event_id = next(self._next_life_event_id)
        self.timestamp = world.resources.get_resource(SimDate).copy()

    @abstractmethod
    def on_dispatch(self) -> None:
        """Called when dispatching the event."""

        raise NotImplementedError()

    def dispatch(self, skip_logging: bool = False) -> None:
        """Dispatches the event to the proper listeners."""

        if not skip_logging:
            self.world.resources.get_resource(GlobalEventHistory).append(self)

            _logger.info("[%s]: %s", str(self.timestamp), str(self))

        self.world.events.dispatch_event(self)

        self.on_dispatch()

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.event_id}, "
            f"event_type={self.event_type!r}, timestamp={self.timestamp!r})"
        )

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.event_id}, "
            f"event_type={self.event_type!r}, timestamp={self.timestamp!r})"
        )


class EventHistory(Component):
    """Stores a record of all past events for a specific GameObject."""

    __slots__ = ("_history",)

    _history: list[LifeEvent]
    """A list of events in chronological-order."""

    def __init__(self) -> None:
        super().__init__()
        self._history = []

    @property
    def history(self) -> Iterable[LifeEvent]:
        """A collection of events in chronological-order."""
        return self._history

    def append(self, event: LifeEvent) -> None:
        """Record a new life event.

        Parameters
        ----------
        event
            The event to record.
        """
        self._history.append(event)

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        history = [f"{type(e).__name__}({e.event_id})" for e in self._history]
        return f"{self.__class__.__name__}({history})"


class GlobalEventHistory:
    """Stores a record of all past life events."""

    __slots__ = ("history",)

    history: list[LifeEvent]
    """All recorded life events mapped to their event ID."""

    def __init__(self) -> None:
        self.history = []

    def append(self, event: LifeEvent) -> None:
        """Record a new life event.

        Parameters
        ----------
        event
            The event to record.
        """
        self.history.append(event)
