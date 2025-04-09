"""Minerva Game Actions and System(s).

This implementation mixes the old way events were handled in Neighborly
with an ActionSystem implementation from the following YouTube video
by The Code Otter: https://www.youtube.com/watch?v=ls5zeiDCfvI

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Literal, Optional, Type, TypeVar, cast

from minerva.ecs import World


class GameAction(ABC):
    """An operation performed during the simulation.

    This class is not to be confused with AIAction. GameActions encapsulate data used
    to perform an action that changes the state if the game. They are more generic than
    AI actions, often serving as utility functions. Thus AIActions instantiate
    GameActions to perform operations.
    """

    __slots__ = ("world", "pre_reactions", "reactions", "post_reactions")

    world: World
    pre_reactions: list[GameAction]
    reactions: list[GameAction]
    post_reactions: list[GameAction]

    def __init__(self, world: World) -> None:
        super().__init__()
        self.world = world
        self.pre_reactions = []
        self.reactions = []
        self.post_reactions = []

    def add_reaction(self, action: GameAction) -> None:
        """Add a reaction to the action."""
        self.world.get_resource(ActionSystem).add_reaction(action)

    @abstractmethod
    def on_execute(self) -> None:
        """Executes logic of this action."""
        raise NotImplementedError()

    def execute(self) -> None:
        """Execute the action."""
        self.world.get_resource(ActionSystem).perform(self)


_T_co = TypeVar("_T_co", covariant=True, bound=GameAction)


class ActionSystem:
    """Data used by the action system."""

    __slots__ = (
        "reactions",
        "pre_listeners",
        "post_listeners",
        "performers",
    )

    reactions: Optional[list[GameAction]]
    pre_listeners: dict[Type[GameAction], list[Callable[[GameAction], None]]]
    post_listeners: dict[Type[GameAction], list[Callable[[GameAction], None]]]
    performers: dict[Type[GameAction], Callable[[GameAction], None]]

    def __init__(self) -> None:
        self.reactions = None
        self.pre_listeners = {}
        self.post_listeners = {}
        self.performers = {}

    def perform(self, game_action: GameAction) -> None:
        """Perform the provided action."""
        self.reactions = game_action.pre_reactions
        self._perform_subscribers(game_action, self.pre_listeners)
        self._perform_reactions()

        self.reactions = game_action.reactions
        game_action.on_execute()
        self._perform_reactions()

        self.reactions = game_action.post_reactions
        self._perform_subscribers(game_action, self.post_listeners)
        self._perform_reactions()

    def add_reaction(self, game_action: GameAction) -> None:
        """Add the given action as a reaction."""
        if self.reactions is not None:
            self.reactions.append(game_action)

    def _perform_reactions(self) -> None:
        """Perform reaction list."""
        if self.reactions is not None:
            for action in self.reactions:
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

        try:
            listener_collection[action_type].remove(
                cast(Callable[[GameAction], None], listener)
            )

        except ValueError:
            pass

        finally:
            if len(listener_collection[action_type]) == 0:
                del listener_collection[action_type]
