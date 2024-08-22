"""Life Events for character aging."""

from minerva.characters.components import LifeStage
from minerva.ecs import GameObject
from minerva.life_events.base_types import EventHistory, LifeEvent
from minerva.sim_db import SimDB


class LifeStageChangeEvent(LifeEvent):
    """Event dispatched when a character changes life stages."""

    __slots__ = ("character", "life_stage")

    character: GameObject
    life_stage: LifeStage

    def __init__(self, character: GameObject, life_stage: LifeStage) -> None:
        super().__init__(
            event_type="life-stage-change",
            world=character.world,
            character=character,
            life_stage=life_stage,
        )
        self.character = character
        self.life_stage = life_stage

    def on_dispatch(self) -> None:
        self.character.dispatch_event(self)
        self.character.get_component(EventHistory).append(self)

        db = self.world.resources.get_resource(SimDB).db
        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO life_events (event_id, event_type, timestamp)
            VALUES (?, ?, ?);
            """,
            (self.event_id, self.event_type, self.timestamp.to_iso_str()),
        )
        cur.execute(
            """
            INSERT INTO life_stage_change_events
            (event_id, character_id, life_stage, timestamp)
            VALUES (?, ?, ?, ?);
            """,
            (
                self.event_id,
                self.character.uid,
                self.life_stage,
                self.timestamp.to_iso_str(),
            ),
        )
        db.commit()

    def __str__(self) -> str:
        return f"{self.character.name} became an {self.life_stage.name.lower()}."


class CharacterDeathEvent(LifeEvent):
    """Event dispatched when a character dies."""

    __slots__ = ("character",)

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(
            event_type="character-death",
            world=character.world,
            character=character,
        )
        self.character = character

    def on_dispatch(self) -> None:
        self.character.dispatch_event(self)
        self.character.get_component(EventHistory).append(self)

        db = self.world.resources.get_resource(SimDB).db
        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO life_events (event_id, event_type, timestamp)
            VALUES (?, ?, ?);
            """,
            (self.event_id, self.event_type, self.timestamp.to_iso_str()),
        )
        cur.execute(
            """
            INSERT INTO death_events (event_id, character_id, timestamp)
            VALUES (?, ?, ?);
            """,
            (self.event_id, self.character.uid, self.timestamp.to_iso_str()),
        )
        db.commit()

    def __str__(self) -> str:
        return f"{self.character.name} died."
