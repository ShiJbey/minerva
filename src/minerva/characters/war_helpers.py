"""Helper functions for wrs and alliances."""

import statistics
from typing import Optional

from minerva.actions.scheme_helpers import create_scheme, destroy_scheme
from minerva.actions.scheme_types import AllianceScheme, CoupScheme, WarScheme
from minerva.characters.components import Family, Martial, Prowess
from minerva.characters.stat_helpers import (
    StatLevel,
    get_martial_level,
    get_stewardship_level,
)
from minerva.characters.war_data import Alliance, War, WarRole, WarTracker
from minerva.datetime import SimDate
from minerva.ecs import GameObject
from minerva.sim_db import SimDB


def start_alliance(*families: GameObject) -> GameObject:
    """Start a new alliance between the two families."""

    if len(families) < 2:
        raise ValueError("An alliance requires a minimum of two families.")

    founder_family = families[0]
    founder_family_component = founder_family.get_component(Family)
    founder = founder_family_component.head

    world = founder_family.world
    current_date = world.resources.get_resource(SimDate)

    if founder is None:
        raise TypeError("Alliance founding family is missing a family head.")

    # Create the new alliance object
    alliance = world.gameobjects.spawn_gameobject()
    alliance_component = alliance.add_component(
        Alliance(
            founder=founder,
            founder_family=founder_family,
            member_families=families,
            start_date=current_date,
        )
    )

    # Verify that none of the families are currently in an alliance and set
    # their alliance variables
    for family in alliance_component.member_families:
        family_component = family.get_component(Family)
        if family_component.alliance is not None:
            raise RuntimeError(
                f"The {family_component.name} family already belongs to an alliance."
            )
        else:
            family_component.alliance = alliance

    db = world.resources.get_resource(SimDB).db
    db_cursor = db.cursor()

    db_cursor.execute(
        """
        INSERT INTO alliances (uid, founder_id, founder_family_id, start_date)
        VALUES (?, ?, ?, ?);
        """,
        (
            alliance.uid,
            founder.uid,
            founder_family.uid,
            current_date.to_iso_str(),
        ),
    )

    db_cursor.executemany(
        """
        INSERT INTO alliance_members (family_id, alliance_id, date_joined)
        VALUES (?, ?, ?);
        """,
        [
            (f.uid, alliance.uid, current_date.to_iso_str())
            for f in alliance_component.member_families
        ],
    )

    db.commit()

    return alliance


