"""Territory Generation Functions and Classes."""

from typing import Optional

from minerva.config import Config
from minerva.ecs import Entity, World
from minerva.pcg.base_types import (
    NameFactory,
    PCGFactories,
    TerritoryFactory,
    TerritoryGenOptions,
)
from minerva.sim_db import SimDB
from minerva.stats.helpers import default_stat_calc_strategy
from minerva.world_map.components import PopulationHappiness, Territory


class DefaultTerritoryFactory(TerritoryFactory):
    """Built-in implementation of a territory factory."""

    __slots__ = ("name_factory",)

    name_factory: NameFactory

    def __init__(self, name_factory: NameFactory) -> None:
        super().__init__()
        self.name_factory = name_factory

    def generate_territory(self, world: World, options: TerritoryGenOptions) -> Entity:
        """Construct a new territory."""
        config = world.get_resource(Config)

        territory = world.entity()
        name = (
            options.name if options.name else self.name_factory.generate_name(territory)
        )
        territory.add_component(Territory(name=name))
        territory.add_component(
            PopulationHappiness(
                config.base_territory_happiness,
                config.max_territory_happiness,
                default_stat_calc_strategy,
            )
        )
        territory.name = name

        db = world.get_resource(SimDB).db

        db.execute(
            """INSERT INTO territories (uid, name) VALUES (?, ?);""",
            (territory.uid, name),
        )
        db.commit()

        return territory


def spawn_territory(
    world: World, options: Optional[TerritoryGenOptions] = None
) -> Entity:
    """Spawn a new territory."""
    return world.get_resource(PCGFactories).territory_factory.generate_territory(
        world, options if options else TerritoryGenOptions()
    )
