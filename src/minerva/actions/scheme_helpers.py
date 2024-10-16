"""Helper functions for interacting with Schemes."""

from minerva.actions.base_types import Scheme, SchemeManager, SchemeStrategyLibrary
from minerva.datetime import SimDate
from minerva.ecs import World, GameObject
from minerva.sim_db import SimDB


def create_scheme(world: World, scheme_type: str, initiator: GameObject) -> GameObject:
    """Create a new scheme."""
    scheme_obj = world.gameobjects.spawn_gameobject()

    strategy_library = world.resources.get_resource(SchemeStrategyLibrary)

    if not strategy_library.has_strategy(scheme_type):
        raise KeyError(f"Missing strategy for scheme type: {scheme_type}")

    scheme_strategy = strategy_library.get_strategy(scheme_type)
    current_date = world.resources.get_resource(SimDate)

    scheme_component = scheme_obj.add_component(
        Scheme(
            scheme_type=scheme_type,
            initiator=initiator,
            strategy=scheme_strategy,
            date_started=current_date.copy(),
        )
    )

    db = world.resources.get_resource(SimDB).db
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO schemes
        (uid, scheme_type, start_date, initiator_id, description)
        VALUES (?, ?, ?, ?, ?);
        """,
        (
            scheme_obj.uid,
            scheme_type,
            current_date.to_iso_str(),
            initiator.uid,
            scheme_component.get_description(),
        ),
    )

    db.commit()

    add_member_to_scheme(scheme_obj, initiator)

    return scheme_obj


def destroy_scheme(scheme: GameObject) -> None:
    """Destroy a scheme object."""
    scheme_component = scheme.get_component(Scheme)

    for member in [*scheme_component.members]:
        remove_member_from_scheme(scheme, member)

    db = scheme.world.resources.get_resource(SimDB).db
    cursor = db.cursor()

    cursor.execute(
        """
        DELETE FROM schemes WHERE uid=?;
        """,
        (scheme.uid,),
    )

    cursor.execute(
        """
        DELETE FROM scheme_members WHERE scheme_id=?;
        """,
        (scheme.uid,),
    )

    cursor.execute(
        """
        DELETE FROM scheme_targets WHERE scheme_id=?;
        """,
        (scheme.uid,),
    )

    db.commit()

    scheme.destroy()


def add_member_to_scheme(scheme: GameObject, new_member: GameObject) -> None:
    """Add a new member to a scheme."""
    scheme_component = scheme.get_component(Scheme)

    scheme_component.members.add(new_member)

    db = scheme.world.resources.get_resource(SimDB).db
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO scheme_members (scheme_id, member_id) VALUES (?, ?);
        """,
        (scheme.uid, new_member.uid),
    )

    db.commit()

    new_member.get_component(SchemeManager).add_scheme(scheme)


def remove_member_from_scheme(scheme: GameObject, member: GameObject) -> None:
    """Remove a member from a scheme."""
    scheme_component = scheme.get_component(Scheme)

    scheme_component.members.remove(member)

    db = scheme.world.resources.get_resource(SimDB).db
    cursor = db.cursor()

    cursor.execute(
        """
        DELETE FROM scheme_members WHERE scheme_id=? AND member_id=?;
        """,
        (scheme.uid, member.uid),
    )

    db.commit()

    member.get_component(SchemeManager).remove_scheme(scheme)


def add_target_to_scheme(scheme: GameObject, new_target: GameObject) -> None:
    """Add a new target to a scheme."""
    scheme_component = scheme.get_component(Scheme)

    scheme_component.targets.add(new_target)

    db = scheme.world.resources.get_resource(SimDB).db
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO scheme_targets (scheme_id, target_id) VALUES (?, ?);
        """,
        (scheme.uid, new_target.uid),
    )

    db.commit()


def get_character_schemes_of_type(
    character: GameObject, scheme_type: str, did_initiate: bool = False
) -> list[Scheme]:
    """Get all active schemes of a given type that a character initiated."""
    scheme_manager = character.get_component(SchemeManager)

    matching_schemes: list[Scheme] = []

    for scheme in scheme_manager.get_schemes():
        scheme_component = scheme.get_component(Scheme)

        if did_initiate and scheme_component.initiator != character:
            continue

        if scheme_component.get_type() == scheme_type:
            matching_schemes.append(scheme_component)

    return matching_schemes
