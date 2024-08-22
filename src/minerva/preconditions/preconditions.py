"""Built-in Precondition Types."""

from __future__ import annotations

import enum
from typing import Any

from minerva.characters.components import Character, LifeStage, Sex
from minerva.ecs import GameObject, World
from minerva.preconditions.base_types import Precondition, PreconditionFactory
from minerva.relationships.base_types import Relationship
from minerva.stats.helpers import get_stat, has_stat_with_name
from minerva.traits.helpers import has_trait


class HasTraitPrecondition(Precondition):
    """A precondition that check if a GameObject has a given trait."""

    __slots__ = ("trait",)

    trait: str
    """The ID of the trait to check for."""

    def __init__(
        self,
        trait: str,
    ) -> None:
        super().__init__()
        self.trait = trait

    @property
    def description(self) -> str:
        return f"requires a(n) {self.trait!r} trait"

    def check(self, gameobject: GameObject) -> bool:
        return has_trait(gameobject, self.trait)


class HasTraitPreconditionFactory(PreconditionFactory):
    """Creates HasTraitPrecondition instances."""

    def __init__(self) -> None:
        super().__init__("HasTrait")

    def instantiate(self, world: World, params: dict[str, Any]) -> Precondition:
        trait = params["trait"]
        return HasTraitPrecondition(trait=trait)


class OwnerHasTraitPrecondition(Precondition):
    """A precondition that check if a relationship's owner has a given trait."""

    __slots__ = ("trait",)

    trait: str
    """The ID of the trait to check for."""

    def __init__(
        self,
        trait: str,
    ) -> None:
        super().__init__()
        self.trait = trait

    @property
    def description(self) -> str:
        return f"requires relationship owner to have a(n) {self.trait!r} trait"

    def check(self, gameobject: GameObject) -> bool:
        return has_trait(gameobject.get_component(Relationship).owner, self.trait)


class OwnerHasTraitPreconditionFactory(PreconditionFactory):
    """Creates OwnerHasTraitPrecondition instances"""

    def __init__(self) -> None:
        super().__init__("OwnerHasTrait")

    def instantiate(self, world: World, params: dict[str, Any]) -> Precondition:
        trait = params["trait"]
        return OwnerHasTraitPrecondition(trait=trait)


class TargetHasTraitPrecondition(Precondition):
    """A precondition that check if a relationship's target has a given trait."""

    __slots__ = ("trait",)

    trait: str
    """The ID of the trait to check for."""

    def __init__(
        self,
        trait: str,
    ) -> None:
        super().__init__()
        self.trait = trait

    @property
    def description(self) -> str:
        return f"requires relationship target to have a(n) {self.trait!r} trait"

    def check(self, gameobject: GameObject) -> bool:
        return has_trait(gameobject.get_component(Relationship).target, self.trait)


class TargetHasTraitPreconditionFactory(PreconditionFactory):
    """Creates TargetHasTraitPrecondition instances"""

    def __init__(self) -> None:
        super().__init__("TargetHasTrait")

    def instantiate(self, world: World, params: dict[str, Any]) -> Precondition:
        trait = params["trait"]
        return TargetHasTraitPrecondition(trait=trait)


class AreSameSex(Precondition):
    """Checks if the owner and target of a relationship belong to the dame sex."""

    def __init__(self) -> None:
        super().__init__()

    @property
    def description(self) -> str:
        return "owner and target of the relationship are the same sex"

    def check(self, gameobject: GameObject) -> bool:
        relationship = gameobject.get_component(Relationship)

        owner_sex = relationship.owner.get_component(Character).sex
        target_sex = relationship.target.get_component(Character).sex

        return owner_sex == target_sex


class AreSameSexPreconditionFactory(PreconditionFactory):
    """Creates AreSameSex precondition instances."""

    def __init__(self) -> None:
        super().__init__("AreSameSex")

    def instantiate(self, world: World, params: dict[str, Any]) -> Precondition:
        return AreSameSex()


