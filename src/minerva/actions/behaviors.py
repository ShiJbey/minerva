"""Minerva concrete behavior classes."""

from __future__ import annotations

import logging
import random

from minerva.actions.base_types import (
    AIAction,
    AIActionCollection,
    AIActionLibrary,
    AIActionType,
    AIBehavior,
    AIBrain,
    AIContext,
    Scheme,
)
from minerva.actions.scheme_helpers import add_member_to_scheme
from minerva.actions.scheme_types import CoupScheme
from minerva.characters.components import Character, Family, HeadOfFamily
from minerva.characters.succession_helpers import get_current_ruler
from minerva.characters.war_data import Alliance
from minerva.characters.war_helpers import (
    create_alliance_scheme,
    create_coup_scheme,
    create_war_scheme,
    end_alliance,
    join_alliance,
)
from minerva.config import Config
from minerva.datetime import SimDate
from minerva.ecs import Active, GameObject
from minerva.life_events.events import TakeOverProvinceEvent
from minerva.relationships.base_types import Opinion
from minerva.relationships.helpers import get_relationship
from minerva.world_map.components import InRevolt, PopulationHappiness, Territory
from minerva.world_map.helpers import (
    increment_political_influence,
    set_territory_controlling_family,
)

_logger = logging.getLogger(__name__)


class IdleBehavior(AIBehavior):
    """A behavior that does nothing."""

    def execute(self, character: GameObject) -> bool:
        current_date = character.world.resources.get_resource(SimDate)

        _logger.debug(
            "[%s]: %s is idle.", current_date.to_iso_str(), character.name_with_uid
        )
        return True


class GiveBackToTerritoryActionType(AIActionType):
    """Two characters get married."""

    def execute(self, context: AIContext) -> bool:
        current_date = context.world.resources.get_resource(SimDate)

        territory: GameObject = context.blackboard["territory"]
        family: GameObject = context.blackboard["family"]

        increment_political_influence(territory, family, 5)

        territory.get_component(PopulationHappiness).base_value += 5

        # TODO: Fire and log event
        _logger.info(
            "[%s]: %s gave back to the smallfolk of %s.",
            current_date.to_iso_str(),
            context.character.name_with_uid,
            territory.name_with_uid,
        )

        return True


class GiveBackToTerritoryAction(AIAction):
    """An instance of a get married action."""

    def __init__(
        self, context: AIContext, family: GameObject, territory: GameObject
    ) -> None:
        action_library = context.world.resources.get_resource(AIActionLibrary)
        super().__init__(
            context,
            action_library.get_action_with_name(GiveBackToTerritoryActionType.__name__),
        )
        self.context.blackboard["family"] = family
        self.context.blackboard["territory"] = territory


class GiveToSmallfolkBehavior(AIBehavior):
    """A family head  will try to increase their political influence in a territory."""

    def execute(self, character: GameObject) -> bool:
        # Choose the territory with the lowest political influence
        # and spend influence points to increase political power
        rng = character.world.resources.get_resource(random.Random)
        brain = character.get_component(AIBrain)

        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        actions: AIActionCollection = AIActionCollection()

        for territory in family_component.territories:
            action = GiveBackToTerritoryAction(
                brain.context,
                family=family_component.gameobject,
                territory=territory,
            )
            utility = action.calculate_utility()

            if utility > 0:
                actions.add(action, utility)

        if len(actions) > 0:
            rng = character.world.resources.get_resource(random.Random)
            selected_action = actions.select_weighted_random(rng)

            return selected_action.execute()

        return False


class QuellRevoltActionType(AIActionType):
    """The action of quelling a specific revolt."""

    def execute(self, context: AIContext) -> bool:
        current_date = context.world.resources.get_resource(SimDate)
        config = context.world.resources.get_resource(Config)

        family_head: GameObject = context.blackboard["family_head"]
        territory: GameObject = context.blackboard["territory"]

        territory.remove_component(InRevolt)

        population_happiness = territory.get_component(PopulationHappiness)

        population_happiness.base_value = config.base_territory_happiness

        # TODO: Fire and log events
        _logger.info(
            "[%s]: %s quelled the revolt in %s",
            current_date.to_iso_str(),
            family_head.name_with_uid,
            territory.name_with_uid,
        )

        return True


