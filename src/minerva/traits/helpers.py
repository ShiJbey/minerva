"""Modifier and accessor functions to manipulate traits."""

from __future__ import annotations

from minerva.ecs import GameObject
from minerva.traits.base_types import Trait, TraitLibrary, TraitManager


def add_trait(gameobject: GameObject, trait_id: str) -> bool:
    """Add a trait to a GameObject.

    Parameters
    ----------
    gameobject
        The gameobject to add the trait to.
    trait_id
        The trait.

    Returns
    -------
    bool
        True if the trait was added successfully, False if already present or
        if the trait conflict with existing traits.
    """

    library = gameobject.world.resources.get_resource(TraitLibrary)
    trait = library.get_trait(trait_id)

    traits = gameobject.get_component(TraitManager)

    if trait_id in traits.traits:
        return False

    if _has_conflicting_trait(gameobject, trait):
        return False

    traits.traits[trait.trait_id] = trait

    for effect in trait.effects:
        effect.apply(gameobject)

    return True


def remove_trait(gameobject: GameObject, trait_id: str) -> bool:
    """Remove a trait from a GameObject.

    Parameters
    ----------
    gameobject
        The gameobject to remove the trait from.
    trait_id
        The trait.

    Returns
    -------
    bool
        True if the trait was removed successfully, False otherwise.
    """

    library = gameobject.world.resources.get_resource(TraitLibrary)
    trait = library.get_trait(trait_id)

    traits = gameobject.get_component(TraitManager)

    if trait_id in traits.traits:
        del traits.traits[trait.trait_id]

        for effect in trait.effects:
            effect.remove(gameobject)

        return True

    return False


def _has_conflicting_trait(gameobject: GameObject, trait: Trait) -> bool:
    """Check if a trait conflicts with current traits.

    Parameters
    ----------
    gameobject
        The object to check.
    trait
        The trait to check.

    Returns
    -------
    bool
        True if the trait conflicts with any of the current traits or if any current
        traits conflict with the given trait. False otherwise.
    """
    traits = gameobject.get_component(TraitManager)

    for existing_trait in traits.traits.values():
        if existing_trait.trait_id in trait.conflicting_traits:
            return True

        if trait.trait_id in existing_trait.conflicting_traits:
            return True

    return False


def has_trait(gameobject: GameObject, trait_id: str) -> bool:
    """Check if a GameObject has a given trait.

    Parameters
    ----------
    gameobject
        The gameobject to check.
    trait_id
        The trait.

    Returns
    -------
    bool
        True if the trait was removed successfully, False otherwise.
    """

    return trait_id in gameobject.get_component(TraitManager).traits
