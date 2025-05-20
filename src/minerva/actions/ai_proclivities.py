"""Action Proclivity Considerations."""

from minerva.actions.base_types import AIAction, IProclivity
from minerva.characters.components import (
    SKILL_MAX,
    Character,
    Dynasty,
    DynastyTracker,
    Family,
)
from minerva.characters.helpers import (
    get_diplomacy_skill,
    get_intrigue_skill,
    get_martial_skill,
    get_stewardship_skill,
)
from minerva.characters.war_data import Alliance
from minerva.ecs import Entity
from minerva.relationships.base_types import (
    ATTRACTION_EXCELLENT,
    ATTRACTION_GOOD,
    ATTRACTION_NEUTRAL,
    ATTRACTION_POOR,
    OPINION_EXCELLENT,
    OPINION_GOOD,
    OPINION_NEUTRAL,
    OPINION_POOR,
)
from minerva.relationships.helpers import get_attraction, get_opinion


def opinion_to_proclivity(opinion: int) -> int:
    """Convert opinion score to a proclivity score."""
    if opinion >= OPINION_EXCELLENT:
        return 5
    elif opinion >= OPINION_GOOD:
        return 3
    elif opinion >= OPINION_NEUTRAL:
        return 0
    elif opinion >= OPINION_POOR:
        return -3
    else:
        return -5


def attraction_to_proclivity(opinion: int) -> int:
    """Convert opinion score to a proclivity score."""
    if opinion >= ATTRACTION_EXCELLENT:
        return 5
    elif opinion >= ATTRACTION_GOOD:
        return 3
    elif opinion >= ATTRACTION_NEUTRAL:
        return 0
    elif opinion >= ATTRACTION_POOR:
        return -3
    else:
        return -5


class OpinionOfRecipientCons(IProclivity):
    """Consider the relationship to the recipient when giving something."""

    def __call__(self, action: AIAction) -> int:
        sender = action.initiator
        recipient: Entity = action.context["recipient"]
        opinion_value = get_opinion(sender, recipient)
        score = opinion_to_proclivity(opinion_value)
        return score


class OpinionOfTargetCons(IProclivity):
    """Consider the relationship to the target of the action."""

    def __call__(self, action: AIAction) -> int:
        sender = action.initiator
        target: Entity = action.context["target"]
        opinion = get_opinion(sender, target)
        score = opinion_to_proclivity(opinion)
        return score


class StewardshipConsideration(IProclivity):
    """A consideration of a character's stewardship stat."""

    def __call__(self, action: AIAction) -> int:
        skill_value = get_stewardship_skill(action.initiator)
        score = int(5 * float(skill_value) / SKILL_MAX)
        return score


class DiplomacyConsideration(IProclivity):
    """A consideration of a character's diplomacy stat."""

    def __call__(self, action: AIAction) -> int:
        skill_value = get_diplomacy_skill(action.initiator)
        score = int(5 * float(skill_value) / SKILL_MAX)
        return score


class MartialConsideration(IProclivity):
    """A consideration of a character's martial stat."""

    def __call__(self, action: AIAction) -> int:
        skill_value = get_martial_skill(action.initiator)
        score = int(5 * float(skill_value) / SKILL_MAX)
        return score


class IntrigueConsideration(IProclivity):
    """A consideration of a character's intrigue stat."""

    def __call__(self, action: AIAction) -> int:
        skill_value = get_intrigue_skill(action.initiator)
        score = int(5 * float(skill_value) / SKILL_MAX)
        return score


class InfluencePointGoalConsideration(IProclivity):
    """A consideration for influence points up to a given saturation value.

    As the number of influence points get closer to the target value, the
    consideration score increases.
    """

    __slots__ = ("target_value",)

    target_value: int

    def __init__(self, saturation_value: int) -> None:
        super().__init__()
        self.target_value = saturation_value

    def __call__(self, action: AIAction) -> int:
        influence_points = action.initiator.get_component(Character).influence_points
        consideration_score = min(1.0, float(influence_points) / self.target_value)
        proclivity_score = int(5 * consideration_score)
        return proclivity_score


class OpinionOfRulerConsideration(IProclivity):
    """A consideration of the characters opinion of the ruler (if applicable)."""

    def __call__(self, action: AIAction) -> int:
        world = action.world
        dynasty_tracker = world.get_resource(DynastyTracker)

        if dynasty_tracker.current_dynasty is None:
            return 0

        dynasty_component = dynasty_tracker.current_dynasty.get_component(Dynasty)

        if dynasty_component.current_ruler is not None:
            if action.initiator == dynasty_component.current_ruler:
                return 1
            else:
                opinion = get_opinion(action.initiator, dynasty_component.current_ruler)
                score = opinion_to_proclivity(opinion)
                return score

        return 0


class OpinionOfAllianceLeader(IProclivity):
    """A consideration for how characters feel about the leader of their alliance."""

    def __call__(self, action: AIAction) -> int:
        character_component = action.initiator.get_component(Character)

        family = character_component.family

        if family is None:
            return 0

        family_component = family.get_component(Family)

        alliance = family_component.alliance

        if alliance is None:
            return 0

        alliance_component = alliance.get_component(Alliance)

        alliance_family_head = alliance_component.founder_family.get_component(
            Family
        ).head

        if alliance_family_head is not None:
            opinion = get_opinion(action.initiator, alliance_family_head)
            score = opinion_to_proclivity(opinion)
            return score

        else:
            return 0


class OpinionOfSpouse(IProclivity):
    """A consideration of how a character feels about their spouse."""

    def __call__(self, action: AIAction) -> int:
        character_component = action.initiator.get_component(Character)

        spouse = character_component.spouse

        if spouse is None:
            return 0

        opinion = get_opinion(action.initiator, spouse)
        score = opinion_to_proclivity(opinion)
        return score


class AttractionToSpouse(IProclivity):
    """A consideration of how attracted a character is to their spouse."""

    def __call__(self, action: AIAction) -> int:
        character_component = action.initiator.get_component(Character)

        spouse = character_component.spouse

        if spouse is None:
            return 0

        attraction = get_attraction(action.initiator, spouse)
        score = attraction_to_proclivity(attraction)
        return score


class AttractionToTarget(IProclivity):
    """A consideration of how attracted a character is to a character."""

    __slots__ = ("context_key",)

    context_key: str

    def __init__(self, context_key: str) -> None:
        super().__init__()
        self.context_key = context_key

    def __call__(self, action: AIAction) -> int:
        target: Entity = action.context[self.context_key]
        attraction = get_attraction(action.initiator, target)
        score = attraction_to_proclivity(attraction)
        return score


class OpinionOfTarget(IProclivity):
    """A consideration of a character's opinion of another."""

    __slots__ = ("context_key",)

    context_key: str

    def __init__(self, context_key: str) -> None:
        super().__init__()
        self.context_key = context_key

    def __call__(self, action: AIAction) -> int:
        target: Entity = action.context[self.context_key]
        opinion = get_opinion(action.initiator, target)
        score = opinion_to_proclivity(opinion)
        return score
