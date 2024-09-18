# pylint: disable=W0621
"""Test helper functions for wars.

"""

import pathlib

import pytest

from minerva.characters.war_data import AllianceTracker, War, WarRole, WarTracker
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
    load_species_types,
    load_surnames,
)
from minerva.pcg.character import generate_family
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
    load_species_types(sim, data_dir / "species_types.yaml")

    return sim


def test_start_alliance(test_sim: Simulation):
    """Test starting new alliances."""
    db = test_sim.world.resources.get_resource(SimDB).db

    family_0 = generate_family(test_sim.world)
    family_1 = generate_family(test_sim.world)

    family_0_alliances = family_0.get_component(AllianceTracker)
    family_1_alliances = family_1.get_component(AllianceTracker)

    start_alliance(family_0, family_1)

    assert family_1.uid in family_0_alliances.alliances
    assert family_0.uid in family_1_alliances.alliances

    result = db.execute(
        """SELECT ally_id FROM alliances WHERE family_id=?""",
        (family_0.uid,),
    ).fetchone()
    assert result[0] == family_1.uid

    result = db.execute(
        """SELECT ally_id FROM alliances WHERE family_id=?""",
        (family_1.uid,),
    ).fetchone()
    assert result[0] == family_0.uid


def test_end_alliance(test_sim: Simulation):
    """Test terminating an existing alliance."""
    db = test_sim.world.resources.get_resource(SimDB).db

    family_0 = generate_family(test_sim.world)
    family_1 = generate_family(test_sim.world)

    family_0_alliances = family_0.get_component(AllianceTracker)
    family_1_alliances = family_1.get_component(AllianceTracker)

    start_alliance(family_0, family_1)

    assert family_1.uid in family_0_alliances.alliances
    assert family_0.uid in family_1_alliances.alliances

    end_alliance(family_0, family_1)

    assert family_1.uid not in family_0_alliances.alliances
    assert family_0.uid not in family_1_alliances.alliances

    result = db.execute(
        """SELECT end_date FROM alliances WHERE family_id=? AND ally_id=?;""",
        (family_0.uid, family_1.uid),
    ).fetchone()
    assert result[0] == "0001-01"

    result = db.execute(
        """SELECT end_date FROM alliances WHERE family_id=? AND ally_id=?;""",
        (family_1.uid, family_0.uid),
    ).fetchone()
    assert result[0] == "0001-01"


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
