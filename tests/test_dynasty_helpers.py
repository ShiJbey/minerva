# pylint: disable=W0621
"""Test Dynasty functionality."""

import pathlib

import pytest

from minerva.characters.components import Character, LifeStage, Sex, SexualOrientation
from minerva.characters.helpers import (
    set_character_biological_father,
    set_character_family,
    set_character_father,
    set_character_mother,
    set_relation_child,
    set_relation_sibling,
    start_marriage,
)
from minerva.ecs import Active
from minerva.loaders import (
    load_female_first_names,
    load_male_first_names,
    load_settlement_names,
    load_species_types,
    load_surnames,
)
from minerva.pcg.character import generate_character, generate_family
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

    # Test

    # Configure characters

    viserys = generate_character(
        sim.world,
        first_name="Viserys",
        surname="Targaryen",
        sex=Sex.MALE,
        life_stage=LifeStage.SENIOR,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    rhaenyra = generate_character(
        sim.world,
        first_name="Rhaenyra",
        surname="Targaryen",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
        species="human",
    )

    alicent = generate_character(
        sim.world,
        first_name="Alicent",
        surname="Hightower",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
    )

    daemon = generate_character(
        sim.world,
        first_name="Daemon",
        surname="Targaryen",
        sex=Sex.MALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    aegon_2 = generate_character(
        sim.world,
        first_name="Aegon",
        surname="Targaryen",
        sex=Sex.MALE,
        age=20,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    aemond = generate_character(
        sim.world,
        first_name="Aemond",
        surname="Targaryen",
        sex=Sex.MALE,
        age=16,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    corlys = generate_character(
        sim.world,
        first_name="Corlys",
        surname="Velaryon",
        sex=Sex.MALE,
        age=54,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    laena = generate_character(
        sim.world,
        first_name="Laena",
        surname="Velaryon",
        sex=Sex.FEMALE,
        age=34,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    targaryen_family = generate_family(sim.world, name="Targaryen")
    velaryon_family = generate_family(sim.world, name="Velaryon")

    # Create family ties
    set_character_family(viserys, targaryen_family)
    set_character_family(rhaenyra, targaryen_family)
    set_character_family(corlys, velaryon_family)
    set_character_family(laena, velaryon_family)

    # Configure Relationships
    set_relation_child(viserys, rhaenyra)
    set_relation_child(viserys, aegon_2)
    set_relation_child(viserys, aemond)
    set_relation_child(alicent, aegon_2)
    set_relation_child(alicent, aemond)
    start_marriage(viserys, alicent)
    set_relation_sibling(viserys, daemon)
    set_relation_sibling(daemon, viserys)
    start_marriage(rhaenyra, daemon)
    set_character_father(rhaenyra, viserys)
    set_character_biological_father(rhaenyra, viserys)
    set_character_mother(aegon_2, alicent)
    set_character_father(rhaenyra, viserys)
    set_character_biological_father(rhaenyra, viserys)
    set_character_mother(aegon_2, alicent)
    set_character_father(rhaenyra, viserys)
    set_character_biological_father(rhaenyra, viserys)
    set_character_mother(aegon_2, alicent)
    set_relation_sibling(rhaenyra, aegon_2)
    set_relation_sibling(aegon_2, rhaenyra)
    set_character_father(laena, corlys)
    set_character_biological_father(laena, corlys)

    return sim


def test_set_current_ruler(test_sim: Simulation):
    """Test setting the current ruler."""

    viserys = [
        character.gameobject
        for _, (character, _) in test_sim.world.get_components((Character, Active))
        if character.first_name == "Viserys"
    ]

    corlys = [
        character.gameobject
        for _, (character, _) in test_sim.world.get_components((Character, Active))
        if character.first_name == "Corlys"
    ]

    # start_new_dynasty(test_sim.world, viserys)

    assert False


def test_end_current_dynasty():
    """Test ending the current dynasty.

    This should ensure that all termination information is saved
    to the dynasty upon ending. It should also allow us to create
    a new dynasty afterward that has the proper references to the
    previous dynasty.
    """
    assert False


def test_changing_ruler():
    """Set the current emperor for the dynasty.

    This test checks that we can set the current ruler.
    Changing rulers will cause an error if the new ruler is not
    part of the family royal family, as this would signal a dynasty
    change.

    This test also ensures that rulers correctly reference their
    predecessor if any.
    """
    assert False
