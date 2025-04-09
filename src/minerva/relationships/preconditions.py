"""Built-in RelationshipPrecondition Types."""

from __future__ import annotations

import enum

from minerva.characters.components import Character, CharacterStat, LifeStage, Sex
from minerva.characters.helpers import (
    get_diplomacy_skill,
    get_intrigue_skill,
    get_luck_skill,
    get_martial_skill,
    get_prowess_skill,
)
from minerva.ecs import Entity
from minerva.relationships.base_types import Relationship, RelationshipPrecondition
from minerva.traits.helpers import has_trait


class RelationshipHasTrait(RelationshipPrecondition):
    """A RelationshipPrecondition that check if an entity has a given trait."""

    __slots__ = ("trait",)

    trait: str
    """The ID of the trait to check for."""

    def __init__(
        self,
        trait: str,
    ) -> None:
        super().__init__()
        self.trait = trait

    def __call__(self, relationship: Entity) -> bool:
        return has_trait(relationship, self.trait)


class OwnerHasTrait(RelationshipPrecondition):
    """A RelationshipPrecondition that check if a relationship's owner has a given trait."""

    __slots__ = ("trait",)

    trait: str
    """The ID of the trait to check for."""

    def __init__(
        self,
        trait: str,
    ) -> None:
        super().__init__()
        self.trait = trait

    def __call__(self, relationship: Entity) -> bool:
        return has_trait(relationship.get_component(Relationship).owner, self.trait)


class TargetHasTrait(RelationshipPrecondition):
    """A RelationshipPrecondition that check if a relationship's target has a given trait."""

    __slots__ = ("trait",)

    trait: str
    """The ID of the trait to check for."""

    def __init__(
        self,
        trait: str,
    ) -> None:
        super().__init__()
        self.trait = trait

    def __call__(self, relationship: Entity) -> bool:
        return has_trait(relationship.get_component(Relationship).target, self.trait)


class AreSameSex(RelationshipPrecondition):
    """Checks if the owner and target of a relationship belong to the dame sex."""

    def __call__(self, relationship: Entity) -> bool:
        relationship_component = relationship.get_component(Relationship)

        owner_sex = relationship_component.owner.get_component(Character).sex
        target_sex = relationship_component.target.get_component(Character).sex

        return owner_sex == target_sex


class AreOppositeSex(RelationshipPrecondition):
    """Checks if the owner and target of a relationship belong to the dame sex."""

    def __call__(self, relationship: Entity) -> bool:
        relationship_component = relationship.get_component(Relationship)

        owner_sex = relationship_component.owner.get_component(Character).sex
        target_sex = relationship_component.target.get_component(Character).sex

        return owner_sex != target_sex


class ComparatorOp(enum.Enum):
    """Comparator Operators."""

    EQ = enum.auto()
    """Equal to."""
    NEQ = enum.auto()
    """Not equal to."""
    LT = enum.auto()
    """Less than."""
    GT = enum.auto()
    """Greater than."""
    LTE = enum.auto()
    """Less than or equal to."""
    GTE = enum.auto()
    """Greater than or equal to."""

    def __str__(self) -> str:
        if self.value == ComparatorOp.EQ:
            return "equal to"

        elif self.value == ComparatorOp.NEQ:
            return "not equal to"

        elif self.value == ComparatorOp.LT:
            return "less than"

        elif self.value == ComparatorOp.GT:
            return "greater than"

        elif self.value == ComparatorOp.LTE:
            return "less than or equal to"

        elif self.value == ComparatorOp.GTE:
            return "greater than or equal to"

        else:
            return self.name


