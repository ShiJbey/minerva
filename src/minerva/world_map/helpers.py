"""Helper functions for the world map."""

from __future__ import annotations

from typing import Optional

from minerva.characters.components import Family
from minerva.ecs import Entity
from minerva.events import LoseControlOfTerritoryEvent, TakeControlOfTerritoryEvent
from minerva.game_action import GameAction
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


class UnsetControllingFamily(GameAction):
    """Unset the controlling family of a territory."""

    __slots__ = ("territory",)

    territory: Entity

    def __init__(self, territory: Entity) -> None:
        super().__init__(territory.world)
        self.territory = territory

    def on_execute(self) -> None:
        territory_component = self.territory.get_component(Territory)
        controlling_family = territory_component.controlling_family

        if controlling_family is None:
            return

        family_component = controlling_family.get_component(Family)
        family_component.controlled_territories.remove(self.territory)
        territory_component.controlling_family = None

        with self.world.get_resource(SimDB) as db:
            db.execute(
                """UPDATE Territory SET controlling_family_uid=? WHERE uid=?;""",
                (None, self.territory.uid),
            )


class SetTerritoryControllingFamily(GameAction):
    """Set the controlling family of a territory."""

    __slots__ = ("territory", "family")

    territory: Entity
    family: Optional[Entity]

    def __init__(self, territory: Entity, family: Optional[Entity]) -> None:
        super().__init__(territory.world)
        self.territory = territory
        self.family = family

    def on_execute(self) -> None:
        territory = self.territory
        family = self.family

        territory_component = territory.get_component(Territory)

        if territory_component.controlling_family is not None:
            former_sovereign = territory_component.controlling_family
            family_component = former_sovereign.get_component(Family)
            family_component.controlled_territories.remove(territory)

            family_head = territory_component.controlling_family.get_component(
                Family
            ).head
            if family_head is not None:
                LoseControlOfTerritoryEvent(
                    family=territory_component.controlling_family,
                    territory=territory,
                ).log_event()

            territory_component.controlling_family = None

        if family is not None:
            family_component = family.get_component(Family)
            family_component.controlled_territories.add(territory)
            territory_component.controlling_family = family
            family_head = family.get_component(Family).head
            if family_head is not None:
                TakeControlOfTerritoryEvent(
                    territory=self.territory, family=family, family_head=family_head
                ).log_event()

        with territory.world.get_resource(SimDB) as db:
            db.execute(
                """UPDATE Territory SET controlling_family_uid=? WHERE uid=?;""",
                (family, territory),
            )
