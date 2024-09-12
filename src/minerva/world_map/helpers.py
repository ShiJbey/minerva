"""Helper functions for the world map."""

from __future__ import annotations

from typing import Optional

from minerva.characters.components import Family
from minerva.ecs import GameObject
from minerva.sim_db import SimDB
from minerva.world_map.components import Settlement


def get_settlement_influence(
    territory: GameObject,
    clan: GameObject,
) -> int:
    """Get the political influence of a clan over a given territory."""

    territory_component = territory.get_component(Settlement)

    influence = territory_component.political_influence.get(clan, 0)

    return influence


def set_settlement_controlling_family(
    settlement: GameObject, family: Optional[GameObject]
) -> None:
    """Set what clan currently controls the settlement."""

    settlement_component = settlement.get_component(Settlement)

    if settlement_component.controlling_family is not None:
        former_sovereign = settlement_component.controlling_family
        family_component = former_sovereign.get_component(Family)
        family_component.territories.remove(settlement)
        settlement_component.controlling_family = None

    if family is not None:
        family_component = family.get_component(Family)
        family_component.territories.append(settlement)
        settlement_component.controlling_family = family

    db = settlement.world.resources.get_resource(SimDB).db

    db.execute(
        """UPDATE settlements SET controlling_family=? WHERE uid=?;""",
        (family, settlement),
    )

    db.commit()
