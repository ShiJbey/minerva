"""Minerva concrete behavior classes."""

from __future__ import annotations

from ordered_set import OrderedSet

from minerva.actions.actions import (
    ClaimThroneAction,
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
    TryCheatOnSpouseAction,
)
from minerva.actions.base_types import (
    AIAction,
    AIBehavior,
    AIBrain,
    AIPrecondition,
    Scheme,
    SchemeManager,
)
from minerva.actions.scheme_types import AllianceScheme, CoupScheme
from minerva.characters.components import (
    Character,
    DynastyTracker,
    Family,
    HeadOfFamily,
    LifeStage,
    Sex,
    SexualOrientation,
)
from minerva.characters.succession_helpers import get_current_ruler
from minerva.characters.war_data import Alliance
from minerva.ecs import Active, Entity
from minerva.relationships.base_types import Attraction
from minerva.relationships.helpers import get_relationship
from minerva.world_map.components import InRevolt, Territory


class IdleBehavior(AIBehavior):
    """A behavior that does nothing."""

    def get_actions(self, character: Entity) -> list[AIAction]:
        return [
            IdleAction(character),
        ]


class GiveToSmallFolkBehavior(AIBehavior):
    """A family head  will try to increase their political influence in a territory."""

    def get_actions(self, character: Entity) -> list[AIAction]:
        # Choose the territory with the lowest political influence
        # and spend influence points to increase political power
        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        actions: list[AIAction] = []

        for territory in family_component.territories_present_in:
            territory_component = territory.get_component(Territory)
            if territory_component.controlling_family == family_component.entity:
                action = GiveBackToTerritoryAction(
                    performer=character,
                    family=family_component.entity,
                    territory=territory,
                )
                actions.append(action)

        return actions


class GrowPoliticalInfluenceBehavior(AIBehavior):
    """A family head  will try to increase their political influence in a territory."""

    def get_actions(self, character: Entity) -> list[AIAction]:
        # Choose the territory with the lowest political influence
        # and spend influence points to increase political power
        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        actions: list[AIAction] = []

        for territory in family_component.territories_present_in:
            action = GrowPoliticalInfluenceAction(
                performer=character,
                family=family_component.entity,
                territory=territory,
            )
            actions.append(action)

        return actions


