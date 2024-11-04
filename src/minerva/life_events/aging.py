"""Life Events for character aging."""

from minerva.characters.components import LifeStage
from minerva.ecs import GameObject
from minerva.life_events.base_types import LifeEvent
from minerva.sim_db import SimDB


class LifeStageChangeEvent(LifeEvent):
    """Event dispatched when a character changes life stages."""

    __slots__ = ("life_stage",)

    life_stage: LifeStage

    def __init__(self, subject: GameObject, life_stage: LifeStage) -> None:
        super().__init__(subject)
        self.life_stage = life_stage

    def get_event_type(self) -> str:
        return "LifeStageChange"

    def on_event_logged(self) -> None:
        db = self.world.resources.get_resource(SimDB).db
        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO life_stage_change_events
            (event_id, character_id, life_stage, timestamp)
            VALUES (?, ?, ?, ?);
            """,
            (
                self.event_id,
                self.subject.uid,
                self.life_stage,
                self.timestamp.to_iso_str(),
            ),
        )
        db.commit()

    def get_description(self) -> str:
        return f"{self.subject.name_with_uid} became an {self.life_stage.name.lower()}."


class DeathEvent(LifeEvent):
    """Event dispatched when a character dies."""

    __slots__ = ("cause",)

    cause: str

    def __init__(self, subject: GameObject, cause: str = "") -> None:
        super().__init__(subject)
        self.cause = cause

    def get_event_type(self) -> str:
        return "Death"

    def on_event_logged(self) -> None:
        db = self.world.resources.get_resource(SimDB).db
        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO death_events (event_id, character_id, timestamp, cause)
            VALUES (?, ?, ?, ?);
            """,
            (self.event_id, self.subject.uid, self.timestamp.to_iso_str(), self.cause),
        )
        db.commit()

    def get_description(self) -> str:
        return f"{self.subject.name_with_uid} died (cause: {self.cause})."
