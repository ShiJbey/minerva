"""Modifier and accessor functions to manipulate traits."""

from __future__ import annotations

from minerva.ecs import Entity
from minerva.sim_db import SimDB
from minerva.traits.base_types import CharacterTrait, CharacterTraitDatabase, Traits


def add_trait(entity: Entity, trait_id: str) -> bool:
    """Add a trait to an entity.

    Parameters
    ----------
    entity
        The entity to add the trait to.
    trait_id
        The trait.

    Returns
    -------
    bool
        True if the trait was added successfully, False if already present or
        if the trait conflict with existing traits.
    """

    library = entity.world.get_resource(CharacterTraitDatabase)
    trait = library.get_trait(trait_id)

    traits = entity.get_component(Traits)

    if trait.uid in traits.traits:
        return False

    if has_conflicting_trait(entity, trait):
        return False

    traits.traits.add(trait.uid)

    for effect in trait.effects:
        effect.apply(entity)

    db = entity.world.get_resource(SimDB).conn

    db.execute(
        """INSERT INTO character_traits (character_id, trait_id) VALUES (?, ?);""",
        (entity.uid, trait.trait_id),
    )

    db.commit()

    return True


def remove_trait(entity: Entity, trait_id: str) -> bool:
    """Remove a trait from an entity.

    Parameters
    ----------
    entity
        The entity to remove the trait from.
    trait_id
        The trait.

    Returns
    -------
    bool
        True if the trait was removed successfully, False otherwise.
    """

    trait_db = entity.world.get_resource(CharacterTraitDatabase)
    trait = trait_db.get_trait(trait_id)

    traits = entity.get_component(Traits)

    if trait.uid in traits.traits:
        traits.traits.remove(trait.uid)

        for effect in trait.effects:
            effect.remove(entity)

        db = entity.world.get_resource(SimDB).conn

        db.execute(
            """DELETE FROM character_traits WHERE character_id=? AND trait_id=?;""",
            (entity.uid, trait.trait_id),
        )

        db.commit()

        return True

    return False


def has_conflicting_trait(entity: Entity, trait: CharacterTrait) -> bool:
    """Check if a trait conflicts with current traits.

    Parameters
    ----------
    entity
        The object to check.
    trait
        The trait to check.

    Returns
    -------
    bool
        True if the trait conflicts with any of the current traits or if any current
        traits conflict with the given trait. False otherwise.
    """
    trait_db = entity.world.get_resource(CharacterTraitDatabase)
    traits = entity.get_component(Traits)

    for existing_trait_uid in traits.traits:
        existing_trait = trait_db.get_trait_by_uid(existing_trait_uid)

        if existing_trait.trait_id in trait.conflicting_traits:
            return True

        if trait.trait_id in existing_trait.conflicting_traits:
            return True

    return False


def has_trait(entity: Entity, trait_id: str) -> bool:
    """Check if an entity has a given trait.

    Parameters
    ----------
    entity
        The entity to check.
    trait_id
        The trait.

    Returns
    -------
    bool
        True if the trait was removed successfully, False otherwise.
    """
    trait_db = entity.world.get_resource(CharacterTraitDatabase)
    trait = trait_db.get_trait_by_name(trait_id)
    return trait.uid in entity.get_component(Traits).traits


def get_personality_traits(entity: Entity) -> list[CharacterTrait]:
    """Get all a character's personality traits."""
    personality_traits: list[CharacterTrait] = []

    trait_manager = entity.get_component(Traits)
    trait_db = entity.world.get_resource(CharacterTraitDatabase)

    for trait_uid in trait_manager.traits:
        trait = trait_db.get_trait_by_uid(trait_uid)
        if "personality" in trait.tags:
            personality_traits.append(trait)

    personality_traits = sorted(personality_traits, key=lambda t: t.uid)
    return personality_traits
