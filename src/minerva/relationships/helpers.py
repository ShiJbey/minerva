"""Helper functions for relationships."""

from __future__ import annotations

from minerva.actions.base_types import ProclivityTracker
from minerva.ecs import Entity, System, World
from minerva.game_action import ActionSystem, GameAction
from minerva.relationships.base_types import (
    Attraction,
    Opinion,
    Relationship,
    RelationshipManager,
    RelationshipModifierDatabase,
)
from minerva.sim_db import SimDB
from minerva.stats.base_types import (
    StatModifier,
    add_stat_modifier,
    get_stat_value,
    increment_stat_base,
    remove_stat_modifier,
    set_stat_base,
)
from minerva.status.data import StatusManager
from minerva.traits.base_types import (
    RelationshipTrait,
    RelationshipTraitDatabase,
    Traits,
)


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
    relationship.add_component(StatusManager())
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


def get_attraction(owner: Entity, target: Entity) -> int:
    """Get the attraction stat for the relationship."""
    action = RecalculateAttraction(owner, target)
    action.execute()
    return get_stat_value(get_relationship(owner, target).get_component(Attraction))


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


def get_opinion(owner: Entity, target: Entity) -> int:
    """Get the lifespan for the entity."""
    RecalculateOpinion(owner, target).execute()
    return get_stat_value(get_relationship(owner, target).get_component(Opinion))


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


class IncrementOpinion(GameAction):
    """Increment the base opinion score from one character to another."""

    __slots__ = ("owner", "target", "amount")

    owner: Entity
    target: Entity
    amount: int

    def __init__(self, owner: Entity, target: Entity, amount: int) -> None:
        super().__init__(owner.world)
        self.owner = owner
        self.target = target
        self.amount = amount

    def on_execute(self) -> None:
        relationship = get_relationship(self.owner, self.target)
        increment_opinion_base(relationship, self.amount)


class IncrementAttraction(GameAction):
    """Increment the base attraction score from one character to another."""

    __slots__ = ("owner", "target", "amount")

    owner: Entity
    target: Entity
    amount: int

    def __init__(self, owner: Entity, target: Entity, amount: int) -> None:
        super().__init__(owner.world)
        self.owner = owner
        self.target = target
        self.amount = amount

    def on_execute(self) -> None:
        relationship = get_relationship(self.owner, self.target)
        increment_attraction_base(relationship, self.amount)


class RecalculateOpinion(GameAction):
    """Recalculate the opinion from one character to another."""

    __slots__ = ("owner", "target", "value")

    owner: Entity
    target: Entity
    value: int

    def __init__(self, owner: Entity, target: Entity) -> None:
        super().__init__(owner.world)
        self.owner = owner
        self.target = target
        self.value = 0

    def on_execute(self) -> None:
        relationship = get_relationship(self.owner, self.target)
        relationship_component = relationship.get_component(Relationship)
        owner = relationship_component.owner
        target = relationship_component.target
        stat_component = relationship.get_component(Opinion)

        final_value: float = stat_component.base_value
        sum_percent_add: float = 0.0

        # Get modifiers from owners outgoing modifiers
        target_relationship_mod_iter = owner.get_component(
            RelationshipManager
        ).iter_opinion_modifiers("outgoing")
        for modifier in target_relationship_mod_iter:
            score = modifier(relationship)
            final_value += score

        # Get modifiers from targets incoming relationship modifiers
        target_relationship_mod_iter = target.get_component(
            RelationshipManager
        ).iter_opinion_modifiers("incoming")
        for modifier in target_relationship_mod_iter:
            score = modifier(relationship)
            final_value += score

        # Get modifiers from global modifier database.
        social_rule_library = relationship.world.get_resource(
            RelationshipModifierDatabase
        )
        for rule in social_rule_library.iter_opinion_modifiers("outgoing"):
            score = rule(relationship)
            final_value += score

        final_value = final_value + (final_value * sum_percent_add)

        self.value = int(final_value)
        stat_component.value = int(final_value)


class RecalculateAttraction(GameAction):
    """Recalculate the attraction from one character to another."""

    __slots__ = ("owner", "target", "value")

    owner: Entity
    target: Entity
    value: int

    def __init__(self, owner: Entity, target: Entity) -> None:
        super().__init__(owner.world)
        self.owner = owner
        self.target = target
        self.value = 0

    def on_execute(self) -> None:
        relationship = get_relationship(self.owner, self.target)
        relationship_component = relationship.get_component(Relationship)
        owner = relationship_component.owner
        target = relationship_component.target
        stat_component = relationship.get_component(Attraction)

        final_value: float = stat_component.base_value
        sum_percent_add: float = 0.0

        # Get modifiers from owners outgoing modifiers
        target_relationship_mod_iter = owner.get_component(
            RelationshipManager
        ).iter_attraction_modifiers("outgoing")
        for modifier in target_relationship_mod_iter:
            score = modifier(relationship)
            final_value += score

        # Get modifiers from targets incoming relationship modifiers
        target_relationship_mod_iter = target.get_component(
            RelationshipManager
        ).iter_attraction_modifiers("incoming")
        for modifier in target_relationship_mod_iter:
            score = modifier(relationship)
            final_value += score

        # Get modifiers from global modifier database
        social_rule_library = relationship.world.get_resource(
            RelationshipModifierDatabase
        )
        for rule in social_rule_library.iter_opinion_modifiers("outgoing"):
            score = rule(relationship)
            final_value += score

        # Get modifiers from social rules
        social_rule_library = relationship.world.get_resource(
            RelationshipModifierDatabase
        )
        for rule in social_rule_library.iter_attraction_modifiers("outgoing"):
            score = rule(relationship)
            final_value += score

        final_value = final_value + (final_value * sum_percent_add)

        self.value = int(final_value)
        stat_component.value = int(final_value)


