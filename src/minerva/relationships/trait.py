"""Relationship Traits.

Permanent tags attached to relationship entities.
"""

from minerva.status.data import StatusData
from minerva.traits.base_types import RelationshipTrait

RELATIONSHIP_TRAITS: list[RelationshipTrait] = [
    RelationshipTrait(
        trait_id="mother",
        name="Mother",
    ),
    RelationshipTrait(
        trait_id="father",
        name="Father",
    ),
    RelationshipTrait(
        trait_id="biologicalFather",
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
]


RELATIONSHIP_STATUSES: list[StatusData] = [
    StatusData(
        status_id="spouse",
        name="Spouse",
    ),
    StatusData(
        status_id="heir",
        name="Heir",
    ),
    StatusData(
        status_id="heir_to",
        name="Heir To",
    ),
]
