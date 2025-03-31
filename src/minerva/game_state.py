"""Minerva Game State."""

from typing import Optional

from minerva.ecs import Entity


class GameState:
    """Manages information about the current state of a minerva simulation."""

    __slots__ = (
        "year",
        "characters",
        "families",
        "territories",
        "alliances",
        "current_dynasty",
        "previous_dynasties",
    )

    year: int
    """The current year in the simulation."""
    characters: list[Entity]
    """All active characters."""
    families: list[Entity]
    """All active families."""
    territories: list[Entity]
    """All active territories."""
    alliances: list[Entity]
    """All active alliances."""
    current_dynasty: Optional[Entity]
    """The dynasty of the current ruler."""
    previous_dynasties: list[Entity]
    """Previous dynasties."""

    def __init__(self) -> None:
        self.year = 1
        self.characters = []
        self.families = []
        self.territories = []
        self.alliances = []
        self.current_dynasty = None
        self.previous_dynasties = []