class RelationshipSystem(System):
    """Registers callbacks and action performers for manipulating relationships."""

    def on_start(self, world: World) -> None:
        action_system = world.get_resource(ActionSystem)
        action_system.add_listener(
            RecalculateOpinion, RelationshipSystem.sync_opinion_with_db, "post"
        )
        action_system.add_listener(
            RecalculateAttraction, RelationshipSystem.sync_attraction_with_db, "post"
        )

    @staticmethod
    def sync_opinion_with_db(action: RecalculateOpinion) -> None:
        """Update the opinion score in the database."""
        relationship = get_relationship(action.owner, action.target)

        db = action.world.get_resource(SimDB).conn
        cursor = db.cursor()

        cursor.execute(
            """UPDATE Relationship SET opinion=? WHERE uid=?""",
            (action.value, relationship.uid),
        )

        db.commit()
        cursor.close()

    @staticmethod
    def sync_attraction_with_db(action: RecalculateAttraction) -> None:
        """Update the attraction score in the database."""
        relationship = get_relationship(action.owner, action.target)

        db = action.world.get_resource(SimDB).conn
        cursor = db.cursor()

        cursor.execute(
            """UPDATE Relationship SET attraction=? WHERE uid=?""",
            (action.value, relationship.uid),
        )

        db.commit()
        cursor.close()

    def on_update(self, world: World) -> None:
        return


def add_relationship_trait(owner: Entity, target: Entity, trait_id: str) -> bool:
    """Add a trait to a relationship entity.

    Parameters
    ----------
    owner
        The character that owns the relationship.
    target
        The character the relationship is about/directed toward.
    trait_id
        The ID of the trait to add.

    Returns
    -------
    bool
        True if the trait was added successfully, False if already present or
        if the trait conflict with existing traits.
    """
    relationship = get_relationship(owner, target)

    library = owner.world.get_resource(RelationshipTraitDatabase)
    trait = library.get_trait(trait_id)

    traits = relationship.get_component(Traits)

    if trait.uid in traits.traits:
        return False

    if _has_conflicting_trait(relationship, trait):
        return False

    traits.traits.add(trait.uid)

    for effect in trait.effects:
        effect.apply(relationship)

    with relationship.world.get_resource(SimDB) as db:
        db.execute(
            """
            INSERT INTO
                RelationshipTrait (uid, owner_uid, target_uid, trait_id)
            VALUES
                (?, ?, ?, ?);
            """,
            (relationship.uid, owner.uid, target.uid, trait_id),
        )

    return True


def remove_relationship_trait(owner: Entity, target: Entity, trait_id: str) -> bool:
    """Remove a trait from a relationship entity.

    Parameters
    ----------
    owner
        The character that owns the relationship.
    target
        The character the relationship is about/directed toward.
    trait_id
        The ID of the trait to remove.

    Returns
    -------
    bool
        True if the trait was removed successfully, False otherwise.
    """
    relationship = get_relationship(owner, target)
    trait_db = relationship.world.get_resource(RelationshipTraitDatabase)
    trait = trait_db.get_trait(trait_id)

    traits = relationship.get_component(Traits)

    if trait.uid in traits.traits:
        traits.traits.remove(trait.uid)

        for effect in trait.effects:
            effect.remove(relationship)

        with relationship.world.get_resource(SimDB) as db:
            db.execute(
                """
                DELETE FROM
                    RelationshipTrait
                WHERE
                    uid=? AND trait_id=?;
                """,
                (relationship.uid, trait_id),
            )

        return True

    return False


def _has_conflicting_trait(relationship: Entity, trait: RelationshipTrait) -> bool:
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
    trait_db = relationship.world.get_resource(RelationshipTraitDatabase)
    traits = relationship.get_component(Traits)

    for existing_trait_uid in traits.traits:
        existing_trait = trait_db.get_trait_by_uid(existing_trait_uid)

        if existing_trait.trait_id in trait.conflicting_traits:
            return True

        if trait.trait_id in existing_trait.conflicting_traits:
            return True

    return False


def has_relationship_trait(owner: Entity, target: Entity, trait_id: str) -> bool:
    """Check if an entity has a given trait.

    Parameters
    ----------
    owner
        The character that owns the relationship.
    target
        The character the relationship is about/directed toward.
    trait_id
        The ID of the trait to check for.

    trait_id
        The trait.

    Returns
    -------
    bool
        True if the trait was removed successfully, False otherwise.
    """
    relationship = get_relationship(owner, target)
    trait_db = relationship.world.get_resource(RelationshipTraitDatabase)
    trait = trait_db.get_trait_by_name(trait_id)
    return trait.uid in relationship.get_component(Traits).traits
