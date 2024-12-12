"""Helper functions for the world map."""

from __future__ import annotations

from typing import Optional

from minerva.characters.components import Family
from minerva.ecs import Entity
from minerva.sim_db import SimDB
from minerva.world_map.components import Territory


def get_territory_political_influence(
    territory: Entity,
    family: Entity,
) -> int:
    """Get the political influence of a family over a given territory."""

    territory_component = territory.get_component(Territory)

    influence = territory_component.political_influence.get(family, 0)

    return influence


def increment_political_influence(
    territory: Entity,
    family: Entity,
    amount: int,
) -> None:
    """Get the political influence of a family over a given territory."""

    territory_component = territory.get_component(Territory)

    if family not in territory_component.political_influence:
        territory_component.political_influence[family] = 0

    territory_component.political_influence[family] += amount


def set_territory_controlling_family(
    territory: Entity, family: Optional[Entity]
) -> None:
    """Set what family currently controls the territory."""

    territory_component = territory.get_component(Territory)

    if territory_component.controlling_family is not None:
        former_sovereign = territory_component.controlling_family
        family_component = former_sovereign.get_component(Family)
        family_component.territories.remove(territory)
        territory_component.controlling_family = None

    if family is not None:
        family_component = family.get_component(Family)
        family_component.territories.add(territory)
        territory_component.controlling_family = family

    db = territory.world.get_resource(SimDB).db

    db.execute(
        """UPDATE territories SET controlling_family=? WHERE uid=?;""",
        (family, territory),
    )

    db.commit()
