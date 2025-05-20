"""Stat System.

This module contains an implementation of stat components. Stats are things
like health, strength, dexterity, defense, attraction, etc. Stats can have modifiers
associated with them that change their final value.

"""

from __future__ import annotations

import enum
from abc import ABC

from minerva.ecs import Component, Entity


class StatModifierType(enum.IntEnum):
    """Specifies how the value of a StatModifier is applied in stat calculation."""

    FLAT = 100
    """Adds a constant value to the base value."""

    PERCENT = 200
    """Additively stacks percentage increases on a modified stat."""


class StatModifier:
    """Stat modifiers provide buffs and de-buffs to the value of stats."""

    __slots__ = ("value", "modifier_type")

    value: int
    modifier_type: StatModifierType

    def __init__(
        self,
        value: int,
        modifier_type: StatModifierType = StatModifierType.FLAT,
    ) -> None:
        self.value = value
        self.modifier_type = modifier_type


class StatModifiers(Component):
    """Tracks all the stat modifiers attached to an entity."""

    __slots__ = ("modifiers",)

    modifiers: list[StatModifier]

    def __init__(self) -> None:
        super().__init__()
        self.modifiers = []


class Stat(Component, ABC):
    """Tracks the value for a stat (e.g., intelligence, lifespan, happiness)."""

    __slots__ = (
        "base_value",
        "value",
        "boost_flat",
        "boost_percent",
        "min_value",
        "max_value",
    )

    base_value: int
    value: int
    boost_flat: int
    boost_percent: int
    max_value: int
    min_value: int

    def __init__(
        self, base_value: int = 0, min_value: int = -999_999, max_value: int = 999_999
    ) -> None:
        super().__init__()
        self.base_value = base_value
        self.value = base_value
        self.boost_flat = 0
        self.boost_percent = 0
        self.min_value = min_value
        self.max_value = max_value


def recalculate_stat(stat: Stat) -> None:
    """Recalculate a stat's value."""

    stat.value = stat.base_value
    stat.value += stat.boost_flat
    stat.value += int(stat.base_value * (float(stat.boost_percent) / 100.0))
    stat.value = min(stat.max_value, stat.value)
    stat.value = max(stat.min_value, stat.value)


def get_stat_value(stat: Stat) -> int:
    """Get the martial skill for the entity."""
    return stat.value


def get_stat_base(stat: Stat) -> int:
    """Get the base value for a stat."""
    return stat.base_value


def set_stat_base(stat: Stat, value: int) -> None:
    """Set the base value for an stat."""
    stat.base_value = value
    recalculate_stat(stat)


def increment_stat_base(stat: Stat, value: int) -> None:
    """Increment the stats base value by an value."""
    stat.base_value += value
    recalculate_stat(stat)


def add_stat_modifier(entity: Entity, stat: Stat, modifier: StatModifier) -> None:
    """Add a modifier to the stat."""
    entity.get_component(StatModifiers).modifiers.append(modifier)

    if modifier.modifier_type == StatModifierType.FLAT:
        stat.boost_flat += modifier.value
    elif modifier.modifier_type == StatModifierType.PERCENT:
        stat.boost_percent += modifier.value

    recalculate_stat(stat)


def remove_stat_modifier(entity: Entity, stat: Stat, modifier: StatModifier) -> None:
    """Remove a modifier from the stat."""

    stat_modifiers = entity.get_component(StatModifiers)

    try:
        # This line will throw a ValueError if the modifier is not
        # present. So, we catch the error and ignore it.
        stat_modifiers.modifiers.remove(modifier)

        if modifier.modifier_type == StatModifierType.FLAT:
            stat.boost_flat -= modifier.value
        elif modifier.modifier_type == StatModifierType.PERCENT:
            stat.boost_percent -= modifier.value

        recalculate_stat(stat)
    except ValueError:
        return