class AreOppositeSex(Precondition):
    """Checks if the owner and target of a relationship belong to the dame sex."""

    def __init__(self) -> None:
        super().__init__()

    @property
    def description(self) -> str:
        return "owner and target of the relationship are the opposite sex"

    def check(self, gameobject: GameObject) -> bool:
        relationship = gameobject.get_component(Relationship)

        owner_sex = relationship.owner.get_component(Character).sex
        target_sex = relationship.target.get_component(Character).sex

        return owner_sex != target_sex


class AreOppositeSexPreconditionFactory(PreconditionFactory):
    """Creates AreOppositeSex precondition instances."""

    def __init__(self) -> None:
        super().__init__("AreOppositeSex")

    def instantiate(self, world: World, params: dict[str, Any]) -> Precondition:
        return AreOppositeSex()


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


class StatRequirement(Precondition):
    """A precondition that requires a GameObject to have a certain stat value."""

    __slots__ = ("stat_name", "required_value", "comparator")

    stat_name: str
    """The name of the stat to check."""
    required_value: float
    """The skill level to check for."""
    comparator: ComparatorOp
    """Comparison for the skill level."""

    def __init__(
        self,
        stat: str,
        required_value: float,
        comparator: ComparatorOp,
    ) -> None:
        super().__init__()
        self.stat_name = stat
        self.required_value = required_value
        self.comparator = comparator

    @property
    def description(self) -> str:
        return (
            f"requires a(n) {self.stat_name} stat value of {self.comparator}"
            f" {self.required_value}"
        )

    def check(self, gameobject: GameObject) -> bool:
        if has_stat_with_name(gameobject, self.stat_name):
            stat = get_stat(gameobject, self.stat_name)

            if self.comparator == ComparatorOp.EQ:
                return stat.value == self.required_value

            elif self.comparator == ComparatorOp.NEQ:
                return stat.value != self.required_value

            elif self.comparator == ComparatorOp.LT:
                return stat.value < self.required_value

            elif self.comparator == ComparatorOp.GT:
                return stat.value > self.required_value

            elif self.comparator == ComparatorOp.LTE:
                return stat.value <= self.required_value

            elif self.comparator == ComparatorOp.GTE:
                return stat.value >= self.required_value

        return False


class StatRequirementPreconditionFactory(PreconditionFactory):
    """Creates StatRequirement precondition instances."""

    def __init__(self) -> None:
        super().__init__("StatRequirement")

    def instantiate(self, world: World, params: dict[str, Any]) -> Precondition:
        stat = params["stat"]
        value = params["value"]
        comparator = ComparatorOp[params.get("op", "gte").upper()]
        return StatRequirement(
            stat=stat,
            required_value=value,
            comparator=comparator,
        )


class OwnerStatRequirement(Precondition):
    """Check a relationship owner has a certain stat value."""

    __slots__ = ("stat_name", "required_value", "comparator")

    stat_name: str
    """The name of the stat to check."""
    required_value: float
    """The skill level to check for."""
    comparator: ComparatorOp
    """Comparison for the skill level."""

    def __init__(
        self,
        stat: str,
        required_value: float,
        comparator: ComparatorOp,
    ) -> None:
        super().__init__()
        self.stat_name = stat
        self.required_value = required_value
        self.comparator = comparator

    @property
    def description(self) -> str:
        return (
            f"requires a(n) {self.stat_name} stat value of {self.comparator}"
            f" {self.required_value}"
        )

    def check(self, gameobject: GameObject) -> bool:
        character = gameobject.get_component(Relationship).owner

        if has_stat_with_name(character, self.stat_name):
            stat = get_stat(character, self.stat_name)

            if self.comparator == ComparatorOp.EQ:
                return stat.value == self.required_value

            elif self.comparator == ComparatorOp.NEQ:
                return stat.value != self.required_value

            elif self.comparator == ComparatorOp.LT:
                return stat.value < self.required_value

            elif self.comparator == ComparatorOp.GT:
                return stat.value > self.required_value

            elif self.comparator == ComparatorOp.LTE:
                return stat.value <= self.required_value

            elif self.comparator == ComparatorOp.GTE:
                return stat.value >= self.required_value

        return False


