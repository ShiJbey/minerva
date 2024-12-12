"""Helper functions for creating and manipulating marriage betrothals.

"""

from minerva.characters.components import Betrothal, Character
from minerva.datetime import SimDate
from minerva.ecs import Entity
from minerva.sim_db import SimDB


def init_betrothal(character_a: Entity, character_b: Entity) -> None:
    """Initialize a betrothal between two characters."""
    world = character_a.world
    character_a_component = character_a.get_component(Character)
    character_b_component = character_b.get_component(Character)

    # Check that both characters are not married
    if character_a_component.betrothed_to:
        raise RuntimeError(f"Error: {character_a.name_with_uid} is already betrothed.")

    if character_b_component.betrothed_to:
        raise RuntimeError(f"Error: {character_b.name_with_uid} is already betrothed.")

    current_date = world.get_resource(SimDate)
    db = world.get_resource(SimDB).db
    cur = db.cursor()

    # Create a new marriage entries into the database
    a_to_b = world.entity(
        components=[
            Betrothal(character_a, character_b, current_date),
        ]
    )
    character_a_component.betrothed_to = character_b
    character_a_component.betrothal = a_to_b
    cur.execute(
        """
        INSERT INTO betrothals (uid, character_id, betrothed_id, start_date)
        VALUES (?, ?, ?, ?);
        """,
        (a_to_b.uid, character_b.uid, character_a.uid, current_date.to_iso_str()),
    )

    b_to_a = world.entity(
        components=[
            Betrothal(character_b, character_a, current_date),
        ]
    )
    character_b_component.betrothed_to = character_a
    character_b_component.betrothal = b_to_a
    cur.execute(
        """
        INSERT INTO betrothals (uid, character_id, betrothed_id, start_date)
        VALUES (?, ?, ?, ?);
        """,
        (b_to_a.uid, character_a.uid, character_b.uid, current_date.to_iso_str()),
    )

    db.commit()


def terminate_betrothal(character_a: Entity, character_b: Entity) -> None:
    """Remove the betrothal from the characters."""
    world = character_a.world
    character_a_component = character_a.get_component(Character)
    character_b_component = character_b.get_component(Character)

    if character_a_component.betrothed_to != character_b:
        raise RuntimeError(
            f"Error: {character_a.name_with_uid} is not betrothed to"
            f" {character_b.name_with_uid}."
        )

    if character_b_component.betrothed_to != character_a:
        raise RuntimeError(
            f"Error: {character_b.name_with_uid} is not married to"
            f" {character_a.name_with_uid}."
        )

    current_date = world.get_resource(SimDate).to_iso_str()
    db = world.get_resource(SimDB).db
    cur = db.cursor()

    character_a_current_betrothal = character_a_component.betrothal
    character_b_current_betrothal = character_b_component.betrothal

    assert character_a_current_betrothal is not None
    assert character_b_current_betrothal is not None

    # Update marriage entries in the database
    cur.execute(
        """
        UPDATE betrothals SET end_date=?
        WHERE uid=?;
        """,
        (current_date, character_a_current_betrothal.uid),
    )
    character_a_component.past_betrothals.append(character_a_current_betrothal)
    character_a_component.betrothal = None
    character_a_component.betrothed_to = None

    cur.execute(
        """
        UPDATE betrothals SET end_date=?
        WHERE uid=?;
        """,
        (current_date, character_b_current_betrothal.uid),
    )
    character_b_component.past_betrothals.append(character_b_current_betrothal)
    character_b_component.betrothal = None
    character_b_component.betrothed_to = None

    db.commit()
