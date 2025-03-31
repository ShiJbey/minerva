"""Built-in Effect Types and Factories."""

from __future__ import annotations

from minerva.characters.helpers import (
    add_diplomacy_skill_modifier,
    add_fertility_modifier,
    add_intrigue_skill_modifier,
    add_lifespan_modifier,
    add_luck_skill_modifier,
    add_martial_skill_modifier,
    add_prowess_skill_modifier,
    add_stewardship_skill_modifier,
    remove_diplomacy_skill_modifier,
    remove_fertility_modifier,
    remove_intrigue_skill_modifier,
    remove_lifespan_modifier,
    remove_luck_skill_modifier,
    remove_martial_skill_modifier,
    remove_prowess_skill_modifier,
    remove_stewardship_skill_modifier,
)
from minerva.ecs import Entity
from minerva.stats.base_types import StatModifier
from minerva.traits.base_types import TraitEffect


class AddLifespanModifier(TraitEffect):
    """Add a modifier the lifespan stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        add_lifespan_modifier(target, self.modifier)

    def remove(self, target: Entity) -> None:
        remove_lifespan_modifier(target, self.modifier)


class AddFertilityModifier(TraitEffect):
    """Add a modifier the fertility stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        add_fertility_modifier(target, self.modifier)

    def remove(self, target: Entity) -> None:
        remove_fertility_modifier(target, self.modifier)


class AddStewardshipModifier(TraitEffect):
    """Add a modifier the stewardship stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        add_stewardship_skill_modifier(target, self.modifier)

    def remove(self, target: Entity) -> None:
        remove_stewardship_skill_modifier(target, self.modifier)


class AddMartialModifier(TraitEffect):
    """Add a modifier the martial stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        add_martial_skill_modifier(target, self.modifier)

    def remove(self, target: Entity) -> None:
        remove_martial_skill_modifier(target, self.modifier)


class AddIntrigueModifier(TraitEffect):
    """Add a modifier the intrigue stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        add_intrigue_skill_modifier(target, self.modifier)

    def remove(self, target: Entity) -> None:
        remove_intrigue_skill_modifier(target, self.modifier)


class AddProwessModifier(TraitEffect):
    """Add a modifier the prowess stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        add_prowess_skill_modifier(target, self.modifier)

    def remove(self, target: Entity) -> None:
        remove_prowess_skill_modifier(target, self.modifier)


class AddDiplomacyModifier(TraitEffect):
    """Add a modifier the diplomacy stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        add_diplomacy_skill_modifier(target, self.modifier)

    def remove(self, target: Entity) -> None:
        remove_diplomacy_skill_modifier(target, self.modifier)


class AddLuckModifier(TraitEffect):
    """Add a modifier the luck stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        add_luck_skill_modifier(target, self.modifier)

    def remove(self, target: Entity) -> None:
        remove_luck_skill_modifier(target, self.modifier)
