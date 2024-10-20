# pylint: disable=W0621
"""Test classes and functions related to succession."""

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
from minerva.data import japanese_city_names, japanese_names
from minerva.pcg.base_types import PCGFactories
from minerva.simulation import Simulation


@pytest.fixture
def test_sim() -> Simulation:
    """Create a test simulation."""
    sim = Simulation()

    japanese_city_names.load_names(sim.world)
    japanese_names.load_names(sim.world)

    return sim


def test_get_succession_depth_chart(test_sim: Simulation):
    """Test depth chart calculations."""
    character_factory = test_sim.world.resources.get_resource(
        PCGFactories
    ).character_factory

    viserys = character_factory.generate_character(
        test_sim.world,
        first_name="Viserys",
        surname="Targaryen",
        sex=Sex.MALE,
        life_stage=LifeStage.SENIOR,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    rhaenyra = character_factory.generate_character(
        test_sim.world,
        first_name="Rhaenyra",
        surname="Targaryen",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
        species="human",
    )

    alicent = character_factory.generate_character(
        test_sim.world,
        first_name="Alicent",
        surname="Hightower",
        sex=Sex.FEMALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.BISEXUAL,
    )

    daemon = character_factory.generate_character(
        test_sim.world,
        first_name="Daemon",
        surname="Targaryen",
        sex=Sex.MALE,
        life_stage=LifeStage.ADULT,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    aegon_2 = character_factory.generate_character(
        test_sim.world,
        first_name="Aegon",
        surname="Targaryen",
        sex=Sex.MALE,
        age=20,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    aemond = character_factory.generate_character(
        test_sim.world,
        first_name="Aemond",
        surname="Targaryen",
        sex=Sex.MALE,
        age=16,
        sexual_orientation=SexualOrientation.HETEROSEXUAL,
        species="human",
    )

    rhaenys = character_factory.generate_character(
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
    assert depth_chart.get_depth(alicent) == -1
    assert depth_chart.get_depth(daemon) == 3
    assert depth_chart.get_depth(rhaenys) == -1
