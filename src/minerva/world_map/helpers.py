"""Helper functions for the world map."""

from __future__ import annotations

from typing import Optional

from minerva.characters.components import Clan
from minerva.ecs import GameObject, World
from minerva.stats.base_types import StatManager
from minerva.stats.helpers import default_stat_calc_strategy
from minerva.world_map.components import Territory, TerritoryHappiness, WorldMap


def set_territory_sovereign(
    territory: GameObject,
    sovereign_clan: Optional[GameObject],
) -> None:
    """Set the sovereign clan for a territory."""

    territory_component = territory.get_component(Territory)

    if territory_component.sovereign_clan is not None:
        former_sovereign = territory_component.sovereign_clan
        clan_component = former_sovereign.get_component(Clan)
        clan_component.territories.remove(territory)
        territory_component.sovereign_clan = None

    if sovereign_clan is not None:
        clan_component = sovereign_clan.get_component(Clan)
        clan_component.territories.append(territory)
        territory_component.sovereign_clan = sovereign_clan


def get_territory_influence(
    territory: GameObject,
    clan: GameObject,
) -> int:
    """Get the political influence of a clan over a given territory."""

    territory_component = territory.get_component(Territory)

    influence = territory_component.political_influence.get(clan.uid, 0)

    return influence


def create_territory(world: World, position: tuple[int, int]) -> GameObject:
    """Create a new territory."""

    obj = world.gameobjects.spawn_gameobject()
    obj.metadata["object_type"] = "territory"
    obj.add_component(Territory(position))
    obj.add_component(StatManager())
    obj.add_component(TerritoryHappiness(default_stat_calc_strategy))

    return obj


def initialize_world_map(world: World, size: tuple[int, int]) -> WorldMap:
    """Reset the world map for the game."""

    world_map = WorldMap(size)

    world.resources.add_resource(world_map)

    return world_map


def generate_world_map(world: World) -> None:
    """Initialize territory GameObjects in the world map."""

    world_map = WorldMap(size)

    world.resources.add_resource(world_map)

    return world_map

    # for (x, y), _ in world_map.territories.enumerate():
    #     world_map.territories.set(x, y, create_territory(world, (x, y)))
