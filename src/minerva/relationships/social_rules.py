"""Built-in social rule implementations."""

from minerva.characters.components import Character
from minerva.ecs import GameObject
from minerva.relationships.base_types import (
    Relationship,
    RelationshipPrecondition,
    SocialRule,
)
from minerva.stats.base_types import StatModifierData, StatModifierType


class BelongToSameFamily(RelationshipPrecondition):
    """Checks if the owner and target belong to the same family."""

    def evaluate(self, relationship: GameObject) -> bool:
        relationship_component = relationship.get_component(Relationship)
        owner_character = relationship_component.owner.get_component(Character)
        target_character = relationship_component.target.get_component(Character)

        if owner_character.family is None or target_character.family is None:
            return False

        return owner_character.family == target_character.family


class BelongToSameBirthFamily(RelationshipPrecondition):
    """Checks if the owner and target belong to the same birth family."""

    def evaluate(self, relationship: GameObject) -> bool:
        relationship_component = relationship.get_component(Relationship)
        owner_character = relationship_component.owner.get_component(Character)
        target_character = relationship_component.target.get_component(Character)

        if (
            owner_character.birth_family is None
            or target_character.birth_family is None
        ):
            return False

        return owner_character.birth_family == target_character.birth_family


class TargetIsParent(RelationshipPrecondition):
    """Checks if the target is the owner's parent."""

    def evaluate(self, relationship: GameObject) -> bool:
        relationship_component = relationship.get_component(Relationship)
        owner_character = relationship_component.owner.get_component(Character)

        return (
            owner_character.mother == relationship_component.target
            or owner_character.father == relationship_component.target
        )


class TargetIsChild(RelationshipPrecondition):
    """Checks if the target is a child of the owner."""

    def evaluate(self, relationship: GameObject) -> bool:
        relationship_component = relationship.get_component(Relationship)
        owner_character = relationship_component.owner.get_component(Character)

        return relationship_component.target in owner_character.children


class TargetIsSibling(RelationshipPrecondition):
    """Checks if the owner and target are siblings."""

    def evaluate(self, relationship: GameObject) -> bool:
        relationship_component = relationship.get_component(Relationship)
        owner_character = relationship_component.owner.get_component(Character)

        return relationship_component.target in owner_character.siblings


class TargetIsSpouse(RelationshipPrecondition):
    """Check if the target is the owner's spouse."""

    def evaluate(self, relationship: GameObject) -> bool:
        relationship_component = relationship.get_component(Relationship)
        owner_character = relationship_component.owner.get_component(Character)

        return relationship_component.target == owner_character.spouse


reputation_boost_for_family = SocialRule(
    rule_id="boost_for_family_members",
    precondition=BelongToSameFamily(),
    modifiers={
        "Reputation": StatModifierData(
            modifier_type=StatModifierType.FLAT,
            value=10,
        )
    },
)

reputation_boost_for_birth_family = SocialRule(
    rule_id="boost_for_birth_family_members",
    precondition=BelongToSameBirthFamily(),
    modifiers={
        "Reputation": StatModifierData(
            modifier_type=StatModifierType.FLAT,
            value=5,
        )
    },
)

not_attracted_to_parents = SocialRule(
    "not_attracted_to_parents",
    precondition=TargetIsParent(),
    modifiers={
        "Romance": StatModifierData(
            modifier_type=StatModifierType.FLAT,
            value=-50,
        )
    },
)

reputation_boost_for_parents = SocialRule(
    "reputation_boost_for_parents",
    precondition=TargetIsParent(),
    modifiers={
        "Reputation": StatModifierData(
            modifier_type=StatModifierType.FLAT,
            value=10,
        )
    },
)

romance_drop_for_children = SocialRule(
    "romance_drop_for_children",
    precondition=TargetIsChild(),
    modifiers={
        "Romance": StatModifierData(
            modifier_type=StatModifierType.FLAT,
            value=-100,
        )
    },
)

reputation_boost_for_children = SocialRule(
    "reputation_boost_for_children",
    precondition=TargetIsChild(),
    modifiers={
        "Reputation": StatModifierData(
            modifier_type=StatModifierType.FLAT,
            value=10,
        )
    },
)

romance_drop_for_siblings = SocialRule(
    "romance_drop_for_siblings",
    precondition=TargetIsSibling(),
    modifiers={
        "Romance": StatModifierData(
            modifier_type=StatModifierType.FLAT,
            value=-50,
        )
    },
)

reputation_boost_for_siblings = SocialRule(
    "reputation_boost_for_siblings",
    precondition=TargetIsSibling(),
    modifiers={
        "Reputation": StatModifierData(
            modifier_type=StatModifierType.FLAT,
            value=10,
        )
    },
)

reputation_boost_for_spouse = SocialRule(
    "reputation_boost_for_spouse",
    precondition=TargetIsSpouse(),
    modifiers={
        "Reputation": StatModifierData(
            modifier_type=StatModifierType.FLAT,
            value=10,
        )
    },
)

romance_boost_for_spouse = SocialRule(
    "romance_boost_for_spouse",
    precondition=TargetIsSpouse(),
    modifiers={
        "Romance": StatModifierData(
            modifier_type=StatModifierType.FLAT,
            value=10,
        )
    },
)
