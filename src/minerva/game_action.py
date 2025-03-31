"""Minerva Game Actions and System(s).

This implementation mixes the old way events were handled in Neighborly
with an ActionSystem implementation from the following YouTube video
by The Code Otter: https://www.youtube.com/watch?v=ls5zeiDCfvI

"""

from __future__ import annotations

from abc import ABC
from typing import Callable, Literal, Optional, Type, TypeVar, cast


class GameAction(ABC):
    """An operation performed during the simulation.

    This class is not to be confused with AIAction. GameActions encapsulate data used
    to perform an action that changes the state if the game. They are more generic than
    AI actions, often serving as utility functions. Thus AIActions instantiate
    GameActions to perform operations.
    """

    __slots__ = ("pre_actions", "actions", "post_actions")

    pre_actions: list[GameAction]
    actions: list[GameAction]
    post_actions: list[GameAction]

    def __init__(self) -> None:
        super().__init__()
        self.pre_actions = []
        self.actions = []
        self.post_actions = []


_T_co = TypeVar("_T_co", covariant=True, bound=GameAction)


class ActionSystem:
    """Data used by the action system."""

    __slots__ = (
        "listeners",
        "pre_listeners",
        "post_listeners",
        "performers",
    )

    listeners: Optional[list[GameAction]]
    pre_listeners: dict[Type[GameAction], list[Callable[[GameAction], None]]]
    post_listeners: dict[Type[GameAction], list[Callable[[GameAction], None]]]
    performers: dict[Type[GameAction], Callable[[GameAction], None]]

    def __init__(self) -> None:
        self.listeners = None
        self.pre_listeners = {}
        self.post_listeners = {}
        self.performers = {}

    def perform(self, game_action: GameAction) -> None:
        """Perform the provided action."""
        self.listeners = game_action.pre_actions
        self._perform_subscribers(game_action, self.pre_listeners)
        self._perform_reactions()

        self.listeners = game_action.actions
        self._perform_performer(game_action)
        self._perform_reactions()

        self.listeners = game_action.post_actions
        self._perform_subscribers(game_action, self.post_listeners)
        self._perform_reactions()

    def add_reaction(self, game_action: GameAction) -> None:
        """Add the given action as a reaction."""
        if self.listeners is not None:
            self.listeners.append(game_action)

    def _perform_reactions(self) -> None:
        """Perform reaction list."""
        if self.listeners is not None:
            for action in self.listeners:
                self.perform(action)

    def _perform_subscribers(
        self,
        game_action: GameAction,
        subscribers: dict[Type[GameAction], list[Callable[[GameAction], None]]],
    ) -> None:
        """Call the subscribers on the given action."""
        if type(game_action) in subscribers:
            for listener in subscribers[type(game_action)]:
                listener(game_action)

    def _perform_performer(self, game_action: GameAction) -> None:
        """Perform the action."""
        if type(game_action) in self.performers:
            self.performers[type(game_action)](game_action)

    def attach_performer(
        self, action_type: Type[_T_co], performer: Callable[[_T_co], None]
    ) -> None:
        """Attach a performer function for the given game action type."""
        self.performers[action_type] = cast(Callable[[GameAction], None], performer)

    def detach_performer(self, action_type: Type[_T_co]) -> None:
        """Detach a performer function for the given game action type."""
        del self.performers[action_type]

    def add_listener(
        self,
        action_type: Type[_T_co],
        listener: Callable[[_T_co], None],
        timing: Literal["pre", "post"],
    ) -> None:
        """Add a listener for an action type."""

        listener_collection = (
            self.pre_listeners if timing == "pre" else self.post_listeners
        )

        if action_type not in listener_collection:
            listener_collection[action_type] = []

        listener_collection[action_type].append(
            cast(Callable[[GameAction], None], listener)
        )

    def remove_listener(
        self,
        action_type: Type[_T_co],
        listener: Callable[[_T_co], None],
        timing: Literal["pre", "post"],
    ) -> None:
        """Remove a listener for an action type."""

        listener_collection = (
            self.pre_listeners if timing == "pre" else self.post_listeners
        )

        if action_type not in listener_collection:
            return

        listener_collection[action_type].append(
            cast(Callable[[GameAction], None], listener)
        )

        if len(listener_collection[action_type]) == 0:
            del listener_collection[action_type]
