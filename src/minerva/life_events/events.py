"""General Life Events."""

from minerva.ecs import Entity
from minerva.life_events.base_types import LifeEvent
from minerva.sim_db import SimDB


class MarriageEvent(LifeEvent):
    """Event dispatched when a character gets married."""

    __slots__ = ("spouse",)

    spouse: Entity

    def __init__(self, subject: Entity, spouse: Entity) -> None:
        super().__init__(subject)
        self.spouse = spouse

    def get_event_type(self) -> str:
        return "Marriage"

    def on_event_logged(self) -> None:
        db = self.world.get_resource(SimDB).db
        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO marriage_events (event_id, character_id, spouse_id, timestamp)
            VALUES (?, ?, ?, ?);
            """,
            (
                self.event_id,
                self.subject.uid,
                self.spouse.uid,
                self.timestamp.to_iso_str(),
            ),
        )
        db.commit()

    def get_description(self) -> str:
        return f"{self.subject.name_with_uid} married {self.spouse.name_with_uid}."


class PregnancyEvent(LifeEvent):
    """Event dispatched when a character gets pregnant."""

    def get_event_type(self) -> str:
        return "Pregnancy"

    def on_event_logged(self) -> None:
        db = self.world.get_resource(SimDB).db
        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO pregnancy_events (event_id, character_id, timestamp)
            VALUES (?, ?, ?);
            """,
            (
                self.event_id,
                self.subject.uid,
                self.timestamp.to_iso_str(),
            ),
        )
        db.commit()

    def get_description(self) -> str:
        return f"{self.subject.name_with_uid} became pregnant."


class ChildBirthEvent(LifeEvent):
    """Event dispatched when a character gives birth to another."""

    __slots__ = ("child",)

    child: Entity

    def __init__(self, subject: Entity, child: Entity) -> None:
        super().__init__(subject)
        self.child = child

    def get_event_type(self) -> str:
        return "ChildBirth"

    def on_event_logged(self) -> None:
        db = self.world.get_resource(SimDB).db
        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO give_birth_events (event_id, character_id, child_id, timestamp)
            VALUES (?, ?, ?, ?);
            """,
            (
                self.event_id,
                self.subject.uid,
                self.child.uid,
                self.timestamp.to_iso_str(),
            ),
        )
        db.commit()

    def get_description(self) -> str:
        return f"{self.subject.name_with_uid} gave birth to {self.child.name_with_uid}."


class BirthEvent(LifeEvent):
    """Event dispatched when a character is born."""

    def get_event_type(self) -> str:
        return "Birth"

    def on_event_logged(self) -> None:
        db = self.world.get_resource(SimDB).db
        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO born_events (event_id, character_id, timestamp)
            VALUES (?, ?, ?);
            """,
            (
                self.event_id,
                self.subject.uid,
                self.timestamp.to_iso_str(),
            ),
        )
        db.commit()

    def get_description(self) -> str:
        return f"{self.subject.name_with_uid} was born."


class TakeOverTerritoryEvent(LifeEvent):
    """Event dispatched when a family head seizes power over a territory."""

    __slots__ = ("territory", "family")

    territory: Entity
    family: Entity

    def __init__(self, subject: Entity, territory: Entity, family: Entity) -> None:
        super().__init__(subject)
        self.territory = territory
        self.family = family

    def get_event_type(self) -> str:
        return "TakeOverTerritory"

    def on_event_logged(self) -> None:
        # db = self.world.get_resource(SimDB).db
        # cur = db.cursor()
        # cur.execute(
        #     """
        #     INSERT INTO life_events (event_id, event_type, timestamp, description)
        #     VALUES (?, ?, ?, ?);
        #     """,
        #     (
        #         self.event_id,
        #         self.event_type,
        #         self.timestamp.to_iso_str(),
        #         self.get_description(),
        #     ),
        # )
        # cur.execute(
        #     """
        #     INSERT INTO born_events (event_id, character_id, timestamp)
        #     VALUES (?, ?, ?);
        #     """,
        #     (
        #         self.event_id,
        #         self.character.uid,
        #         self.timestamp.to_iso_str(),
        #     ),
        # )
        # db.commit()
        pass

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} took control of the "
            f"{self.territory.name_with_uid} territory for the "
            f"{self.family.name_with_uid} family."
        )


