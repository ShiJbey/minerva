# pylint: disable=W0621
"""Test helper functions for wars.

"""

import pathlib

import pytest

from minerva.characters.components import Family
from minerva.characters.helpers import set_family_head
from minerva.characters.war_data import Alliance, War, WarRole, WarTracker
from minerva.characters.war_helpers import (
    end_alliance,
    end_war,
    join_war_as,
    start_alliance,
    start_war,
)
from minerva.datetime import SimDate
from minerva.loaders import (
    load_female_first_names,
    load_male_first_names,
    load_settlement_names,
    load_surnames,
)
from minerva.pcg.character import generate_character, generate_family
from minerva.sim_db import SimDB
from minerva.simulation import Simulation


@pytest.fixture
def test_sim() -> Simulation:
    """Create a test simulation."""
    sim = Simulation()

    data_dir = pathlib.Path(__file__).parent.parent / "data"

    load_male_first_names(sim, data_dir / "masculine_japanese_names.txt")
    load_female_first_names(sim, data_dir / "feminine_japanese_names.txt")
    load_surnames(sim, data_dir / "japanese_surnames.txt")
    load_settlement_names(sim, data_dir / "japanese_city_names.txt")

    return sim


def test_start_alliance(test_sim: Simulation):
    """Test starting new alliances."""

    character_0 = generate_character(test_sim.world)
    character_1 = generate_character(test_sim.world)

    family_0 = generate_family(test_sim.world)
    family_1 = generate_family(test_sim.world)

    set_family_head(family_0, character_0)
    set_family_head(family_1, character_1)

    family_0_component = family_0.get_component(Family)
    family_1_component = family_1.get_component(Family)

    alliance = start_alliance(family_0, family_1)
    alliance_component = alliance.get_component(Alliance)

    assert family_0_component.alliance == alliance
    assert family_1_component.alliance == alliance
    assert family_1 in alliance_component.member_families
    assert family_0 in alliance_component.member_families
    assert alliance_component.founder_family == family_0
    assert alliance_component.founder == character_0


def test_end_alliance(test_sim: Simulation):
    """Test terminating an existing alliance."""
    db = test_sim.world.resources.get_resource(SimDB).db

    character_0 = generate_character(test_sim.world)
    character_1 = generate_character(test_sim.world)

    family_0 = generate_family(test_sim.world)
    family_1 = generate_family(test_sim.world)

    set_family_head(family_0, character_0)
    set_family_head(family_1, character_1)

    family_0_component = family_0.get_component(Family)
    family_1_component = family_1.get_component(Family)

    alliance = start_alliance(family_0, family_1)
    alliance_component = alliance.get_component(Alliance)

    test_sim.world.resources.add_resource(SimDate(10, 1))

    end_alliance(alliance)

    assert family_0_component.alliance is None
    assert family_1_component.alliance is None
    assert family_1 in alliance_component.member_families
    assert family_0 in alliance_component.member_families
    assert alliance_component.founder_family == family_0
    assert alliance_component.founder == character_0

    result = db.execute(
        """SELECT end_date FROM alliances WHERE uid=?;""",
        (alliance.uid,),
    ).fetchone()
    assert result[0] == "0010-01"


def test_start_war(test_sim: Simulation):
    """Test starting a war."""
    db = test_sim.world.resources.get_resource(SimDB).db

    family_0 = generate_family(test_sim.world)
    family_1 = generate_family(test_sim.world)

    war = start_war(family_0, family_1)

    assert war in family_0.get_component(WarTracker).offensive_wars
    assert war in family_1.get_component(WarTracker).defensive_wars

    result = db.execute(
        """SELECT aggressor_id, defender_id FROM wars WHERE uid=?;""",
        (war.uid,),
    ).fetchone()
    assert result == (family_0.uid, family_1.uid)


def test_end_war(test_sim: Simulation):
    """Test ending a war."""
    db = test_sim.world.resources.get_resource(SimDB).db

    family_0 = generate_family(test_sim.world)
    family_1 = generate_family(test_sim.world)
    family_2 = generate_family(test_sim.world)
    family_3 = generate_family(test_sim.world)

    war = start_war(family_0, family_1)

    join_war_as(war, family_2, WarRole.AGGRESSOR_ALLY)
    join_war_as(war, family_3, WarRole.DEFENDER_ALLY)

    test_sim.world.resources.get_resource(SimDate).increment(years=3)

    end_war(war, family_1)

    assert war not in family_0.get_component(WarTracker).offensive_wars
    assert war not in family_1.get_component(WarTracker).defensive_wars
    assert war not in family_2.get_component(WarTracker).offensive_wars
    assert war not in family_3.get_component(WarTracker).defensive_wars

    result = db.execute(
        """SELECT start_date, end_date FROM wars WHERE uid=?;""",
        (war.uid,),
    ).fetchone()
    assert result == ("0001-01", "0004-01")


def test_join_war_as(test_sim: Simulation):
    """Test character's joining a war on a specific side."""
    db = test_sim.world.resources.get_resource(SimDB).db

    family_0 = generate_family(test_sim.world)
    family_1 = generate_family(test_sim.world)
    family_2 = generate_family(test_sim.world)
    family_3 = generate_family(test_sim.world)

    war = start_war(family_0, family_1)
    war_component = war.get_component(War)

    join_war_as(war, family_2, WarRole.AGGRESSOR_ALLY)
    join_war_as(war, family_3, WarRole.DEFENDER_ALLY)

    assert family_2 in war_component.aggressor_allies
    assert family_3 in war_component.defender_allies
    assert war in family_2.get_component(WarTracker).offensive_wars
    assert war in family_3.get_component(WarTracker).defensive_wars

    result = db.execute(
        """
        SELECT family_id FROM war_participants WHERE war_id=? AND role=?;
        """,
        (war.uid, WarRole.AGGRESSOR_ALLY),
    ).fetchone()
    assert result == (family_2.uid,)

    result = db.execute(
        """
        SELECT family_id FROM war_participants WHERE war_id=? AND role=?;
        """,
        (war.uid, WarRole.DEFENDER_ALLY),
    ).fetchone()
    assert result == (family_3.uid,)