class OwnerStatRequirementFactory(PreconditionFactory):
    """Creates AreSameSex precondition instances."""

    def __init__(self) -> None:
        super().__init__("OwnerStatRequirement")

    def instantiate(self, world: World, params: dict[str, Any]) -> Precondition:
        stat = params["stat"]
        value = params["value"]
        comparator = ComparatorOp[params.get("op", "gte").upper()]
        return OwnerStatRequirement(
            stat=stat,
            required_value=value,
            comparator=comparator,
        )


class TargetStatRequirement(Precondition):
    """Check a relationship target has a certain stat value."""

    __slots__ = ("stat_name", "required_value", "comparator")

    stat_name: str
    """The name of the stat to check."""
    required_value: float
    """The skill level to check for."""
    comparator: ComparatorOp
    """Comparison for the skill level."""

    def __init__(
        self,
        stat: str,
        required_value: float,
        comparator: ComparatorOp,
    ) -> None:
        super().__init__()
        self.stat_name = stat
        self.required_value = required_value
        self.comparator = comparator

    @property
    def description(self) -> str:
        return (
            f"requires a(n) {self.stat_name} stat value of {self.comparator}"
            f" {self.required_value}"
        )

    def check(self, gameobject: GameObject) -> bool:
        character = gameobject.get_component(Relationship).target

        if has_stat_with_name(character, self.stat_name):
            stat = get_stat(character, self.stat_name)

            if self.comparator == ComparatorOp.EQ:
                return stat.value == self.required_value

            elif self.comparator == ComparatorOp.NEQ:
                return stat.value != self.required_value

            elif self.comparator == ComparatorOp.LT:
                return stat.value < self.required_value

            elif self.comparator == ComparatorOp.GT:
                return stat.value > self.required_value

            elif self.comparator == ComparatorOp.LTE:
                return stat.value <= self.required_value

            elif self.comparator == ComparatorOp.GTE:
                return stat.value >= self.required_value

        return False


class TargetStatRequirementFactory(PreconditionFactory):
    """Creates TargetStatRequirement precondition instances."""

    def __init__(self) -> None:
        super().__init__("TargetStatRequirement")

    def instantiate(self, world: World, params: dict[str, Any]) -> Precondition:
        stat = params["stat"]
        value = params["value"]
        comparator = ComparatorOp[params.get("op", "gte").upper()]
        return TargetStatRequirement(
            stat=stat,
            required_value=value,
            comparator=comparator,
        )


class LifeStageRequirement(Precondition):
    """A precondition that requires a character to be at least a given life stage."""

    __slots__ = ("life_stage", "comparator")

    life_stage: LifeStage
    """The life stage to check for."""
    comparator: ComparatorOp
    """Comparison for the life stage."""

    def __init__(self, life_stage: LifeStage, comparator: ComparatorOp) -> None:
        super().__init__()
        self.life_stage = life_stage
        self.comparator = comparator

    @property
    def description(self) -> str:
        return f"requires a life stage {self.comparator} {self.life_stage.name}"

    def check(self, gameobject: GameObject) -> bool:
        character = gameobject.get_component(Character)

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

        return False


class LifeStageRequirementFactory(PreconditionFactory):
    """Creates LifeStageRequirement precondition instances."""

    def __init__(self) -> None:
        super().__init__("LifeStageRequirement")

    def instantiate(self, world: World, params: dict[str, Any]) -> Precondition:
        life_stage = LifeStage[params["life_stage"]]
        comparator = ComparatorOp[params.get("op", "gte").upper()]
        return LifeStageRequirement(life_stage=life_stage, comparator=comparator)