class QuellRevoltAction(AIAction):
    """A parameterized instance of a quell revolt action."""

    def __init__(
        self, context: AIContext, family_head: GameObject, territory: GameObject
    ) -> None:
        super().__init__(
            context=context,
            action=context.world.resources.get_resource(
                AIActionLibrary
            ).get_action_with_name(QuellRevoltActionType.__name__),
        )
        self.context.blackboard["family_head"] = family_head
        self.context.blackboard["territory"] = territory


class QuellRevolt(AIBehavior):
    """The head of the family controlling a territory will try to quell a revolt."""

    def execute(self, character: GameObject) -> bool:
        # This behavior requires at least on territory to be in revolt. This
        # information is picked up by the

        # Get all the villages in revolt
        character_brain = character.get_component(AIBrain)
        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        actions: AIActionCollection = AIActionCollection()

        for territory in family_component.territories:
            if territory.has_component(InRevolt):
                actions.add(
                    QuellRevoltAction(
                        context=character_brain.context,
                        family_head=character,
                        territory=territory,
                    ),
                    0.5,
                )

        # Select one territory and
        if len(actions) > 0:
            rng = character.world.resources.get_resource(random.Random)
            selected_action = actions.select_weighted_random(rng)

            return selected_action.execute()

        return False


class FormAlliance(AIBehavior):
    """A family head will try to start a new alliance."""

    def execute(self, character: GameObject) -> bool:
        # Character will start a new scheme to form an alliance. Other family heads can
        # choose to join before the alliance is officially formed.
        world = character.world

        create_alliance_scheme(character)

        # TODO: Fire and log event
        _logger.info(
            "[%s]: %s is attempting to form a new alliance.",
            world.resources.get_resource(SimDate).to_iso_str(),
            character.name_with_uid,
        )

        return True


class JoinAllianceScheme(AIBehavior):
    """A family head will have their family join an existing alliance."""

    def execute(self, character: GameObject) -> bool:
        # The family head will try to join an alliance scheme.

        world = character.world

        # Find all active alliances and join one based on the opinion of the character
        # toward the person who is the head of the founding family.
        eligible_schemes: list[GameObject] = []
        scheme_scores: list[float] = []
        for _, (scheme, _) in world.get_components((Scheme, Active)):
            if scheme.get_type() != "alliance":
                continue

            initiator = scheme.initiator

            opinion_score = (
                get_relationship(character, initiator).get_component(Opinion).normalized
            )

            if opinion_score > 0:
                eligible_schemes.append(scheme.gameobject)
                scheme_scores.append(opinion_score)

        if eligible_schemes:

            rng = world.resources.get_resource(random.Random)
            chosen_scheme = rng.choices(eligible_schemes, scheme_scores, k=1)[0]

            add_member_to_scheme(chosen_scheme, character)

            # TODO: Fire and log event
            _logger.info(
                "[%s]: %s has joined %s's alliance scheme.",
                world.resources.get_resource(SimDate).to_iso_str(),
                character.name_with_uid,
                chosen_scheme.get_component(Scheme).initiator.name_with_uid,
            )

        return True


class JoinExistingAlliance(AIBehavior):
    """A family head will have their family join an existing alliance."""

    def execute(self, character: GameObject) -> bool:
        # The family head will try to join an existing alliance.

        world = character.world

        # Find all active alliances and join one based on the opinion of the character
        # toward the person who is the head of the founding family.
        eligible_alliances: list[GameObject] = []
        alliance_scores: list[float] = []
        for _, (alliance, _) in world.get_components((Alliance, Active)):
            if not alliance.founder_family.is_active:
                continue

            founder_family_head = alliance.founder_family.get_component(Family).head

            if founder_family_head is None:
                continue

            opinion_score = (
                get_relationship(character, founder_family_head)
                .get_component(Opinion)
                .value
            )

            if opinion_score > 0:
                eligible_alliances.append(alliance.gameobject)
                alliance_scores.append(opinion_score)

        if eligible_alliances:

            rng = world.resources.get_resource(random.Random)
            chosen_alliance = rng.choices(eligible_alliances, alliance_scores, k=1)[0]

            family = character.get_component(Character).family

            if family is None:
                raise RuntimeError(f"{character.name_with_uid} is missing a family.")

            join_alliance(alliance=chosen_alliance, family=family)

            # TODO: Fire and log event
            _logger.info(
                "[%s]: the %s family has joined the alliance started by the %s family.",
                world.resources.get_resource(SimDate).to_iso_str(),
                family.name_with_uid,
                chosen_alliance.get_component(Alliance).founder_family.name_with_uid,
            )

        return True


