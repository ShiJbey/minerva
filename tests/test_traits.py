# pylint: disable=W0621
"""Test for Neighborly's Trait System."""

import pytest

from minerva.characters.components import Sociability
from minerva.ecs import Entity, World
from minerva.relationships.base_types import (
    Attraction,
    RelationshipManager,
    RelationshipModifier,
    SocialRuleLibrary,
)
from minerva.relationships.helpers import add_relationship
from minerva.relationships.preconditions import ConstantPrecondition
from minerva.sim_db import SimDB
from minerva.simulation_events import SimulationEvents
from minerva.stats.base_types import (
    StatComponent,
    StatModifier,
    StatModifierType,
    StatusEffectManager,
)
from minerva.stats.helpers import default_stat_calc_strategy
from minerva.traits.base_types import Trait, TraitLibrary, TraitManager
from minerva.traits.effects import (
    AddIncomingRelationshipModifier,
    AddOutgoingRelationshipModifier,
    AddSociabilityModifier,
)
from minerva.traits.helpers import add_trait, has_trait, remove_trait


class Hunger(StatComponent):
    """Tracks an entity's hunger."""

    MAX_VALUE: int = 1000

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(
            default_stat_calc_strategy, base_value, (0, self.MAX_VALUE), True
        )


@pytest.fixture
def world() -> World:
    """Create test world."""

    w = World()
    w.add_resource(SimDB())
    w.add_resource(SimulationEvents())
    w.add_resource(SocialRuleLibrary())
    w.add_resource(TraitLibrary())
    w.get_resource(TraitLibrary).add_trait(
        Trait(
            trait_id="flirtatious",
            name="Flirtatious",
            effects=[
                AddOutgoingRelationshipModifier(
                    RelationshipModifier(
                        precondition=ConstantPrecondition(True),
                        attraction_modifier=StatModifier(
                            modifier_type=StatModifierType.FLAT, value=10
                        ),
                    )
                )
            ],
        )
    )
    w.get_resource(TraitLibrary).add_trait(
        Trait(
            trait_id="charming",
            name="Charming",
            effects=[
                AddIncomingRelationshipModifier(
                    RelationshipModifier(
                        precondition=ConstantPrecondition(True),
                        attraction_modifier=StatModifier(12),
                    )
                )
            ],
        )
    )
    w.get_resource(TraitLibrary).add_trait(
        Trait(
            trait_id="gullible",
            name="Gullible",
            effects=[
                AddSociabilityModifier(StatModifier(10)),
            ],
            conflicting_traits=["skeptical"],
        )
    )
    w.get_resource(TraitLibrary).add_trait(
        Trait(
            trait_id="skeptical",
            name="Skeptical",
            effects=[
                AddSociabilityModifier(StatModifier(-10)),
            ],
            conflicting_traits=["gullible"],
        )
    )

    return w


def create_test_character(world: World) -> Entity:
    """Creates a simplified character for testing."""

    return world.entity(
        components=[
            RelationshipManager(),
            StatusEffectManager(),
            TraitManager(),
            Hunger(0),
            Sociability(default_stat_calc_strategy),
        ]
    )


def test_add_trait(world: World) -> None:
    """Test that adding a trait makes it visible with has_trait."""

    character = create_test_character(world)

    assert has_trait(character, "flirtatious") is False

    success = add_trait(character, "flirtatious")

    assert success is True


def test_remove_trait(world: World) -> None:
    """Test that removing a trait makes it not available to has_trait."""

    character = create_test_character(world)

    assert has_trait(character, "flirtatious") is False

    add_trait(character, "flirtatious")

    assert has_trait(character, "flirtatious") is True

    success = remove_trait(character, "flirtatious")

    assert success is True


def test_add_remove_trait_effects(world: World) -> None:
    """Test that trait effects are added and removed with the trait."""

    farmer = create_test_character(world)

    sociability = farmer.get_component(Sociability)

    sociability.base_value = 0

    success = add_trait(farmer, "gullible")

    assert success is True
    assert sociability.value == 10

    success = remove_trait(farmer, "gullible")

    assert success is True
    assert sociability.value == 0


def test_try_add_conflicting_trait(world: World) -> None:
    """Test that adding a conflicting trait to a character fails"""

    character = create_test_character(world)

    success = add_trait(character, "skeptical")

    assert success is True

    success = add_trait(character, "gullible")

    assert success is False

    success = add_trait(character, "skeptical")

    assert success is False


def test_trait_relationship_modifiers(world: World) -> None:
    """Test using traits with relationship modifiers."""

    c1 = create_test_character(world)
    c2 = create_test_character(world)

    relationship = add_relationship(c1, c2)
    attraction = relationship.get_component(Attraction)

    assert attraction.value == 0

    add_trait(c1, "flirtatious")

    assert attraction.value == 10

    add_trait(c2, "charming")

    assert attraction.value == 22

    remove_trait(c1, "flirtatious")

    assert attraction.value == 12