class OwnerStatRequirement(RelationshipPrecondition):
    """Check a relationship owner has a certain stat value."""

    __slots__ = ("stat", "required_value", "comparator")

    stat: CharacterStat
    """The name of the stat to check."""
    required_value: float
    """The skill level to check for."""
    comparator: ComparatorOp
    """Comparison for the skill level."""

    def __init__(
        self,
        stat: CharacterStat,
        required_value: float,
        comparator: ComparatorOp,
    ) -> None:
        super().__init__()
        self.stat = stat
        self.required_value = required_value
        self.comparator = comparator

    def __call__(self, relationship: Entity) -> bool:
        character = relationship.get_component(Relationship).owner

        if self.stat == CharacterStat.MARTIAL:
            stat_value = get_martial_skill(character)
        elif self.stat == CharacterStat.INTRIGUE:
            stat_value = get_intrigue_skill(character)
        elif self.stat == CharacterStat.PROWESS:
            stat_value = get_prowess_skill(character)
        elif self.stat == CharacterStat.DIPLOMACY:
            stat_value = get_diplomacy_skill(character)
        elif self.stat == CharacterStat.LUCK:
            stat_value = get_luck_skill(character)
        else:
            raise ValueError(f"Unsupported stat for op: {self.stat}.")

        if self.comparator == ComparatorOp.EQ:
            return stat_value == self.required_value

        elif self.comparator == ComparatorOp.NEQ:
            return stat_value != self.required_value

        elif self.comparator == ComparatorOp.LT:
            return stat_value < self.required_value

        elif self.comparator == ComparatorOp.GT:
            return stat_value > self.required_value

        elif self.comparator == ComparatorOp.LTE:
            return stat_value <= self.required_value

        elif self.comparator == ComparatorOp.GTE:
            return stat_value >= self.required_value

        return False


class TargetStatRequirement(RelationshipPrecondition):
    """Check a relationship target has a certain stat value."""

    __slots__ = ("stat", "required_value", "comparator")

    stat: CharacterStat
    """The name of the stat to check."""
    required_value: float
    """The skill level to check for."""
    comparator: ComparatorOp
    """Comparison for the skill level."""

    def __init__(
        self,
        stat: CharacterStat,
        required_value: float,
        comparator: ComparatorOp,
    ) -> None:
        super().__init__()
        self.stat = stat
        self.required_value = required_value
        self.comparator = comparator

    def __call__(self, relationship: Entity) -> bool:
        character = relationship.get_component(Relationship).target

        if self.stat == CharacterStat.MARTIAL:
            stat_value = get_martial_skill(character)
        elif self.stat == CharacterStat.INTRIGUE:
            stat_value = get_intrigue_skill(character)
        elif self.stat == CharacterStat.PROWESS:
            stat_value = get_prowess_skill(character)
        elif self.stat == CharacterStat.DIPLOMACY:
            stat_value = get_diplomacy_skill(character)
        elif self.stat == CharacterStat.LUCK:
            stat_value = get_luck_skill(character)
        else:
            raise ValueError(f"Unsupported stat for op: {self.stat}.")

        if self.comparator == ComparatorOp.EQ:
            return stat_value == self.required_value

        elif self.comparator == ComparatorOp.NEQ:
            return stat_value != self.required_value

        elif self.comparator == ComparatorOp.LT:
            return stat_value < self.required_value

        elif self.comparator == ComparatorOp.GT:
            return stat_value > self.required_value

        elif self.comparator == ComparatorOp.LTE:
            return stat_value <= self.required_value

        elif self.comparator == ComparatorOp.GTE:
            return stat_value >= self.required_value

        return False


class OwnerLifeStageRequirement(RelationshipPrecondition):
    """A RelationshipPrecondition that requires a relationship owner to be a given life stage."""

    __slots__ = ("life_stage", "comparator")

    life_stage: LifeStage
    """The life stage to check for."""
    comparator: ComparatorOp
    """Comparison for the life stage."""

    def __init__(self, life_stage: LifeStage, comparator: ComparatorOp) -> None:
        super().__init__()
        self.life_stage = life_stage
        self.comparator = comparator

    def __call__(self, relationship: Entity) -> bool:
        character = relationship.get_component(Relationship).owner.get_component(
            Character
        )

        if self.comparator == ComparatorOp.EQ:
            return character.life_stage == self.life_stage

        elif self.comparator == ComparatorOp.NEQ:
            return character.life_stage != self.life_stage

        elif self.comparator == ComparatorOp.LT:
            return character.life_stage < self.life_stage

        elif self.comparator == ComparatorOp.GT:
            return character.life_stage > self.life_stage

        elif self.comparator == ComparatorOp.LTE:
            return character.life_stage <= self.life_stage

        elif self.comparator == ComparatorOp.GTE:
            return character.life_stage >= self.life_stage

        else:
            return False


