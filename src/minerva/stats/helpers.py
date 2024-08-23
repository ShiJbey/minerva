"""Modifier and accessor functions for stats."""

from __future__ import annotations

from typing import Optional

from minerva.ecs import GameObject
from minerva.stats.base_types import (
    StatComponent,
    StatManager,
    StatModifier,
    StatModifierType,
    StatusEffect,
    StatusEffectManager,
)


def has_stat_with_name(gameobject: GameObject, name: str) -> bool:
    """Check if the GameObject has a stat with the given name.

    Parameters
    ----------
    gameobject
        The GameObject to check.
    name
        The name of a stat to check for.

    Returns
    -------
    bool
        True if the GameObject has the stat. False otherwise.
    """

    return name in gameobject.get_component(StatManager).stats


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

    # if stat.max_value:
    #     final_value = min(final_value, stat.max_value)

    # if stat.min_value:
    #     final_value = max(final_value, stat.min_value)

    # if stat.is_discrete:
    #     final_value = math.trunc(final_value)

    # # stat.value = final_value

    # if stat.cached_value != final_value:
    #     stat.cached_value = final_value
    #     stat.on_value_changed()

    return final_value


def get_stat(gameobject: GameObject, state_name: str) -> StatComponent:
    """Get the stat from the gameobject with the given name."""

    return gameobject.get_component(StatManager).stats[state_name]


def add_status_effect(target: GameObject, status_effect: StatusEffect) -> None:
    """Add a status effect to a GameObject."""

    target.get_component(StatusEffectManager).status_effects.append(status_effect)

    status_effect.apply(target)


def remove_status_effect(target: GameObject, status_effect: StatusEffect) -> bool:
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


def remove_status_effects_from_source(
    target: GameObject, source: Optional[object]
) -> bool:
    """Remove all modifiers from a given source.

    Returns
    -------
    bool
        True if any modifiers were removed
    """
    status_effect_manager = target.get_component(StatusEffectManager)

    effects_to_remove = [
        entry
        for entry in status_effect_manager.status_effects
        if entry.source == source
    ]

    for entry in effects_to_remove:
        remove_status_effect(target, entry)

    return len(effects_to_remove) > 0


def add_stat_modifier(
    target: GameObject,
    stat_name: str,
    modifier: StatModifier,
) -> None:
    """Add a modifier to the stat with the given name."""

    target.get_component(StatManager).stats[stat_name].add_modifier(modifier)
