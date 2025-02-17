# pylint: disable=W0621
"""Test Dynasty functionality."""

import pytest

from minerva.characters.components import (
    Dynasty,
    DynastyTracker,
    LifeStage,
    Sex,
    SexualOrientation,
)
from minerva.characters.helpers import set_character_family
from minerva.characters.succession_helpers import (
    remove_current_ruler,
    set_current_ruler,
)
from minerva.ecs import Entity
from minerva.pcg.base_types import CharacterGenOptions, FamilyGenOptions
from minerva.pcg.character import spawn_character, spawn_family
from minerva.sim_db import SimDB
from minerva.simulation import Simulation


@pytest.fixture
def sim() -> Simulation:
    """Create a test simulation."""
    test_sim = Simulation()

    return test_sim


def test_set_current_ruler(sim: Simulation):
    """Test setting the current ruler."""

    viserys = spawn_character(
        sim.world,
        CharacterGenOptions(
            first_name="Viserys",
            surname="Targaryen",
            sex=Sex.MALE,
            life_stage=LifeStage.SENIOR,
            sexual_orientation=SexualOrientation.HETEROSEXUAL,
            species="human",
        ),
    )

    rhaenyra = spawn_character(
        sim.world,
        CharacterGenOptions(
            first_name="Rhaenyra",
            surname="Targaryen",
            sex=Sex.FEMALE,
            life_stage=LifeStage.ADULT,
            sexual_orientation=SexualOrientation.BISEXUAL,
            species="human",
        ),
    )

    corlys = spawn_character(
        sim.world,
        CharacterGenOptions(
            first_name="Corlys",
            surname="Velaryon",
            sex=Sex.MALE,
            life_stage=LifeStage.ADULT,
            sexual_orientation=SexualOrientation.HETEROSEXUAL,
            species="human",
        ),
    )

    targaryen_family = spawn_family(sim.world, FamilyGenOptions(name="Targaryen"))
    velaryon_family = spawn_family(sim.world, FamilyGenOptions(name="Velaryon"))

    set_character_family(viserys, targaryen_family)
    set_character_family(rhaenyra, targaryen_family)
    set_character_family(corlys, velaryon_family)

    dynasty_tracker = sim.world.get_resource(DynastyTracker)
    db = sim.world.get_resource(SimDB).db

    set_current_ruler(sim.world, viserys)

    assert dynasty_tracker.current_dynasty is not None
    assert dynasty_tracker.last_dynasty is None
    assert len(dynasty_tracker.all_rulers) == 1
    assert dynasty_tracker.all_rulers[-1] == viserys

    targaryen_dynasty: Entity = dynasty_tracker.current_dynasty
    current_dynasty_component = dynasty_tracker.current_dynasty.get_component(Dynasty)
    assert current_dynasty_component.family == targaryen_family
    assert current_dynasty_component.current_ruler == viserys

    # Verify ruler data is in the database
    result = db.execute(
        """SELECT start_date, end_date, predecessor_id FROM rulers WHERE character_id=?;""",
        (viserys.uid,),
    ).fetchone()
    assert result == ("0001-01", None, None)

    # Verify that the database entry for the dynasty is up to date
    result = db.execute(
        """
        SELECT family_id, founder_id, start_date, end_date, previous_dynasty_id
        FROM dynasties WHERE uid=?;""",
        (dynasty_tracker.current_dynasty.uid,),
    ).fetchone()
    assert result == (targaryen_family.uid, viserys.uid, "0001-01", None, None)

    current_dynasty_component = dynasty_tracker.current_dynasty.get_component(Dynasty)
    assert current_dynasty_component.current_ruler == viserys

    # Set the next ruler to come from the same family
    set_current_ruler(sim.world, rhaenyra)

    # Verify that the dynasty has not changed
    result = db.execute(
        """
        SELECT family_id, founder_id, start_date, end_date, previous_dynasty_id
        FROM dynasties WHERE uid=?;""",
        (dynasty_tracker.current_dynasty.uid,),
    ).fetchone()
    assert result == (
        targaryen_family.uid,
        viserys.uid,
        "0001-01",
        None,
        None,
    )

    result = db.execute(
        """SELECT start_date, end_date, predecessor_id FROM rulers WHERE character_id=?;""",
        (rhaenyra.uid,),
    ).fetchone()
    assert result == ("0001-01", None, viserys.uid)

    result = db.execute(
        """SELECT start_date, end_date, predecessor_id FROM rulers WHERE character_id=?;""",
        (viserys.uid,),
    ).fetchone()
    assert result == ("0001-01", "0001-01", None)

    # Set the next ruler to come from a different family, ending the current dynasty.
    set_current_ruler(sim.world, corlys)

    result = db.execute(
        """SELECT start_date, end_date, predecessor_id FROM rulers WHERE character_id=?;""",
        (rhaenyra.uid,),
    ).fetchone()
    assert result == ("0001-01", "0001-01", viserys.uid)

    result = db.execute(
        """
        SELECT family_id, founder_id, start_date, end_date, previous_dynasty_id
        FROM dynasties WHERE uid=?;""",
        (dynasty_tracker.current_dynasty.uid,),
    ).fetchone()
    assert result == (
        velaryon_family.uid,
        corlys.uid,
        "0001-01",
        None,
        targaryen_dynasty.uid,
    )

    assert dynasty_tracker.current_dynasty is not None
    assert dynasty_tracker.last_dynasty is not None
    assert len(dynasty_tracker.all_rulers) == 3
    assert dynasty_tracker.all_rulers[-1] == corlys

    current_dynasty_component = dynasty_tracker.current_dynasty.get_component(Dynasty)
    assert current_dynasty_component.family == velaryon_family
    assert current_dynasty_component.current_ruler == corlys

    # Remove the final rule from power and do not place anyone as a replacement.
    remove_current_ruler(sim.world)

    assert dynasty_tracker.current_dynasty is None
    assert len(dynasty_tracker.previous_dynasties) == 2
    assert len(dynasty_tracker.all_rulers) == 3
    assert dynasty_tracker.all_rulers[-1] == corlys
