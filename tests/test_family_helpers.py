# pylint: disable=W0621
"""Test helper functions that modify families.

"""

import pathlib

import pytest

import minerva.constants
from minerva.characters.components import (
    Character,
    Diplomacy,
    Family,
    FamilyRoleFlags,
    HeadOfFamily,
    LifeStage,
    Martial,
    Prowess,
    Stewardship,
)
from minerva.characters.helpers import (
    assign_family_member_to_roles,
    get_advisor_candidates,
    get_warrior_candidates,
    merge_family_with,
    remove_family_from_play,
    set_character_family,
    set_family_head,
    set_family_home_base,
    set_family_name,
    unassign_family_member_from_roles,
)
from minerva.loaders import (
    load_female_first_names,
    load_male_first_names,
    load_settlement_names,
    load_species_types,
    load_surnames,
)
from minerva.pcg.character import generate_character, generate_family
from minerva.pcg.settlement import generate_settlement
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


def test_set_family_head(test_sim: Simulation):
    """Test updating who is the head of a family."""

    test_family = generate_family(test_sim.world, "Test Family")
    c0 = generate_character(test_sim.world)
    c1 = generate_character(test_sim.world)
    db = test_sim.world.resources.get_resource(SimDB).db

    family_component = test_family.get_component(Family)

    assert family_component.head is None
    assert c0.has_component(HeadOfFamily) is False
    assert c1.has_component(HeadOfFamily) is False

    # This should do nothing and not throw an error
    set_family_head(test_family, None)

    # Set c0 as the family head
    set_family_head(test_family, c0)
    assert family_component.head == c0
    assert c0.has_component(HeadOfFamily) is True

    cur = db.execute("""SELECT head FROM families WHERE uid=?;""", (test_family.uid,))
    result = cur.fetchone()
    assert result[0] == c0.uid

    cur = db.execute(
        """SELECT start_date, end_date, predecessor FROM family_heads WHERE head=?;""",
        (c0.uid,),
    )
    result = cur.fetchone()
    assert result == ("0001-01", None, None)

    # Set the family head to c0 again. This should do nothing
    set_family_head(test_family, c0)
    assert family_component.head == c0
    assert c0.has_component(HeadOfFamily) is True

    # Set the family head to c1. This should swap them out and
    # remove the additional family head component from c0
    set_family_head(test_family, c1)
    assert family_component.head == c1
    assert c0.has_component(HeadOfFamily) is False
    assert c1.has_component(HeadOfFamily) is True

    cur = db.execute("""SELECT head FROM families WHERE uid=?;""", (test_family.uid,))
    result = cur.fetchone()
    assert result[0] == c1.uid

    cur = db.execute(
        """SELECT start_date, end_date FROM family_heads WHERE head=?;""", (c0.uid,)
    )
    result = cur.fetchone()
    assert result == ("0001-01", "0001-01")

    cur = db.execute(
        """SELECT start_date, predecessor FROM family_heads WHERE head=?;""", (c1.uid,)
    )
    result = cur.fetchone()
    assert result == ("0001-01", c0.uid)


def test_set_family_name(test_sim: Simulation):
    """Test updating the name of the family."""

    test_family = generate_family(test_sim.world, "Test Family")

    assert test_family.name == "Test Family"

    assert test_family.get_component(Family).name == "Test Family"

    db = test_sim.world.resources.get_resource(SimDB).db

    cur = db.execute("""SELECT name FROM families WHERE uid=?;""", (test_family.uid,))
    result = cur.fetchone()

    assert result[0] == "Test Family"

    set_family_name(test_family, "Production Family")

    assert test_family.name == "Production Family"

    assert test_family.get_component(Family).name == "Production Family"

    cur = db.execute("""SELECT name FROM families WHERE uid=?;""", (test_family.uid,))
    result = cur.fetchone()

    assert result[0] == "Production Family"


def test_add_character_to_family(test_sim: Simulation):
    """Test adding a character to a family."""

    test_family = generate_family(test_sim.world)
    c0 = generate_character(test_sim.world)

    character_component = c0.get_component(Character)
    family_component = test_family.get_component(Family)

    # Test the initial state
    assert character_component.family is None
    assert len(family_component.active_members) == 0

    # Test the state after the character has been added to the family
    set_character_family(c0, test_family)
    assert character_component.family == test_family
    assert len(family_component.active_members) == 1


def test_remove_character_from_family(test_sim: Simulation):
    """Test removing a character from a family."""
    test_family = generate_family(test_sim.world)
    c0 = generate_character(test_sim.world)

    character_component = c0.get_component(Character)
    family_component = test_family.get_component(Family)

    # Test the initial state
    assert character_component.family is None
    assert len(family_component.active_members) == 0
    assert len(family_component.former_members) == 0

    # Test the state after the character has been added to the family
    set_character_family(c0, test_family)
    assert character_component.family == test_family
    assert len(family_component.active_members) == 1
    assert len(family_component.former_members) == 0

    # Remove the character from the family
    set_character_family(c0, None)
    assert character_component.family is None
    assert len(family_component.active_members) == 0
    assert len(family_component.former_members) == 1


