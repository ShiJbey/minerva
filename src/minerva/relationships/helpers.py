"""Helper functions for relationships."""

from __future__ import annotations

from minerva.ecs import Event, GameObject
from minerva.relationships.base_types import (
    Attraction,
    Opinion,
    Relationship,
    RelationshipManager,
    SocialRuleLibrary,
)
from minerva.stats.base_types import (
    StatComponent,
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
    if target in relationships.outgoing_relationships:
        return relationships.outgoing_relationships[target]

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
    return target in relationships.outgoing_relationships


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
    relationship.add_component(StatusEffectManager())
    relationship.add_component(TraitManager())
    relationship.add_component(Opinion(opinion_calc_strategy))
    relationship.add_component(Attraction(attraction_calc_strategy))

    relationship.name = f"[{owner.name} -> {target.name}]"

    _add_outgoing_relationship(owner, relationship)
    _add_incoming_relationship(target, relationship)

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
        _remove_outgoing_relationship(owner, relationship)
        _remove_incoming_relationship(target, relationship)
        relationship.destroy()
        return True

    return False


def deactivate_relationships(gameobject: GameObject) -> None:
    """Deactivates all an objects incoming and outgoing relationships."""

    relationships = gameobject.get_component(RelationshipManager)

    for _, relationship in relationships.outgoing_relationships.items():
        relationship.deactivate()

    for _, relationship in relationships.incoming_relationships.items():
        relationship.deactivate()


def _add_outgoing_relationship(character: GameObject, relationship: GameObject) -> None:
    """Add a new relationship to a target.

    Parameters
    ----------
    target
        The GameObject that the Relationship is directed toward.
    relationship
        The relationship.
    """
    relationship_manager = character.get_component(RelationshipManager)
    relationship_target = relationship.get_component(Relationship).target
    if relationship in relationship_manager.outgoing_relationships:
        raise ValueError(
            f"{character.name_with_uid} has existing outgoing relationship to "
            f"{relationship_target.name_with_uid}."
        )

    relationship_manager.outgoing_relationships[relationship_target] = relationship


def _remove_outgoing_relationship(
    character: GameObject, relationship: GameObject
) -> bool:
    """Remove the outgoing relationship from the character."""
    relationship_manager = character.get_component(RelationshipManager)
    relationship_target = relationship.get_component(Relationship).target

    if relationship_target in relationship_manager.outgoing_relationships:
        del relationship_manager.outgoing_relationships[relationship_target]
        return True

    return False


def _add_incoming_relationship(character: GameObject, relationship: GameObject) -> None:
    """Add a new incoming relationship to character."""
    relationship_manager = character.get_component(RelationshipManager)
    relationship_owner = relationship.get_component(Relationship).owner

    if relationship_owner in relationship_manager.incoming_relationships:
        raise ValueError(
            f"{character.name_with_uid} has existing incoming relationship from "
            f" {relationship_owner.name}."
        )

    relationship_manager.incoming_relationships[relationship_owner] = relationship


def _remove_incoming_relationship(
    character: GameObject, relationship: GameObject
) -> bool:
    """Remove the incoming relationship from the character."""
    relationship_manager = character.get_component(RelationshipManager)
    relationship_owner = relationship.get_component(Relationship).owner

    if relationship_owner in relationship_manager.incoming_relationships:
        del relationship_manager.incoming_relationships[relationship_owner]
        return True

    return False


def opinion_calc_strategy(stat_component: StatComponent) -> float:
    """Calculation strategy for opinion stats."""

    relationship = stat_component.gameobject
    relationship_component = relationship.get_component(Relationship)
    owner = relationship_component.owner
    target = relationship_component.target

    final_value: float = stat_component.base_value
    sum_percent_add: float = 0.0

    stat_component.active_modifiers.clear()

    # Get all the stat modifiers
    for modifier in stat_component.modifiers:
        if modifier.modifier_type == StatModifierType.FLAT:
            final_value += modifier.value

        elif modifier.modifier_type == StatModifierType.PERCENT:
            sum_percent_add += modifier.value

    # Get modifiers from owners outgoing modifiers
    owner_relationship_modifiers = owner.get_component(
        RelationshipManager
    ).outgoing_modifiers
    for relationship_modifier in owner_relationship_modifiers:
        if relationship_modifier.opinion_modifier is None:
            continue

        if relationship_modifier.evaluate_precondition(relationship):
            modifier = relationship_modifier.opinion_modifier
            if modifier.modifier_type == StatModifierType.FLAT:
                final_value += modifier.value

            elif modifier.modifier_type == StatModifierType.PERCENT:
                sum_percent_add += modifier.value

    # Get modifiers from targets incoming relationship modifiers
    target_relationship_modifiers = target.get_component(
        RelationshipManager
    ).incoming_modifiers
    for relationship_modifier in target_relationship_modifiers:
        if relationship_modifier.opinion_modifier is None:
            continue

        if relationship_modifier.evaluate_precondition(relationship):
            modifier = relationship_modifier.opinion_modifier
            if modifier.modifier_type == StatModifierType.FLAT:
                final_value += modifier.value

            elif modifier.modifier_type == StatModifierType.PERCENT:
                sum_percent_add += modifier.value

    # Get modifiers from social rules
    social_rule_library = relationship.world.resources.get_resource(SocialRuleLibrary)
    for rule in social_rule_library.iter_rules():
        if rule.opinion_modifier is None:
            continue

        if rule.evaluate_precondition(relationship):
            modifier = rule.opinion_modifier
            if modifier.modifier_type == StatModifierType.FLAT:
                final_value += modifier.value

            elif modifier.modifier_type == StatModifierType.PERCENT:
                sum_percent_add += modifier.value

    final_value = final_value + (final_value * sum_percent_add)

    return final_value


def attraction_calc_strategy(stat_component: StatComponent) -> float:
    """Calculation strategy for attraction stats."""
    relationship = stat_component.gameobject
    relationship_component = relationship.get_component(Relationship)
    owner = relationship_component.owner
    target = relationship_component.target

    final_value: float = stat_component.base_value
    sum_percent_add: float = 0.0

    stat_component.active_modifiers.clear()

    # Get all the stat modifiers
    for modifier in stat_component.modifiers:
        if modifier.modifier_type == StatModifierType.FLAT:
            final_value += modifier.value

        elif modifier.modifier_type == StatModifierType.PERCENT:
            sum_percent_add += modifier.value

    # Get modifiers from owners outgoing modifiers
    owner_relationship_modifiers = owner.get_component(
        RelationshipManager
    ).outgoing_modifiers
    for relationship_modifier in owner_relationship_modifiers:
        if relationship_modifier.attraction_modifier is None:
            continue

        if relationship_modifier.evaluate_precondition(relationship):
            modifier = relationship_modifier.attraction_modifier
            if modifier.modifier_type == StatModifierType.FLAT:
                final_value += modifier.value

            elif modifier.modifier_type == StatModifierType.PERCENT:
                sum_percent_add += modifier.value

    # Get modifiers from targets incoming relationship modifiers
    target_relationship_modifiers = target.get_component(
        RelationshipManager
    ).incoming_modifiers
    for relationship_modifier in target_relationship_modifiers:
        if relationship_modifier.attraction_modifier is None:
            continue

        if relationship_modifier.evaluate_precondition(relationship):
            modifier = relationship_modifier.attraction_modifier
            if modifier.modifier_type == StatModifierType.FLAT:
                final_value += modifier.value

            elif modifier.modifier_type == StatModifierType.PERCENT:
                sum_percent_add += modifier.value

    # Get modifiers from social rules
    social_rule_library = relationship.world.resources.get_resource(SocialRuleLibrary)
    for rule in social_rule_library.iter_rules():
        if rule.attraction_modifier is None:
            continue

        if rule.evaluate_precondition(relationship):
            modifier = rule.attraction_modifier
            if modifier.modifier_type == StatModifierType.FLAT:
                final_value += modifier.value

            elif modifier.modifier_type == StatModifierType.PERCENT:
                sum_percent_add += modifier.value

    final_value = final_value + (final_value * sum_percent_add)

    return final_value
