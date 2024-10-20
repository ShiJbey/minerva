"""Settlement Generation Functions and Classes."""

from minerva.ecs import Event, GameObject, World
from minerva.pcg.base_types import NameFactory, TerritoryFactory
from minerva.sim_db import SimDB
from minerva.stats.helpers import default_stat_calc_strategy
from minerva.world_map.components import PopulationHappiness, Settlement


class DefaultTerritoryFactory(TerritoryFactory):
    """Built-in implementation of a territory factory."""

    __slots__ = ("name_factory",)

    name_factory: NameFactory

    def __init__(self, name_factory: NameFactory) -> None:
        super().__init__()
        self.name_factory = name_factory

    def generate_territory(self, world: World, name: str = "") -> GameObject:
        """Construct a new settlement."""
        settlement = world.gameobjects.spawn_gameobject()
        name = name if name else self.name_factory.generate_name(settlement)
        settlement.metadata["object_type"] = "settlement"
        settlement.add_component(Settlement(name=name))
        settlement.add_component(PopulationHappiness(default_stat_calc_strategy))
        settlement.name = name

        db = world.resources.get_resource(SimDB).db

        db.execute(
            """INSERT INTO settlements (uid, name) VALUES (?, ?);""",
            (settlement.uid, name),
        )
        db.commit()

        world.events.dispatch_event(
            Event(event_type="settlement-added", world=world, settlement=settlement)
        )

        return settlement
