"""General Life Events."""

from minerva.ecs import Entity
from minerva.life_events.base_types import LifeEvent


class MarriageEvent(LifeEvent):
    """Event dispatched when a character gets married."""

    def __init__(self, subject: Entity, spouse: Entity) -> None:
        super().__init__("Marriage", subject)
        self.event_args["spouse_name"] = spouse.name
        self.event_args["spouse_id"] = str(spouse.uid)


class PregnancyEvent(LifeEvent):
    """Event dispatched when a character gets pregnant."""

    def __init__(self, subject: Entity) -> None:
        super().__init__("Pregnancy", subject)


class ChildBirthEvent(LifeEvent):
    """Event dispatched when a character gives birth to another."""

    def __init__(self, subject: Entity, child: Entity) -> None:
        super().__init__("ChildBirth", subject)
        self.event_args["child_name"] = child.name
        self.event_args["child_id"] = str(child.uid)


class BirthEvent(LifeEvent):
    """Event dispatched when a character is born."""

    def __init__(self, subject: Entity) -> None:
        super().__init__("Birth", subject)


class TakeOverTerritoryEvent(LifeEvent):
    """Event dispatched when a family head seizes power over a territory."""

    def __init__(self, subject: Entity, territory: Entity, family: Entity) -> None:
        super().__init__("TakeOverTerritory", subject)
        self.event_args["territory_name"] = territory.name
        self.event_args["territory_id"] = str(territory.uid)
        self.event_args["family_name"] = family.name
        self.event_args["family_id"] = str(family.uid)


class ExpandedFamilyTerritoryEvent(LifeEvent):
    """Logs a person expanding the territory of their family."""

    def __init__(self, subject: Entity, family: Entity, territory: Entity) -> None:
        super().__init__("ExpandedFamilyTerritory", subject)
        self.event_args["family_name"] = family.name
        self.event_args["family_id"] = str(family.uid)
        self.event_args["territory_name"] = territory.name
        self.event_args["territory_id"] = str(territory.uid)


class DisbandedAllianceEvent(LifeEvent):
    """Logs a character disbanding their alliance."""

    def __init__(self, subject: Entity, alliance: Entity) -> None:
        super().__init__("DisbandedAlliance", subject)
        self.event_args["alliance_id"] = str(alliance.uid)


class LeftDisbandedAllianceEvent(LifeEvent):
    """Logs a family head leaving their alliance after it is disbanded."""

    def __init__(self, subject: Entity, alliance: Entity) -> None:
        super().__init__("LeftDisbandedAlliance", subject)
        self.event_args["alliance_id"] = str(alliance.uid)


class JoinedAllianceEvent(LifeEvent):
    """Logs a character bringing their family into an alliance."""

    def __init__(self, subject: Entity, alliance: Entity) -> None:
        super().__init__("JoinedAlliance", subject)
        self.event_args["alliance_id"] = str(alliance.uid)


class FamilyJoinedAllianceEvent(LifeEvent):
    """Logs a family joining an alliance."""

    def __init__(self, subject: Entity, alliance: Entity) -> None:
        super().__init__("FamilyJoinedAlliance", subject)
        self.event_args["alliance_id"] = str(alliance.uid)


class AttemptingFormAllianceEvent(LifeEvent):
    """Logs a character attempting to form an alliance."""

    def __init__(self, subject: Entity) -> None:
        super().__init__("AttemptingFormAlliance", subject)


class JoinAllianceSchemeEvent(LifeEvent):
    """Logs a character joining someone's alliance scheme."""

    def __init__(self, subject: Entity, scheme_initiator: Entity) -> None:
        super().__init__("JoinAllianceScheme", subject)
        self.event_args["initiator_id"] = str(scheme_initiator.uid)
        self.event_args["initiator_name"] = scheme_initiator.name


class GiveBackToSmallFolkEvent(LifeEvent):
    """Logs a character giving back to the small folk of a territory."""

    def __init__(self, subject: Entity, territory: Entity) -> None:
        super().__init__("GiveBackToSmallFolk", subject)
        self.event_args["territory_name"] = territory.name
        self.event_args["territory_id"] = str(territory.uid)


class GrowPoliticalInfluenceEvent(LifeEvent):
    """Logs a character increasing the political influence of their family."""

    def __init__(self, subject: Entity, family: Entity, territory: Entity) -> None:
        super().__init__("GrowPoliticalInfluence", subject)
        self.event_args["family_name"] = family.name
        self.event_args["family_id"] = str(family.uid)
        self.event_args["territory_name"] = territory.name
        self.event_args["territory_id"] = str(territory.uid)


class JoinCoupSchemeEvent(LifeEvent):
    """Logs a character joining someone's coup scheme."""

    def __init__(self, subject: Entity, scheme_initiator: Entity) -> None:
        super().__init__("JoinCoupScheme", subject)
        self.event_args["initiator_id"] = str(scheme_initiator.uid)
        self.event_args["initiator_name"] = scheme_initiator.name


class StartCoupSchemeEvent(LifeEvent):
    """Logs a character attempting to overthrow the current ruler."""

    def __init__(self, subject: Entity, ruler: Entity) -> None:
        super().__init__("StartCoupScheme", subject)
        self.event_args["ruler_name"] = ruler.name
        self.event_args["ruler_id"] = str(ruler.uid)


class LostTerritoryEvent(LifeEvent):
    """Logs when a family head loses control over a territory."""

    def __init__(self, subject: Entity, territory: Entity) -> None:
        super().__init__("LostTerritory", subject)
        self.event_args["territory_name"] = territory.name
        self.event_args["territory_id"] = str(territory.uid)


