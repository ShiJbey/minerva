"""Minerva concrete behavior classes."""

from __future__ import annotations

from ordered_set import OrderedSet

from minerva.actions.actions import (
    ClaimThroneAction,
    ExtortLocalFamiliesAction,
    ExtortTerritoryOwnersAction,
    GiveToTerritoriesAction,
    JoinAllianceAction,
    JoinAllianceSchemeAction,
    JoinCoupSchemeAction,
    LeaveAllianceAction,
    QuellRevoltAction,
    SeizeTerritoryAction,
    SendAidAction,
    SendGiftAction,
    StartAllianceSchemeAction,
    StartCoupSchemeAction,
    StartWarSchemeAction,
    TaxTerritoriesAction,
    TryCheatOnSpouseAction,
)
from minerva.actions.base_types import AIAction, AIBehavior, AIPreconditionGroup
from minerva.actions.preconditions import (
    FamilyInAlliancePrecondition,
    HasActiveSchemes,
    HasControlledTerritories,
    IsAllianceMemberPlottingCoup,
    IsCurrentlyAtWar,
    IsFamilyHeadPrecondition,
    IsRulerPrecondition,
    JoinedAllianceScheme,
    Not,
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
from minerva.relationships.helpers import get_attraction
from minerva.world_map.components import InRevolt, Territory


class GiveBackToTerritoriesBehavior(AIBehavior):
    """A family head will pay to improve happiness in their territories."""

    def __init__(self) -> None:
        super().__init__(
            "GiveToSmallFolk",
            AIPreconditionGroup(
                IsFamilyHeadPrecondition(),
                HasControlledTerritories(),
            ),
        )

    def get_actions(self, character: Entity) -> list[AIAction]:
        family_head_component = character.get_component(HeadOfFamily)

        return [GiveToTerritoriesAction(character, family_head_component.family)]


class SendGiftBehavior(AIBehavior):
    """Family heads will send gifts to each other to increase opinion scores.

    This behavior can only be executed by family heads. However, the choices of
    who to send gifts to changes based on if the character controls their home base.

    - Family heads who control their home base (and any other territories) may send
      gifts to the heads of families who also own territories. They do not send gifts to
      family heads who do not control land

    - Family heads who do NOT control their home base can send gifts to other families
      in the same territory or family heads of adjacent territories.
    """

    def __init__(self) -> None:
        super().__init__(
            "SendGift",
            AIPreconditionGroup(
                IsFamilyHeadPrecondition(),
            ),
        )

    def get_actions(self, character: Entity) -> list[AIAction]:
        # Get all the families within the same territories
        world = character.world
        family_head_component = character.get_component(HeadOfFamily)
        family = family_head_component.family
        family_component = family.get_component(Family)

        recipients: OrderedSet[Entity] = OrderedSet([])
        actions: list[AIAction] = []

        all_territories = world.query_components((Territory, Active))

        # This family controls territories
        if family_component.controlled_territories:
            # Iterate territories
            for uid, (territory_component, _) in all_territories:
                territory = world.get_entity(uid)

                if territory in family_component.controlled_territories:
                    continue

                if territory_component.controlling_family is None:
                    continue

                other_family = territory_component.controlling_family.get_component(
                    Family
                )

                if other_family.head:
                    actions.append(SendGiftAction(character, other_family.head))

        # This family does not control territories
        else:
            home_base = family_component.home_base
            assert home_base
            home_base_territory = home_base.get_component(Territory)

            # Add options to send gifts to family heads in the same territory
            for other_family in home_base_territory.families:
                # Skip your own family
                if other_family == family:
                    continue

                # Check that the other family has a family head to send the gift to
                other_family_component = other_family.get_component(Family)
                if (
                    other_family_component.head
                    and other_family_component.head not in recipients
                ):
                    recipients.add(other_family_component.head)
                    actions.append(
                        SendGiftAction(character, other_family_component.head)
                    )

            # Add the option to send gifts to family heads controlling neighboring
            # territories.
            for territory in home_base_territory.neighbors:
                territory_component = territory.get_component(Territory)

                if territory_component.controlling_family is None:
                    continue

                other_family = territory_component.controlling_family.get_component(
                    Family
                )

                if other_family.head:
                    actions.append(SendGiftAction(character, other_family.head))

        return actions


class SendAidBehavior(AIBehavior):
    """Character will try to increase favor with a family dealing with a revolt."""

    def __init__(self) -> None:
        super().__init__(
            "SendAid",
            AIPreconditionGroup(
                IsFamilyHeadPrecondition(),
            ),
        )

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

    def __init__(self) -> None:
        super().__init__(
            "ExtortTerritoryOwners",
            AIPreconditionGroup(
                IsRulerPrecondition(),
            ),
        )

    def get_actions(self, character: Entity) -> list[AIAction]:
        return [ExtortTerritoryOwnersAction(character)]


class ExtortLocalFamiliesBehavior(AIBehavior):
    """A family head will extort families that live in their controlled territories."""

    def __init__(self) -> None:
        super().__init__(
            "ExtortLocalFamilies",
            AIPreconditionGroup(
                IsFamilyHeadPrecondition(),
            ),
        )

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

    def __init__(self) -> None:
        super().__init__(
            "QuellRevolt",
            AIPreconditionGroup(
                IsFamilyHeadPrecondition(),
            ),
        )

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
                actions.append(QuellRevoltAction(character, territory))

        return actions


class StartAllianceSchemeBehavior(AIBehavior):
    """A family head will try to start a new alliance."""

    def __init__(self) -> None:
        super().__init__(
            "StartAllianceScheme",
            AIPreconditionGroup(
                IsFamilyHeadPrecondition(),
                Not(FamilyInAlliancePrecondition()),
                Not(HasActiveSchemes()),
                Not(IsCurrentlyAtWar()),
            ),
        )

    def get_actions(self, character: Entity) -> list[AIAction]:
        # Character will start a new scheme to form an alliance. Other family heads can
        # choose to join before the alliance is officially formed.
        family_head_component = character.get_component(HeadOfFamily)
        return [StartAllianceSchemeAction(character, family_head_component.family)]


class JoinAllianceSchemeBehavior(AIBehavior):
    """A family head will have their family join an existing alliance."""

    def __init__(self) -> None:
        super().__init__(
            "JoinAllianceScheme",
            AIPreconditionGroup(
                IsFamilyHeadPrecondition(),
                Not(FamilyInAlliancePrecondition()),
                Not(JoinedAllianceScheme()),
                Not(HasActiveSchemes()),
                Not(IsCurrentlyAtWar()),
            ),
        )

    def get_actions(self, character: Entity) -> list[AIAction]:
        world = character.world
        actions: list[AIAction] = []

        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        if family_component.alliance:
            return []

        for _, (scheme, _) in world.query_components((AllianceScheme, Active)):
            if not scheme.is_valid:
                continue

            if scheme.initiator == character or scheme.has_character(character):
                continue

            actions.append(
                JoinAllianceSchemeAction(
                    character, family_head_component.family, scheme.entity
                )
            )

        return actions


class JoinExistingAlliance(AIBehavior):
    """A family head will have their family join an existing alliance."""

    def __init__(self) -> None:
        super().__init__(
            "JoinAlliance",
            AIPreconditionGroup(
                IsFamilyHeadPrecondition(),
                Not(FamilyInAlliancePrecondition()),
                Not(JoinedAllianceScheme()),
                Not(IsCurrentlyAtWar()),
            ),
        )

    def get_actions(self, character: Entity) -> list[AIAction]:
        # The family head will try to join an existing alliance.
        world = character.world
        family_head_component = character.get_component(HeadOfFamily)

        actions: list[AIAction] = []

        for _, (alliance, _) in world.query_components((Alliance, Active)):
            actions.append(
                JoinAllianceAction(
                    character, family_head_component.family, alliance.entity
                )
            )

        return actions


class LeaveAlliance(AIBehavior):
    """A family head will try to leave their current alliance."""

    def __init__(self) -> None:
        super().__init__(
            "LeaveAlliance",
            AIPreconditionGroup(
                IsFamilyHeadPrecondition(),
                FamilyInAlliancePrecondition(),
                Not(IsCurrentlyAtWar()),
            ),
        )

    def get_actions(self, character: Entity) -> list[AIAction]:
        family_head_component = character.get_component(HeadOfFamily)
        family = family_head_component.family
        family_component = family.get_component(Family)
        alliance = family_component.alliance

        if alliance is None:
            return []

        alliance_component = alliance.get_component(Alliance)

        if alliance_component.founder_family == family:
            return []

        else:
            return [LeaveAllianceAction(character, family, alliance)]


class DeclareWarBehavior(AIBehavior):
    """A family head will declare war on another."""

    def __init__(self) -> None:
        super().__init__(
            "DeclareWar",
            AIPreconditionGroup(
                IsFamilyHeadPrecondition(),
                Not(IsAllianceMemberPlottingCoup()),
                Not(HasActiveSchemes()),
                Not(IsCurrentlyAtWar()),
            ),
        )

    def get_actions(self, character: Entity) -> list[AIAction]:
        # The character will try to fight another family in a territory for control
        # over that territory. They will not declare war on a territory held by someone
        # in their alliance.
        family_head_component = character.get_component(HeadOfFamily)
        family = family_head_component.family
        family_component = family.get_component(Family)

        # If the family does not control their home base, they can only declare war on
        # the family that controls it
        if len(family_component.controlled_territories) == 0:
            if family_component.home_base is not None:
                territory_component = family_component.home_base.get_component(
                    Territory
                )
                controlling_family = territory_component.controlling_family

                if controlling_family is None:
                    return []

                controlling_family_head = controlling_family.get_component(Family).head

                if controlling_family != family and controlling_family_head is not None:
                    return [
                        StartWarSchemeAction(
                            character,
                            controlling_family_head,
                            family_component.home_base,
                        )
                    ]
            else:
                return []

        # Otherwise, land-controlling families can declare war on any territory
        # neighboring one they control.
        actions: list[AIAction] = []

        for territory in family_component.controlled_territories:
            for neighbor in territory.get_component(Territory).neighbors:
                territory_component = neighbor.get_component(Territory)

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
                    character=character,
                    target=enemy_family_component.head,
                    territory=territory,
                )

                actions.append(action)

        return actions


