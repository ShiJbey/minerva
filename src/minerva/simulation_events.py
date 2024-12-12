"""An event bus for events fired by the simulation.

"""

from minerva.ecs import Entity
from minerva.viz.game_events import EventEmitter
from minerva.world_map.components import WorldMap


class SimulationEvents:
    """An event bus for events fired by the simulation."""

    __slots__ = (
        "family_added",
        "relationship_created",
        "map_generated",
    )

    family_added: EventEmitter[Entity]
    relationship_created: EventEmitter[Entity]
    map_generated: EventEmitter[WorldMap]

    def __init__(self) -> None:
        self.family_added = EventEmitter()
        self.relationship_created = EventEmitter()
        self.map_generated = EventEmitter()
