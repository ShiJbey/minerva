"""Relationship Traits."""

from minerva.ecs import World
from minerva.traits.base_types import RelationshipTrait, RelationshipTraitDatabase
from minerva.traits.effects import IncrementOpinionEffect

RELATIONSHIP_TRAITS: list[RelationshipTrait] = [
    RelationshipTrait(
        trait_id="parent",
        name="Parent",
    ),
    RelationshipTrait(
        trait_id="mother",
        name="Mother",
    ),
    RelationshipTrait(
        trait_id="father",
        name="Father",
    ),
    RelationshipTrait(
        trait_id="biological_father",
        name="Biological Father",
    ),
    RelationshipTrait(
        trait_id="sibling",
        name="Sibling",
    ),
    RelationshipTrait(
        trait_id="child",
        name="child",
    ),
    RelationshipTrait(
        trait_id="grandchild",
        name="Grandchild",
    ),
    RelationshipTrait(
        trait_id="grandparent",
        name="Grandparent",
    ),
    RelationshipTrait(
        trait_id="spouse",
        name="Spouse",
    ),
    RelationshipTrait(
        trait_id="ex_spouse",
        name="Ex-Spouse",
    ),
    RelationshipTrait(
        trait_id="heir",
        name="Heir",
    ),
    RelationshipTrait(
        trait_id="heir_to",
        name="Heir To",
    ),
    RelationshipTrait(
        trait_id="vendetta",
        name="Vendetta",
        effects=[IncrementOpinionEffect(-20)],
    ),
]


def load_traits(world: World) -> None:
    """Load trait data."""
    trait_db = world.get_resource(RelationshipTraitDatabase)
    for entry in RELATIONSHIP_TRAITS:
        trait_db.add_trait(entry)
