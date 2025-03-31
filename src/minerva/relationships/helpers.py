"""Helper functions for relationships."""

from __future__ import annotations

from minerva.actions.base_types import ProclivityTracker
from minerva.ecs import Entity
from minerva.relationships.base_types import (
    Attraction,
    Opinion,
    Relationship,
    RelationshipManager,
)
from minerva.stats.base_types import (
    StatModifier,
    add_stat_modifier,
    get_stat_value,
    increment_stat_base,
    remove_stat_modifier,
    set_stat_base,
)
from minerva.traits.base_types import Traits


def get_relationship(
    owner: Entity,
    target: Entity,
) -> Entity:
    """Get a relationship from one entity to another.

    This function will create a new instance of a relationship if one does not exist.

    Parameters
    ----------
    owner
        The owner of the relationship.
    target
        The target of the relationship.

    Returns
    -------
    Entity
        A relationship instance.
    """
    relationships = owner.get_component(RelationshipManager)
    if target in relationships.outgoing_relationships:
        return relationships.outgoing_relationships[target]

    return add_relationship(owner, target)


def has_relationship(owner: Entity, target: Entity) -> bool:
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
        True if there is an existing Relationship between the entities,
        False otherwise.
    """
    relationships = owner.get_component(RelationshipManager)
    return target in relationships.outgoing_relationships


def add_relationship(owner: Entity, target: Entity) -> Entity:
    """
    Creates a new relationship from the subject to the target

    Parameters
    ----------
    owner
        The entity that owns the relationship
    target
        The entity that the Relationship is directed toward

    Returns
    -------
    Entity
        The new relationship instance
    """
    if has_relationship(owner, target):
        return get_relationship(owner, target)

    relationship = owner.world.entity()

    relationship.add_component(Relationship(owner=owner, target=target))
    relationship.add_component(Traits())
    relationship.add_component(Opinion())
    relationship.add_component(Attraction())
    relationship.add_component(ProclivityTracker())

    relationship.name = f"[{owner.name} -> {target.name}]"

    _add_outgoing_relationship(owner, relationship)
    _add_incoming_relationship(target, relationship)

    return relationship


def destroy_relationship(owner: Entity, target: Entity) -> bool:
    """Destroy the relationship entity to the target.

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


def deactivate_relationships(entity: Entity) -> None:
    """Deactivates all an objects incoming and outgoing relationships."""

    relationships = entity.get_component(RelationshipManager)

    for _, relationship in relationships.outgoing_relationships.items():
        relationship.deactivate()

    for _, relationship in relationships.incoming_relationships.items():
        relationship.deactivate()


def _add_outgoing_relationship(character: Entity, relationship: Entity) -> None:
    """Add a new relationship to a target.

    Parameters
    ----------
    character
        The entity that the Relationship is directed toward.
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


def _remove_outgoing_relationship(character: Entity, relationship: Entity) -> bool:
    """Remove the outgoing relationship from the character."""
    relationship_manager = character.get_component(RelationshipManager)
    relationship_target = relationship.get_component(Relationship).target

    if relationship_target in relationship_manager.outgoing_relationships:
        del relationship_manager.outgoing_relationships[relationship_target]
        return True

    return False


def _add_incoming_relationship(character: Entity, relationship: Entity) -> None:
    """Add a new incoming relationship to character."""
    relationship_manager = character.get_component(RelationshipManager)
    relationship_owner = relationship.get_component(Relationship).owner

    if relationship_owner in relationship_manager.incoming_relationships:
        raise ValueError(
            f"{character.name_with_uid} has existing incoming relationship from "
            f" {relationship_owner.name}."
        )

    relationship_manager.incoming_relationships[relationship_owner] = relationship


def _remove_incoming_relationship(character: Entity, relationship: Entity) -> bool:
    """Remove the incoming relationship from the character."""
    relationship_manager = character.get_component(RelationshipManager)
    relationship_owner = relationship.get_component(Relationship).owner

    if relationship_owner in relationship_manager.incoming_relationships:
        del relationship_manager.incoming_relationships[relationship_owner]
        return True

    return False


def get_attraction(entity: Entity) -> int:
    """Get the attraction stat for the relationship."""
    return get_stat_value(entity.get_component(Attraction))


def increment_attraction_base(entity: Entity, value: int) -> None:
    """Increment the attraction base value by the given amount."""
    increment_stat_base(entity.get_component(Attraction), value)


def set_attraction_base(entity: Entity, value: int) -> None:
    """Set the base value for an entity's attraction."""
    set_stat_base(entity.get_component(Attraction), value)


def add_attraction_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Add a modifier to the attraction stat."""
    add_stat_modifier(entity, entity.get_component(Attraction), modifier)


def remove_attraction_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Remove a modifier from the attraction stat."""
    remove_stat_modifier(entity, entity.get_component(Attraction), modifier)


def get_opinion(entity: Entity) -> int:
    """Get the lifespan for the entity."""
    return get_stat_value(entity.get_component(Opinion))


def increment_opinion_base(entity: Entity, value: int) -> None:
    """Increment the opinion base value by the given amount."""
    increment_stat_base(entity.get_component(Opinion), value)


def set_opinion_base(entity: Entity, value: int) -> None:
    """Set the base value for an entity's opinion."""
    set_stat_base(entity.get_component(Opinion), value)


def add_opinion_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Add a modifier to the opinion stat."""
    add_stat_modifier(entity, entity.get_component(Opinion), modifier)


def remove_opinion_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Remove a modifier from the opinion stat."""
    remove_stat_modifier(entity, entity.get_component(Opinion), modifier)