class TaxTerritories(AIBehavior):
    """A family head will tax their controlling territories for influence points."""

    def __init__(self) -> None:
        super().__init__(
            "TaxTerritories", AIPreconditionGroup(IsFamilyHeadPrecondition())
        )

    def get_actions(self, character: Entity) -> list[AIAction]:
        # Choose the territory with the lowest political influence
        # and spend influence points to increase political power
        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        if family_component.controlled_territories:
            return [TaxTerritoriesAction(character)]

        return []


class PlanCoupBehavior(AIBehavior):
    """A family head will attempt to overthrow the royal family."""

    def __init__(self) -> None:
        super().__init__(
            "PlanCoup",
            AIPreconditionGroup(
                IsFamilyHeadPrecondition(),
                Not(IsRulerPrecondition()),
                Not(IsAllianceMemberPlottingCoup()),
                Not(HasActiveSchemes()),
                Not(IsCurrentlyAtWar()),
            ),
        )

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

    def __init__(self) -> None:
        super().__init__(
            "JoinCoupScheme", AIPreconditionGroup(IsFamilyHeadPrecondition())
        )

    def get_actions(self, character: Entity) -> list[AIAction]:
        world = character.world

        # Find all active alliances and join one based on the opinion of the character
        # toward the person who is the head of the founding family.
        actions: list[AIAction] = []

        for _, (scheme, _) in world.query_components((CoupScheme, Active)):
            if not scheme.is_valid:
                continue

            if scheme.initiator == character or character in scheme.members:
                continue

            actions.append(JoinCoupSchemeAction(character, scheme.entity))

        return actions


