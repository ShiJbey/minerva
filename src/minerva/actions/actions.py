"""Concrete Action implementations."""

from __future__ import annotations

from minerva.actions.base_types import Action
from minerva.characters.components import Character, Household
from minerva.characters.helpers import (
    set_character_alive,
    set_character_death_date,
    set_character_household,
    set_household_head,
    set_relation_spouse,
)
from minerva.datetime import SimDate
from minerva.ecs import GameObject
from minerva.life_events.aging import CharacterDeathEvent
from minerva.relationships.helpers import deactivate_relationships


class Die(Action):
    """A character dies."""

    __action_id__ = "die"

    __slots__ = ("character",)

    character: GameObject

    def __init__(self, character: GameObject, is_silent: bool = False) -> None:
        super().__init__(character.world, is_silent=is_silent, performer=character)
        self.character = character

    def execute(self) -> bool:
        """Have a character die."""
        current_date = self.world.resources.get_resource(SimDate).copy()
        set_character_alive(self.character, False)
        self.character.deactivate()

        character_component = self.character.get_component(Character)

        if character_component.household is not None:
            former_household = character_component.household
            household_component = former_household.get_component(Household)
            if household_component.head == self.character:
                set_household_head(former_household, None)

            set_character_household(self.character, None)

        set_character_death_date(self.character, current_date)

        set_relation_spouse(self.character, None)

        # remove_all_frequented_locations(self.character)

        # add_trait(self.character, "deceased")

        deactivate_relationships(self.character)

        CharacterDeathEvent(self.character).dispatch()

        # character_relations = self.character.get_component(KeyRelations)

        # # Adjust relationships
        # partner = character_relations.partner
        # if partner:
        #     partner_relations = partner.get_component(KeyRelations)

        #     remove_trait(get_relationship(partner, self.character), "dating")
        #     remove_trait(get_relationship(self.character, partner), "dating")
        #     partner_relations.partner = None
        #     character_relations.partner = None

        #     add_trait(get_relationship(partner, self.character), "ex_partner")
        #     add_trait(get_relationship(self.character, partner), "ex_partner")

        # partner = character_relations.spouse
        # if partner:
        #     partner_relations = partner.get_component(KeyRelations)

        #     remove_trait(get_relationship(self.character, partner), "spouse")
        #     remove_trait(get_relationship(partner, self.character), "spouse")
        #     partner_relations.spouse = None
        #     character_relations.spouse = None

        #     add_trait(get_relationship(partner, self.character), "ex_spouse")
        #     add_trait(get_relationship(self.character, partner), "ex_spouse")

        #     add_trait(get_relationship(partner, self.character), "widow")

        return True
