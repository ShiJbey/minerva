"""Simulation configuration."""

from __future__ import annotations

import random
from typing import Any, Literal, Union

import pydantic

WORLD_SIZE = {
    "small": (2, 3),
    "medium": (3, 3),
    "large": (4, 3),
    "xlarge": (5, 5),
}


class Config(pydantic.BaseModel):
    """Configuration settings for a Simulation instance."""

    seed: Union[str, int] = pydantic.Field(
        default_factory=lambda: random.randint(0, 9999999)
    )
    """Value used for pseudo-random number generation."""
    db_path: str = ":memory:"
    """Path to the sqlite database instance."""

    # === LOGGING ===

    logging_enabled: bool = True
    """Toggles if logging messages are sent anywhere."""
    log_level: str = "INFO"
    """The logging level to use."""
    log_filepath: str = ""
    """Toggles if logging output should be save to this file name in log_directory."""
    log_to_terminal: bool = True
    """Toggles if logs should be printed to the terminal or saved to a file."""

    # === INITIAL GENERATION ===

    world_size: Literal["small", "medium", "large", "xlarge"] = "small"
    """The number of settlements to generate."""
    n_initial_clans: int = 20
    """How many clans to spawn at start."""
    chance_noble_family: float = 0.2
    """Chance of a family spawning as a noble family."""
    max_families_per_clan: int = 5
    """The max number of families to spawn per initial clan."""
    max_households_per_family: int = 3
    """The max number of households to spawn per initial family."""
    max_children_per_household: int = 4
    """The max number of children to spawn per initial household."""
    chance_spawn_with_children: float = 0.8
    """Chance that the head of an initial household will spawn with children."""
    chance_spawn_with_spouse: float = 0.9
    """Chance that the head of an initial household will spawn with a spouse."""

    # === MISC ===

    settings: dict[str, Any] = pydantic.Field(default_factory=dict)
    """Various key-value pair configuration settings."""
