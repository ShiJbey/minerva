"""Helper classes and functions for character behaviors."""

import random
from typing import Iterable, Optional

import numpy as np
from ordered_set import OrderedSet

from minerva.actions.base_types import (
    ActionSelectionStrategy,
    AIAction,
    AIBehavior,
    AIContext,
    AIPrecondition,
    AISensor,
    AIUtilityConsideration,
    BehaviorSelectionStrategy,
    Scheme,
    SchemeManager,
)
from minerva.actions.scheme_helpers import get_character_schemes_of_type
from minerva.actions.scheme_types import CoupScheme
from minerva.characters.components import (
    Boldness,
    Character,
    Compassion,
    Diplomacy,
    Dynasty,
    DynastyTracker,
    Emperor,
    Family,
    Greed,
    HeadOfFamily,
    Honor,
    Intrigue,
    Martial,
    Rationality,
    Stewardship,
    WantForPower,
)
from minerva.characters.motive_helpers import MotiveVector, get_character_motives
from minerva.characters.war_data import Alliance, WarTracker
from minerva.ecs import Active, GameObject
from minerva.relationships.base_types import Reputation
from minerva.relationships.helpers import get_relationship
from minerva.world_map.components import InRevolt, Settlement


class IfAny(AIPrecondition):
    """Groups preconditions together and returns true if any evaluate to True."""

    __slots__ = ("preconditions",)

    preconditions: list[AIPrecondition]

    def __init__(self, *preconditions: AIPrecondition) -> None:
        super().__init__()
        self.preconditions = list(preconditions)

    def evaluate(self, context: AIContext) -> bool:
        return any(p.evaluate(context) for p in self.preconditions)


class Not(AIPrecondition):
    """Groups preconditions together and returns true if any evaluate to True."""

    __slots__ = ("precondition",)

    precondition: AIPrecondition

    def __init__(self, precondition: AIPrecondition) -> None:
        super().__init__()
        self.precondition = precondition

    def evaluate(self, context: AIContext) -> bool:
        return not self.precondition.evaluate(context)


class Invert(AIUtilityConsideration):
    """Inverts a consideration score."""

    __slots__ = ("consideration",)

    consideration: AIUtilityConsideration

    def __init__(self, consideration: AIUtilityConsideration) -> None:
        super().__init__()
        self.consideration = consideration

    def evaluate(self, context: AIContext) -> float:
        return 1 - self.consideration.evaluate(context)


class BehaviorMotiveConsideration(AIUtilityConsideration):
    """A consideration of the behavior's motives against a character's"""

    def evaluate(self, context: AIContext) -> float:
        behavior_motives: MotiveVector = context.blackboard["behavior_motives"]
        character_motives = get_character_motives(context.character)

        utility_vect = behavior_motives.vect * (character_motives.vect * 2)
        utility_score = float(np.sum(utility_vect) / 9)  # total of 9 motives

        return utility_score


class StewardshipConsideration(AIUtilityConsideration):
    """A consideration of a character's stewardship stat."""

    def evaluate(self, context: AIContext) -> float:
        return context.character.get_component(Stewardship).normalized


class RationalityConsideration(AIUtilityConsideration):
    """A consideration of a character's rationality stat."""

    def evaluate(self, context: AIContext) -> float:
        return context.character.get_component(Rationality).normalized


class DiplomacyConsideration(AIUtilityConsideration):
    """A consideration of a character's diplomacy stat."""

    def evaluate(self, context: AIContext) -> float:
        return context.character.get_component(Diplomacy).normalized


class GreedConsideration(AIUtilityConsideration):
    """A consideration of a character's greed stat."""

    def evaluate(self, context: AIContext) -> float:
        return context.character.get_component(Greed).normalized


class HonorConsideration(AIUtilityConsideration):
    """A consideration of a character's honor stat."""

    def evaluate(self, context: AIContext) -> float:
        return context.character.get_component(Honor).normalized


class CompassionConsideration(AIUtilityConsideration):
    """A consideration of a character's compassion stat."""

    def evaluate(self, context: AIContext) -> float:
        return context.character.get_component(Compassion).normalized


