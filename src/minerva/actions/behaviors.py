"""Minerva concrete behavior classes."""

from __future__ import annotations

import logging
import random

from minerva import constants
from minerva.actions.base_types import (
    AIAction,
    AIActionCollection,
    AIActionLibrary,
    AIActionType,
    AIBehavior,
    AIBrain,
    AIContext,
    Scheme,
    SchemeStrategy,
)
from minerva.actions.scheme_helpers import add_member_to_scheme, create_scheme
from minerva.characters.components import Character, Family, HeadOfFamily
from minerva.characters.war_data import Alliance
from minerva.characters.war_helpers import end_alliance, join_alliance, start_alliance
from minerva.datetime import SimDate
from minerva.ecs import Active, GameObject
from minerva.life_events.events import TakeOverProvinceEvent
from minerva.relationships.base_types import Reputation
from minerva.relationships.helpers import get_relationship
from minerva.world_map.components import InRevolt, PopulationHappiness, Settlement
from minerva.world_map.helpers import (
    increment_political_influence,
    set_settlement_controlling_family,
)

_logger = logging.getLogger(__name__)


class IdleBehavior(AIBehavior):
    """A behavior that does nothing."""

    def execute(self, character: GameObject) -> bool:
        # Do Nothing
        return True


class GiveBackToTerritoryActionType(AIActionType):
    """Two characters get married."""

    def execute(self, context: AIContext) -> bool:
        current_date = context.world.resources.get_resource(SimDate)

        territory: GameObject = context.blackboard["territory"]
        family: GameObject = context.blackboard["family"]

        increment_political_influence(territory, family, 5)

        territory.get_component(PopulationHappiness).base_value += 5

        _logger.info(
            "[%s]: %s increased influence of %s in %s.",
            current_date.to_iso_str(),
            context.character.name_with_uid,
            family.name_with_uid,
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


class IncreasePoliticalPower(AIBehavior):
    """A family head  will try to increase their political influence in a settlement."""

    def execute(self, character: GameObject) -> bool:
        # Choose the territory with the lowest political influence
        # and spend influence points to increase political power
        rng = character.world.resources.get_resource(random.Random)
        brain = character.get_component(AIBrain)

        character_component = character.get_component(Character)
        character_component.influence_points -= self.cost

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

            character_component = character.get_component(Character)
            character_component.influence_points -= self.cost

            return selected_action.execute()

        return False


class QuellRevoltActionType(AIActionType):
    """The action of quelling a specific revolt."""

    def execute(self, context: AIContext) -> bool:
        current_date = context.world.resources.get_resource(SimDate)

        family_head: GameObject = context.blackboard["family_head"]
        territory: GameObject = context.blackboard["territory"]

        territory.remove_component(InRevolt)

        population_happiness = territory.get_component(PopulationHappiness)

        population_happiness.base_value = constants.BASE_SETTLEMENT_HAPPINESS

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
    """The head of the family controlling a settlement will try to quell a revolt."""

    def execute(self, character: GameObject) -> bool:
        # This behavior requires at least on settlement to be in revolt. This
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

            character_component = character.get_component(Character)
            character_component.influence_points -= self.cost

            return selected_action.execute()

        return False


class AllianceScheme(SchemeStrategy):
    """Create a new alliance scheme"""

    def get_description(self, scheme: Scheme) -> str:
        """Get a string description of the scheme."""
        return f"{scheme.initiator.name_with_uid} is trying to start an alliance."

    def update(self, scheme: Scheme) -> None:
        """Update the scheme and execute any code."""
        world = scheme.gameobject.world
        current_date = world.resources.get_resource(SimDate).copy()
        elapsed_months = (current_date - scheme.start_date).total_months

        if elapsed_months >= self.required_time:
            # Check that other people have joined the scheme for the alliance to be
            # created. Otherwise, this scheme fails
            if len(scheme.members) > 1:

                # Need to get all the families of scheme members
                alliance_families: list[GameObject] = []
                for member in scheme.members:
                    character_component = member.get_component(Character)
                    if character_component.family is None:
                        raise RuntimeError("Alliance member is missing family.")
                    alliance_families.append(character_component.family)

                start_alliance(*alliance_families)
                _logger.info(
                    "[%s]: %s founded a new alliance.",
                    world.resources.get_resource(SimDate).to_iso_str(),
                    scheme.initiator.name_with_uid,
                )
            else:
                _logger.info(
                    "[%s]: %s failed to start a new alliance.",
                    world.resources.get_resource(SimDate).to_iso_str(),
                    scheme.initiator.name_with_uid,
                )

            scheme.is_valid = False


class FormAlliance(AIBehavior):
    """A family head will try to start a new alliance."""

    def execute(self, character: GameObject) -> bool:
        # Character will start a new scheme to form an alliance. Other family heads can
        # choose to join before the alliance is officially formed.
        character_component = character.get_component(Character)
        character_component.influence_points -= self.cost

        world = character.world

        create_scheme(world=world, scheme_type="alliance", initiator=character)

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

            reputation_score = (
                get_relationship(character, initiator).get_component(Reputation).value
            )

            if reputation_score > 0:
                eligible_schemes.append(scheme.gameobject)
                scheme_scores.append(reputation_score)

        if eligible_schemes:
            character_component = character.get_component(Character)
            character_component.influence_points -= self.cost

            rng = world.resources.get_resource(random.Random)
            chosen_scheme = rng.choices(eligible_schemes, scheme_scores, k=1)[0]

            add_member_to_scheme(chosen_scheme, character)

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

            reputation_score = (
                get_relationship(character, founder_family_head)
                .get_component(Reputation)
                .value
            )

            if reputation_score > 0:
                eligible_alliances.append(alliance.gameobject)
                alliance_scores.append(reputation_score)

        if eligible_alliances:
            character_component = character.get_component(Character)
            character_component.influence_points -= self.cost

            rng = world.resources.get_resource(random.Random)
            chosen_alliance = rng.choices(eligible_alliances, alliance_scores, k=1)[0]

            family = character_component.family

            if family is None:
                raise RuntimeError(f"{character.name_with_uid} is missing a family.")

            join_alliance(alliance=chosen_alliance, family=family)

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

        end_alliance(family_component.alliance)

        world = character.world

        _logger.info(
            "[%s]: the %s family has disbanded the alliance started by the %s family.",
            world.resources.get_resource(SimDate).to_iso_str(),
            family.name_with_uid,
            founding_family.name_with_uid,
        )

        return True


class WarScheme(SchemeStrategy):
    """Create a new war scheme"""

    def get_description(self, scheme: Scheme) -> str:
        """Get a string description of the scheme."""
        target = scheme.targets[0]
        return (
            f"{scheme.initiator.name_with_uid} is trying to start an war against "
            f"{target.name_with_uid}."
        )

    def update(self, scheme: Scheme) -> None:
        """Update the scheme and execute any code."""
        world = scheme.gameobject.world
        current_date = world.resources.get_resource(SimDate).copy()
        elapsed_months = (current_date - scheme.start_date).total_months

        if elapsed_months >= self.required_time:
            # Check that other people have joined the scheme for the alliance to be
            # created. Otherwise, this scheme fails
            # start_war()
            pass


class StartWarSchemeActionType(AIActionType):
    """Executes action starting a war scheme."""

    def execute(self, context: AIContext) -> bool:
        # return super().execute(context)
        return True


class StartWarSchemeAction(AIAction):
    """Action instance data for starting a war scheme against a specific person."""

    def __init__(
        self, context: AIContext, aggressor: GameObject, defender: GameObject
    ) -> None:
        super().__init__(
            context,
            context.world.resources.get_resource(AIActionLibrary).get_action_with_name(
                StartWarSchemeActionType.__name__
            ),
        )
        self.context.blackboard["aggressor"] = aggressor
        self.context.blackboard["defender"] = defender


class DeclareWar(AIBehavior):
    """A family head will declare war on another."""

    def execute(self, character: GameObject) -> bool:
        # The character will try to fight another family in a territory for control
        # over that territory. They will not declare war on a territory held by someone
        # in their alliance.

        return True


class TaxTerritory(AIBehavior):
    """A family head will tax their controlling settlement for influence points."""

    def execute(self, character: GameObject) -> bool:
        # Choose the territory with the lowest political influence
        # and spend influence points to increase political power
        rng = character.world.resources.get_resource(random.Random)
        brain = character.get_component(AIBrain)

        character_component = character.get_component(Character)
        character_component.influence_points -= self.cost

        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        actions: list[GiveBackToTerritoryAction] = []
        action_weights: list[float] = []
        for territory in family_component.territories:
            action = GiveBackToTerritoryAction(
                brain.context,
                family=family_component.gameobject,
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


class CoupScheme(SchemeStrategy):
    """A scheme to overthrow the royal family and establish the coup organizer."""

    def get_description(self, scheme: Scheme) -> str:
        """Get a string description of the scheme."""
        target = scheme.targets[0]
        return (
            f"{scheme.initiator.name_with_uid} is planning a coup against "
            f"{target.name_with_uid}."
        )

    def update(self, scheme: Scheme) -> None:
        """Update the scheme and execute any code."""
        world = scheme.gameobject.world
        current_date = world.resources.get_resource(SimDate).copy()
        elapsed_months = (current_date - scheme.start_date).total_months

        # Check if the scheme is discovered by the ruling family

        if elapsed_months >= self.required_time:
            # Check that other people have joined the scheme for the alliance to be
            # created. Otherwise, this scheme fails
            # start_war()
            pass


class PlanCoupActionType(AIActionType):
    """Start a scheme to overthrow the ruling family."""

    def execute(self, context: AIContext) -> bool:
        current_date = context.world.resources.get_resource(SimDate).copy()

        initiator: GameObject = context.blackboard["initiator"]
        target: GameObject = context.blackboard["target"]

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


class CoupDEtat(AIBehavior):
    """A family head will attempt to overthrow the royal family."""

    def execute(self, character: GameObject) -> bool:
        # The family head will start a scheme to overthrow the royal family and other
        # characters can join. This is effectively the same as declaring war, but
        # alliances don't join and if discovered, all family heads involved are
        # executed and their families lose control of provinces

        return True


class ExpandIntoTerritoryActionType(AIActionType):
    """."""

    def execute(self, context: AIContext) -> bool:
        current_date = context.world.resources.get_resource(SimDate)

        family_head: GameObject = context.blackboard["family_head"]
        territory: GameObject = context.blackboard["territory"]

        family_head_component = family_head.get_component(HeadOfFamily)

        territory_component = territory.get_component(Settlement)
        territory_component.political_influence[family_head_component.family] = 50

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
    """A family head expands the family's political influence to a new settlement."""

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

            character_component = character.get_component(Character)
            character_component.influence_points -= self.cost

            return selected_action.execute()

        return False


class SeizeTerritoryActionType(AIActionType):
    """."""

    def execute(self, context: AIContext) -> bool:
        family_head: GameObject = context.blackboard["family_head"]
        territory: GameObject = context.blackboard["territory"]

        family_head_component = family_head.get_component(HeadOfFamily)

        set_settlement_controlling_family(territory, family_head_component.family)

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
    """A family head takes control of an unclaimed settlement."""

    def execute(self, character: GameObject) -> bool:
        # Loop through all the territories where this character has political influence
        # For all those that that are unclaimed and the settlement to a list of
        # potential provinces to expand into.

        actions: AIActionCollection = AIActionCollection()

        character_brain = character.get_component(AIBrain)
        family_head_component = character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        for territory in family_component.territories:
            settlement_component = territory.get_component(Settlement)
            if settlement_component.controlling_family is None:
                action = SeizeTerritoryAction(
                    character_brain.context, character, territory
                )
                actions.add(action, action.calculate_utility())

        if len(actions) > 0:
            rng = character.world.resources.get_resource(random.Random)
            selected_action = actions.select_weighted_random(rng)

            character_component = character.get_component(Character)
            character_component.influence_points -= self.cost

            return selected_action.execute()

        return False
