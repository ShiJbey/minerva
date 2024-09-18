"""Helper functions for wrs and alliances."""

from minerva.characters.war_data import (
    Alliance,
    AllianceTracker,
    War,
    WarRole,
    WarTracker,
)
from minerva.datetime import SimDate
from minerva.ecs import GameObject
from minerva.sim_db import SimDB


def start_alliance(family_a: GameObject, family_b: GameObject) -> None:
    """Start a new alliance between the two families."""
    world = family_a.world
    current_date = world.resources.get_resource(SimDate)
    db = world.resources.get_resource(SimDB).db
    db_cursor = db.cursor()

    a_to_b_alliance_obj = world.gameobjects.spawn_gameobject(
        components=[Alliance(family_a, family_b, current_date.copy())]
    )

    family_a_alliances = family_a.get_component(AllianceTracker)
    family_a_alliances.alliances[family_b.uid] = a_to_b_alliance_obj

    db_cursor.execute(
        """
        INSERT INTO alliances (uid, family_id, ally_id, start_date)
        VALUES (?, ?, ?, ?);
        """,
        (
            a_to_b_alliance_obj.uid,
            family_a.uid,
            family_b.uid,
            current_date.to_iso_str(),
        ),
    )

    b_to_a_alliance_obj = world.gameobjects.spawn_gameobject(
        components=[Alliance(family_a, family_b, current_date.copy())]
    )

    family_b_alliances = family_b.get_component(AllianceTracker)
    family_b_alliances.alliances[family_a.uid] = b_to_a_alliance_obj

    db_cursor.execute(
        """
        INSERT INTO alliances (uid, family_id, ally_id, start_date)
        VALUES (?, ?, ?, ?);
        """,
        (
            b_to_a_alliance_obj.uid,
            family_b.uid,
            family_a.uid,
            current_date.to_iso_str(),
        ),
    )

    db.commit()


def end_alliance(family_a: GameObject, family_b: GameObject) -> None:
    """End an existing alliance between families."""

    world = family_a.world
    current_date = world.resources.get_resource(SimDate)
    db = world.resources.get_resource(SimDB).db
    db_cursor = db.cursor()

    family_a_alliances = family_a.get_component(AllianceTracker)
    family_b_alliances = family_b.get_component(AllianceTracker)

    a_to_b_alliance_obj = family_a_alliances.alliances[family_b.uid]
    b_to_a_alliance_obj = family_b_alliances.alliances[family_a.uid]

    del family_a_alliances.alliances[family_b.uid]
    del family_b_alliances.alliances[family_a.uid]

    db_cursor.executemany(
        """
        UPDATE alliances
        SET end_date=?
        WHERE uid=?;
        """,
        [
            (current_date.to_iso_str(), a_to_b_alliance_obj.uid),
            (current_date.to_iso_str(), b_to_a_alliance_obj.uid),
        ],
    )

    a_to_b_alliance_obj.destroy()
    b_to_a_alliance_obj.destroy()

    db.commit()


def start_war(family_a: GameObject, family_b: GameObject) -> GameObject:
    """One family declares war on another."""
    world = family_a.world
    current_date = world.resources.get_resource(SimDate)
    db = world.resources.get_resource(SimDB).db
    db_cursor = db.cursor()

    family_a_wars = family_a.get_component(WarTracker)
    family_b_wars = family_b.get_component(WarTracker)

    war_obj = world.gameobjects.spawn_gameobject(
        components=[War(family_a, family_b, current_date.copy())]
    )

    family_a_wars.offensive_wars.add(war_obj)
    family_b_wars.defensive_wars.add(war_obj)

    db_cursor.execute(
        """
        INSERT INTO wars
        (uid, aggressor_id, defender_id, start_date)
        VALUES (?, ?, ?, ?);
        """,
        (war_obj.uid, family_a.uid, family_b.uid, current_date.to_iso_str()),
    )

    db_cursor.executemany(
        """
        INSERT INTO war_participants (family_id, war_id, role, date_joined)
        VALUES (?, ?, ?, ?);
        """,
        [
            (family_a.uid, war_obj.uid, WarRole.AGGRESSOR, current_date.to_iso_str()),
            (family_b.uid, war_obj.uid, WarRole.DEFENDER, current_date.to_iso_str()),
        ],
    )

    db.commit()

    return war_obj


def end_war(war: GameObject, winner: GameObject) -> None:
    """End a war between families."""

    world = war.world
    current_date = world.resources.get_resource(SimDate)
    db = world.resources.get_resource(SimDB).db
    db_cursor = db.cursor()

    war_component = war.get_component(War)

    aggressor = war_component.aggressor
    defender = war_component.defender

    aggressor_wars = aggressor.get_component(WarTracker)
    defender_wars = defender.get_component(WarTracker)

    aggressor_wars.offensive_wars.remove(war)
    defender_wars.defensive_wars.remove(war)

    for ally in war_component.aggressor_allies:
        ally_wars = ally.get_component(WarTracker)
        ally_wars.offensive_wars.remove(war)

    for ally in war_component.defender_allies:
        ally_wars = ally.get_component(WarTracker)
        ally_wars.defensive_wars.remove(war)

    db_cursor.execute(
        """
        UPDATE wars SET end_date=?, winner_id=? WHERE uid=?;
        """,
        (current_date.to_iso_str(), winner.uid, war.uid),
    )

    db.commit()

    war.destroy()


def join_war_as(war: GameObject, family: GameObject, role: WarRole) -> None:
    """Join a war under the given role."""

    world = war.world
    current_date = world.resources.get_resource(SimDate)
    db = world.resources.get_resource(SimDB).db
    db_cursor = db.cursor()

    war_component = war.get_component(War)
    family_wars = family.get_component(WarTracker)

    if role == WarRole.AGGRESSOR:
        raise ValueError("Error: Cannot join existing war as the aggressor.")
    elif role == WarRole.DEFENDER:
        raise ValueError("Error: Cannot join existing war as the defender.")
    elif role == WarRole.AGGRESSOR_ALLY:
        family_wars.offensive_wars.add(war)
        war_component.aggressor_allies.add(family)
    elif role == WarRole.DEFENDER_ALLY:
        family_wars.defensive_wars.add(war)
        war_component.defender_allies.add(family)
    else:
        raise ValueError("Error: Unrecognized war role.")

    db_cursor.execute(
        """
        INSERT INTO war_participants (family_id, war_id, role, date_joined)
        VALUES (?, ?, ?, ?);
        """,
        (family.uid, war.uid, role, current_date.to_iso_str()),
    )

    db.commit()
