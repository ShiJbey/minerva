"""Helper functions for interacting with Schemes."""

from minerva.actions.base_types import Scheme, SchemeData, SchemeManager
from minerva.datetime import SimDate
from minerva.ecs import Entity, World
from minerva.sim_db import SimDB


def create_scheme(
    world: World,
    scheme_type: str,
    required_time: int,
    initiator: Entity,
    data: SchemeData,
) -> Entity:
    """Create a new scheme."""
    scheme_obj = world.entity()

    current_date = world.get_resource(SimDate)

    scheme_component = scheme_obj.add_component(
        Scheme(
            scheme_type=scheme_type,
            initiator=initiator,
            required_time=required_time,
            data=data,
            date_started=current_date.copy(),
        )
    )

    scheme_obj.add_component(data)

    db = world.get_resource(SimDB).db
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


def destroy_scheme(scheme: Entity) -> None:
    """Destroy a scheme object."""
    scheme_component = scheme.get_component(Scheme)

    for member in [*scheme_component.members]:
        remove_member_from_scheme(scheme, member)

    scheme_component.initiator.get_component(SchemeManager)

    db = scheme.world.get_resource(SimDB).db
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


def add_member_to_scheme(scheme: Entity, new_member: Entity) -> None:
    """Add a new member to a scheme."""
    scheme_component = scheme.get_component(Scheme)

    scheme_component.members.add(new_member)

    db = scheme.world.get_resource(SimDB).db
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO scheme_members (scheme_id, member_id) VALUES (?, ?);
        """,
        (scheme.uid, new_member.uid),
    )

    db.commit()

    new_member.get_component(SchemeManager).add_scheme(scheme)


def remove_member_from_scheme(scheme: Entity, member: Entity) -> None:
    """Remove a member from a scheme."""
    scheme_component = scheme.get_component(Scheme)

    scheme_component.members.remove(member)

    db = scheme.world.get_resource(SimDB).db
    cursor = db.cursor()

    cursor.execute(
        """
        DELETE FROM scheme_members WHERE scheme_id=? AND member_id=?;
        """,
        (scheme.uid, member.uid),
    )

    db.commit()

    member.get_component(SchemeManager).remove_scheme(scheme)


def get_character_schemes_of_type(
    character: Entity, scheme_type: str, did_initiate: bool = False
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