class ExpandedTerritoryEvent(LifeEvent):
    """Logs a family expanding their territory."""

    __slots__ = ("territory",)

    territory: Entity

    def __init__(self, subject: Entity, territory: Entity) -> None:
        super().__init__(subject)
        self.territory = territory

    def get_event_type(self) -> str:
        return "ExpandedTerritory"

    def on_event_logged(self) -> None:
        return

    def get_description(self) -> str:
        return (
            f"The {self.subject.name_with_uid} family expanded into the "
            f"{self.territory.name_with_uid} territory."
        )


class ExpandedFamilyTerritoryEvent(LifeEvent):
    """Logs a person expanding the territory of their family."""

    __slots__ = ("family", "territory")

    family: Entity
    territory: Entity

    def __init__(self, subject: Entity, family: Entity, territory: Entity) -> None:
        super().__init__(subject)
        self.family = family
        self.territory = territory

    def get_event_type(self) -> str:
        return "ExpandedFamilyTerritory"

    def on_event_logged(self) -> None:
        return

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} expanded the "
            f"{self.family.name_with_uid} family into the "
            f"{self.territory.name_with_uid} territory."
        )


class DisbandedAllianceEvent(LifeEvent):
    """Logs a character disbanding their alliance."""

    __slots__ = ("founding_family",)

    founding_family: Entity

    def __init__(self, subject: Entity, founding_family: Entity) -> None:
        super().__init__(subject)
        self.founding_family = founding_family

    def get_event_type(self) -> str:
        return "DisbandedAlliance"

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} has disbanded the alliance started by "
            f"the {self.founding_family.name_with_uid} family."
        )


class LeftDisbandedAllianceEvent(LifeEvent):
    """Logs a family head leaving their alliance after it is disbanded."""

    __slots__ = ("alliance",)

    alliance: Entity

    def __init__(self, subject: Entity, alliance: Entity) -> None:
        super().__init__(subject)
        self.alliance = alliance

    def get_event_type(self) -> str:
        return "LeftDisbandedAllianceEvent"

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} left their Alliance ({self.alliance.uid}) "
            "after it was disbanded."
        )


class FamilyLeftAllianceEvent(LifeEvent):
    """Logs a family leaving and alliance."""


class JoinedAllianceEvent(LifeEvent):
    """Logs a character bringing their family into an alliance."""

    __slots__ = ("alliance",)

    alliance: Entity

    def __init__(self, subject: Entity, alliance: Entity) -> None:
        super().__init__(subject)
        self.alliance = alliance

    def get_event_type(self) -> str:
        return "JoinedAlliance"

    def get_description(self) -> str:
        return f"{self.subject.name_with_uid} joined Alliance ({self.alliance.uid})."


class FamilyJoinedAllianceEvent(LifeEvent):
    """Logs a family joining an alliance."""

    __slots__ = ("alliance",)

    alliance: Entity

    def __init__(self, subject: Entity, alliance: Entity) -> None:
        super().__init__(subject)
        self.alliance = alliance

    def get_event_type(self) -> str:
        return "FamilyJoinedAlliance"

    def get_description(self) -> str:
        return (
            f"The {self.subject.name_with_uid} family joined the "
            f"{self.alliance.name} alliance."
        )


class AttemptingFormAllianceEvent(LifeEvent):
    """Logs a character attempting to form an alliance."""

    def get_event_type(self) -> str:
        return "AttemptingFormAlliance"

    def get_description(self) -> str:
        return f"{self.subject.name_with_uid} is attempting to form a new alliance."


class JoinAllianceSchemeEvent(LifeEvent):
    """Logs a character joining someone's alliance scheme."""

    __slots__ = ("scheme_initiator",)

    scheme_initiator: Entity

    def __init__(self, subject: Entity, scheme_initiator: Entity) -> None:
        super().__init__(subject)
        self.scheme_initiator = scheme_initiator

    def get_event_type(self) -> str:
        return "JoinAllianceScheme"

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} joined "
            f"{self.scheme_initiator.name_with_uid}'s alliance scheme."
        )


class GiveBackToSmallFolkEvent(LifeEvent):
    """Logs a character giving back to the small folk of a territory."""

    __slots__ = ("territory",)

    territory: Entity

    def __init__(self, subject: Entity, territory: Entity) -> None:
        super().__init__(subject)
        self.territory = territory

    def get_event_type(self) -> str:
        return "GiveBackToSmallFolk"

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} gave back to the small folk of the "
            f"{self.territory.name_with_uid} territory."
        )


