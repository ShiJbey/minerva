"""Built-in social rule implementations."""

from minerva.relationships.base_types import RelationshipModifier
from minerva.relationships.preconditions import (
    BelongToSameBirthFamily,
    BelongToSameFamily,
    TargetIsChild,
    TargetIsParent,
    TargetIsSibling,
    TargetIsSpouse,
)

OPINION_RULES: list[RelationshipModifier] = [
    RelationshipModifier(10).where(BelongToSameFamily()),
    RelationshipModifier(5).where(BelongToSameBirthFamily()),
    RelationshipModifier(10).where(TargetIsParent()),
    RelationshipModifier(10).where(TargetIsChild()),
    RelationshipModifier(10).where(TargetIsSibling()),
    RelationshipModifier(10).where(TargetIsSpouse()),
]

ATTRACTION_RULES: list[RelationshipModifier] = [
    RelationshipModifier(-50).where(TargetIsParent()),
    RelationshipModifier(-100).where(TargetIsChild()),
    RelationshipModifier(-50).where(TargetIsSibling()),
    RelationshipModifier(10).where(TargetIsSpouse()),
]
