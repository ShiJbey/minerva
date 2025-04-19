"""Helper functions for wrs and alliances."""

from __future__ import annotations

import statistics
from typing import Optional

from minerva.actions.scheme_types import (
    AllianceScheme,
    CoupScheme,
    SchemeManager,
    WarScheme,
)
from minerva.characters.components import (
    SKILL_BAD,
    SKILL_EXCELLENT,
    SKILL_NEUTRAL,
    Character,
    Family,
    Martial,
    Prowess,
)
from minerva.characters.helpers import get_martial_skill, get_stewardship_skill
from minerva.characters.war_data import Alliance, War, WarRole, WarTracker
from minerva.ecs import Entity
from minerva.game_action import GameAction
from minerva.game_state import GameState
from minerva.sim_db import SimDB


class StartAllianceScheme(GameAction):
    """Start a new alliance scheme."""

    def on_execute(self) -> None:
        pass


class EndAllianceScheme(GameAction):
    """End an alliance scheme."""

    def on_execute(self) -> None:
        pass


class StartAlliance(GameAction):
    """Add a new alliance to the simulation."""

    def on_execute(self) -> None:
        pass


class EndAlliance(GameAction):
    """Remove an alliance from the simulation."""

    def on_execute(self) -> None:
        pass


class AddFamilyToAlliance(GameAction):
    """Add a family to an alliance."""

    def on_execute(self) -> None:
        pass


class RemoveFamilyFromAlliance(GameAction):
    """Remove a family from an alliance."""

    def on_execute(self) -> None:
        pass


class StartWarScheme(GameAction):
    """Start a new scheme to go to war."""

    def on_execute(self) -> None:
        pass


class EndWarScheme(GameAction):
    """End a war scheme."""

    def on_execute(self) -> None:
        pass


class StartCoupScheme(GameAction):
    """Start a scheme to overthrow the current ruler."""

    def on_execute(self) -> None:
        pass


class EndCoupScheme(GameAction):
    """End a scheme to overthrow the current ruler."""

    def on_execute(self) -> None:
        pass


def start_alliance(founder: Entity, founder_family: Entity) -> Entity:
    """Start a new alliance between the two families."""

    world = founder_family.world
    current_year = world.get_resource(GameState).year

    # Create the new alliance object
    founder_surname = founder.get_component(Character).surname
    alliance = world.entity(name=f"The {founder_surname} Alliance")
    alliance.add_component(
        Alliance(
            founder=founder,
            founder_family=founder_family,
            member_families=[],
            start_year=current_year,
        )
    )

    with world.get_resource(SimDB) as db:
        db.execute(
            """
            INSERT INTO Alliance (uid, founder_uid, founder_family_uid, start_year)
            VALUES (?, ?, ?, ?);
            """,
            (
                alliance.uid,
                founder.uid,
                founder_family.uid,
                current_year,
            ),
        )

    return alliance


def add_family_to_alliance(alliance: Entity, family: Entity) -> None:
    """Add a family to an alliance."""
    alliance_component = alliance.get_component(Alliance)
    family_component = family.get_component(Family)

    if family_component.alliance is not None:
        raise RuntimeError("Family cannot belong to more than one alliance.")

    if family in alliance_component.member_families:
        raise RuntimeError("Family is already a a member of this alliance.")

    family_component.alliance = alliance
    alliance_component.member_families.add(family)

    with alliance.world.get_resource(SimDB) as db:
        db.execute(
            """
            UPDATE Family SET alliance_uid=? WHERE uid=?;
            """,
            (alliance.uid, family.uid),
        )


def remove_family_from_alliance(alliance: Entity, family: Entity) -> None:
    """Remove a  member family from the alliance."""
    alliance_component = alliance.get_component(Alliance)

    alliance_component.member_families.remove(family)
    family.get_component(Family).alliance = None

    with alliance.world.get_resource(SimDB) as db:
        db.execute(
            """UPDATE Family SET alliance_uid=NULL WHERE uid=?""",
            (family.uid,),
        )


def end_alliance(alliance: Entity) -> None:
    """End an existing alliance between families."""

    world = alliance.world
    current_year = world.get_resource(GameState).year

    alliance_component = alliance.get_component(Alliance)
    alliance_component.end_year = current_year

    # Remove the alliance from all member families
    for family in alliance_component.member_families:
        family_component = family.get_component(Family)
        family_component.alliance = None

        with alliance.world.get_resource(SimDB) as db:
            db.execute(
                """UPDATE Family SET alliance_uid=NULL WHERE uid=?""",
                (family.uid,),
            )

    with world.get_resource(SimDB) as db:
        db.execute(
            """UPDATE Alliance SET end_year=? WHERE uid=?""",
            (current_year, alliance.uid),
        )

    alliance.destroy()


