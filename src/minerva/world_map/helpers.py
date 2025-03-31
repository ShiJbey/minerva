"""Helper functions for the world map."""

from __future__ import annotations

from typing import Optional

from minerva.characters.components import Family
from minerva.ecs import Entity
from minerva.sim_db import SimDB
from minerva.stats.base_types import (
    StatModifier,
    add_stat_modifier,
    get_stat_base,
    get_stat_value,
    increment_stat_base,
    remove_stat_modifier,
    set_stat_base,
)
from minerva.world_map.components import PopulationHappiness, Territory


def get_happiness(entity: Entity) -> int:
    """Get the population happiness for the entity."""
    return get_stat_value(entity.get_component(PopulationHappiness))


def increment_happiness_base(entity: Entity, value: int) -> None:
    """Increment the happiness base value by the given amount."""
    increment_stat_base(entity.get_component(PopulationHappiness), value)


def get_happiness_base(entity: Entity) -> int:
    """Get the base value for an entity's happiness."""
    return get_stat_base(entity.get_component(PopulationHappiness))


def set_happiness_base(entity: Entity, value: int) -> None:
    """Set the base value for an entity's happiness."""
    set_stat_base(entity.get_component(PopulationHappiness), value)


def add_happiness_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Add a modifier to the happiness stat."""
    add_stat_modifier(entity, entity.get_component(PopulationHappiness), modifier)


def remove_happiness_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Remove a modifier from the happiness stat."""
    remove_stat_modifier(entity, entity.get_component(PopulationHappiness), modifier)


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
        family_component.controlled_territories.remove(territory)
        territory_component.controlling_family = None

    if family is not None:
        family_component = family.get_component(Family)
        family_component.controlled_territories.add(territory)
        territory_component.controlling_family = family

    db = territory.world.get_resource(SimDB).conn

    db.execute(
        """UPDATE territories SET controlling_family=? WHERE uid=?;""",
        (family, territory),
    )

    db.commit()