class BoldnessConsideration(AIUtilityConsideration):
    """A consideration of a character's boldness stat."""

    def evaluate(self, context: AIContext) -> float:
        return context.character.get_component(Boldness).normalized


class MartialConsideration(AIUtilityConsideration):
    """A consideration of a character's martial stat."""

    def evaluate(self, context: AIContext) -> float:
        return context.character.get_component(Martial).normalized


class WantForPowerConsideration(AIUtilityConsideration):
    """A consideration of a character's WantForPower stat."""

    def evaluate(self, context: AIContext) -> float:
        return context.character.get_component(WantForPower).normalized


class IntrigueConsideration(AIUtilityConsideration):
    """A consideration of a character's intrigue stat."""

    def evaluate(self, context: AIContext) -> float:
        return context.character.get_component(Intrigue).normalized


class InfluencePointConsideration(AIUtilityConsideration):
    """A consideration for influence points up to a given saturation value.

    As the number of influence points get closer to the target value, the
    consideration score increases.
    """

    __slots__ = ("target_value",)

    target_value: int

    def __init__(self, saturation_value: int) -> None:
        super().__init__()
        self.target_value = saturation_value

    def evaluate(self, context: AIContext) -> float:
        influence_points = context.character.get_component(Character).influence_points
        consideration_score = min(1.0, float(influence_points) / self.target_value)
        return consideration_score


class OpinionOfRulerConsideration(AIUtilityConsideration):
    """A consideration of the characters opinion of the ruler (if applicable)."""

    def evaluate(self, context: AIContext) -> float:
        world = context.world
        dynasty_tracker = world.resources.get_resource(DynastyTracker)

        if dynasty_tracker.current_dynasty is None:
            return 0

        dynasty_component = dynasty_tracker.current_dynasty.get_component(Dynasty)

        if dynasty_component.current_ruler is not None:
            if context.character == dynasty_component.current_ruler:
                return 1.0
            else:
                return (
                    get_relationship(context.character, dynasty_component.current_ruler)
                    .get_component(Reputation)
                    .normalized
                )

        return 0


class OpinionOfAllianceLeader(AIUtilityConsideration):
    """A consideration for how characters feel about the leader of their alliance."""

    def evaluate(self, context: AIContext) -> float:
        return 1.0


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


class FamilyInAlliancePrecondition(AIPrecondition):
    """Check if the character's family belongs to an alliance."""

    def evaluate(self, context: AIContext) -> bool:
        character_component = context.character.get_component(Character)
        family = character_component.family

        if family is None:
            return False

        family_component = family.get_component(Family)

        return family_component.alliance is not None


class JoinedAllianceScheme(AIPrecondition):
    """Evaluates to true if the character has already joined an alliance scheme."""

    def evaluate(self, context: AIContext) -> bool:
        schemes = get_character_schemes_of_type(context.character, "alliance")
        return len(schemes) > 0


class AreAllianceSchemesActive(AIPrecondition):
    """Evaluate to True if there are alliance schemes available to join."""

    def evaluate(self, context: AIContext) -> bool:
        alliance_schemes: list[Scheme] = []

        for _, (scheme, _) in context.world.get_components((Scheme, Active)):
            if scheme.get_type() == "alliance":
                alliance_schemes.append(scheme)

        return len(alliance_schemes) > 0


class AreAlliancesActive(AIPrecondition):
    """Evaluate to True if there are alliances available to join."""

    def evaluate(self, context: AIContext) -> bool:
        return len(context.world.get_components((Alliance, Active))) > 0


class IsRulerPrecondition(AIPrecondition):
    """Evaluates to true if the character is the current ruler."""

    def evaluate(self, context: AIContext) -> bool:
        return context.character.has_component(Emperor)


class AreCoupSchemesActive(AIPrecondition):
    """Evaluates to True when there are active coup schemes."""

    def evaluate(self, context: AIContext) -> bool:
        return len(context.world.get_components((CoupScheme, Active))) > 0


