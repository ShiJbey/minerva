"""Helper classes and functions for character behaviors."""

from typing import Any

import numpy as np
from ordered_set import OrderedSet

from minerva.actions.base_types import (
    AIContext,
    AIPrecondition,
    AISensor,
    AIUtilityConsideration,
)
from minerva.characters.components import Character, Family, HeadOfFamily
from minerva.characters.motive_helpers import MotiveVector, get_character_motives
from minerva.characters.war_data import Alliance
from minerva.ecs import GameObject
from minerva.world_map.components import InRevolt, Settlement


class BehaviorMotiveConsideration(AIUtilityConsideration):
    """A consideration of the behavior's motives against a character's"""

    def evaluate(self, context: AIContext) -> float:
        behavior_motives: MotiveVector = context.blackboard["behavior_motives"]
        character_motives = get_character_motives(context.character)

        utility_vect = behavior_motives.vect * (character_motives.vect * 2)
        utility_score = float(np.sum(utility_vect) / 9)  # total of 9 motives

        return utility_score


class BehaviorCostPrecondition(AIPrecondition):
    """Check that character has enough influence points."""

    def evaluate(self, context: AIContext) -> bool:
        character_component = context.character.get_component(Character)
        behavior_cost: int = context.blackboard["behavior_cost"]
        return character_component.influence_points >= behavior_cost


class IsFamilyHeadPrecondition(AIPrecondition):
    """Check that the character is head of a family."""

    def evaluate(self, context: AIContext) -> bool:
        return context.character.has_component(HeadOfFamily)


class HasTerritoriesInRevolt(AIPrecondition):
    """Checks if the character has any territories in revolt."""

    def evaluate(self, context: AIContext) -> bool:
        territories: list[GameObject] = context.blackboard.get(
            "territories_in_revolt", []
        )
        return bool(territories)


class TerritoriesInRevoltSensor(AISensor):
    """Get all settlements in revolt and write it to the blackboard."""

    def evaluate(self, context: AIContext) -> Any:
        # Check if the character is a family head
        territories_in_revolt: list[GameObject] = []

        if family_head_component := context.character.try_component(HeadOfFamily):
            family_component = family_head_component.family.get_component(Family)

            for territory in family_component.territories:
                if territory.has_component(InRevolt):
                    territories_in_revolt.append(territory)

        return territories_in_revolt


class UnexpandedTerritoriesSensor(AISensor):
    """Get all territories without political foothold that border territories."""

    def evaluate(self, context: AIContext) -> Any:
        # Check if the character is a family head
        unexpanded_territories: OrderedSet[GameObject] = OrderedSet([])

        if family_head_component := context.character.try_component(HeadOfFamily):
            family_component = family_head_component.family.get_component(Family)
            for territory in family_component.territories:
                settlement_component = territory.get_component(Settlement)
                for neighboring_territory in settlement_component.neighbors:
                    if neighboring_territory not in family_component.territories:
                        unexpanded_territories.add(neighboring_territory)

        return list(unexpanded_territories)


class UnControlledTerritoriesSensor(AISensor):
    """Get all territories the family has that don't have a controlling family."""

    def evaluate(self, context: AIContext) -> Any:
        # Check if the character is a family head
        uncontrolled_territories: OrderedSet[GameObject] = OrderedSet([])

        if family_head_component := context.character.try_component(HeadOfFamily):
            family_component = family_head_component.family.get_component(Family)

            for territory in family_component.territories:
                settlement_component = territory.get_component(Settlement)
                if settlement_component.controlling_family is None:
                    uncontrolled_territories.add(territory)

        return list(uncontrolled_territories)


class TerritoriesControlledByOpps(AISensor):
    """Get all territories a family is within that are controlled by other families.

    This sensor excludes territories controlled by allies
    """

    def evaluate(self, context: AIContext) -> Any:
        # Check if the character is a family head
        enemy_territories: OrderedSet[GameObject] = OrderedSet([])

        if family_head_component := context.character.try_component(HeadOfFamily):
            family_component = family_head_component.family.get_component(Family)

            allies: set[GameObject] = set()
            if family_component.alliance:
                alliance_component = family_component.alliance.get_component(Alliance)
                for member in alliance_component.member_families:
                    allies.add(member)

            for territory in family_component.territories:
                settlement_component = territory.get_component(Settlement)
                if (
                    settlement_component.controlling_family is not None
                    and settlement_component.controlling_family not in allies
                ):
                    enemy_territories.add(territory)

        return list(enemy_territories)
