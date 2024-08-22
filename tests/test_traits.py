# pylint: disable=W0621
"""Test for Neighborly's Trait System."""

import pytest

from minerva.characters.components import Sociability
from minerva.ecs import World, GameObject
from minerva.effects.base_types import EffectLibrary
from minerva.effects.effects import (
    AddStatModifier,
    AddRelationshipModifier,
    RelationshipModifierDir,
)
from minerva.preconditions.base_types import PreconditionLibrary
from minerva.relationships.base_types import (
    Romance,
    add_relationship,
    RelationshipManager,
    SocialRuleLibrary,
)
from minerva.stats.base_types import (
    StatManager,
    StatusEffectManager,
    StatComponent,
    StatModifierType,
    StatModifierData,
)
from minerva.stats.helpers import get_stat, get_stat_value, get_relationship_stat_value
from minerva.traits.base_types import TraitLibrary, Trait, TraitManager
from minerva.traits.helpers import add_trait, has_trait, remove_trait


class Hunger(StatComponent):
    """Tracks a GameObject's hunger."""

    MAX_VALUE: int = 1000

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


@pytest.fixture
def world() -> World:
    """Create test world."""

    w = World()
    w.resources.add_resource(SocialRuleLibrary())
    w.resources.add_resource(PreconditionLibrary())
    w.resources.add_resource(EffectLibrary())
    w.resources.add_resource(TraitLibrary())
    w.resources.get_resource(TraitLibrary).add_trait(
        Trait(
            trait_id="flirtatious",
            name="Flirtatious",
            effects=[
                AddRelationshipModifier(
                    direction=RelationshipModifierDir.OUTGOING,
                    preconditions=[],
                    description="",
                    modifiers={
                        "Romance": StatModifierData(
                            modifier_type=StatModifierType.FLAT, value=10
                        )
                    },
                )
            ],
        )
    )
    w.resources.get_resource(TraitLibrary).add_trait(
        Trait(
            trait_id="charming",
            name="Charming",
            effects=[
                AddRelationshipModifier(
                    direction=RelationshipModifierDir.INCOMING,
                    preconditions=[],
                    description="",
                    modifiers={
                        "Romance": StatModifierData(
                            modifier_type=StatModifierType.FLAT, value=12
                        )
                    },
                )
            ],
        )
    )
    w.resources.get_resource(TraitLibrary).add_trait(
        Trait(
            trait_id="gullible",
            name="Gullible",
            effects=[
                AddStatModifier(
                    stat="Sociability",
                    label="",
                    modifier_type=StatModifierType.FLAT,
                    value=10,
                )
            ],
            conflicting_traits={"skeptical"},
        )
    )
    w.resources.get_resource(TraitLibrary).add_trait(
        Trait(
            trait_id="skeptical",
            name="Skeptical",
            effects=[
                AddStatModifier(
                    stat="Sociability",
                    label="",
                    modifier_type=StatModifierType.FLAT,
                    value=-10,
                )
            ],
            conflicting_traits={"gullible"},
        )
    )

    return w


def create_test_character(world: World) -> GameObject:
    """Creates a simplified character for testing."""

    return world.gameobjects.spawn_gameobject(
        components=[
            StatManager(),
            RelationshipManager(),
            StatusEffectManager(),
            TraitManager(),
            Hunger(0),
            Sociability(0),
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

    get_stat(farmer, "Sociability").base_value = 0

    success = add_trait(farmer, "gullible")

    assert success is True
    assert get_stat_value(farmer, Sociability) == 10

    success = remove_trait(farmer, "gullible")

    assert success is True
    assert get_stat_value(farmer, Sociability) == 0


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

    add_relationship(c1, c2)

    assert get_relationship_stat_value(c1, c2, Romance) == 0

    add_trait(c1, "flirtatious")

    assert get_relationship_stat_value(c1, c2, Romance) == 10

    add_trait(c2, "charming")

    assert get_relationship_stat_value(c1, c2, Romance) == 22

    remove_trait(c1, "flirtatious")

    assert get_relationship_stat_value(c1, c2, Romance) == 12
