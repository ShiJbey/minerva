"""Preconditions for character behaviors.

"""

from __future__ import annotations

from minerva.actions.base_types import AIPrecondition, AIContext, Scheme, SchemeManager
from minerva.actions.scheme_helpers import get_character_schemes_of_type
from minerva.actions.scheme_types import CoupScheme
from minerva.characters.components import HeadOfFamily, Character, Family, Emperor
from minerva.characters.war_data import Alliance, WarTracker
from minerva.ecs import GameObject, Active


class IsFamilyHeadPrecondition(AIPrecondition):
    """Check that the character is head of a family."""

    def evaluate(self, context: AIContext) -> bool:
        return context.character.has_component(HeadOfFamily)


class HasTerritoriesInRevolt(AIPrecondition):
    """Checks if the character has any territories in revolt."""

    def evaluate(self, context: AIContext) -> bool:
        territories: list[GameObject] = context.get_value("territories_in_revolt", [])
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