class RemovedFromPowerEvent(LifeEvent):
    """Logs when a family is removed from power over a territory."""

    def __init__(self, subject: Entity, territory: Entity) -> None:
        super().__init__("RemovedFromPower", subject)
        self.event_args["territory_name"] = territory.name
        self.event_args["territory_id"] = str(territory.uid)


class StartWarSchemeEvent(LifeEvent):
    """Logs a character starting a war scheme."""

    def __init__(self, subject: Entity, target: Entity, territory: Entity) -> None:
        super().__init__("StartWarScheme", subject)
        self.event_args["target_name"] = target.name
        self.event_args["target_id"] = str(target.uid)
        self.event_args["territory_name"] = territory.name
        self.event_args["territory_id"] = str(territory.uid)


class DeclareWarEvent(LifeEvent):
    """Logs a character officially declaring war against another."""

    def __init__(self, subject: Entity, target: Entity, territory: Entity) -> None:
        super().__init__("DeclareWar", subject)
        self.event_args["target_name"] = target.name
        self.event_args["target_id"] = str(target.uid)
        self.event_args["territory_name"] = territory.name
        self.event_args["territory_id"] = str(territory.uid)


class DefendingTerritoryEvent(LifeEvent):
    """Logs a character defending territory from another who has declared war."""

    def __init__(self, subject: Entity, opponent: Entity, territory: Entity) -> None:
        super().__init__("DefendingTerritory", subject)
        self.event_args["opponent_name"] = opponent.name
        self.event_args["opponent_id"] = str(opponent.uid)
        self.event_args["territory_name"] = territory.name
        self.event_args["territory_id"] = str(territory.uid)


class QuellRevoltEvent(LifeEvent):
    """Logs a character quelling a revolt as head of the family."""

    def __init__(self, subject: Entity, territory: Entity) -> None:
        super().__init__("QuellRevolt", subject)
        self.event_args["territory_name"] = territory.name
        self.event_args["territory_id"] = str(territory.uid)


class TaxTerritoryEvent(LifeEvent):
    """Logs a character taxing a territory as head of the family."""

    def __init__(self, subject: Entity, territory: Entity) -> None:
        super().__init__("TaxTerritory", subject)
        self.event_args["territory_name"] = territory.name
        self.event_args["territory_id"] = str(territory.uid)


class RevoltEvent(LifeEvent):
    """Logs a territory revolting against a family."""

    def __init__(self, subject: Entity, territory: Entity) -> None:
        super().__init__("Revolt", subject)
        self.event_args["territory_name"] = territory.name
        self.event_args["territory_id"] = str(territory.uid)


class WarLostEvent(LifeEvent):
    """Logs a character losing a war."""

    def __init__(self, subject: Entity, winner: Entity, territory: Entity) -> None:
        super().__init__("WarLost", subject)
        self.event_args["winner_name"] = winner.name
        self.event_args["winner_id"] = str(winner.uid)
        self.event_args["territory_name"] = territory.name
        self.event_args["territory_id"] = str(territory.uid)


class WarWonEvent(LifeEvent):
    """Logs a character wining a war."""

    def __init__(self, subject: Entity, loser: Entity, territory: Entity) -> None:
        super().__init__("WarWon", subject)
        self.event_args["loser_name"] = loser.name
        self.event_args["loser_id"] = str(loser.uid)
        self.event_args["territory_name"] = territory.name
        self.event_args["territory_id"] = str(territory.uid)


class AllianceSchemeFailedEvent(LifeEvent):
    """Logs when a character fails to start a new alliance."""

    def __init__(self, subject: Entity) -> None:
        super().__init__("AllianceSchemeFailed", subject)


class AllianceFoundedEvent(LifeEvent):
    """Logs when a character successfully starts a new alliance."""

    def __init__(self, subject: Entity, alliance: Entity) -> None:
        super().__init__("AllianceFounded", subject)
        self.event_args["alliance_id"] = str(alliance.uid)


class CoupSchemeDiscoveredEvent(LifeEvent):
    """Logs when a character's coup scheme is discovered."""

    def __init__(self, subject: Entity) -> None:
        super().__init__("CoupSchemeDiscovered", subject)


class SentencedToDeathEvent(LifeEvent):
    """Logs when a character is sentenced to death for a failed coup."""

    def __init__(self, subject: Entity, reason: str) -> None:
        super().__init__("SentencedToDeath", subject)
        self.event_args["reason"] = reason


class RuleOverthrownEvent(LifeEvent):
    """Logs when a character is overthrown by another."""

    def __init__(self, subject: Entity, usurper: Entity) -> None:
        super().__init__("RuleOverthrown", subject)
        self.event_args["usurper_name"] = usurper.name
        self.event_args["usurper_id"] = str(usurper.uid)


class UsurpEvent(LifeEvent):
    """Logs when a character usurps another for the thrown."""

    def __init__(self, subject: Entity, former_ruler: Entity) -> None:
        super().__init__("Usurp", subject)
        self.event_args["former_ruler_name"] = former_ruler.name
        self.event_args["former_ruler_id"] = str(former_ruler.uid)


class CheatOnSpouseEvent(LifeEvent):
    """Logs when a character cheats on their spouse."""

    def __init__(self, subject: Entity, spouse: Entity, accomplice: Entity) -> None:
        super().__init__("CheatOnSpouse", subject)
        self.event_args["spouse_name"] = spouse.name
        self.event_args["spouse_id"] = str(spouse.uid)
        self.event_args["accomplice_name"] = accomplice.name
        self.event_args["accomplice_id"] = str(accomplice.uid)
