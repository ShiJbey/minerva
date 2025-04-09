"""Preconditions for character behaviors."""

from __future__ import annotations

from minerva.actions.base_types import AIPrecondition, CharacterController
from minerva.actions.scheme_types import AllianceScheme, CoupScheme, SchemeManager
from minerva.characters.components import Character, Family, HeadOfFamily, Ruler
from minerva.characters.war_data import Alliance, WarTracker
from minerva.ecs import Active, Entity


class IsFamilyHeadPrecondition(AIPrecondition):
    """Check that the character is head of a family."""

    def __call__(self, entity: Entity) -> bool:
        return entity.has_component(HeadOfFamily)


class HasTerritoriesInRevolt(AIPrecondition):
    """Checks if the character has any territories in revolt."""

    def __call__(self, entity: Entity) -> bool:
        blackboard = entity.get_component(CharacterController).blackboard
        territories: list[Entity] = blackboard.get("territories_in_revolt", [])
        return bool(territories)


class FamilyInAlliancePrecondition(AIPrecondition):
    """Check if the character's family belongs to an alliance."""

    def __call__(self, entity: Entity) -> bool:
        character_component = entity.get_component(Character)
        family = character_component.family

        if family is None:
            return False

        family_component = family.get_component(Family)

        return family_component.alliance is not None


class JoinedAllianceScheme(AIPrecondition):
    """Evaluates to true if the character has already joined an alliance scheme."""

    def __call__(self, entity: Entity) -> bool:
        scheme_manager = entity.get_component(SchemeManager)
        return scheme_manager.alliance_scheme is not None


class AreAllianceSchemesActive(AIPrecondition):
    """Evaluate to True if there are alliance schemes available to join."""

    def __call__(self, entity: Entity) -> bool:
        alliance_schemes: list[AllianceScheme] = []

        for _, (scheme, _) in entity.world.query_components((AllianceScheme, Active)):
            alliance_schemes.append(scheme)

        return len(alliance_schemes) > 0


class AreAlliancesActive(AIPrecondition):
    """Evaluate to True if there are alliances available to join."""

    def __call__(self, entity: Entity) -> bool:
        return len(list(entity.world.query_components((Alliance, Active)))) > 0


class IsRulerPrecondition(AIPrecondition):
    """Evaluates to true if the character is the current ruler."""

    def __call__(self, entity: Entity) -> bool:
        return entity.has_component(Ruler)


class AreCoupSchemesActive(AIPrecondition):
    """Evaluates to True when there are active coup schemes."""

    def __call__(self, entity: Entity) -> bool:
        return len(list(entity.world.query_components((CoupScheme, Active)))) > 0


class IsAllianceMemberPlottingCoup(AIPrecondition):
    """Returns true if an alliance member is plotting a coup."""

    def __call__(self, entity: Entity) -> bool:
        family = entity.get_component(Character).family

        if family is None:
            return False

        family_component = family.get_component(Family)

        if family_component.alliance is None:
            return False

        alliance_component = family_component.alliance.get_component(Alliance)

        for _, (coup_scheme, _) in entity.world.query_components((CoupScheme, Active)):
            scheme_initiator_family = coup_scheme.initiator.get_component(
                Character
            ).family
            if scheme_initiator_family in alliance_component.member_families:
                return True

        return False


class HasControlledTerritories(AIPrecondition):
    """Returns True if a character's family controls territories."""

    def __call__(self, entity: Entity) -> bool:
        family = entity.get_component(Character).family

        if family is None:
            return False

        family_component = family.get_component(Family)

        return len(family_component.controlled_territories) > 0


class HasActiveSchemes(AIPrecondition):
    """Evaluates to true if the character is currently involved with any schemes."""

    def __call__(self, entity: Entity) -> bool:
        scheme_manager = entity.get_component(SchemeManager)
        return (
            scheme_manager.alliance_scheme is not None
            or scheme_manager.war_scheme is not None
            or scheme_manager.coup_scheme is not None
        )


class IsCurrentlyAtWar(AIPrecondition):
    """Evaluates to true if the character's family is currently involved in a war."""

    def __call__(self, entity: Entity) -> bool:
        family = entity.get_component(Character).family

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

    def __call__(self, entity: Entity) -> bool:
        return any(p(entity) for p in self.preconditions)


class Not(AIPrecondition):
    """Groups preconditions together and returns true if any evaluate to True."""

    __slots__ = ("precondition",)

    precondition: AIPrecondition

    def __init__(self, precondition: AIPrecondition) -> None:
        super().__init__()
        self.precondition = precondition

    def __call__(self, entity: Entity) -> bool:
        return not self.precondition(entity)
