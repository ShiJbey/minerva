"""Concrete Action implementations."""

from __future__ import annotations

from minerva.actions.base_types import Action
from minerva.characters.helpers import remove_character_from_play, set_character_alive
from minerva.ecs import GameObject
from minerva.life_events.aging import CharacterDeathEvent


class GetMarried(Action["GetMarried"]):
    """Two characters get married."""

    __slot__ = ("initiator", "partner")

    initiator: GameObject
    partner: GameObject

    def __init__(self, initiator: GameObject, partner: GameObject) -> None:
        super().__init__(world=initiator.world)
        self.initiator = initiator
        self.partner = partner

    def execute(self) -> bool:
        return True


@GetMarried.consideration
def marriage_empty_consideration(action: Action[GetMarried]) -> float:
    """Empty marriage consideration"""
    assert action.data.initiator
    return 1.0


class Die(Action["Die"]):
    """A character dies."""

    __slots__ = ("character",)

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(world=character.world)
        self.character = character

    def execute(self) -> bool:
        """Have a character die."""
        set_character_alive(self.character, False)
        self.character.deactivate()

        CharacterDeathEvent(self.character).dispatch()

        remove_character_from_play(self.character)

        return True