class SeizeControlOfTerritory(AIBehavior):
    """A family head takes control of an unclaimed territory."""

    def __init__(self) -> None:
        super().__init__(
            "SeizeControlOfTerritory", AIPreconditionGroup(IsFamilyHeadPrecondition())
        )

    def get_actions(self, character: Entity) -> list[AIAction]:
        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        # Claim the home base if not controlled
        if family_component.home_base:
            territory_component = family_component.home_base.get_component(Territory)
            if territory_component.controlling_family is None:
                return [SeizeTerritoryAction(character, family_component.home_base)]

        # Otherwise, loop through controlled territory neighbors.
        actions: list[AIAction] = []
        for territory in family_component.controlled_territories:
            for neighbor in territory.get_component(Territory).neighbors:
                territory_component = neighbor.get_component(Territory)
                if territory_component.controlling_family is None:
                    actions.append(SeizeTerritoryAction(character, territory))

        return actions


class CheatOnSpouseBehavior(AIBehavior):
    """."""

    def __init__(self) -> None:
        super().__init__("CheatOnSpouse")

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

        if character_component.life_stage < LifeStage.YOUNG_ADULT:
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
                attraction = get_attraction(character, c.entity)
                accomplices_in_territory.append((c, attraction))

        accomplices_in_territory.sort(key=lambda e: e[1])

        if accomplices_in_territory:
            actions: list[AIAction] = []

            for accomplice, _ in accomplices_in_territory[:3]:
                actions.append(
                    TryCheatOnSpouseAction(
                        character, character_spouse, accomplice.entity
                    )
                )

            return actions

        return []


class ClaimThroneBehavior(AIBehavior):
    """Territory-controlling family heads will try to claim the throne if empty."""

    def __init__(self) -> None:
        super().__init__(
            "ClaimThrone",
            AIPreconditionGroup(
                IsFamilyHeadPrecondition(),
                Not(IsRulerPrecondition()),
                Not(IsCurrentlyAtWar()),
            ),
        )

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
