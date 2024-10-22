"""Helper classes for tracking metrics about a character."""

import dataclasses
from typing import Optional

from minerva.datetime import SimDate
from minerva.ecs import Component


@dataclasses.dataclass
class CharacterMetricData:
    """Metrics about a character."""

    times_married: int = 0
    num_wars: int = 0
    num_wars_started: int = 0
    num_wars_won: int = 0
    num_wars_lost: int = 0
    num_revolts_quelled: int = 0
    num_coups_planned: int = 0
    num_territories_taken: int = 0
    times_as_ruler: int = 0
    num_alliances_founded: int = 0
    num_failed_alliance_attempts: int = 0
    num_alliances_disbanded: int = 0
    directly_inherited_throne: bool = False
    date_of_last_declared_war: Optional[SimDate] = None


class CharacterMetrics(Component):
    """Tracks numerical metrics about a character."""

    __slots__ = ("data",)

    data: CharacterMetricData

    def __init__(self) -> None:
        super().__init__()
        self.data = CharacterMetricData()