class DisbandAlliance(AIBehavior):
    """A family head will try to disband their current alliance."""

    def execute(self, character: GameObject) -> bool:
        # The family head has the option to leave the current alliance, causing the
        # entire alliance to disband

        character_component = character.get_component(Character)
        family = character_component.family

        if family is None:
            raise RuntimeError(f"{character.name_with_uid} is missing a family.")

        family_component = family.get_component(Family)

        if family_component.alliance is None:
            raise RuntimeError(
                f"{family.name_with_uid} is not currently in an alliance"
            )

        founding_family = family_component.alliance.get_component(
            Alliance
        ).founder_family

        alliance_component = family_component.alliance.get_component(Alliance)
        for member_family in alliance_component.member_families:
            if member_family == family:
                continue

            member_family_component = member_family.get_component(Family)

            if member_family_component.head is not None:
                get_relationship(
                    member_family_component.head, member_family
                ).get_component(Opinion).base_value -= 20

        end_alliance(family_component.alliance)

        world = character.world

        # TODO: Fire and log event
        _logger.info(
            "[%s]: the %s family has disbanded the alliance started by the %s family.",
            world.resources.get_resource(SimDate).to_iso_str(),
            family.name_with_uid,
            founding_family.name_with_uid,
        )

        return True


class StartWarSchemeActionType(AIActionType):
    """Executes action starting a war scheme."""

    def execute(self, context: AIContext) -> bool:
        current_date = context.world.resources.get_resource(SimDate)
        character: GameObject = context.blackboard["aggressor"]
        defender: GameObject = context.blackboard["defender"]
        territory: GameObject = context.blackboard["territory"]

        create_war_scheme(initiator=character, target=defender, territory=territory)

        # TODO: Fire and log event
        _logger.info(
            "[%s]: %s started a war scheme against %s for the %s territory.",
            current_date.to_iso_str(),
            character.name_with_uid,
            defender.name_with_uid,
            territory.name_with_uid,
        )

        return True


class StartWarSchemeAction(AIAction):
    """Action instance data for starting a war scheme against a specific person."""

    def __init__(
        self,
        context: AIContext,
        aggressor: GameObject,
        defender: GameObject,
        territory: GameObject,
    ) -> None:
        super().__init__(
            context,
            context.world.resources.get_resource(AIActionLibrary).get_action_with_name(
                StartWarSchemeActionType.__name__
            ),
        )
        self.context.blackboard["aggressor"] = aggressor
        self.context.blackboard["defender"] = defender
        self.context.blackboard["territory"] = territory


class DeclareWar(AIBehavior):
    """A family head will declare war on another."""

    def execute(self, character: GameObject) -> bool:
        # The character will try to fight another family in a territory for control
        # over that territory. They will not declare war on a territory held by someone
        # in their alliance.

        brain = character.get_component(AIBrain)

        potential_targets: list[GameObject] = brain.context.blackboard[
            "enemy_territories"
        ]

        actions: AIActionCollection = AIActionCollection()

        for territory in potential_targets:
            territory_component = territory.get_component(Territory)

            if territory_component.controlling_family is None:
                continue

            family_component = territory_component.controlling_family.get_component(
                Family
            )

            if family_component.head is None:
                continue

            if family_component.head == character:
                continue

            action = StartWarSchemeAction(
                context=brain.context,
                aggressor=character,
                defender=family_component.head,
                territory=territory,
            )

            utility = action.calculate_utility()

            actions.add(action, utility)

        if len(actions) > 0:
            rng = character.world.resources.get_resource(random.Random)
            selected_action = actions.select_weighted_random(rng)
            selected_action.execute()

        return True