def join_alliance(alliance: GameObject, family: GameObject) -> None:
    """Add a family to an alliance."""
    alliance_component = alliance.get_component(Alliance)
    family_component = family.get_component(Family)

    if family_component.alliance is not None:
        raise RuntimeError("Family cannot belong to more than one alliance.")

    if family in alliance_component.member_families:
        raise RuntimeError("Family is already a a member of this alliance.")

    family_component.alliance = alliance
    alliance_component.member_families.add(family)

    world = alliance.world
    current_date = world.resources.get_resource(SimDate)
    db = world.resources.get_resource(SimDB).db
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO alliance_members (family_id, alliance_id, date_joined)
        VALUES (?, ?, ?);
        """,
        (family.uid, alliance.uid, current_date.to_iso_str()),
    )

    db.commit()


def end_alliance(alliance: GameObject) -> None:
    """End an existing alliance between families."""

    world = alliance.world
    current_date = world.resources.get_resource(SimDate)
    db = world.resources.get_resource(SimDB).db
    db_cursor = db.cursor()

    alliance_component = alliance.get_component(Alliance)
    alliance_component.end_date = current_date.copy()

    # Remove the alliance from all member families
    for family in alliance_component.member_families:
        family_component = family.get_component(Family)
        family_component.alliance = None

    db_cursor.execute(
        """UPDATE alliances SET end_date=? WHERE uid=?""",
        (current_date.to_iso_str(), alliance.uid),
    )

    db_cursor.executemany(
        """
        UPDATE alliance_members
        SET date_left=?
        WHERE family_id=? AND alliance_id=?;
        """,
        [
            (current_date.to_iso_str(), f.uid, alliance.uid)
            for f in alliance_component.member_families
        ],
    )

    db.commit()

    alliance.destroy()


def start_war(
    family_a: GameObject, family_b: GameObject, contested_territory: GameObject
) -> GameObject:
    """One family declares war on another."""
    world = family_a.world
    current_date = world.resources.get_resource(SimDate)
    db = world.resources.get_resource(SimDB).db
    db_cursor = db.cursor()

    family_a_wars = family_a.get_component(WarTracker)
    family_b_wars = family_b.get_component(WarTracker)

    war_obj = world.gameobjects.spawn_gameobject(
        components=[
            War(
                family_a,
                family_b,
                start_date=current_date.copy(),
                contested_territory=contested_territory,
            )
        ]
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


def end_war(war: GameObject, winner: Optional[GameObject]) -> None:
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
        (current_date.to_iso_str(), winner, war.uid),
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


def create_alliance_scheme(initiator: GameObject) -> GameObject:
    """Creates a new alliance scheme."""
    scheme = create_scheme(
        world=initiator.world,
        scheme_type="alliance",
        required_time=3,
        initiator=initiator,
        data=AllianceScheme(),
    )

    # Update the database with scheme-specific information

    return scheme


def destroy_alliance_scheme(scheme: GameObject) -> None:
    """Destroy an alliance scheme."""
    destroy_scheme(scheme)


def create_war_scheme(
    initiator: GameObject, target: GameObject, territory: GameObject
) -> GameObject:
    """Create a new war scheme."""
    scheme = create_scheme(
        world=initiator.world,
        scheme_type="war",
        required_time=3,
        initiator=initiator,
        data=WarScheme(aggressor=initiator, defender=target, territory=territory),
    )

    # Update the database with scheme-specific information

    return scheme


def destroy_war_scheme(scheme: GameObject) -> None:
    """Destroy a war scheme."""
    destroy_scheme(scheme)


def create_coup_scheme(initiator: GameObject, target: GameObject) -> GameObject:
    """Create a new war scheme."""
    scheme = create_scheme(
        world=initiator.world,
        scheme_type="coup",
        required_time=5,
        initiator=initiator,
        data=CoupScheme(target=target),
    )

    # Update the database with scheme-specific information

    return scheme


def destroy_coup_scheme(scheme: GameObject) -> None:
    """Destroy a coup scheme."""
    destroy_scheme(scheme)


def calculate_alliance_martial(*families: GameObject) -> float:
    """Calculates the avg martial score of a collection of families."""
    martial_sum: float = 0.0
    total_warriors: int = 0

    for family in families:
        family_component = family.get_component(Family)

        if len(family_component.warriors) == 0 and family_component.head:
            martial_sum += family_component.head.get_component(Martial).value
            total_warriors += 1

        else:
            for character in family_component.warriors:
                martial_sum += character.get_component(Martial).value
                total_warriors += 1

    if total_warriors == 0:
        return 0

    return martial_sum / total_warriors


def calculate_warrior_prowess_dist(war: War) -> tuple[float, float]:
    """Calculate the mean and std deviation of prowess scores for all warriors."""
    prowess_scores: list[float] = []

    for warrior in war.aggressor.get_component(Family).warriors:
        prowess_scores.append(warrior.get_component(Prowess).value)

    for warrior in war.defender.get_component(Family).warriors:
        prowess_scores.append(warrior.get_component(Prowess).value)

    for family in war.aggressor_allies:
        for warrior in family.get_component(Family).warriors:
            prowess_scores.append(warrior.get_component(Prowess).value)

    for family in war.defender_allies:
        for warrior in family.get_component(Family).warriors:
            prowess_scores.append(warrior.get_component(Prowess).value)

    if len(prowess_scores) == 0:
        return 0, 0
    elif len(prowess_scores) == 1:
        return prowess_scores[0], 0

    score_mean = statistics.mean(prowess_scores)
    score_stdev = statistics.stdev(prowess_scores)

    return score_mean, score_stdev


def calculate_war_score(lead_family: GameObject, allies: list[GameObject]) -> int:
    """Calculate a strength score for a family and their allies in a war."""

    total_prowess: float = 0

    for warrior in lead_family.get_component(Family).warriors:
        total_prowess += warrior.get_component(Prowess).value

    for family in allies:
        for warrior in family.get_component(Family).warriors:
            total_prowess += warrior.get_component(Prowess).value

    final_score = total_prowess

    # Apply changes for lead family head martial skill
    lead_family_head = lead_family.get_component(Family).head
    assert lead_family_head is not None
    martial_skill_level = get_martial_level(lead_family_head)

    if martial_skill_level == StatLevel.TERRIBLE:
        final_score = final_score * 0.6  # Final score - 40%

    elif martial_skill_level == StatLevel.BAD:
        final_score = final_score * 0.9  # Final score - 10%

    elif martial_skill_level == StatLevel.GOOD:
        final_score = final_score * 1.1  # Final score + 10%

    elif martial_skill_level == StatLevel.EXCELLENT:
        final_score = final_score * 1.4  # Final score + 40%

    # Apply changes for lead family head stewardship
    if allies:
        lead_family_head = lead_family.get_component(Family).head
        assert lead_family_head is not None
        stewardship_skill_level = get_stewardship_level(lead_family_head)

        if stewardship_skill_level == StatLevel.TERRIBLE:
            final_score = final_score * 0.5  # Final score - 50%
        elif stewardship_skill_level == StatLevel.BAD:
            final_score = final_score * 0.6  # Final score - 40%

    return int(final_score)


def calculate_aggressor_win_probability(
    aggressor_score: int, defender_score: float
) -> float:
    """Return the probability of the aggressor defeating the defender."""
    return aggressor_score / (aggressor_score + defender_score + 1e-10)


def get_casualty_chance(
    prowess_mean: float, prowess_stdev: float, prowess: float
) -> float:
    """Get the probability of a character dying in a war."""

    normalized_prowess = (prowess - prowess_mean) / (prowess_stdev + 1e-10)

    if normalized_prowess >= 2:
        return 0.0
    elif normalized_prowess >= 1:
        return 0.1
    elif normalized_prowess >= 0:
        return 0.12
    elif normalized_prowess >= -1:
        return 0.25
    elif normalized_prowess >= -2:
        return 0.4
    else:
        return 0.8
