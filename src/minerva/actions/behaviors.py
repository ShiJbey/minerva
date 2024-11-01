"""Minerva concrete behavior classes."""

from __future__ import annotations

from ordered_set import OrderedSet

from minerva.actions.actions import (
    DisbandAllianceAction,
    ExpandIntoTerritoryAction,
    ExtortLocalFamiliesAction,
    ExtortTerritoryOwnersAction,
    GiveBackToTerritoryAction,
    GrowPoliticalInfluenceAction,
    IdleAction,
    JoinAllianceSchemeAction,
    JoinCoupSchemeAction,
    JoinExistingAllianceAction,
    QuellRevoltAction,
    SeizeTerritoryAction,
    SendAidAction,
    SendGiftAction,
    StartAllianceSchemeAction,
    StartCoupSchemeAction,
    StartWarSchemeAction,
    TaxTerritoryAction,
)
from minerva.actions.base_types import (
    AIAction,
    AIBehavior,
    AIBrain,
    Scheme,
    SchemeManager,
)
from minerva.actions.scheme_types import AllianceScheme, CoupScheme
from minerva.characters.components import Family, HeadOfFamily
from minerva.characters.succession_helpers import get_current_ruler
from minerva.characters.war_data import Alliance
from minerva.ecs import Active, GameObject
from minerva.world_map.components import InRevolt, Territory


class IdleBehavior(AIBehavior):
    """A behavior that does nothing."""

    def get_actions(self, character: GameObject) -> list[AIAction]:
        return [
            IdleAction(character),
        ]


class GiveToSmallFolkBehavior(AIBehavior):
    """A family head  will try to increase their political influence in a territory."""

    def get_actions(self, character: GameObject) -> list[AIAction]:
        # Choose the territory with the lowest political influence
        # and spend influence points to increase political power
        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        actions: list[AIAction] = []

        for territory in family_component.territories:
            territory_component = territory.get_component(Territory)
            if territory_component.controlling_family == family_component.gameobject:
                action = GiveBackToTerritoryAction(
                    performer=character,
                    family=family_component.gameobject,
                    territory=territory,
                )
                actions.append(action)

        return actions


class GrowPoliticalInfluenceBehavior(AIBehavior):
    """A family head  will try to increase their political influence in a territory."""

    def get_actions(self, character: GameObject) -> list[AIAction]:
        # Choose the territory with the lowest political influence
        # and spend influence points to increase political power
        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        actions: list[AIAction] = []

        for territory in family_component.territories:
            action = GrowPoliticalInfluenceAction(
                performer=character,
                family=family_component.gameobject,
                territory=territory,
            )
            actions.append(action)

        return actions


class SendGiftBehavior(AIBehavior):
    """Family heads will send gifts to each other to increase opinion scores."""

    def get_actions(self, character: GameObject) -> list[AIAction]:
        # Get all the families within the same territories
        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        recipients: OrderedSet[GameObject] = OrderedSet([])
        actions: list[AIAction] = []

        for territory in family_component.territories:
            territory_component = territory.get_component(Territory)
            for other_family in territory_component.families:
                # Skip your own family
                if other_family == family_component.gameobject:
                    continue

                other_family_component = other_family.get_component(Family)

                if (
                    other_family_component.head
                    and other_family_component.head not in recipients
                ):
                    recipients.add(other_family_component.head)
                    actions.append(
                        SendGiftAction(character, other_family_component.head)
                    )

        return actions


class SendAidBehavior(AIBehavior):
    """Character will try to increase favor with a family dealing with a revolt."""

    def get_actions(self, character: GameObject) -> list[AIAction]:

        # Get all territories in revolt and the family heads in charge
        # of those territories
        recipients: OrderedSet[GameObject] = OrderedSet([])
        actions: list[AIAction] = []

        for _, (territory, _, _) in character.world.get_components(
            (Territory, InRevolt, Active)
        ):
            if territory.controlling_family:
                family_component = territory.controlling_family.get_component(Family)
                if family_component.head and family_component.head != character:
                    recipients.add(family_component.head)
                    actions.append(SendAidAction(character, family_component.head))

        return actions


class ExtortTerritoryOwners(AIBehavior):
    """The ruler will take influence points from the land-owning families."""

    def get_actions(self, character: GameObject) -> list[AIAction]:
        return [ExtortTerritoryOwnersAction(character)]


class ExtortLocalFamiliesBehavior(AIBehavior):
    """A family head will extort families that live in their controlled territories."""

    def get_actions(self, character: GameObject) -> list[AIAction]:

        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        controlled_territory_count = 0
        for territory in family_component.territories:
            territory_component = territory.get_component(Territory)
            if territory_component.controlling_family == family_component.gameobject:
                controlled_territory_count += 1

        if controlled_territory_count > 0:
            return [ExtortLocalFamiliesAction(character)]
        else:
            return []


class QuellRevolt(AIBehavior):
    """The head of the family controlling a territory will try to quell a revolt."""

    def get_actions(self, character: GameObject) -> list[AIAction]:
        # This behavior requires at least on territory to be in revolt. This
        # information is picked up by the
        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        actions: list[AIAction] = []

        for territory in family_component.territories:
            territory_component = territory.get_component(Territory)

            if territory_component.controlling_family != family_component.gameobject:
                continue

            if territory.has_component(InRevolt):
                actions.append(
                    QuellRevoltAction(performer=character, territory=territory)
                )

        return actions


class StartAllianceSchemeBehavior(AIBehavior):
    """A family head will try to start a new alliance."""

    def get_actions(self, character: GameObject) -> list[AIAction]:
        # Character will start a new scheme to form an alliance. Other family heads can
        # choose to join before the alliance is officially formed.
        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        if family_component.alliance:
            return []

        return [StartAllianceSchemeAction(character)]