class IsAllianceMemberPlottingCoup(AIPrecondition):
    """Returns true if an alliance member is plotting a coup."""

    def evaluate(self, context: AIContext) -> bool:
        family = context.character.get_component(Character).family

        if family is None:
            return False

        family_component = family.get_component(Family)

        if family_component.alliance is None:
            return False

        alliance_component = family_component.alliance.get_component(Alliance)

        for _, (scheme, _, _) in context.world.get_components(
            (Scheme, CoupScheme, Active)
        ):
            scheme_initiator_family = scheme.initiator.get_component(Character).family
            if scheme_initiator_family in alliance_component.member_families:
                return True

        return False


class HasActiveSchemes(AIPrecondition):
    """Evaluates to true if the character is currently involved with any schemes."""

    def evaluate(self, context: AIContext) -> bool:
        return len(context.character.get_component(SchemeManager).schemes) > 0


class IsCurrentlyAtWar(AIPrecondition):
    """Evaluates to true if the character's family is currently involved in a war."""

    def evaluate(self, context: AIContext) -> bool:
        family = context.character.get_component(Character).family

        if family is None:
            return False

        war_tracker = family.get_component(WarTracker)

        return (
            len(war_tracker.offensive_wars) > 0 or len(war_tracker.defensive_wars) > 0
        )


class TerritoriesInRevoltSensor(AISensor):
    """Get all settlements in revolt and write it to the blackboard."""

    def evaluate(self, context: AIContext) -> None:
        # Check if the character is a family head
        territories_in_revolt: list[GameObject] = []

        if family_head_component := context.character.try_component(HeadOfFamily):
            family_component = family_head_component.family.get_component(Family)

            for territory in family_component.territories:
                if territory.has_component(InRevolt):
                    territories_in_revolt.append(territory)

        context.blackboard["territories_in_revolt"] = territories_in_revolt

    def clear_output(self, context: AIContext) -> None:
        if "territories_in_revolt" in context.blackboard:
            del context.blackboard["territories_in_revolt"]


class UnexpandedTerritoriesSensor(AISensor):
    """Get all territories without political foothold that border territories."""

    def evaluate(self, context: AIContext) -> None:
        # Check if the character is a family head
        unexpanded_territories: OrderedSet[GameObject] = OrderedSet([])

        if family_head_component := context.character.try_component(HeadOfFamily):
            family_component = family_head_component.family.get_component(Family)
            for territory in family_component.territories:
                settlement_component = territory.get_component(Settlement)
                for neighboring_territory in settlement_component.neighbors:
                    if neighboring_territory not in family_component.territories:
                        unexpanded_territories.add(neighboring_territory)

        context.blackboard["unexpanded_territories"] = list(unexpanded_territories)

    def clear_output(self, context: AIContext) -> None:
        if "unexpanded_territories" in context.blackboard:
            del context.blackboard["unexpanded_territories"]


class UnControlledTerritoriesSensor(AISensor):
    """Get all territories the family has that don't have a controlling family."""

    def evaluate(self, context: AIContext) -> None:
        # Check if the character is a family head
        uncontrolled_territories: OrderedSet[GameObject] = OrderedSet([])

        if family_head_component := context.character.try_component(HeadOfFamily):
            family_component = family_head_component.family.get_component(Family)

            for territory in family_component.territories:
                settlement_component = territory.get_component(Settlement)
                if settlement_component.controlling_family is None:
                    uncontrolled_territories.add(territory)

        context.blackboard["uncontrolled_territories"] = list(uncontrolled_territories)

    def clear_output(self, context: AIContext) -> None:
        if "uncontrolled_territories" in context.blackboard:
            del context.blackboard["uncontrolled_territories"]


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
                settlement_component = territory.get_component(Settlement)
                if (
                    settlement_component.controlling_family is not None
                    and settlement_component.controlling_family not in allies
                ):
                    enemy_territories.add(territory)

        context.blackboard["enemy_territories"] = list(enemy_territories)

    def clear_output(self, context: AIContext) -> None:
        if "enemy_territories" in context.blackboard:
            del context.blackboard["enemy_territories"]