class TaxTerritoryActionType(AIActionType):
    """Two characters get married."""

    def execute(self, context: AIContext) -> bool:
        current_date = context.world.resources.get_resource(SimDate)

        territory: GameObject = context.blackboard["territory"]

        character_component = context.character.get_component(Character)
        character_component.influence_points += 200

        territory.get_component(PopulationHappiness).base_value -= 15

        # TODO: Fire and log event
        _logger.info(
            "[%s]: %s taxed the %s territory.",
            current_date.to_iso_str(),
            context.character.name_with_uid,
            territory.name_with_uid,
        )

        return True


class TaxTerritoryAction(AIAction):
    """An instance of a get married action."""

    def __init__(self, context: AIContext, territory: GameObject) -> None:
        action_library = context.world.resources.get_resource(AIActionLibrary)
        super().__init__(
            context,
            action_library.get_action_with_name(TaxTerritoryActionType.__name__),
        )
        self.context.blackboard["territory"] = territory


class TaxTerritory(AIBehavior):
    """A family head will tax their controlling territory for influence points."""

    def execute(self, character: GameObject) -> bool:
        # Choose the territory with the lowest political influence
        # and spend influence points to increase political power
        rng = character.world.resources.get_resource(random.Random)
        brain = character.get_component(AIBrain)

        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        actions: list[TaxTerritoryAction] = []
        action_weights: list[float] = []
        for territory in family_component.territories:
            action = TaxTerritoryAction(
                brain.context,
                territory=territory,
            )
            utility = action.calculate_utility()

            if utility > 0:
                actions.append(action)
                action_weights.append(utility)

        if actions:
            chosen_action = rng.choices(
                population=actions, weights=action_weights, k=1
            )[0]

            chosen_action.execute()

            return True

        return False


class PlanCoupActionType(AIActionType):
    """Start a scheme to overthrow the ruling family."""

    def execute(self, context: AIContext) -> bool:
        current_date = context.world.resources.get_resource(SimDate).copy()

        initiator: GameObject = context.blackboard["initiator"]
        target: GameObject = context.blackboard["target"]

        # TODO: Fire and log event
        _logger.info(
            "[%s]: %s began a scheme to overthrow %s",
            current_date.to_iso_str(),
            initiator.name_with_uid,
            target.name_with_uid,
        )

        return True


class PlanCoupAction(AIAction):
    """Instance data for starting a scheme to overthrow the royal family."""

    def __init__(
        self, context: AIContext, initiator: GameObject, target: GameObject
    ) -> None:
        super().__init__(
            context,
            context.world.resources.get_resource(AIActionLibrary).get_action_with_name(
                PlanCoupActionType.__name__
            ),
        )
        self.context.blackboard["initiator"] = initiator
        self.context.blackboard["target"] = target


class PlanCoupBehavior(AIBehavior):
    """A family head will attempt to overthrow the royal family."""

    def execute(self, character: GameObject) -> bool:
        # The family head will start a scheme to overthrow the royal family and other
        # characters can join. This is effectively the same as declaring war, but
        # alliances don't join and if discovered, all family heads involved are
        # executed and their families lose control of provinces

        current_date = character.world.resources.get_resource(SimDate)

        current_ruler = get_current_ruler(character.world)

        if current_ruler is None:
            return False

        create_coup_scheme(initiator=character, target=current_ruler)

        # TODO: Fire and log events
        _logger.info(
            "[%s]: %s began a coup scheme to overthrow %s",
            current_date.to_iso_str(),
            character.name_with_uid,
            current_ruler.name_with_uid,
        )

        return True


class JoinCoupScheme(AIBehavior):
    """A family head joins someones coup scheme."""

    def execute(self, character: GameObject) -> bool:
        world = character.world

        # Find all active alliances and join one based on the opinion of the character
        # toward the person who is the head of the founding family.
        eligible_schemes: list[GameObject] = []
        scheme_scores: list[float] = []
        for _, (scheme, _, _) in world.get_components((Scheme, CoupScheme, Active)):

            initiator = scheme.initiator

            opinion_score = (
                get_relationship(character, initiator).get_component(Opinion).normalized
            )

            if character in scheme.members:
                continue

            if opinion_score > 0:
                eligible_schemes.append(scheme.gameobject)
                scheme_scores.append(opinion_score)

        if eligible_schemes:
            rng = world.resources.get_resource(random.Random)
            chosen_scheme = rng.choices(eligible_schemes, scheme_scores, k=1)[0]

            add_member_to_scheme(chosen_scheme, character)

            # TODO: Fire and log event
            _logger.info(
                "[%s]: %s has joined %s's coup scheme.",
                world.resources.get_resource(SimDate).to_iso_str(),
                character.name_with_uid,
                chosen_scheme.get_component(Scheme).initiator.name_with_uid,
            )

            return True

        return False


