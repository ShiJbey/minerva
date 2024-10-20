"""Simulation configuration."""

from __future__ import annotations

import random
from typing import Union

import pydantic


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

    world_size: tuple[int, int] = (20, 20)
    """The size of the world map."""
    n_territories: int = 10
    """The number of territories to generate."""
    n_initial_families: int = 20
    """The number of initial families to generate."""
    max_households_per_family: int = 3
    """The max number of households to spawn per initial family."""
    max_children_per_household: int = 4
    """The max number of children to spawn per initial household."""
    chance_spawn_with_children: float = 0.8
    """Chance that the head of an initial household will spawn with children."""
    chance_spawn_with_spouse: float = 0.9
    """Chance that the head of an initial household will spawn with a spouse."""

    # === PYGAME ===

    window_width: int = 1280
    """Width of the game window in pixels."""
    window_height: int = 720
    """Height of the game window inf pixels."""
    fps: int = 60
    """Desired frames per second."""
    show_debug: bool = False
    """Display debug outputs."""
    sim_update_frequency: int = 12
    """Number of simulation steps per second."""
    background_color: str = "#42ACAF"
    """Background color of the pygame window."""

    # === Character Settings ===

    max_personality_traits: int = 3
    """The max number of initial personality traits given to generated characters."""
    n_personality_traits_from_parents: int = 2
    """The max number of personality traits inherited from parents."""
    influence_points_max: int = 10_000
    """The max number of influence points that a character can have."""
    influence_points_base: int = 100
    """The starting number of influence points given to each character."""
    behavior_utility_threshold: float = 0.01
    """The required utility score for a behavior to be considered."""

    # === Family Settings ===

    max_advisors_per_family: int = 3
    """The max number of advisors families can have in their courts."""
    max_warriors_per_family: int = 3
    """The max number of warriors families can have in their courts."""
    family_colors_primary: list[str] = pydantic.Field(
        default_factory=lambda: (
            [
                "#01161E",  # Rich Black
                "#124559",  # Midnight Green
                "#598392",  # Air Force Blue
                "#AEC3B0",  # Ash Grey
                "#654236",  # Liver
            ]
        )
    )
    """Primary colors for a family's flag."""
    family_colors_secondary: list[str] = pydantic.Field(
        default_factory=lambda: (
            [
                "#e90000",  # red
                "#31d5c8",  # light blue
                "#a538c6",  # violet
                "#05fb00",  # green
                "#001eba",  # royal blue
            ]
        )
    )
    """Secondary colors for a family's flag."""
    family_colors_tertiary: list[str] = pydantic.Field(
        default_factory=lambda: (
            [
                "#FF338C",  # Crimson
                "#33FF57",  # Bittersweet
                "#ffffff",  # Orange
                "#FB62F6",  # Pink
                "#fff500",  # Yellow
            ]
        )
    )
    """Tertiary colors for a family's flag."""
    family_banner_symbols: list[str] = pydantic.Field(
        default_factory=lambda: (
            [
                "circle",
                "square",
                "diamond",
                "triangle_up",
                "triangle_down",
            ]
        )
    )
    """Symbols that can appear on a family's flag."""

    # === Territory Settings ===

    max_political_influence: int = 100
    """Max political influence a family can have in a territory."""
    base_territory_happiness: float = 50
    """The starting population happiness score for territories."""
    max_territory_happiness: float = 100
    """The max possible score for population happiness in a territory."""
    happiness_revolt_threshold: float = 10
    """The value below which a territory will revolt against its controlling family."""
    months_to_quell_revolt: int = 3
    """The number of months a family has to stop a rebellion in a territory."""