class MaxUtilActionSelectStrategy(ActionSelectionStrategy):
    """Select the action with the highest utility."""

    __slots__ = ("utility_threshold",)

    utility_threshold: float

    def __init__(self, utility_threshold: float = 0) -> None:
        super().__init__()
        self.utility_threshold = utility_threshold

    def choose_action(self, actions: Iterable[AIAction]) -> AIAction:

        max_utility: float = -999_999
        best_action: Optional[AIAction] = None

        for action in actions:
            utility = action.calculate_utility()

            if utility < self.utility_threshold:
                continue

            if utility > max_utility:
                best_action = action

        if best_action is None:
            raise ValueError(
                "No actions found in list with utility greater than "
                f"{self.utility_threshold}."
            )

        return best_action


class WeightedActionSelectStrategy(ActionSelectionStrategy):
    """PErform weighted random selection using the utility is the weight."""

    __slots__ = ("utility_threshold", "rng")

    utility_threshold: float
    rng: Optional[random.Random]

    def __init__(
        self, utility_threshold: float = 0, rng: Optional[random.Random] = None
    ) -> None:
        super().__init__()
        self.utility_threshold = utility_threshold
        self.rng = rng

    def choose_action(self, actions: Iterable[AIAction]) -> AIAction:
        action_list = [*actions]

        if len(action_list) == 0:
            raise ValueError("No actions provided.")

        # Filter those with weights less than or equal to zero
        filtered_actions: list[AIAction] = []
        filtered_utilities: list[float] = []

        for action in action_list:
            utility = action.calculate_utility()

            if utility < self.utility_threshold:
                continue

            filtered_actions.append(action)
            filtered_utilities.append(utility)

        if len(filtered_actions) == 0:
            raise ValueError("No actions found in list after filtering.")

        if self.rng is not None:
            return self.rng.choices(filtered_actions, filtered_utilities, k=1)[0]
        else:
            return random.choices(filtered_actions, filtered_utilities, k=1)[0]


class MaxUtilBehaviorSelectStrategy(BehaviorSelectionStrategy):
    """Select the behavior with the highest utility."""

    __slots__ = ("utility_threshold",)

    utility_threshold: float

    def __init__(self, utility_threshold: float = 0) -> None:
        super().__init__()
        self.utility_threshold = utility_threshold

    def choose_behavior(
        self, character: GameObject, behaviors: Iterable[AIBehavior]
    ) -> AIBehavior:

        max_utility: float = -999_999
        best_behavior: Optional[AIBehavior] = None

        for behavior in behaviors:
            utility = behavior.calculate_utility(character)

            if utility < self.utility_threshold:
                continue

            if utility > max_utility:
                best_behavior = behavior

        if best_behavior is None:
            raise ValueError(
                "No actions found in list with utility greater than "
                f"{self.utility_threshold}."
            )

        return best_behavior


class WeightedBehaviorSelectStrategy(BehaviorSelectionStrategy):
    """PErform weighted random selection using the utility is the weight."""

    __slots__ = ("utility_threshold", "rng", "top_n")

    utility_threshold: float
    rng: Optional[random.Random]
    top_n: int

    def __init__(
        self,
        utility_threshold: float = 0,
        rng: Optional[random.Random] = None,
        top_n: int = 10,
    ) -> None:
        super().__init__()
        self.utility_threshold = utility_threshold
        self.rng = rng
        self.top_n = top_n

    def choose_behavior(
        self, character: GameObject, behaviors: Iterable[AIBehavior]
    ) -> AIBehavior:
        behavior_list = [*behaviors]

        if len(behavior_list) == 0:
            raise ValueError("No actions provided.")

        # Filter those with weights less than or equal to zero
        filtered_behaviors: list[AIBehavior] = []
        filtered_utilities: list[float] = []

        for behavior in behavior_list:
            utility = behavior.calculate_utility(character)

            if utility < self.utility_threshold:
                continue

            filtered_behaviors.append(behavior)
            filtered_utilities.append(utility)

        if len(filtered_behaviors) == 0:
            raise ValueError("No actions found in list after filtering.")

        if self.rng is not None:
            return self.rng.choices(filtered_behaviors, filtered_utilities, k=1)[0]
        else:
            return random.choices(filtered_behaviors, filtered_utilities, k=1)[0]