class ExpandIntoTerritoryActionType(AIActionType):
    """."""

    def execute(self, context: AIContext) -> bool:
        current_date = context.world.resources.get_resource(SimDate)

        family_head: GameObject = context.blackboard["family_head"]
        territory: GameObject = context.blackboard["territory"]

        family_head_component = family_head.get_component(HeadOfFamily)

        territory_component = territory.get_component(Territory)
        territory_component.political_influence[family_head_component.family] = 50

        # TODO: Fire and log event
        _logger.info(
            "[%s]: %s expanded the %s family into %s",
            current_date.to_iso_str(),
            family_head.name_with_uid,
            family_head_component.family.name_with_uid,
            territory.name_with_uid,
        )

        return True


class ExpandIntoTerritoryAction(AIAction):
    """."""

    def __init__(
        self, context: AIContext, family_head: GameObject, territory: GameObject
    ) -> None:
        super().__init__(
            context=context,
            action=context.world.resources.get_resource(
                AIActionLibrary
            ).get_action_with_name(ExpandIntoTerritoryActionType.__name__),
        )
        self.context.blackboard["family_head"] = family_head
        self.context.blackboard["territory"] = territory


class ExpandPoliticalDomain(AIBehavior):
    """A family head expands the family's political influence to a new territory."""

    def execute(self, character: GameObject) -> bool:
        # Loop through all provinces that neighbor existing political territories
        # Consider all those where the family does not have an existing political
        # foothold
        character_brain = character.get_component(AIBrain)
        actions: AIActionCollection = AIActionCollection()
        unexpanded_territories: list[GameObject] = character_brain.context.blackboard[
            "unexpanded_territories"
        ]
        for territory in unexpanded_territories:
            action = ExpandIntoTerritoryAction(
                character_brain.context, family_head=character, territory=territory
            )
            actions.add(action, action.calculate_utility())

        if len(actions) > 0:
            rng = character.world.resources.get_resource(random.Random)
            selected_action = actions.select_weighted_random(rng)

            return selected_action.execute()

        return False


class SeizeTerritoryActionType(AIActionType):
    """."""

    def execute(self, context: AIContext) -> bool:
        family_head: GameObject = context.blackboard["family_head"]
        territory: GameObject = context.blackboard["territory"]

        family_head_component = family_head.get_component(HeadOfFamily)

        set_territory_controlling_family(territory, family_head_component.family)

        TakeOverProvinceEvent(
            character=family_head,
            province=territory,
            family=family_head_component.family,
        ).dispatch()

        return True


class SeizeTerritoryAction(AIAction):
    """."""

    def __init__(
        self, context: AIContext, family_head: GameObject, territory: GameObject
    ) -> None:
        super().__init__(
            context=context,
            action=context.world.resources.get_resource(
                AIActionLibrary
            ).get_action_with_name(SeizeTerritoryActionType.__name__),
        )
        self.context.blackboard["family_head"] = family_head
        self.context.blackboard["territory"] = territory


class SeizeControlOfTerritory(AIBehavior):
    """A family head takes control of an unclaimed territory."""

    def execute(self, character: GameObject) -> bool:
        # Loop through all the territories where this character has political influence
        # For all those that that are unclaimed and the territory to a list of
        # potential provinces to expand into.

        actions: AIActionCollection = AIActionCollection()

        character_brain = character.get_component(AIBrain)
        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        for territory in family_component.territories:
            territory_component = territory.get_component(Territory)
            if territory_component.controlling_family is None:
                action = SeizeTerritoryAction(
                    character_brain.context, character, territory
                )
                actions.add(action, action.calculate_utility())

        if len(actions) > 0:
            rng = character.world.resources.get_resource(random.Random)
            selected_action = actions.select_weighted_random(rng)

            return selected_action.execute()

        return False
