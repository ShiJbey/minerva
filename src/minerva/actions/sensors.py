"""AI Brain Sensors Classes.

"""

from ordered_set import OrderedSet

from minerva.actions.base_types import AISensor, AIContext
from minerva.characters.components import HeadOfFamily, Family
from minerva.characters.war_data import Alliance
from minerva.ecs import GameObject
from minerva.world_map.components import InRevolt, Territory


class TerritoriesInRevoltSensor(AISensor):
    """Get all territories in revolt and write it to the blackboard."""

    def evaluate(self, context: AIContext) -> None:
        # Check if the character is a family head
        territories_in_revolt: list[GameObject] = []

        if family_head_component := context.character.try_component(HeadOfFamily):
            family_component = family_head_component.family.get_component(Family)

            for territory in family_component.territories:
                if territory.has_component(InRevolt):
                    territories_in_revolt.append(territory)

        context["territories_in_revolt"] = territories_in_revolt


class UnexpandedTerritoriesSensor(AISensor):
    """Get all territories without political foothold that border territories."""

    def evaluate(self, context: AIContext) -> None:
        # Check if the character is a family head
        unexpanded_territories: OrderedSet[GameObject] = OrderedSet([])

        if family_head_component := context.character.try_component(HeadOfFamily):
            family_component = family_head_component.family.get_component(Family)
            for territory in family_component.territories:
                territory_component = territory.get_component(Territory)
                for neighboring_territory in territory_component.neighbors:
                    if neighboring_territory not in family_component.territories:
                        unexpanded_territories.add(neighboring_territory)

        context["unexpanded_territories"] = list(unexpanded_territories)


class UnControlledTerritoriesSensor(AISensor):
    """Get all territories the family has that don't have a controlling family."""

    def evaluate(self, context: AIContext) -> None:
        # Check if the character is a family head
        uncontrolled_territories: OrderedSet[GameObject] = OrderedSet([])

        if family_head_component := context.character.try_component(HeadOfFamily):
            family_component = family_head_component.family.get_component(Family)

            for territory in family_component.territories:
                territory_component = territory.get_component(Territory)
                if territory_component.controlling_family is None:
                    uncontrolled_territories.add(territory)

        context["uncontrolled_territories"] = list(uncontrolled_territories)


class TerritoriesControlledByOpps(AISensor):
    """Get all territories a family is within that are controlled by other families.

    This sensor excludes territories controlled by allies
    """

    def evaluate(self, context: AIContext) -> None:
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
                territory_component = territory.get_component(Territory)
                if (
                    territory_component.controlling_family is not None
                    and territory_component.controlling_family not in allies
                ):
                    enemy_territories.add(territory)

        context["enemy_territories"] = list(enemy_territories)