class GrowPoliticalInfluenceEvent(LifeEvent):
    """Logs a character increasing the political influence of their family."""

    __slots__ = ("family", "territory")

    family: Entity
    territory: Entity

    def __init__(self, subject: Entity, family: Entity, territory: Entity) -> None:
        super().__init__(subject)
        self.family = family
        self.territory = territory

    def get_event_type(self) -> str:
        return "GrowPoliticalInfluence"

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} grew the political influence of the "
            f"{self.family.name_with_uid} family in the "
            f"{self.territory.name_with_uid} territory."
        )


class JoinCoupSchemeEvent(LifeEvent):
    """Logs a character joining someone's coup scheme."""

    __slots__ = ("scheme_initiator",)

    scheme_initiator: Entity

    def __init__(self, subject: Entity, scheme_initiator: Entity) -> None:
        super().__init__(subject)
        self.scheme_initiator = scheme_initiator

    def get_event_type(self) -> str:
        return "JoinCoupScheme"

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} joined "
            f"{self.scheme_initiator.name_with_uid}'s coup scheme."
        )


class StartCoupSchemeEvent(LifeEvent):
    """Logs a character attempting to over throw the current ruler."""

    __slots__ = ("ruler",)

    ruler: Entity

    def __init__(self, subject: Entity, ruler: Entity) -> None:
        super().__init__(subject)
        self.ruler = ruler

    def get_event_type(self) -> str:
        return "StartCoupScheme"

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} started a new coup scheme against "
            f"{self.ruler.name_with_uid}."
        )


class LostTerritoryEvent(LifeEvent):
    """Logs when a family head loses control over a territory."""

    __slots__ = ("territory",)

    territory: Entity

    def __init__(self, subject: Entity, territory: Entity) -> None:
        super().__init__(subject)
        self.territory = territory

    def get_event_type(self) -> str:
        return "LostTerritory"

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} lost control of the "
            f"{self.territory.name_with_uid} territory."
        )


class RemovedFromPowerEvent(LifeEvent):
    """Logs when a family is removed from power over a territory."""

    __slots__ = ("territory",)

    territory: Entity

    def __init__(self, subject: Entity, territory: Entity) -> None:
        super().__init__(subject)
        self.territory = territory

    def get_event_type(self) -> str:
        return "LostTerritory"

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} was removed from power over the "
            f"{self.territory.name_with_uid} territory."
        )


class StartWarSchemeEvent(LifeEvent):
    """Logs a character starting a war scheme."""

    __slots__ = ("target", "territory")

    target: Entity
    territory: Entity

    def __init__(self, subject: Entity, target: Entity, territory: Entity) -> None:
        super().__init__(subject)
        self.target = target
        self.territory = territory

    def get_event_type(self) -> str:
        return "StartWarScheme"

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} started a war scheme against "
            f"{self.target.name_with_uid} for the "
            f"{self.territory.name_with_uid} territory."
        )


class DeclareWarEvent(LifeEvent):
    """Logs a character starting a officially declaring war against another."""

    __slots__ = ("target", "territory")

    target: Entity
    territory: Entity

    def __init__(self, subject: Entity, target: Entity, territory: Entity) -> None:
        super().__init__(subject)
        self.target = target
        self.territory = territory

    def get_event_type(self) -> str:
        return "DeclareWar"

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} declared war against "
            f"{self.target.name_with_uid} for the "
            f"{self.territory.name_with_uid} territory."
        )


class DefendingTerritoryEvent(LifeEvent):
    """Logs a character starting a officially declaring war against another."""

    __slots__ = ("opponent", "territory")

    opponent: Entity
    territory: Entity

    def __init__(self, subject: Entity, opponent: Entity, territory: Entity) -> None:
        super().__init__(subject)
        self.opponent = opponent
        self.territory = territory

    def get_event_type(self) -> str:
        return "DefendingTerritory"

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} is defending the  "
            f"{self.territory.name_with_uid} territory from "
            f"{self.opponent.name_with_uid}."
        )


class QuellRevoltEvent(LifeEvent):
    """Logs a character quelling a revolt as head of the family."""

    __slots__ = ("territory",)

    territory: Entity

    def __init__(self, subject: Entity, territory: Entity) -> None:
        super().__init__(subject)
        self.territory = territory

    def get_event_type(self) -> str:
        return "QuellRevolt"

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} quelled a revolt in the "
            f"{self.territory.name_with_uid} territory."
        )


class TaxTerritoryEvent(LifeEvent):
    """Logs a character taxing a territory as head of the family."""

    __slots__ = ("territory",)

    territory: Entity

    def __init__(self, subject: Entity, territory: Entity) -> None:
        super().__init__(subject)
        self.territory = territory

    def get_event_type(self) -> str:
        return "TaxTerritory"

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} taxed the "
            f"{self.territory.name_with_uid} territory."
        )


