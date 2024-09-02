"""Event bus for events in the game.

"""

from __future__ import annotations

from typing import Callable, Generic, TypeVar

_ET = TypeVar("_ET")


class EventEmitter(Generic[_ET]):
    """Emits events with or without data"""

    __slots__ = ("_listeners",)

    _listeners: list[Callable[[_ET], None]]
    """Event listeners"""

    def __init__(self) -> None:
        super().__init__()
        self._listeners = []

    def add_listener(self, listener: Callable[[_ET], None]) -> None:
        """Add a new listener."""
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[_ET], None]) -> bool:
        """Remove a listener."""
        try:
            self._listeners.remove(listener)
            return True
        except ValueError:
            return False


simulation_started = EventEmitter[None]()

simulation_paused = EventEmitter[None]()
