"""Helper functions for creating and manipulating marriage betrothals.

"""

from minerva.characters.betrothal_data import Betrothal, BetrothalTracker
from minerva.datetime import SimDate
from minerva.ecs import GameObject
from minerva.sim_db import SimDB


def init_betrothal(character_a: GameObject, character_b: GameObject) -> None:
    """Initialize a betrothal between two characters."""
    world = character_a.world
    character_a_betrothals = character_a.get_component(BetrothalTracker)
    character_b_betrothals = character_b.get_component(BetrothalTracker)

    # Check that both characters are not married
    if character_a_betrothals.current_betrothal:
        raise RuntimeError(f"Error: {character_a.name_with_uid} is already betrothed.")

    if character_b_betrothals.current_betrothal:
        raise RuntimeError(f"Error: {character_b.name_with_uid} is already betrothed.")

    current_date = world.resources.get_resource(SimDate)
    db = world.resources.get_resource(SimDB).db
    cur = db.cursor()

    # Create a new marriage entries into the database
    a_to_b = world.gameobjects.spawn_gameobject(
        components=[
            Betrothal(character_a, character_b, current_date),
        ]
    )
    character_a_betrothals.current_betrothal = a_to_b
    cur.execute(
        """
        INSERT INTO betrothals (uid, character_id, betrothed_id, start_date)
        VALUES (?, ?, ?, ?);
        """,
        (a_to_b.uid, character_b.uid, character_a.uid, current_date.to_iso_str()),
    )

    b_to_a = world.gameobjects.spawn_gameobject(
        components=[
            Betrothal(character_b, character_a, current_date),
        ]
    )
    character_b_betrothals.current_betrothal = b_to_a
    cur.execute(
        """
        INSERT INTO betrothals (uid, character_id, betrothed_id, start_date)
        VALUES (?, ?, ?, ?);
        """,
        (b_to_a.uid, character_a.uid, character_b.uid, current_date.to_iso_str()),
    )

    db.commit()


def terminate_betrothal(character_a: GameObject, character_b: GameObject) -> None:
    """Remove the betrothal from the characters."""
    world = character_a.world
    character_a_betrothals = character_a.get_component(BetrothalTracker)
    character_b_betrothals = character_b.get_component(BetrothalTracker)

    # Check that both characters are betrothed to each other
    character_a_current_betrothal = character_a_betrothals.current_betrothal
    character_b_current_betrothal = character_b_betrothals.current_betrothal

    if character_a_current_betrothal is None:
        raise RuntimeError(
            f"Error: {character_a.name_with_uid} is not betrothed to anyone."
        )
    elif (
        character_a_current_betrothal.get_component(Betrothal).betrothed != character_b
    ):
        raise RuntimeError(
            f"Error: {character_a.name_with_uid} is not betrothed to"
            f" {character_b.name_with_uid}."
        )

    if character_b_current_betrothal is None:
        raise RuntimeError(
            f"Error: {character_b.name_with_uid} is not betrothed to anyone."
        )
    elif (
        character_b_current_betrothal.get_component(Betrothal).betrothed != character_a
    ):
        raise RuntimeError(
            f"Error: {character_b.name_with_uid} is not married to"
            f" {character_a.name_with_uid}."
        )

    current_date = world.resources.get_resource(SimDate).to_iso_str()
    db = world.resources.get_resource(SimDB).db
    cur = db.cursor()

    # Update marriage entries in the database
    cur.execute(
        """
        UPDATE betrothals SET end_date=?
        WHERE uid=?;
        """,
        (current_date, character_a_current_betrothal.uid),
    )
    character_a_betrothals.past_betrothal_ids.append(character_a_current_betrothal.uid)
    character_a_current_betrothal.destroy()
    character_a_betrothals.current_betrothal = None

    cur.execute(
        """
        UPDATE betrothals SET end_date=?
        WHERE uid=?;
        """,
        (current_date, character_b_current_betrothal.uid),
    )
    character_b_betrothals.past_betrothal_ids.append(character_b_current_betrothal.uid)
    character_b_current_betrothal.destroy()
    character_b_betrothals.current_betrothal = None

    db.commit()
