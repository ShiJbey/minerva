"""Modifier and accessor functions for stats."""

from __future__ import annotations

import math
from typing import Optional, Type

from minerva.ecs import GameObject
from minerva.relationships.base_types import (
    RelationshipManager,
    SocialRuleLibrary,
    get_relationship,
)
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

    if stat.max_value:
        final_value = min(final_value, stat.max_value)

    if stat.min_value:
        final_value = max(final_value, stat.min_value)

    if stat.is_discrete:
        final_value = math.trunc(final_value)

    stat.value = final_value

    if stat.cached_value != final_value:
        stat.cached_value = final_value
        stat.on_value_changed()

    return final_value


def get_stat(gameobject: GameObject, state_name: str) -> StatComponent:
    """Get the stat from the gameobject with the given name."""

    return gameobject.get_component(StatManager).stats[state_name]


def get_stat_value(gameobject: GameObject, stat_type: Type[StatComponent]) -> float:
    """Get the value of the stat with the given type.

    Parameters
    ----------
    gameobject
        A GameObject.
    stat_type
        The class type of the stat to calculate.

    Returns
    -------
    float
        The current value of the stat.
    """
    stat = gameobject.get_component(stat_type)

    return _recalculate_stat(stat)


def get_stat_value_with_name(gameobject: GameObject, stat_name: str) -> float:
    """Get the value of the stat with the given type.

    Parameters
    ----------
    gameobject
        A GameObject.
    stat_name
        The name of the stat to calculate.

    Returns
    -------
    float
        The current value of the stat.
    """
    stat = gameobject.get_component(StatManager).stats[stat_name]

    return _recalculate_stat(stat)


def _recalculate_relationship_stat(
    owner: GameObject,
    target: GameObject,
    relationship: GameObject,
    stat: StatComponent,
) -> float:
    """Recalculate the given stat for the given relationship."""

    final_value: float = stat.base_value
    sum_percent_add: float = 0.0

    stat.active_modifiers.clear()

    # Get all the stat modifiers
    for modifier in stat.modifiers:
        if modifier.modifier_type == StatModifierType.FLAT:
            final_value += modifier.value

        elif modifier.modifier_type == StatModifierType.PERCENT:
            sum_percent_add += modifier.value

    # Get modifiers from owners outgoing modifiers
    owner_relationship_modifiers = owner.get_component(
        RelationshipManager
    ).outgoing_modifiers
    for relationship_modifier in owner_relationship_modifiers:
        if stat.stat_name not in relationship_modifier.modifiers:
            continue

        if relationship_modifier.check_preconditions_for(relationship):
            modifier = relationship_modifier.modifiers[stat.stat_name]
            if modifier.modifier_type == StatModifierType.FLAT:
                final_value += modifier.value

            elif modifier.modifier_type == StatModifierType.PERCENT:
                sum_percent_add += modifier.value

    # Get modifiers from targets incoming relationship modifiers
    target_relationship_modifiers = target.get_component(
        RelationshipManager
    ).incoming_modifiers
    for relationship_modifier in target_relationship_modifiers:
        if stat.stat_name not in relationship_modifier.modifiers:
            continue

        if relationship_modifier.check_preconditions_for(relationship):
            modifier = relationship_modifier.modifiers[stat.stat_name]
            if modifier.modifier_type == StatModifierType.FLAT:
                final_value += modifier.value

            elif modifier.modifier_type == StatModifierType.PERCENT:
                sum_percent_add += modifier.value

    # Get modifiers from social rules
    social_rule_library = relationship.world.resources.get_resource(SocialRuleLibrary)
    for rule in social_rule_library.rules:
        if stat.stat_name not in rule.modifiers:
            continue

        if rule.check_preconditions_for(relationship):
            modifier = rule.modifiers[stat.stat_name]
            if modifier.modifier_type == StatModifierType.FLAT:
                final_value += modifier.value

            elif modifier.modifier_type == StatModifierType.PERCENT:
                sum_percent_add += modifier.value

    final_value = final_value + (final_value * sum_percent_add)

    if stat.max_value:
        final_value = min(final_value, stat.max_value)

    if stat.min_value:
        final_value = max(final_value, stat.min_value)

    if stat.is_discrete:
        final_value = math.trunc(final_value)

    stat.value = final_value

    if stat.cached_value != final_value:
        stat.cached_value = final_value
        stat.on_value_changed()

    return final_value


def get_relationship_stat(
    owner: GameObject,
    target: GameObject,
    stat_name: str,
) -> StatComponent:
    """Get the value of the stat with the given name."""

    return get_relationship(owner, target).get_component(StatManager).stats[stat_name]


def get_relationship_stat_value_with_name(
    owner: GameObject,
    target: GameObject,
    stat_name: str,
) -> float:
    """Get the value of the stat with the given name."""
    relationship = get_relationship(owner, target)
    stat_component = relationship.get_component(StatManager).stats[stat_name]

    return _recalculate_relationship_stat(owner, target, relationship, stat_component)


def get_relationship_stat_value(
    owner: GameObject,
    target: GameObject,
    stat_type: Type[StatComponent],
) -> float:
    """Get the value of the stat with the given type."""
    relationship = get_relationship(owner, target)
    stat_component = relationship.get_component(stat_type)

    return _recalculate_relationship_stat(owner, target, relationship, stat_component)


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


def remove_stat_modifier(
    target: GameObject,
    stat_name: str,
    modifier: StatModifier,
) -> None:
    """Remove a modifier from the stat with the given name."""

    target.get_component(StatManager).stats[stat_name].remove_modifier(modifier)


def add_relationship_stat_modifier(
    owner: GameObject,
    target: GameObject,
    stat_name: str,
    modifier: StatModifier,
) -> None:
    """Add a modifier to the stat with the given name."""

    (
        get_relationship(owner, target)
        .get_component(StatManager)
        .stats[stat_name]
        .add_modifier(modifier)
    )


def remove_relationship_stat_modifier(
    owner: GameObject,
    target: GameObject,
    stat_name: str,
    modifier: StatModifier,
) -> None:
    """Remove a modifier from the stat with the given name."""

    (
        get_relationship(owner, target)
        .get_component(StatManager)
        .stats[stat_name]
        .remove_modifier(modifier)
    )
