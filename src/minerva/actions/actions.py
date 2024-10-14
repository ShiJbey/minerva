"""Concrete Action implementations."""

from __future__ import annotations

from minerva.actions.base_types import (
    AIAction,
    AIActionLibrary,
    AIActionType,
    AIContext,
)
from minerva.characters.helpers import remove_character_from_play, set_character_alive
from minerva.ecs import GameObject
from minerva.life_events.aging import CharacterDeathEvent


class GetMarriedActionType(AIActionType):
    """Two characters get married."""

    def execute(self, context: AIContext) -> bool:
        # Do nothing
        return True


class GetMarriedAction(AIAction):
    """An instance of a get married action."""

    def __init__(self, context: AIContext, partner: GameObject) -> None:
        action_library = context.world.resources.get_resource(AIActionLibrary)
        super().__init__(
            context, action_library.get_action_with_name(GetMarriedActionType.__name__)
        )
        self.context = context.copy()
        self.context.blackboard["partner"] = partner


class DieActionType(AIActionType):
    """A character dies."""

    def execute(self, context: AIContext) -> bool:
        """Have a character die."""
        character = context.character

        set_character_alive(character, False)
        character.deactivate()

        CharacterDeathEvent(character).dispatch()

        remove_character_from_play(character)

        return True


class DieAction(AIAction):
    """Instance of an action where a character dies."""

    def __init__(self, context: AIContext) -> None:
        action_library = context.world.resources.get_resource(AIActionLibrary)
        super().__init__(
            context, action_library.get_action_with_name(DieActionType.__name__)
        )
        self.context = context.copy()
