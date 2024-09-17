# pylint: disable=W0621
"""Test helper functions that modify families.

"""

import pathlib

import pytest

from minerva.characters.components import Character, Family, HeadOfFamily
from minerva.characters.helpers import (
    merge_family_with,
    set_character_family,
    set_family_head,
    set_family_home_base,
    set_family_name,
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
    assert len(family_component.members) == 0
    assert len(family_component.active_members) == 0

    # Test the state after the character has been added to the family
    set_character_family(c0, test_family)
    assert character_component.family == test_family
    assert len(family_component.members) == 1
    assert len(family_component.active_members) == 1


def test_remove_character_from_family(test_sim: Simulation):
    """Test removing a character from a family."""
    test_family = generate_family(test_sim.world)
    c0 = generate_character(test_sim.world)

    character_component = c0.get_component(Character)
    family_component = test_family.get_component(Family)

    # Test the initial state
    assert character_component.family is None
    assert len(family_component.members) == 0
    assert len(family_component.active_members) == 0
    assert len(family_component.former_members) == 0

    # Test the state after the character has been added to the family
    set_character_family(c0, test_family)
    assert character_component.family == test_family
    assert len(family_component.members) == 1
    assert len(family_component.active_members) == 1
    assert len(family_component.former_members) == 0

    # Remove the character from the family
    set_character_family(c0, None)
    assert character_component.family is None
    assert len(family_component.members) == 0
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


def test_remove_family_from_play():
    """Test removing a family from the active simulation."""
    assert False


def test_add_family_to_settlement():
    """Test adding a family to a settlement."""
    assert False


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


def test_get_warrior_candidates():
    """Test getting potential candidates for warrior roles in a family."""
    assert False


def test_get_advisor_candidates():
    """Test getting potential advisors for advisor roles in a family."""
    assert False


def test_set_family_role():
    """Test setting a character to have a given role in their family."""
    assert False
