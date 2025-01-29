"""Life Events for character aging."""

from minerva.characters.components import LifeStage
from minerva.ecs import Entity
from minerva.life_events.base_types import LifeEvent


class LifeStageChangeEvent(LifeEvent):
    """Event dispatched when a character changes life stages."""

    __slots__ = ("life_stage",)

    life_stage: LifeStage

    def __init__(self, subject: Entity, life_stage: LifeStage) -> None:
        super().__init__("LifeStageChange", subject)
        self.life_stage = life_stage
        self.event_args["life_stage"] = life_stage.name


class DeathEvent(LifeEvent):
    """Event dispatched when a character dies."""

    __slots__ = ("cause",)

    cause: str

    def __init__(self, subject: Entity, cause: str = "") -> None:
        super().__init__("Death", subject)
        self.cause = cause
        self.event_args["cause"] = cause

    def get_description(self) -> str:
        return f"{self.subject.name_with_uid} died (cause: {self.cause})."
