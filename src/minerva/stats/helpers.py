"""Modifier and accessor functions for stats."""

from __future__ import annotations

from minerva.ecs import Entity
from minerva.stats.base_types import (
    StatComponent,
    StatModifierType,
    StatusEffect,
    StatusEffectManager,
)


def default_stat_calc_strategy(stat_component: StatComponent) -> float:
    """Default stat calculation strategy."""
    return _recalculate_stat(stat_component)


def _recalculate_stat(stat: StatComponent) -> float:
    """Recalculate a stat and return its value."""

    stat.active_modifiers.clear()

    final_value: float = stat.base_value
    sum_percent_add: float = 0.0

    # Get all the stat modifiers
    for modifier in stat.modifiers:
        if modifier.modifier_type == StatModifierType.FLAT:
            final_value += modifier.value

        elif modifier.modifier_type == StatModifierType.PERCENT:
            sum_percent_add += modifier.value

    final_value = final_value + (final_value * sum_percent_add)

    return final_value


def add_status_effect(target: Entity, status_effect: StatusEffect) -> None:
    """Add a status effect to a GameObject."""

    target.get_component(StatusEffectManager).status_effects.append(status_effect)

    status_effect.apply(target)


def remove_status_effect(target: Entity, status_effect: StatusEffect) -> bool:
    """Remove a status effect from a GameObject.

    Returns
    -------
    bool
        True if removed successfully.
    """

    try:
        target.get_component(StatusEffectManager).status_effects.remove(status_effect)

        status_effect.remove(target)

        return True

    except ValueError:
        return False
