"""Helper functions for relationships."""

from __future__ import annotations

from typing import Optional

from minerva.ecs import Event, GameObject
from minerva.relationships.base_types import (
    Relationship,
    RelationshipManager,
    Reputation,
    Romance,
    SocialRuleLibrary,
)
from minerva.stats.base_types import (
    StatComponent,
    StatManager,
    StatModifier,
    StatModifierType,
    StatusEffectManager,
)
from minerva.traits.base_types import TraitManager


def get_relationship(
    owner: GameObject,
    target: GameObject,
) -> GameObject:
    """Get a relationship from one GameObject to another.

    This function will create a new instance of a relationship if one does not exist.

    Parameters
    ----------
    owner
        The owner of the relationship.
    target
        The target of the relationship.

    Returns
    -------
    GameObject
        A relationship instance.
    """
    relationships = owner.get_component(RelationshipManager)
    if target in relationships.outgoing:
        return relationships.outgoing[target]

    return add_relationship(owner, target)


def has_relationship(owner: GameObject, target: GameObject) -> bool:
    """Check if there is an existing relationship from the owner to the target.

    Parameters
    ----------
    owner
        The owner of the relationship.
    target
        The target of the relationship.

    Returns
    -------
    bool
        True if there is an existing Relationship between the GameObjects,
        False otherwise.
    """
    relationships = owner.get_component(RelationshipManager)
    return target in relationships.outgoing


def add_relationship(owner: GameObject, target: GameObject) -> GameObject:
    """
    Creates a new relationship from the subject to the target

    Parameters
    ----------
    owner
        The GameObject that owns the relationship
    target
        The GameObject that the Relationship is directed toward

    Returns
    -------
    GameObject
        The new relationship instance
    """
    if has_relationship(owner, target):
        return get_relationship(owner, target)

    relationship = owner.world.gameobjects.spawn_gameobject()

    relationship.add_component(Relationship(owner=owner, target=target))
    relationship.add_component(StatManager())
    relationship.add_component(StatusEffectManager())
    relationship.add_component(TraitManager())
    relationship.add_component(Reputation(default_relationship_stat_calc_strategy))
    relationship.add_component(Romance(default_relationship_stat_calc_strategy))

    relationship.name = f"[{owner.name} -> {target.name}]"

    owner.get_component(RelationshipManager).add_outgoing_relationship(
        target, relationship
    )
    target.get_component(RelationshipManager).add_incoming_relationship(
        owner, relationship
    )

    relationship.world.events.dispatch_event(
        Event("relationship-added", world=relationship.world, relationship=relationship)
    )

    return relationship


def destroy_relationship(owner: GameObject, target: GameObject) -> bool:
    """Destroy the relationship GameObject to the target.

    Parameters
    ----------
    owner
        The owner of the relationship
    target
        The target of the relationship

    Returns
    -------
    bool
        Returns True if a relationship was removed. False otherwise.
    """
    if has_relationship(owner, target):
        relationship = get_relationship(owner, target)
        owner.get_component(RelationshipManager).remove_outgoing_relationship(target)
        target.get_component(RelationshipManager).remove_incoming_relationship(owner)
        relationship.destroy()
        return True

    return False


def deactivate_relationships(gameobject: GameObject) -> None:
    """Deactivates all an objects incoming and outgoing relationships."""

    relationships = gameobject.get_component(RelationshipManager)

    for _, relationship in relationships.outgoing.items():
        relationship.deactivate()

    for _, relationship in relationships.incoming.items():
        relationship.deactivate()


def remove_relationship_modifiers_from_source(
    relationship: GameObject, source: Optional[object]
) -> None:
    """Remove all modifiers from a given source."""
    relationship_manager = relationship.get_component(RelationshipManager)

    relationship_manager.incoming_modifiers = [
        m for m in relationship_manager.incoming_modifiers if m.source != source
    ]

    relationship_manager.outgoing_modifiers = [
        m for m in relationship_manager.outgoing_modifiers if m.source != source
    ]


def default_relationship_stat_calc_strategy(stat_component: StatComponent) -> float:
    """Default stat calculation strategy for relationships."""
    relationship = stat_component.gameobject
    relationship_component = relationship.get_component(Relationship)

    return _recalculate_relationship_stat(
        relationship_component.owner,
        relationship_component.target,
        relationship,
        stat_component,
    )


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
