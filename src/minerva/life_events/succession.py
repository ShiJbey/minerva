"""Life Events Associated with Power Succession."""

from minerva.ecs import Entity
from minerva.life_events.base_types import LifeEvent


class BecameFamilyHeadEvent(LifeEvent):
    """Event dispatched when a character becomes head of a family."""

    __slots__ = ("family",)

    def __init__(self, subject: Entity, family: Entity) -> None:
        super().__init__("BecameFamilyHead", subject)
        self.family = family
        self.event_args["family_name"] = family.name
        self.event_args["family_id"] = str(family.uid)


class BecameRulerEvent(LifeEvent):
    """Event dispatched when a character becomes the ruler."""

    def __init__(self, subject: Entity) -> None:
        super().__init__("BecameRuler", subject)