class TargetLifeStageRequirement(RelationshipPrecondition):
    """A RelationshipPrecondition that requires a relationship target to be a given life stage."""

    __slots__ = ("life_stage", "comparator")

    life_stage: LifeStage
    """The life stage to check for."""
    comparator: ComparatorOp
    """Comparison for the life stage."""

    def __init__(self, life_stage: LifeStage, comparator: ComparatorOp) -> None:
        super().__init__()
        self.life_stage = life_stage
        self.comparator = comparator

    def __call__(self, relationship: Entity) -> bool:
        character = relationship.get_component(Relationship).target.get_component(
            Character
        )

        if self.comparator == ComparatorOp.EQ:
            return character.life_stage == self.life_stage

        elif self.comparator == ComparatorOp.NEQ:
            return character.life_stage != self.life_stage

        elif self.comparator == ComparatorOp.LT:
            return character.life_stage < self.life_stage

        elif self.comparator == ComparatorOp.GT:
            return character.life_stage > self.life_stage

        elif self.comparator == ComparatorOp.LTE:
            return character.life_stage <= self.life_stage

        elif self.comparator == ComparatorOp.GTE:
            return character.life_stage >= self.life_stage

        else:
            return False


class OwnerIsSex(RelationshipPrecondition):
    """A RelationshipPrecondition that requires a relationship owner to belong to given sex."""

    __slots__ = ("sex",)

    sex: Sex

    def __init__(self, sex: Sex) -> None:
        super().__init__()
        self.sex = sex

    def __call__(self, relationship: Entity) -> bool:
        return (
            relationship.get_component(Relationship).owner.get_component(Character).sex
            == self.sex
        )


class TargetIsSex(RelationshipPrecondition):
    """A RelationshipPrecondition that requires a relationship target to belong to given sex."""

    __slots__ = ("sex",)

    sex: Sex

    def __init__(self, sex: Sex) -> None:
        super().__init__()
        self.sex = sex

    def __call__(self, relationship: Entity) -> bool:
        return (
            relationship.get_component(Relationship).target.get_component(Character).sex
            == self.sex
        )


class BelongToSameFamily(RelationshipPrecondition):
    """Checks if the owner and target belong to the same family."""

    def __call__(self, relationship: Entity) -> bool:
        relationship_component = relationship.get_component(Relationship)
        owner_character = relationship_component.owner.get_component(Character)
        target_character = relationship_component.target.get_component(Character)

        if owner_character.family is None or target_character.family is None:
            return False

        return owner_character.family == target_character.family


class BelongToSameBirthFamily(RelationshipPrecondition):
    """Checks if the owner and target belong to the same birth family."""

    def __call__(self, relationship: Entity) -> bool:
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

    def __call__(self, relationship: Entity) -> bool:
        relationship_component = relationship.get_component(Relationship)
        owner_character = relationship_component.owner.get_component(Character)

        return (
            owner_character.mother == relationship_component.target
            or owner_character.father == relationship_component.target
        )


class TargetIsChild(RelationshipPrecondition):
    """Checks if the target is a child of the owner."""

    def __call__(self, relationship: Entity) -> bool:
        relationship_component = relationship.get_component(Relationship)
        owner_character = relationship_component.owner.get_component(Character)

        return relationship_component.target in owner_character.children


class TargetIsSibling(RelationshipPrecondition):
    """Checks if the owner and target are siblings."""

    def __call__(self, relationship: Entity) -> bool:
        relationship_component = relationship.get_component(Relationship)
        owner_character = relationship_component.owner.get_component(Character)

        return relationship_component.target in owner_character.siblings


class TargetIsSpouse(RelationshipPrecondition):
    """Check if the target is the owner's spouse."""

    def __call__(self, relationship: Entity) -> bool:
        relationship_component = relationship.get_component(Relationship)
        owner_character = relationship_component.owner.get_component(Character)

        return relationship_component.target == owner_character.spouse
