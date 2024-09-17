# pylint: disable=W0621
"""Test classes and functions related to succession."""

import pathlib

import pytest

from minerva.characters.components import LifeStage, Sex, SexualOrientation
from minerva.characters.helpers import (
    set_character_biological_father,
    set_character_father,
    set_character_mother,
    set_relation_child,
    set_relation_sibling,
    start_marriage,
)
from minerva.characters.succession_helpers import get_succession_depth_chart
from minerva.loaders import (
    load_female_first_names,
    load_male_first_names,
    load_settlement_names,
    load_species_types,
    load_surnames,
)
from minerva.pcg.character import generate_character
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


def test_get_succession_depth_chart(test_sim: Simulation):
    """Test depth chart calculations."""

    # Configure characters

    viserys = generate_character(
        test_sim.world,
        first_name="Viserys",
        surname="Targaryen",
        sex=Sex.MALE,
        life_stage=LifeStage.SENIOR,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    rhaenyra = generate_character(
        test_sim.world,
        first_name="Rhaenyra",
        surname="Targaryen",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
        species="human",
    )

    alicent = generate_character(
        test_sim.world,
        first_name="Alicent",
        surname="Hightower",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
    )

    daemon = generate_character(
        test_sim.world,
        first_name="Daemon",
        surname="Targaryen",
        sex=Sex.MALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    aegon_2 = generate_character(
        test_sim.world,
        first_name="Aegon",
        surname="Targaryen",
        sex=Sex.MALE,
        age=20,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    aemond = generate_character(
        test_sim.world,
        first_name="Aemond",
        surname="Targaryen",
        sex=Sex.MALE,
        age=16,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    rhaenys = generate_character(
        test_sim.world,
        first_name="Rhaenys",
        surname="Targaryen",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

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

    # Calculate the depth chart

    depth_chart = get_succession_depth_chart(viserys)

    assert depth_chart.get_depth(rhaenyra) == 0
    assert depth_chart.get_depth(aegon_2) == 1
    assert depth_chart.get_depth(aemond) == 2
    assert depth_chart.get_depth(alicent) == 3
    assert depth_chart.get_depth(daemon) == 4
    assert depth_chart.get_depth(rhaenys) == -1