class OwnerLifeStageRequirement(Precondition):
    """A precondition that requires a relationship owner to be a given life stage."""

    __slots__ = ("life_stage", "comparator")

    life_stage: LifeStage
    """The life stage to check for."""
    comparator: ComparatorOp
    """Comparison for the life stage."""

    def __init__(self, life_stage: LifeStage, comparator: ComparatorOp) -> None:
        super().__init__()
        self.life_stage = life_stage
        self.comparator = comparator

    @property
    def description(self) -> str:
        return f"requires a life stage {self.comparator} {self.life_stage.name}"

    def check(self, gameobject: GameObject) -> bool:
        character = gameobject.get_component(Relationship).owner.get_component(
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


class OwnerLifeStageRequirementFactory(PreconditionFactory):
    """Creates OwnerLifeStageRequirement instances."""

    def __init__(self) -> None:
        super().__init__("OwnerLifeStageRequirement")

    def instantiate(self, world: World, params: dict[str, Any]) -> Precondition:
        life_stage = LifeStage[params["life_stage"]]
        comparator = ComparatorOp[params.get("op", "gte").upper()]
        return OwnerLifeStageRequirement(life_stage=life_stage, comparator=comparator)


class TargetLifeStageRequirement(Precondition):
    """A precondition that requires a relationship target to be a given life stage."""

    __slots__ = ("life_stage", "comparator")

    life_stage: LifeStage
    """The life stage to check for."""
    comparator: ComparatorOp
    """Comparison for the life stage."""

    def __init__(self, life_stage: LifeStage, comparator: ComparatorOp) -> None:
        super().__init__()
        self.life_stage = life_stage
        self.comparator = comparator

    @property
    def description(self) -> str:
        return f"requires a life stage {self.comparator} {self.life_stage.name}"

    def check(self, gameobject: GameObject) -> bool:
        character = gameobject.get_component(Relationship).target.get_component(
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


class TargetLifeStageRequirementFactory(PreconditionFactory):
    """Creates TargetLifeStageRequirement instances."""

    def __init__(self) -> None:
        super().__init__("TargetLifeStageRequirement")

    def instantiate(self, world: World, params: dict[str, Any]) -> Precondition:
        life_stage = LifeStage[params["life_stage"]]
        comparator = ComparatorOp[params.get("op", "gte").upper()]
        return TargetLifeStageRequirement(life_stage=life_stage, comparator=comparator)


class IsSex(Precondition):
    """A precondition that requires a character to belong to given sex."""

    __slots__ = ("sex",)

    sex: Sex

    def __init__(self, sex: Sex) -> None:
        super().__init__()
        self.sex = sex

    @property
    def description(self) -> str:
        return f"Character must be of the {self.sex.name} sex"

    def check(self, gameobject: GameObject) -> bool:
        return gameobject.get_component(Character).sex == self.sex


class IsSexPreconditionFactory(PreconditionFactory):
    """Create IsSex precondition instances."""

    def __init__(self) -> None:
        super().__init__("TargetIsSex")

    def instantiate(self, world: World, params: dict[str, Any]) -> Precondition:
        sex = Sex[params["sex"].upper()]
        return IsSex(sex=sex)


class OwnerIsSex(Precondition):
    """A precondition that requires a relationship owner to belong to given sex."""

    __slots__ = ("sex",)

    sex: Sex

    def __init__(self, sex: Sex) -> None:
        super().__init__()
        self.sex = sex

    @property
    def description(self) -> str:
        return f"Relationship owner must be of the {self.sex.name} sex"

    def check(self, gameobject: GameObject) -> bool:
        return (
            gameobject.get_component(Relationship).owner.get_component(Character).sex
            == self.sex
        )


class OwnerIsSexPreconditionFactory(PreconditionFactory):
    """Create OwnerIsSex precondition instances."""

    def __init__(self) -> None:
        super().__init__("OwnerIsSex")

    def instantiate(self, world: World, params: dict[str, Any]) -> Precondition:
        sex = Sex[params["sex"].upper()]
        return OwnerIsSex(sex=sex)


class TargetIsSex(Precondition):
    """A precondition that requires a relationship target to belong to given sex."""

    __slots__ = ("sex",)

    sex: Sex

    def __init__(self, sex: Sex) -> None:
        super().__init__()
        self.sex = sex

    @property
    def description(self) -> str:
        return f"Relationship target must be of the {self.sex.name} sex"

    def check(self, gameobject: GameObject) -> bool:
        return (
            gameobject.get_component(Relationship).target.get_component(Character).sex
            == self.sex
        )


class TargetIsSexPreconditionFactory(PreconditionFactory):
    """Creates TargetIsSex precondition instances."""

    def __init__(self) -> None:
        super().__init__("TargetIsSex")

    def instantiate(self, world: World, params: dict[str, Any]) -> Precondition:
        sex = Sex[params["sex"].upper()]
        return TargetIsSex(sex=sex)
