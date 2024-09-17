"""Classes and components used to model betrothals.

"""

from __future__ import annotations

from typing import Optional

from minerva.datetime import SimDate
from minerva.ecs import Component, GameObject


class Betrothal(Component):
    """Information about one character betrothal to another."""

    __slots__ = ("character", "betrothed", "start_date")

    character: GameObject
    betrothed: GameObject
    start_date: SimDate

    def __init__(
        self, character: GameObject, betrothed: GameObject, start_date: SimDate
    ) -> None:
        super().__init__()
        self.character = character
        self.betrothed = betrothed
        self.start_date = start_date.copy()


class BetrothalTracker(Component):
    """Tracks a character's current and past betrothals."""

    __slots__ = ("current_betrothal", "past_betrothal_ids")

    current_betrothal: Optional[GameObject]
    past_betrothal_ids: list[int]

    def __init__(self) -> None:
        super().__init__()
        self.current_betrothal = None
        self.past_betrothal_ids = []
