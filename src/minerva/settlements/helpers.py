"""Helper functions for settlements."""

from __future__ import annotations

from typing import Optional

from minerva.ecs import GameObject
from minerva.settlements.base_types import Settlement
from minerva.sim_db import SimDB


def set_settlement_controlling_clan(
    settlement: GameObject, clan: Optional[GameObject]
) -> None:
    """Set what clan currently controls the settlement."""

    settlement_component = settlement.get_component(Settlement)

    settlement_component.controlling_family = clan

    db = settlement.world.resources.get_resource(SimDB).db

    db.execute(
        """UPDATE settlements SET controlling_clan=? WHERE uid=?;""", (clan, settlement)
    )

    db.commit()
