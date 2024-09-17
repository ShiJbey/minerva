# pylint: disable=W0621
"""Test helper functions for modifying clans.

"""


import pathlib

import pytest

from minerva.characters.components import Character, Clan, Family, HeadOfClan
from minerva.characters.helpers import (
    remove_clan_from_play,
    set_character_family,
    set_clan_head,
    set_clan_name,
    set_family_clan,
)
from minerva.loaders import (
    load_clan_names,
    load_female_first_names,
    load_male_first_names,
    load_settlement_names,
    load_species_types,
    load_surnames,
)
from minerva.pcg.character import generate_character, generate_clan, generate_family
from minerva.sim_db import SimDB
from minerva.simulation import Simulation


@pytest.fixture
def test_sim() -> Simulation:
    """Create a test simulation."""
    sim = Simulation()

    data_dir = pathlib.Path(__file__).parent.parent / "data"

    load_male_first_names(sim, data_dir / "masculine_japanese_names.txt")
    load_female_first_names(sim, data_dir / "feminine_japanese_names.txt")
    load_clan_names(sim, data_dir / "japanese_surnames.txt")
    load_surnames(sim, data_dir / "japanese_surnames.txt")
    load_settlement_names(sim, data_dir / "japanese_city_names.txt")
    load_species_types(sim, data_dir / "species_types.yaml")

    return sim


def test_set_clan_name(test_sim: Simulation):
    """Test updating the name of a clan."""

    test_clan = generate_clan(test_sim.world, "Test Clan")

    assert test_clan.name == "Test Clan"

    assert test_clan.get_component(Clan).name == "Test Clan"

    db = test_sim.world.resources.get_resource(SimDB).db

    cur = db.execute("""SELECT name FROM clans WHERE uid=?;""", (test_clan.uid,))
    result = cur.fetchone()

    assert result[0] == "Test Clan"

    set_clan_name(test_clan, "Production Clan")

    assert test_clan.name == "Production Clan"

    assert test_clan.get_component(Clan).name == "Production Clan"

    cur = db.execute("""SELECT name FROM clans WHERE uid=?;""", (test_clan.uid,))
    result = cur.fetchone()

    assert result[0] == "Production Clan"


def test_set_clan_head(test_sim: Simulation):
    """Test updating who is the head of a clan."""
    test_clan = generate_clan(test_sim.world, name="")
    c0 = generate_character(test_sim.world)
    c1 = generate_character(test_sim.world)
    db = test_sim.world.resources.get_resource(SimDB).db

    clan_component = test_clan.get_component(Clan)

    assert clan_component.head is None
    assert c0.has_component(HeadOfClan) is False
    assert c1.has_component(HeadOfClan) is False

    # This should do nothing and not throw an error
    set_clan_head(test_clan, None)

    # Set c0 as the family head
    set_clan_head(test_clan, c0)
    assert clan_component.head == c0
    assert c0.has_component(HeadOfClan) is True

    cur = db.execute("""SELECT head FROM clans WHERE uid=?;""", (test_clan.uid,))
    result = cur.fetchone()
    assert result[0] == c0.uid

    cur = db.execute(
        """SELECT start_date, end_date, predecessor FROM clan_heads WHERE head=?;""",
        (c0.uid,),
    )
    result = cur.fetchone()
    assert result == ("0001-01", None, None)

    # Set the family head to c0 again. This should do nothing
    set_clan_head(test_clan, c0)
    assert clan_component.head == c0
    assert c0.has_component(HeadOfClan) is True

    # Set the family head to c1. This should swap them out and
    # remove the additional family head component from c0
    set_clan_head(test_clan, c1)
    assert clan_component.head == c1
    assert c0.has_component(HeadOfClan) is False
    assert c1.has_component(HeadOfClan) is True

    cur = db.execute("""SELECT head FROM clans WHERE uid=?;""", (test_clan.uid,))
    result = cur.fetchone()
    assert result[0] == c1.uid

    cur = db.execute(
        """SELECT start_date, end_date FROM clan_heads WHERE head=?;""", (c0.uid,)
    )
    result = cur.fetchone()
    assert result == ("0001-01", "0001-01")

    cur = db.execute(
        """SELECT start_date, predecessor FROM clan_heads WHERE head=?;""", (c1.uid,)
    )
    result = cur.fetchone()
    assert result == ("0001-01", c0.uid)


