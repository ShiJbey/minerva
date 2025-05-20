# pylint: disable=W0621
"""Test for Neighborly's Trait System."""

import pytest

from minerva.actions.base_types import Proclivity
from minerva.characters.helpers import get_diplomacy_skill, set_diplomacy_skill_base
from minerva.config import Config
from minerva.pcg.character import spawn_character
from minerva.relationships.base_types import RelationshipModifier
from minerva.relationships.helpers import get_attraction
from minerva.simulation import Simulation
from minerva.stats.base_types import StatModifier, StatModifierType
from minerva.traits.base_types import CharacterTrait, CharacterTraitDatabase
from minerva.traits.effects import (
    AddAttractionModifier,
    AddDiplomacyModifier,
    AddProclivity,
)
from minerva.traits.helpers import add_trait, has_trait, remove_trait


@pytest.fixture
def sim() -> Simulation:
    """Create test world."""

    simulation = Simulation(Config(seed=123))

    simulation.world.get_resource(CharacterTraitDatabase).add_trait(
        CharacterTrait(
            trait_id="flirtatious",
            name="Flirtatious",
            effects=[
                AddAttractionModifier(RelationshipModifier(10, "outgoing")),
                AddProclivity(Proclivity(5).where(lambda a: "romance" in a.tags)),
            ],
        )
    )
    simulation.world.get_resource(CharacterTraitDatabase).add_trait(
        CharacterTrait(
            trait_id="charming",
            name="Charming",
            effects=[
                AddAttractionModifier(RelationshipModifier(12, "incoming")),
            ],
        )
    )
    simulation.world.get_resource(CharacterTraitDatabase).add_trait(
        CharacterTrait(
            trait_id="gullible",
            name="Gullible",
            effects=[AddDiplomacyModifier(StatModifier(10, StatModifierType.FLAT))],
            conflicting_traits=["skeptical"],
        )
    )
    simulation.world.get_resource(CharacterTraitDatabase).add_trait(
        CharacterTrait(
            trait_id="skeptical",
            name="Skeptical",
            effects=[],
            conflicting_traits=["gullible"],
        )
    )

    return simulation


def test_add_trait(sim: Simulation) -> None:
    """Test that adding a trait makes it visible with has_trait."""

    character = spawn_character(sim.world)

    assert has_trait(character, "flirtatious") is False

    success = add_trait(character, "flirtatious")

    assert success is True


def test_remove_trait(sim: Simulation) -> None:
    """Test that removing a trait makes it not available to has_trait."""

    character = spawn_character(sim.world)

    assert has_trait(character, "flirtatious") is False

    add_trait(character, "flirtatious")

    assert has_trait(character, "flirtatious") is True

    success = remove_trait(character, "flirtatious")

    assert success is True


def test_add_remove_trait_effects(sim: Simulation) -> None:
    """Test that trait effects are added and removed with the trait."""

    character = spawn_character(sim.world)

    set_diplomacy_skill_base(character, 0)

    assert get_diplomacy_skill(character) == 0

    success = add_trait(character, "gullible")

    assert success is True
    assert get_diplomacy_skill(character) == 10

    success = remove_trait(character, "gullible")

    assert success is True
    assert get_diplomacy_skill(character) == 0


def test_try_add_conflicting_trait(sim: Simulation) -> None:
    """Test that adding a conflicting trait to a character fails"""

    character = spawn_character(sim.world)

    success = add_trait(character, "skeptical")

    assert success is True

    success = add_trait(character, "gullible")

    assert success is False

    success = add_trait(character, "skeptical")

    assert success is False


def test_trait_relationship_modifiers(sim: Simulation) -> None:
    """Test using traits with relationship modifiers."""

    c1 = spawn_character(sim.world)
    c2 = spawn_character(sim.world)

    assert get_attraction(c1, c2) == 0

    add_trait(c1, "flirtatious")

    assert get_attraction(c1, c2) == 10

    add_trait(c2, "charming")

    assert get_attraction(c1, c2) == 22

    remove_trait(c1, "flirtatious")

    assert get_attraction(c1, c2) == 12
