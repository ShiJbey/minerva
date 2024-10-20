# pylint: disable=W0621
"""Test helper functions for betrothal behavior.

"""

import pytest

from minerva.characters.betrothal_data import BetrothalTracker
from minerva.characters.betrothal_helpers import init_betrothal, terminate_betrothal
from minerva.data import japanese_city_names, japanese_names
from minerva.ecs import GameObject, World
from minerva.pcg.base_types import PCGFactories
from minerva.simulation import Simulation


@pytest.fixture
def test_sim() -> Simulation:
    """Create a test simulation."""
    sim = Simulation()

    japanese_city_names.load_names(sim.world)
    japanese_names.load_names(sim.world)

    return sim


def generate_character(world: World) -> GameObject:
    """Generate character."""
    return world.resources.get_resource(
        PCGFactories
    ).character_factory.generate_character(world)


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