def test_add_family_to_clan(test_sim: Simulation):
    """Test adding a family to a clan."""
    clan = generate_clan(test_sim.world, name="")
    family_0 = generate_family(test_sim.world)
    family_1 = generate_family(test_sim.world)
    character_0 = generate_character(test_sim.world)
    character_1 = generate_character(test_sim.world)

    # Add characters to the families
    set_character_family(character_0, family_0)
    set_character_family(character_1, family_1)

    # Get references to needed components
    clan_component = clan.get_component(Clan)
    family_0_component = family_0.get_component(Family)
    family_1_component = family_1.get_component(Family)
    character_0_component = character_0.get_component(Character)
    character_1_component = character_1.get_component(Character)

    # Check initial conditions
    assert family_0 not in clan_component.active_families
    assert family_1 not in clan_component.active_families
    assert family_0_component.clan is None
    assert family_1_component.clan is None

    # Call the function we want to test
    set_family_clan(family_0, clan)
    set_family_clan(family_1, clan)

    # Check the post conditions
    assert family_0 in clan_component.active_families
    assert family_1 in clan_component.active_families
    assert family_0_component.clan == clan
    assert family_1_component.clan == clan
    assert character_0_component.clan == clan
    assert character_1_component.clan == clan


def test_remove_family_from_clan(test_sim: Simulation):
    """Test removing a family from a clan."""
    clan = generate_clan(test_sim.world, name="")
    family_0 = generate_family(test_sim.world)
    family_1 = generate_family(test_sim.world)
    character_0 = generate_character(test_sim.world)
    character_1 = generate_character(test_sim.world)

    # Add characters to the families
    set_character_family(character_0, family_0)
    set_character_family(character_1, family_1)

    # Get references to needed components
    clan_component = clan.get_component(Clan)
    family_0_component = family_0.get_component(Family)
    family_1_component = family_1.get_component(Family)
    character_0_component = character_0.get_component(Character)
    character_1_component = character_1.get_component(Character)

    # Check initial conditions
    assert family_0 not in clan_component.active_families
    assert family_1 not in clan_component.active_families
    assert family_0_component.clan is None
    assert family_1_component.clan is None

    # Add the families to the clan
    set_family_clan(family_0, clan)
    set_family_clan(family_1, clan)

    # Check the post conditions
    assert family_0 in clan_component.active_families
    assert family_1 in clan_component.active_families
    assert family_0_component.clan == clan
    assert family_1_component.clan == clan
    assert character_0_component.clan == clan
    assert character_1_component.clan == clan

    # Test removing a family from the clan
    set_family_clan(family_1, None)

    # Check post conditions
    assert family_0 in clan_component.active_families
    assert family_1 not in clan_component.active_families
    assert family_1 in clan_component.former_families
    assert family_0_component.clan == clan
    assert family_1_component.clan is None
    assert character_0_component.clan == clan
    assert character_1_component.clan is None


def test_remove_clan_from_play(test_sim: Simulation):
    """Test removing a clan from the active simulation."""
    # Set up model
    clan = generate_clan(test_sim.world, name="")
    family_0 = generate_family(test_sim.world)
    family_1 = generate_family(test_sim.world)
    character_0 = generate_character(test_sim.world)
    character_1 = generate_character(test_sim.world)

    set_character_family(character_0, family_0)
    set_character_family(character_1, family_1)
    set_family_clan(family_0, clan)
    set_family_clan(family_1, clan)

    # Get references to components
    clan_component = clan.get_component(Clan)
    family_0_component = family_0.get_component(Family)
    family_1_component = family_1.get_component(Family)
    character_0_component = character_0.get_component(Character)
    character_1_component = character_1.get_component(Character)

    # Check the initial conditions
    assert family_0 in clan_component.active_families
    assert family_1 in clan_component.active_families
    assert family_0_component.clan == clan
    assert family_1_component.clan == clan
    assert character_0_component.clan == clan
    assert character_1_component.clan == clan

    # Call the function to be tested
    remove_clan_from_play(clan)

    # Test the post conditions
    assert family_0 not in clan_component.active_families
    assert family_0 in clan_component.former_families
    assert family_1 not in clan_component.active_families
    assert family_1 in clan_component.former_families
    assert family_0_component.clan is None
    assert family_1_component.clan is None
    assert character_0_component.clan is None
    assert character_1_component.clan is None
