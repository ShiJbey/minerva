"""Life Event System.

Life events are the building block of story generation. We set them apart from the
ECS-related events by requiring that each have a timestamp of the in-simulation date
they were emitted.

"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from itertools import count
from typing import Any, ClassVar

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

    @abstractmethod
    def get_description(self) -> str:
        """Get a text description of the life event."""
        raise NotImplementedError()

    def dispatch(self, skip_logging: bool = False) -> None:
        """Dispatches the event to the proper listeners."""

        if not skip_logging:
            _logger.info("[%s]: %s", str(self.timestamp), self.get_description())

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


class LifeEventHistory(Component):
    """Stores a record of all past life events for a specific GameObject."""

    __slots__ = ("history",)

    history: list[LifeEvent]
    """A list of events in chronological-order."""

    def __init__(self) -> None:
        super().__init__()
        self.history = []

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.history})"