class SendGiftBehavior(AIBehavior):
    """Family heads will send gifts to each other to increase opinion scores."""

    def get_actions(self, character: Entity) -> list[AIAction]:
        # Get all the families within the same territories
        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        recipients: OrderedSet[Entity] = OrderedSet([])
        actions: list[AIAction] = []

        for territory in family_component.territories_present_in:
            territory_component = territory.get_component(Territory)
            for other_family in territory_component.families:
                # Skip your own family
                if other_family == family_component.entity:
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

    def get_actions(self, character: Entity) -> list[AIAction]:

        # Get all territories in revolt and the family heads in charge
        # of those territories
        recipients: OrderedSet[Entity] = OrderedSet([])
        actions: list[AIAction] = []

        for _, (territory, _, _) in character.world.query_components(
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

    def get_actions(self, character: Entity) -> list[AIAction]:
        return [ExtortTerritoryOwnersAction(character)]


class ExtortLocalFamiliesBehavior(AIBehavior):
    """A family head will extort families that live in their controlled territories."""

    def get_actions(self, character: Entity) -> list[AIAction]:

        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        controlled_territory_count = 0
        for territory in family_component.controlled_territories:
            territory_component = territory.get_component(Territory)
            if territory_component.controlling_family == family_component.entity:
                controlled_territory_count += 1

        if controlled_territory_count > 0:
            return [ExtortLocalFamiliesAction(character)]
        else:
            return []


class QuellRevolt(AIBehavior):
    """The head of the family controlling a territory will try to quell a revolt."""

    def get_actions(self, character: Entity) -> list[AIAction]:
        # This behavior requires at least on territory to be in revolt. This
        # information is picked up by the
        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        actions: list[AIAction] = []

        for territory in family_component.controlled_territories:
            territory_component = territory.get_component(Territory)

            if territory_component.controlling_family != family_component.entity:
                continue

            if territory.has_component(InRevolt):
                actions.append(
                    QuellRevoltAction(performer=character, territory=territory)
                )

        return actions


class StartAllianceSchemeBehavior(AIBehavior):
    """A family head will try to start a new alliance."""

    def get_actions(self, character: Entity) -> list[AIAction]:
        # Character will start a new scheme to form an alliance. Other family heads can
        # choose to join before the alliance is officially formed.
        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        if family_component.alliance:
            return []

        return [StartAllianceSchemeAction(character)]


class JoinAllianceSchemeBehavior(AIBehavior):
    """A family head will have their family join an existing alliance."""

    def get_actions(self, character: Entity) -> list[AIAction]:
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

        for _, (scheme, _, _) in world.query_components(
            (Scheme, AllianceScheme, Active)
        ):
            if not scheme.is_valid:
                continue

            if scheme.initiator == character or character in scheme.members:
                continue

            actions.append(JoinAllianceSchemeAction(character, scheme.entity))

        return actions


class JoinExistingAlliance(AIBehavior):
    """A family head will have their family join an existing alliance."""

    def get_actions(self, character: Entity) -> list[AIAction]:
        # The family head will try to join an existing alliance.

        world = character.world
        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        if family_component.alliance:
            return []

        actions: list[AIAction] = []

        for _, (alliance, _) in world.query_components((Alliance, Active)):
            actions.append(JoinExistingAllianceAction(character, alliance.entity))

        return actions


class DisbandAlliance(AIBehavior):
    """A family head will try to disband their current alliance."""

    def get_actions(self, character: Entity) -> list[AIAction]:
        # The family head has the option to leave the current alliance, causing the
        # entire alliance to disband

        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        if family_component.alliance is None:
            return []

        alliance_component = family_component.alliance.get_component(Alliance)
        if alliance_component.founder_family == family_component.entity:
            return []

        else:
            return [DisbandAllianceAction(character, family_component.alliance)]


class DeclareWarBehavior(AIBehavior):
    """A family head will declare war on another."""

    def get_actions(self, character: Entity) -> list[AIAction]:
        # The character will try to fight another family in a territory for control
        # over that territory. They will not declare war on a territory held by someone
        # in their alliance.
        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        actions: list[AIAction] = []

        for territory in family_component.territories_present_in:
            territory_component = territory.get_component(Territory)

            if (
                territory_component.controlling_family is None
                or territory_component.controlling_family == family_component.entity
            ):
                continue

            enemy_family = territory_component.controlling_family

            enemy_family_component = enemy_family.get_component(Family)

            if enemy_family_component.head is None:
                continue

            action = StartWarSchemeAction(
                performer=character,
                target=enemy_family_component.head,
                territory=territory,
            )

            actions.append(action)

        return actions


class TaxTerritory(AIBehavior):
    """A family head will tax their controlling territory for influence points."""

    def get_actions(self, character: Entity) -> list[AIAction]:
        # Choose the territory with the lowest political influence
        # and spend influence points to increase political power
        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        actions: list[AIAction] = []
        for territory in family_component.controlled_territories:
            action = TaxTerritoryAction(character, territory)
            actions.append(action)

        return actions


class PlanCoupBehavior(AIBehavior):
    """A family head will attempt to overthrow the royal family."""

    def get_actions(self, character: Entity) -> list[AIAction]:
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

    def get_actions(self, character: Entity) -> list[AIAction]:
        world = character.world

        # Find all active alliances and join one based on the opinion of the character
        # toward the person who is the head of the founding family.
        actions: list[AIAction] = []

        for _, (scheme, _, _) in world.query_components((Scheme, CoupScheme, Active)):
            if not scheme.is_valid:
                continue

            if scheme.initiator == character or character in scheme.members:
                continue

            actions.append(JoinCoupSchemeAction(character, scheme.entity))

        return actions


class ExpandPoliticalDomain(AIBehavior):
    """A family head expands the family's political influence to a new territory."""

    def get_actions(self, character: Entity) -> list[AIAction]:
        # Loop through all territories that neighbor existing political territories
        # Consider all those where the family does not have an existing political
        # foothold
        character_brain = character.get_component(AIBrain)
        actions: list[AIAction] = []
        unexpanded_territories: list[Entity] = character_brain.context[
            "unexpanded_territories"
        ]
        for territory in unexpanded_territories:
            action = ExpandIntoTerritoryAction(character, territory)
            actions.append(action)

        return actions


class SeizeControlOfTerritory(AIBehavior):
    """A family head takes control of an unclaimed territory."""

    def get_actions(self, character: Entity) -> list[AIAction]:
        # Loop through all the territories where this character has political influence
        # For all those that that are unclaimed and the territory to a list of
        # potential territories to expand into.

        actions: list[AIAction] = []

        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        for territory in family_component.territories_present_in:
            territory_component = territory.get_component(Territory)
            if territory_component.controlling_family is None:
                action = SeizeTerritoryAction(character, territory)
                actions.append(action)

        return actions


class CheatOnSpouseBehavior(AIBehavior):
    """."""

    def get_actions(self, character: Entity) -> list[AIAction]:
        # Loop through the people that this character is attracted to and are adults
        world = character.world

        character_component = character.get_component(Character)
        character_spouse = character_component.spouse

        if character_component.family is None:
            return []

        character_family = character_component.family.get_component(Family)
        family_home_base = character_family.home_base

        if family_home_base is None:
            return []

        if character_spouse is None:
            return []

        if (
            character_component.life_stage < LifeStage.YOUNG_ADULT
            or character_component.life_stage == LifeStage.SENIOR
        ):
            return []

        eligible_accomplices: list[Character] = []

        if (
            character_component.sexual_orientation == SexualOrientation.HETEROSEXUAL
            and character_component.sex == Sex.MALE
        ):
            # Looking for heterosexual, bisexual, or asexual women
            eligible_accomplices = [
                c
                for _, (c, _) in world.query_components((Character, Active))
                if c.spouse != character
                and c.life_stage >= LifeStage.YOUNG_ADULT
                and c.life_stage != LifeStage.SENIOR
                and c.sex == Sex.FEMALE
                and (
                    c.sexual_orientation == SexualOrientation.HETEROSEXUAL
                    or c.sexual_orientation == SexualOrientation.BISEXUAL
                    or c.sexual_orientation == SexualOrientation.ASEXUAL
                )
                and c.entity not in character_component.siblings
                and c.entity != character_component.mother
                and c.entity != character_component.father
                and c.entity != character_component.biological_father
                and c.entity not in character_component.children
                and c.entity not in character_component.grandchildren
                and c.entity not in character_component.grandparents
                and len(c.grandparents.intersection(character_component.grandparents))
                < 2
                and c != character_component
            ]

        if (
            character_component.sexual_orientation == SexualOrientation.HETEROSEXUAL
            and character_component.sex == Sex.FEMALE
        ):
            # Looking for heterosexual, bisexual, or asexual men
            eligible_accomplices = [
                c
                for _, (c, _) in world.query_components((Character, Active))
                if c.spouse != character
                and c.life_stage >= LifeStage.YOUNG_ADULT
                and c.life_stage != LifeStage.SENIOR
                and c.sex == Sex.MALE
                and (
                    c.sexual_orientation == SexualOrientation.HETEROSEXUAL
                    or c.sexual_orientation == SexualOrientation.BISEXUAL
                    or c.sexual_orientation == SexualOrientation.ASEXUAL
                )
                and c.entity not in character_component.siblings
                and c.entity != character_component.mother
                and c.entity != character_component.father
                and c.entity != character_component.biological_father
                and c.entity not in character_component.children
                and c.entity not in character_component.grandchildren
                and c.entity not in character_component.grandparents
                and len(c.grandparents.intersection(character_component.grandparents))
                < 2
                and c != character_component
            ]

        if (
            character_component.sexual_orientation == SexualOrientation.HOMOSEXUAL
            and character_component.sex == Sex.MALE
        ):
            # Looking for homosexual, asexual, or bisexual men
            eligible_accomplices = [
                c
                for _, (c, _) in world.query_components((Character, Active))
                if c.spouse != character_component
                and c.life_stage >= LifeStage.YOUNG_ADULT
                and c.life_stage != LifeStage.SENIOR
                and c.sex == Sex.MALE
                and (
                    c.sexual_orientation == SexualOrientation.HOMOSEXUAL
                    or c.sexual_orientation == SexualOrientation.BISEXUAL
                    or c.sexual_orientation == SexualOrientation.ASEXUAL
                )
                and c.entity not in character_component.siblings
                and c.entity != character_component.mother
                and c.entity != character_component.father
                and c.entity != character_component.biological_father
                and c.entity not in character_component.children
                and c.entity not in character_component.grandchildren
                and c.entity not in character_component.grandparents
                and len(c.grandparents.intersection(character_component.grandparents))
                < 2
                and c != character_component
            ]

        if (
            character_component.sexual_orientation == SexualOrientation.HOMOSEXUAL
            and character_component.sex == Sex.FEMALE
        ):
            # Looking for homosexual or bisexual women
            eligible_accomplices = [
                c
                for _, (c, _) in world.query_components((Character, Active))
                if c.spouse != character_component
                and c.life_stage >= LifeStage.YOUNG_ADULT
                and c.life_stage != LifeStage.SENIOR
                and c.sex == Sex.FEMALE
                and (
                    c.sexual_orientation == SexualOrientation.HOMOSEXUAL
                    or c.sexual_orientation == SexualOrientation.BISEXUAL
                    or c.sexual_orientation == SexualOrientation.ASEXUAL
                )
                and c.entity not in character_component.siblings
                and c.entity != character_component.mother
                and c.entity != character_component.father
                and c.entity != character_component.biological_father
                and c.entity not in character_component.children
                and c.entity not in character_component.grandchildren
                and c.entity not in character_component.grandparents
                and len(c.grandparents.intersection(character_component.grandparents))
                < 2
                and c != character_component
            ]

        if (
            character_component.sexual_orientation == SexualOrientation.BISEXUAL
            and character_component.sex == Sex.MALE
        ):
            # Looking for homosexual or bisexual men
            eligible_accomplices = [
                c
                for _, (c, _) in world.query_components((Character, Active))
                if c.spouse != character
                and c.life_stage >= LifeStage.YOUNG_ADULT
                and c.life_stage != LifeStage.SENIOR
                and c.sex == Sex.MALE
                and (
                    c.sexual_orientation == SexualOrientation.HOMOSEXUAL
                    or c.sexual_orientation == SexualOrientation.BISEXUAL
                )
                and c.entity not in character_component.siblings
                and c.entity != character_component.mother
                and c.entity != character_component.father
                and c.entity != character_component.biological_father
                and c.entity not in character_component.children
                and c != character_component
            ]

        if (
            character_component.sexual_orientation == SexualOrientation.BISEXUAL
            and character_component.sex == Sex.FEMALE
        ):
            # Looking for homosexual or bisexual women
            eligible_accomplices = [
                c
                for _, (c, _) in world.query_components((Character, Active))
                if c.spouse != character
                and c.life_stage >= LifeStage.YOUNG_ADULT
                and c.life_stage != LifeStage.SENIOR
                and c.sex == Sex.FEMALE
                and (
                    c.sexual_orientation == SexualOrientation.HOMOSEXUAL
                    or c.sexual_orientation == SexualOrientation.BISEXUAL
                )
                and c.entity not in character_component.siblings
                and c.entity != character_component.mother
                and c.entity != character_component.father
                and c.entity != character_component.biological_father
                and c.entity not in character_component.children
                and c != character_component
            ]

        if (
            character_component.sexual_orientation == SexualOrientation.ASEXUAL
            and character_component.sex == Sex.FEMALE
        ):
            # Looking for anyone asexual
            eligible_accomplices = [
                c
                for _, (c, _) in world.query_components((Character, Active))
                if c.spouse != character
                and c.life_stage >= LifeStage.YOUNG_ADULT
                and c.life_stage != LifeStage.SENIOR
                and (
                    c.sexual_orientation == SexualOrientation.ASEXUAL
                    or c.sexual_orientation == SexualOrientation.BISEXUAL
                )
                and c.entity not in character_component.siblings
                and c.entity != character_component.mother
                and c.entity != character_component.father
                and c.entity != character_component.biological_father
                and c.entity not in character_component.children
                and c != character_component
            ]

        # Filter for characters that belong to the same home base
        accomplices_in_territory: list[tuple[Character, float]] = []
        for c in eligible_accomplices:
            if c.family is None:
                continue

            c_family_component = c.family.get_component(Family)

            if c_family_component.home_base is None:
                continue

            if c_family_component.home_base == family_home_base:
                attraction = (
                    get_relationship(character, c.entity)
                    .get_component(Attraction)
                    .value
                )
                accomplices_in_territory.append((c, attraction))

        accomplices_in_territory.sort(key=lambda e: e[1])

        if accomplices_in_territory:
            actions: list[AIAction] = []

            for accomplice, _ in accomplices_in_territory[:3]:
                actions.append(TryCheatOnSpouseAction(character, accomplice.entity))

            return actions

        return []


class ClaimThroneBehavior(AIBehavior):
    """Territory-controlling family heads will try to claim the throne if empty."""

    def __init__(self, precondition: AIPrecondition) -> None:
        super().__init__("ClaimThrone", precondition)

    def get_actions(self, character: Entity) -> list[AIAction]:

        world = character.world

        dynasty_tracker = world.get_resource(DynastyTracker)

        if dynasty_tracker.current_dynasty is not None:
            return []

        family_head_component = character.get_component(HeadOfFamily)

        family_component = family_head_component.family.get_component(Family)

        # Check that the family owns land
        if len(family_component.controlled_territories) == 0:
            return []

        return [ClaimThroneAction(character)]
