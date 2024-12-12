"""An event bus for events fired by the simulation.

"""
from minerva.ecs import Entity
from minerva.viz.game_events import EventEmitter


class SimulationEvents:
    """An event bus for events fired by the simulation."""

    __slots__ = (
        "family_added",
        "relationship_created"
    )

    family_added: EventEmitter[Entity]
    relationship_created: EventEmitter[Entity]

    def __init__(self) -> None:
        self.family_added = EventEmitter()
        self.relationship_created = EventEmitter()
