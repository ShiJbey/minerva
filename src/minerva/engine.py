"""Core Data Tracking and such."""

from __future__ import annotations

from typing import Optional

from minerva.ecs import GameObject


class Engine:

    __slots__ = ("royal_family",)

    royal_family: Optional[GameObject]

    def __init__(self) -> None:
        self.royal_family = None
