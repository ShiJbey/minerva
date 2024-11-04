"""Helper Functions and Data Types for working with character-related stats."""

import enum

from minerva.characters.components import (
    Intelligence,
    Luck,
    Martial,
    Prowess,
    Stewardship,
)
from minerva.ecs import GameObject

EXCELLENT_STAT_THRESHOLD = 85
GOOD_STAT_THRESHOLD = 20
NEUTRAL_STAT_THRESHOLD = -20
BAD_STAT_THRESHOLD = 15


class StatLevel(enum.Enum):
    """A general interval for a stat."""

    TERRIBLE = enum.auto()
    BAD = enum.auto()
    NEUTRAL = enum.auto()
    GOOD = enum.auto()
    EXCELLENT = enum.auto()


def get_intelligence_level(character: GameObject) -> StatLevel:
    """Get the stat level for a character's intelligence stat."""
    stat_value = character.get_component(Intelligence).value

    if stat_value >= EXCELLENT_STAT_THRESHOLD:
        return StatLevel.EXCELLENT
    elif stat_value >= GOOD_STAT_THRESHOLD:
        return StatLevel.GOOD
    elif stat_value >= NEUTRAL_STAT_THRESHOLD:
        return StatLevel.NEUTRAL
    elif stat_value >= BAD_STAT_THRESHOLD:
        return StatLevel.BAD
    else:
        return StatLevel.TERRIBLE


def get_stewardship_level(character: GameObject) -> StatLevel:
    """Get the stat level for a character's stewardship stat."""
    stat_value = character.get_component(Stewardship).value

    if stat_value >= EXCELLENT_STAT_THRESHOLD:
        return StatLevel.EXCELLENT
    elif stat_value >= GOOD_STAT_THRESHOLD:
        return StatLevel.GOOD
    elif stat_value >= NEUTRAL_STAT_THRESHOLD:
        return StatLevel.NEUTRAL
    elif stat_value >= BAD_STAT_THRESHOLD:
        return StatLevel.BAD
    else:
        return StatLevel.TERRIBLE


def get_martial_level(character: GameObject) -> StatLevel:
    """Get the stat level for a character's martial stat."""
    stat_value = character.get_component(Martial).value

    if stat_value >= EXCELLENT_STAT_THRESHOLD:
        return StatLevel.EXCELLENT
    elif stat_value >= GOOD_STAT_THRESHOLD:
        return StatLevel.GOOD
    elif stat_value >= NEUTRAL_STAT_THRESHOLD:
        return StatLevel.NEUTRAL
    elif stat_value >= BAD_STAT_THRESHOLD:
        return StatLevel.BAD
    else:
        return StatLevel.TERRIBLE


def get_luck_level(character: GameObject) -> StatLevel:
    """Get the stat level for a character's luck stat."""
    stat_value = character.get_component(Luck).value

    if stat_value >= EXCELLENT_STAT_THRESHOLD:
        return StatLevel.EXCELLENT
    elif stat_value >= GOOD_STAT_THRESHOLD:
        return StatLevel.GOOD
    elif stat_value >= NEUTRAL_STAT_THRESHOLD:
        return StatLevel.NEUTRAL
    elif stat_value >= BAD_STAT_THRESHOLD:
        return StatLevel.BAD
    else:
        return StatLevel.TERRIBLE


def get_prowess_level(character: GameObject) -> StatLevel:
    """Get the stat level for a character's prowess stat."""
    stat_value = character.get_component(Prowess).value

    if stat_value >= EXCELLENT_STAT_THRESHOLD:
        return StatLevel.EXCELLENT
    elif stat_value >= GOOD_STAT_THRESHOLD:
        return StatLevel.GOOD
    elif stat_value >= NEUTRAL_STAT_THRESHOLD:
        return StatLevel.NEUTRAL
    elif stat_value >= BAD_STAT_THRESHOLD:
        return StatLevel.BAD
    else:
        return StatLevel.TERRIBLE
