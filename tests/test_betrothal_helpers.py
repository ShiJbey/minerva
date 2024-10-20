# pylint: disable=W0621
"""Test helper functions for betrothal behavior.

"""

import pathlib

import pytest

from minerva.characters.betrothal_data import BetrothalTracker
from minerva.characters.betrothal_helpers import init_betrothal, terminate_betrothal
from minerva.loaders import (
    load_female_first_names,
    load_male_first_names,
    load_settlement_names,
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

    return sim


def test_init_betrothal(test_sim: Simulation):
    """Test initializing betrothals."""

    c0 = generate_character(test_sim.world)
    c1 = generate_character(test_sim.world)

    c0_betrothals = c0.get_component(BetrothalTracker)
    c1_betrothals = c1.get_component(BetrothalTracker)

    assert c0_betrothals.current_betrothal is None
    assert c1_betrothals.current_betrothal is None

    init_betrothal(c0, c1)

    assert c0_betrothals.current_betrothal is not None
    assert c1_betrothals.current_betrothal is not None


def test_terminate_betrothal(test_sim: Simulation):
    """Test terminating a betrothal object."""

    c0 = generate_character(test_sim.world)
    c1 = generate_character(test_sim.world)

    c0_betrothals = c0.get_component(BetrothalTracker)
    c1_betrothals = c1.get_component(BetrothalTracker)

    assert c0_betrothals.current_betrothal is None
    assert c1_betrothals.current_betrothal is None

    init_betrothal(c0, c1)

    assert c0_betrothals.current_betrothal is not None
    assert c1_betrothals.current_betrothal is not None

    terminate_betrothal(c0, c1)

    assert c0_betrothals.current_betrothal is None
    assert c1_betrothals.current_betrothal is None
