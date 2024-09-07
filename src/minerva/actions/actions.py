"""Concrete Action implementations."""

from __future__ import annotations

import random
from typing import Optional

from minerva.actions.base_types import Action
from minerva.characters.components import (
    Character,
    Emperor,
    HeadOfClan,
    HeadOfFamily,
    Household,
)
from minerva.characters.helpers import (
    set_character_alive,
    set_character_death_date,
    set_character_household,
    set_clan_head,
    set_family_head,
    set_household_head,
    set_relation_spouse,
)
from minerva.characters.succession_helpers import SuccessionChartCache
from minerva.datetime import SimDate
from minerva.ecs import GameObject
from minerva.life_events.aging import CharacterDeathEvent
from minerva.life_events.succession import (
    BecameClanHeadEvent,
    BecameEmperorEvent,
    BecameFamilyHeadEvent,
)
from minerva.relationships.helpers import deactivate_relationships


class Die(Action["Die"]):
    """A character dies."""

    __slots__ = ("character",)

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(
            world=character.world, considerations=[self._empty_consideration]
        )
        self.character = character

    @staticmethod
    def _empty_consideration(action: Action[Die]) -> float:
        assert action.data.character
        return 1.0

    def execute(self) -> bool:
        """Have a character die."""
        depth_chart_cache = self.data.world.resources.get_resource(SuccessionChartCache)
        current_date = self.data.world.resources.get_resource(SimDate).copy()
        rng = self.data.world.resources.get_resource(random.Random)

        set_character_alive(self.character, False)
        self.character.deactivate()

        CharacterDeathEvent(self.character).dispatch()

        heir: Optional[GameObject] = None

        depth_chart = depth_chart_cache.get_chart_for(self.character, recalculate=True)

        # Get top 3 the eligible heirs
        eligible_heirs = [
            entry.character_id for entry in depth_chart if entry.is_eligible
        ][:3]

        if eligible_heirs:
            # Add selection weights to heirs
            # The second bracket slices the proceeding list to the number of
            # eligible heirs
            heir_weights = [0.8, 0.15, 0.5][: len(eligible_heirs)]

            # Select a random heir from the top 3 with most emphasis on the first
            heir_id = rng.choices(eligible_heirs, heir_weights, k=1)[0]

            heir = self.world.gameobjects.get_gameobject(heir_id)

        if family_head_component := self.character.try_component(HeadOfFamily):
            # Perform succession
            family = family_head_component.family
            set_family_head(family, heir)
            if heir is not None:
                BecameFamilyHeadEvent(heir, family).dispatch()

        if clan_head_component := self.character.try_component(HeadOfClan):
            # Perform succession
            clan = clan_head_component.clan
            set_clan_head(clan, heir)
            if heir is not None:
                BecameClanHeadEvent(heir, clan).dispatch()

        if _ := self.character.try_component(Emperor):
            # Perform succession
            self.character.remove_component(Emperor)
            if heir is not None:
                heir.add_component(Emperor())
                BecameEmperorEvent(heir).dispatch()

        character_component = self.character.get_component(Character)

        if character_component.household is not None:
            former_household = character_component.household
            household_component = former_household.get_component(Household)
            if household_component.head == self.character:
                set_household_head(former_household, None)

        set_character_household(self.character, None)

        set_character_death_date(self.character, current_date)

        if character_component.spouse is not None:
            set_relation_spouse(character_component.spouse, None)
            set_relation_spouse(self.character, None)

        deactivate_relationships(self.character)

        return True
