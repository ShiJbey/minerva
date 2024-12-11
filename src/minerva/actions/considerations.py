"""Action Considerations."""

from minerva.actions.base_types import AIContext, AIUtilityConsideration, Scheme
from minerva.characters.components import (
    Boldness,
    Character,
    Compassion,
    Diplomacy,
    Dynasty,
    DynastyTracker,
    Family,
    Greed,
    Honor,
    Intrigue,
    Martial,
    Rationality,
    Stewardship,
)
from minerva.characters.war_data import Alliance
from minerva.ecs import GameObject
from minerva.relationships.base_types import Attraction, Opinion
from minerva.relationships.helpers import get_relationship


class OpinionOfRecipientCons(AIUtilityConsideration):
    """Consider the relationship to the recipient when giving something."""

    def evaluate(self, context: AIContext) -> float:
        sender = context.character
        recipient: GameObject = context["recipient"]
        return get_relationship(sender, recipient).get_component(Opinion).normalized


class OpinionOfTargetCons(AIUtilityConsideration):
    """Consider the relationship to the target of the action."""

    def evaluate(self, context: AIContext) -> float:
        sender = context.character
        target: GameObject = context["target"]
        return get_relationship(sender, target).get_component(Opinion).normalized


class OpinionOfSchemeInitiatorCons(AIUtilityConsideration):
    """Consider a character's opinion of the scheme initiator."""

    def evaluate(self, context: AIContext) -> float:
        scheme: GameObject = context["scheme"]
        scheme_component = scheme.get_component(Scheme)
        character = context.character
        return (
            get_relationship(character, scheme_component.initiator)
            .get_component(Opinion)
            .normalized
        )


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


class IntrigueConsideration(AIUtilityConsideration):
    """A consideration of a character's intrigue stat."""

    def evaluate(self, context: AIContext) -> float:
        return context.character.get_component(Intrigue).normalized


class InfluencePointGoalConsideration(AIUtilityConsideration):
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
                    .get_component(Opinion)
                    .normalized
                )

        return 0


class OpinionOfAllianceLeader(AIUtilityConsideration):
    """A consideration for how characters feel about the leader of their alliance."""

    def evaluate(self, context: AIContext) -> float:
        character_component = context.character.get_component(Character)

        family = character_component.family

        if family is None:
            return -1

        family_component = family.get_component(Family)

        alliance = family_component.alliance

        if alliance is None:
            return -1

        alliance_component = alliance.get_component(Alliance)

        alliance_family_head = alliance_component.founder_family.get_component(
            Family
        ).head

        if alliance_family_head is not None:
            return (
                get_relationship(context.character, alliance_family_head)
                .get_component(Opinion)
                .normalized
            )

        else:
            return -1


class OpinionOfSpouse(AIUtilityConsideration):
    """A consideration of how a character feels about their spouse."""

    def evaluate(self, context: AIContext) -> float:
        character_component = context.character.get_component(Character)

        spouse = character_component.spouse

        if spouse is None:
            return -1

        return (
            get_relationship(context.character, spouse)
            .get_component(Opinion)
            .normalized
        )


class AttractionToSpouse(AIUtilityConsideration):
    """A consideration of how attracted a character is to their spouse."""

    def evaluate(self, context: AIContext) -> float:
        character_component = context.character.get_component(Character)

        spouse = character_component.spouse

        if spouse is None:
            return -1

        return (
            get_relationship(context.character, spouse)
            .get_component(Attraction)
            .normalized
        )


class AttractionToTarget(AIUtilityConsideration):
    """A consideration of how attracted a character is to a character."""

    __slots__ = ("context_key",)

    context_key: str

    def __init__(self, context_key: str) -> None:
        super().__init__()
        self.context_key = context_key

    def evaluate(self, context: AIContext) -> float:
        target: GameObject = context[self.context_key]

        return (
            get_relationship(context.character, target)
            .get_component(Attraction)
            .normalized
        )


class OpinionOfTarget(AIUtilityConsideration):
    """A consideration of a character's opinion of another."""

    __slots__ = ("context_key",)

    context_key: str

    def __init__(self, context_key: str) -> None:
        super().__init__()
        self.context_key = context_key

    def evaluate(self, context: AIContext) -> float:
        target: GameObject = context[self.context_key]

        return (
            get_relationship(context.character, target)
            .get_component(Opinion)
            .normalized
        )