def test_merge_family_with(test_sim: Simulation):
    """Test merging families into one group."""
    f0 = generate_family(test_sim.world)
    og_f0_members = [generate_character(test_sim.world) for _ in range(5)]

    f1 = generate_family(test_sim.world)
    og_f1_members = [generate_character(test_sim.world) for _ in range(5)]

    for character in og_f0_members:
        set_character_family(character, f0)

    for character in og_f1_members:
        set_character_family(character, f1)

    assert len(f0.get_component(Family).active_members) == 5
    assert len(f1.get_component(Family).active_members) == 5

    # Move all the people in f0 to f1
    merge_family_with(f0, f1)

    assert len(f0.get_component(Family).active_members) == 0
    assert len(f0.get_component(Family).former_members) == 5
    assert len(f1.get_component(Family).active_members) == 10


def test_remove_family_from_play(test_sim: Simulation):
    """Test removing a family from the active simulation."""
    test_family = generate_family(test_sim.world)
    c0 = generate_character(test_sim.world)

    set_character_family(c0, test_family)

    remove_family_from_play(test_family)

    assert c0.is_active is False
    assert test_family.is_active is False


def test_set_family_home_base(test_sim: Simulation):
    """Test updating what settlement a family uses as their home base,"""
    s0 = generate_settlement(test_sim.world)
    f0 = generate_family(test_sim.world)

    family_component = f0.get_component(Family)

    assert family_component.home_base is None

    set_family_home_base(f0, s0)
    assert family_component.home_base == s0

    set_family_home_base(f0, None)
    assert family_component.home_base is None


def test_get_warrior_candidates(test_sim: Simulation):
    """Test getting potential candidates for warrior roles in a family."""
    test_family = generate_family(test_sim.world)

    c0 = generate_character(test_sim.world, life_stage=LifeStage.ADULT)
    c0.get_component(Martial).base_value = 30
    set_character_family(c0, test_family)

    c1 = generate_character(test_sim.world, life_stage=LifeStage.ADULT)
    c1.get_component(Prowess).base_value = 50
    set_character_family(c1, test_family)

    c2 = generate_character(test_sim.world, life_stage=LifeStage.ADULT)
    c2.get_component(Martial).base_value = 10
    set_character_family(c2, test_family)

    c3 = generate_character(test_sim.world, life_stage=LifeStage.ADULT)
    c3.get_component(Martial).base_value = 15
    c3.get_component(Prowess).base_value = 30
    set_character_family(c3, test_family)

    c4 = generate_character(test_sim.world, life_stage=LifeStage.ADULT)
    c4.get_component(Martial).base_value = 20
    set_character_family(c4, test_family)

    candidates = get_warrior_candidates(test_family)

    assert candidates[0] == c1
    assert candidates[1] == c3
    assert candidates[2] == c0
    assert candidates[3] == c4
    assert candidates[4] == c2


def test_get_advisor_candidates(test_sim: Simulation):
    """Test getting potential advisors for advisor roles in a family."""
    test_family = generate_family(test_sim.world)

    c0 = generate_character(test_sim.world, life_stage=LifeStage.ADULT)
    c0.get_component(Stewardship).base_value = 30
    set_character_family(c0, test_family)

    c1 = generate_character(test_sim.world, life_stage=LifeStage.ADULT)
    c1.get_component(Diplomacy).base_value = 50
    set_character_family(c1, test_family)

    c2 = generate_character(test_sim.world, life_stage=LifeStage.ADULT)
    c2.get_component(Stewardship).base_value = 10
    set_character_family(c2, test_family)

    c3 = generate_character(test_sim.world, life_stage=LifeStage.ADULT)
    c3.get_component(Stewardship).base_value = 15
    c3.get_component(Diplomacy).base_value = 30
    set_character_family(c3, test_family)

    c4 = generate_character(test_sim.world, life_stage=LifeStage.ADULT)
    c4.get_component(Stewardship).base_value = 20
    set_character_family(c4, test_family)

    candidates = get_advisor_candidates(test_family)

    assert candidates[0] == c1
    assert candidates[1] == c3
    assert candidates[2] == c0
    assert candidates[3] == c4
    assert candidates[4] == c2


def test_set_family_role(test_sim: Simulation):
    """Test setting a character to have a given role in their family."""

    test_family = generate_family(test_sim.world)

    c0 = generate_character(test_sim.world, life_stage=LifeStage.ADULT)
    set_character_family(c0, test_family)

    c1 = generate_character(test_sim.world, life_stage=LifeStage.ADULT)
    set_character_family(c1, test_family)

    c2 = generate_character(test_sim.world, life_stage=LifeStage.ADULT)
    set_character_family(c2, test_family)

    minerva.constants.MAX_ADVISORS_PER_FAMILY = 1
    minerva.constants.MAX_WARRIORS_PER_FAMILY = 1

    assign_family_member_to_roles(
        test_family, c0, FamilyRoleFlags.ADVISOR | FamilyRoleFlags.WARRIOR
    )

    with pytest.raises(RuntimeError):
        assign_family_member_to_roles(test_family, c1, FamilyRoleFlags.ADVISOR)

    assert FamilyRoleFlags.WARRIOR in c0.get_component(Character).family_roles
    assert FamilyRoleFlags.ADVISOR in c0.get_component(Character).family_roles
    assert FamilyRoleFlags.ADVISOR not in c1.get_component(Character).family_roles

    unassign_family_member_from_roles(test_family, c0, FamilyRoleFlags.ADVISOR)

    assign_family_member_to_roles(test_family, c1, FamilyRoleFlags.ADVISOR)

    assert FamilyRoleFlags.ADVISOR not in c0.get_component(Character).family_roles
    assert FamilyRoleFlags.ADVISOR in c1.get_component(Character).family_roles
