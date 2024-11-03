"""Action Considerations."""

from minerva.actions.base_types import AIContext, AIUtilityConsideration, Scheme
from minerva.characters.components import (
    Boldness,
    Character,
    Compassion,
    Diplomacy,
    Dynasty,
    DynastyTracker,
    Greed,
    Honor,
    Intrigue,
    Martial,
    Rationality,
    Stewardship,
)
from minerva.ecs import GameObject
from minerva.relationships.base_types import Opinion
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
        return 1.0