def start_war(
    family_a: Entity, family_b: Entity, contested_territory: Entity
) -> Entity:
    """One family declares war on another."""
    world = family_a.world
    current_year = world.get_resource(GameState).year

    family_a_wars = family_a.get_component(WarTracker)
    family_b_wars = family_b.get_component(WarTracker)

    war_obj = world.entity(
        components=[
            War(
                family_a,
                family_b,
                start_year=current_year,
                contested_territory=contested_territory,
            )
        ]
    )

    family_a_wars.offensive_wars.add(war_obj)
    family_b_wars.defensive_wars.add(war_obj)

    with world.get_resource(SimDB) as db:
        db.execute(
            """
            INSERT INTO War
            (uid, aggressor_uid, defender_uid, start_year)
            VALUES (?, ?, ?, ?);
            """,
            (war_obj.uid, family_a.uid, family_b.uid, current_year),
        )

    return war_obj


def end_war(war: Entity, winner: Optional[Entity]) -> None:
    """End a war between families."""

    world = war.world
    current_year = world.get_resource(GameState).year
    db = world.get_resource(SimDB).conn
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
        UPDATE War SET end_year=?, winner_uid=? WHERE uid=?;
        """,
        (current_year, winner, war.uid),
    )

    db.commit()

    war.destroy()


def join_war_as(war: Entity, family: Entity, role: WarRole) -> None:
    """Join a war under the given role."""

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

    # TODO: Log event when a family joins a war


def destroy_alliance_scheme(scheme: Entity) -> None:
    """Destroy an alliance scheme."""
    alliance_scheme = scheme.get_component(AllianceScheme)

    alliance_scheme.initiator.get_component(SchemeManager).alliance_scheme = None

    for member in alliance_scheme.members:
        member.character.get_component(SchemeManager).alliance_scheme = None

    scheme.destroy()


def create_war_scheme(initiator: Entity, target: Entity, territory: Entity) -> Entity:
    """Create a new war scheme."""
    scheme = initiator.world.entity(name=f"{initiator.name_with_uid}'s War Scheme")

    scheme.add_component(
        WarScheme(
            initiator=initiator,
            aggressor=initiator,
            defender=target,
            territory=territory,
            start_year=initiator.world.get_resource(GameState).year,
        )
    )

    return scheme


def destroy_war_scheme(scheme: Entity) -> None:
    """Destroy a war scheme."""
    war_scheme = scheme.get_component(WarScheme)

    war_scheme.initiator.get_component(SchemeManager).war_scheme = None

    for member in war_scheme.members:
        member.get_component(SchemeManager).war_scheme = None

    scheme.destroy()


def create_coup_scheme(initiator: Entity, target: Entity) -> Entity:
    """Create a new war scheme."""

    scheme = initiator.world.entity(name=f"{initiator.name_with_uid}'s Coup Scheme")

    scheme.add_component(
        CoupScheme(
            initiator=initiator,
            target=target,
            start_year=initiator.world.get_resource(GameState).year,
        )
    )

    return scheme


def destroy_coup_scheme(scheme: Entity) -> None:
    """Destroy a coup scheme."""
    coup_scheme = scheme.get_component(CoupScheme)

    coup_scheme.initiator.get_component(SchemeManager).coup_scheme = None

    for member in coup_scheme.members:
        member.get_component(SchemeManager).coup_scheme = None

    scheme.destroy()


def calculate_alliance_martial(*families: Entity) -> float:
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


def calculate_war_score(lead_family: Entity, allies: list[Entity]) -> int:
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
    martial_skill_level = get_martial_skill(lead_family_head)

    if martial_skill_level < SKILL_BAD:
        final_score = final_score * 0.6  # Final score - 40%

    elif martial_skill_level < SKILL_NEUTRAL:
        final_score = final_score * 0.9  # Final score - 10%

    elif SKILL_NEUTRAL < martial_skill_level < SKILL_EXCELLENT:
        final_score = final_score * 1.1  # Final score + 10%

    elif martial_skill_level >= SKILL_EXCELLENT:
        final_score = final_score * 1.4  # Final score + 40%

    # Apply changes for lead family head stewardship
    if allies:
        lead_family_head = lead_family.get_component(Family).head
        assert lead_family_head is not None
        stewardship_skill_level = get_stewardship_skill(lead_family_head)

        if stewardship_skill_level < SKILL_BAD:
            final_score = final_score * 0.5  # Final score - 50%
        elif stewardship_skill_level < SKILL_NEUTRAL:
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
