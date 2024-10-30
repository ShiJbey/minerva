"""An event bus for events fired by the simulation.

"""
from minerva.ecs import GameObject
from minerva.viz.game_events import EventEmitter


class SimulationEvents:
    """An event bus for events fired by the simulation."""

    __slots__ = (
        "family_added",
    )

    family_added: EventEmitter[GameObject]

    def __init__(self) -> None:
        self.family_added = EventEmitter()
