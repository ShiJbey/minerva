"""Life Events Associated with Power Succession."""

from minerva.ecs import Entity
from minerva.life_events.base_types import LifeEvent
from minerva.sim_db import SimDB


class BecameFamilyHeadEvent(LifeEvent):
    """Event dispatched when a character becomes head of a family."""

    __slots__ = ("family",)

    def __init__(self, subject: Entity, family: Entity) -> None:
        super().__init__(subject)
        self.family = family

    def get_event_type(self) -> str:
        return "BecameFamilyHead"

    def on_event_logged(self) -> None:
        db = self.world.get_resource(SimDB).db
        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO became_family_head_events
            (event_id, character_id, family_id, timestamp)
            VALUES (?, ?, ?, ?);
            """,
            (
                self.event_id,
                self.subject.uid,
                self.family.uid,
                self.timestamp.to_iso_str(),
            ),
        )
        db.commit()

    def get_description(self) -> str:
        return (
            f"{self.subject.name_with_uid} became the head of the "
            f"{self.family.name_with_uid} family."
        )


class BecameEmperorEvent(LifeEvent):
    """Event dispatched when a character becomes emperor."""

    def get_event_type(self) -> str:
        return "BecameEmperor"

    def on_event_logged(self) -> None:
        db = self.world.get_resource(SimDB).db
        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO became_emperor_events
            (event_id, character_id, timestamp)
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
        return f"{self.subject.name_with_uid} became emperor."


class FamilyRemovedFromPlay(LifeEvent):
    """Event dispatched when a family is removed from play."""

    def get_event_type(self) -> str:
        return "FamilyRemovedFromPlay"

    def on_event_logged(self) -> None:
        pass

    def get_description(self) -> str:
        return f"The {self.subject.name_with_uid} family has been removed from play."