class RevoltEvent(LifeEvent):
    """Logs a territory revolting against a family."""

    __slots__ = ("territory",)

    territory: Entity

    def __init__(self, subject: Entity, territory: Entity) -> None:
        super().__init__(subject)
        self.territory = territory

    def get_event_type(self) -> str:
        return "Revolt"

    def get_description(self) -> str:
        return (
            f"{self.territory.name_with_uid} is revolting against the "
            f"{self.subject.name_with_uid} family."
        )


class WarLostEvent(LifeEvent):
    """Logs a character losing a war."""

    __slots__ = ("winner", "territory")

    winner: Entity
    territory: Entity

    def __init__(self, subject: Entity, winner: Entity, territory: Entity) -> None:
        super().__init__(subject)
        self.winner = winner
        self.territory = territory

    def get_event_type(self) -> str:
        return "WarLost"

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} lost their war against "
            f"{self.winner.name_with_uid} for the "
            f"{self.territory.name_with_uid} territory."
        )


class WarWonEvent(LifeEvent):
    """Logs a character wining a war."""

    __slots__ = ("loser", "territory")

    loser: Entity
    territory: Entity

    def __init__(self, subject: Entity, loser: Entity, territory: Entity) -> None:
        super().__init__(subject)
        self.loser = loser
        self.territory = territory

    def get_event_type(self) -> str:
        return "WarWon"

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} won their war against "
            f"{self.loser.name_with_uid} for the "
            f"{self.territory.name_with_uid} territory."
        )


class AllianceSchemeFailedEvent(LifeEvent):
    """Logs when a character fails to start a new alliance."""

    def get_event_type(self) -> str:
        return "AllianceSchemeFailed"

    def get_description(self) -> str:
        return f"{self.subject.name_with_uid} failed to start a new alliance."


class AllianceFoundedEvent(LifeEvent):
    """Logs when a character successfully starts a new alliance."""

    __slots__ = ("alliance",)

    alliance: Entity

    def __init__(self, subject: Entity, alliance: Entity) -> None:
        super().__init__(subject)
        self.alliance = alliance

    def get_event_type(self) -> str:
        return "AllianceFounded"

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} founded the "
            f"{self.alliance.name_with_uid} alliance."
        )


class CoupSchemeDiscoveredEvent(LifeEvent):
    """Logs when a character's coup scheme is discovered."""

    def get_event_type(self) -> str:
        return "CoupSchemeDiscovered"

    def get_description(self) -> str:
        return f"{self.subject.name_with_uid}'s coup scheme was discovered."


class SentencedToDeathEvent(LifeEvent):
    """Logs when a character is sentenced to death for a failed coup."""

    def __init__(self, subject: Entity, reason: str) -> None:
        super().__init__(subject)
        self.reason = reason

    def get_event_type(self) -> str:
        return "SentencedToDeath"

    def get_description(self) -> str:
        return f"{self.subject.name_with_uid} was sentenced to death for {self.reason}."


class RuleOverthrownEvent(LifeEvent):
    """Logs when a character is overthrown by another."""

    __slots__ = ("usurper",)

    usurper: Entity

    def __init__(self, subject: Entity, usurper: Entity) -> None:
        super().__init__(subject)
        self.usurper = usurper

    def get_event_type(self) -> str:
        return "RuleOverthrown"

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} was overthrown by "
            f"{self.usurper.name_with_uid}."
        )


class UsurpEvent(LifeEvent):
    """Logs when a character usurps another for the thrown."""

    __slots__ = ("former_ruler",)

    former_ruler: Entity

    def __init__(self, subject: Entity, former_ruler: Entity) -> None:
        super().__init__(subject)
        self.former_ruler = former_ruler

    def get_event_type(self) -> str:
        return "Usurp"

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} usurped "
            f"{self.former_ruler.name_with_uid} for the thrown."
        )


class CheatOnSpouseEvent(LifeEvent):
    """Logs when a character cheats on their spouse."""

    __slots__ = ("accomplice",)

    accomplice: Entity

    def __init__(self, subject: Entity, accomplice: Entity) -> None:
        super().__init__(subject)
        self.accomplice = accomplice

    def get_event_type(self) -> str:
        return "CheatOnSpouse"

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} cheated on their spouse with "
            f"{self.accomplice.name_with_uid}."
        )