class JoinAllianceSchemeBehavior(AIBehavior):
    """A family head will have their family join an existing alliance."""

    def get_actions(self, character: GameObject) -> list[AIAction]:
        # The family head will try to join an alliance scheme.

        world = character.world
        actions: list[AIAction] = []

        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        scheme_manager = character.get_component(SchemeManager)
        for scheme in scheme_manager.schemes:
            scheme_type = scheme.get_component(Scheme).get_type()
            if scheme_type == "alliance" or scheme_type == "war":
                return []

        if family_component.alliance:
            return []

        for _, (scheme, _, _) in world.get_components((Scheme, AllianceScheme, Active)):
            if not scheme.is_valid:
                continue

            if scheme.initiator == character or character in scheme.members:
                continue

            actions.append(JoinAllianceSchemeAction(character, scheme.gameobject))

        return actions


class JoinExistingAlliance(AIBehavior):
    """A family head will have their family join an existing alliance."""

    def get_actions(self, character: GameObject) -> list[AIAction]:
        # The family head will try to join an existing alliance.

        world = character.world
        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        if family_component.alliance:
            return []

        actions: list[AIAction] = []

        for _, (alliance, _) in world.get_components((Alliance, Active)):
            actions.append(JoinExistingAllianceAction(character, alliance.gameobject))

        return actions


class DisbandAlliance(AIBehavior):
    """A family head will try to disband their current alliance."""

    def get_actions(self, character: GameObject) -> list[AIAction]:
        # The family head has the option to leave the current alliance, causing the
        # entire alliance to disband

        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        if family_component.alliance is None:
            return []

        alliance_component = family_component.alliance.get_component(Alliance)
        if alliance_component.founder_family == family_component.gameobject:
            return []

        else:
            return [DisbandAllianceAction(character, family_component.alliance)]


class DeclareWarBehavior(AIBehavior):
    """A family head will declare war on another."""

    def get_actions(self, character: GameObject) -> list[AIAction]:
        # The character will try to fight another family in a territory for control
        # over that territory. They will not declare war on a territory held by someone
        # in their alliance.
        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        actions: list[AIAction] = []

        for territory in family_component.territories:
            territory_component = territory.get_component(Territory)

            if (
                territory_component.controlling_family is None
                or territory_component.controlling_family == family_component.gameobject
            ):
                continue

            enemy_family = territory_component.controlling_family

            enemy_family_component = enemy_family.get_component(Family)

            if enemy_family_component.head is None:
                continue
                # raise RuntimeError(
                #     f"{enemy_family_component.gameobject.name_with_uid} is missing a head."
                # )

            action = StartWarSchemeAction(
                performer=character,
                target=enemy_family_component.head,
                territory=territory,
            )

            actions.append(action)

        return actions


class TaxTerritory(AIBehavior):
    """A family head will tax their controlling territory for influence points."""

    def get_actions(self, character: GameObject) -> list[AIAction]:
        # Choose the territory with the lowest political influence
        # and spend influence points to increase political power
        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        actions: list[AIAction] = []
        for territory in family_component.territories:

            territory_component = territory.get_component(Territory)

            if territory_component.controlling_family != family_component.gameobject:
                continue

            action = TaxTerritoryAction(character, territory)
            actions.append(action)

        return actions


class PlanCoupBehavior(AIBehavior):
    """A family head will attempt to overthrow the royal family."""

    def get_actions(self, character: GameObject) -> list[AIAction]:
        # The family head will start a scheme to overthrow the royal family and other
        # characters can join. This is effectively the same as declaring war, but
        # alliances don't join and if discovered, all family heads involved are
        # executed and their families lose control of territory

        current_ruler = get_current_ruler(character.world)

        if current_ruler is None:
            return []

        return [
            StartCoupSchemeAction(character, current_ruler),
        ]


class JoinCoupSchemeBehavior(AIBehavior):
    """A family head joins someones coup scheme."""

    def get_actions(self, character: GameObject) -> list[AIAction]:
        world = character.world

        # Find all active alliances and join one based on the opinion of the character
        # toward the person who is the head of the founding family.
        actions: list[AIAction] = []

        for _, (scheme, _, _) in world.get_components((Scheme, CoupScheme, Active)):
            if not scheme.is_valid:
                continue

            if scheme.initiator == character or character in scheme.members:
                continue

            actions.append(JoinCoupSchemeAction(character, scheme.gameobject))

        return actions


class ExpandPoliticalDomain(AIBehavior):
    """A family head expands the family's political influence to a new territory."""

    def get_actions(self, character: GameObject) -> list[AIAction]:
        # Loop through all territories that neighbor existing political territories
        # Consider all those where the family does not have an existing political
        # foothold
        character_brain = character.get_component(AIBrain)
        actions: list[AIAction] = []
        unexpanded_territories: list[GameObject] = character_brain.context[
            "unexpanded_territories"
        ]
        for territory in unexpanded_territories:
            action = ExpandIntoTerritoryAction(character, territory)
            actions.append(action)

        return actions


class SeizeControlOfTerritory(AIBehavior):
    """A family head takes control of an unclaimed territory."""

    def get_actions(self, character: GameObject) -> list[AIAction]:
        # Loop through all the territories where this character has political influence
        # For all those that that are unclaimed and the territory to a list of
        # potential territories to expand into.

        actions: list[AIAction] = []

        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        for territory in family_component.territories:
            territory_component = territory.get_component(Territory)
            if territory_component.controlling_family is None:
                action = SeizeTerritoryAction(character, territory)
                actions.append(action)

        return actions
