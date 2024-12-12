"""Built-in Effect Types and Factories."""

from __future__ import annotations

from minerva.characters.components import (
    Boldness,
    Compassion,
    Diplomacy,
    Fertility,
    Greed,
    Honor,
    Intelligence,
    Intrigue,
    Lifespan,
    Luck,
    Martial,
    Prowess,
    Rationality,
    RomancePropensity,
    Sociability,
    Stewardship,
    Vengefulness,
)
from minerva.ecs import Entity
from minerva.relationships.base_types import RelationshipManager, RelationshipModifier
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
        target.get_component(Lifespan).add_modifier(self.modifier)

    def remove(self, target: Entity) -> None:
        target.get_component(Lifespan).remove_modifier(self.modifier)


class AddFertilityModifier(TraitEffect):
    """Add a modifier the fertility stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        target.get_component(Fertility).add_modifier(self.modifier)

    def remove(self, target: Entity) -> None:
        target.get_component(Fertility).remove_modifier(self.modifier)


class AddStewardshipModifier(TraitEffect):
    """Add a modifier the stewardship stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        target.get_component(Stewardship).add_modifier(self.modifier)

    def remove(self, target: Entity) -> None:
        target.get_component(Stewardship).remove_modifier(self.modifier)


class AddMartialModifier(TraitEffect):
    """Add a modifier the martial stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        target.get_component(Martial).add_modifier(self.modifier)

    def remove(self, target: Entity) -> None:
        target.get_component(Martial).remove_modifier(self.modifier)


class AddIntrigueModifier(TraitEffect):
    """Add a modifier the intrigue stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        target.get_component(Intrigue).add_modifier(self.modifier)

    def remove(self, target: Entity) -> None:
        target.get_component(Intrigue).remove_modifier(self.modifier)


class AddIntelligenceModifier(TraitEffect):
    """Add a modifier the intelligence stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        target.get_component(Intelligence).add_modifier(self.modifier)

    def remove(self, target: Entity) -> None:
        target.get_component(Intelligence).remove_modifier(self.modifier)


class AddProwessModifier(TraitEffect):
    """Add a modifier the prowess stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        target.get_component(Prowess).add_modifier(self.modifier)

    def remove(self, target: Entity) -> None:
        target.get_component(Prowess).remove_modifier(self.modifier)


class AddSociabilityModifier(TraitEffect):
    """Add a modifier the sociability stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        target.get_component(Sociability).add_modifier(self.modifier)

    def remove(self, target: Entity) -> None:
        target.get_component(Sociability).remove_modifier(self.modifier)


class AddHonorModifier(TraitEffect):
    """Add a modifier the honor stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        target.get_component(Honor).add_modifier(self.modifier)

    def remove(self, target: Entity) -> None:
        target.get_component(Honor).remove_modifier(self.modifier)


class AddBoldnessModifier(TraitEffect):
    """Add a modifier the boldness stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        target.get_component(Boldness).add_modifier(self.modifier)

    def remove(self, target: Entity) -> None:
        target.get_component(Boldness).remove_modifier(self.modifier)


class AddCompassionModifier(TraitEffect):
    """Add a modifier the compassion stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        target.get_component(Compassion).add_modifier(self.modifier)

    def remove(self, target: Entity) -> None:
        target.get_component(Compassion).remove_modifier(self.modifier)


class AddDiplomacyModifier(TraitEffect):
    """Add a modifier the diplomacy stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        target.get_component(Diplomacy).add_modifier(self.modifier)

    def remove(self, target: Entity) -> None:
        target.get_component(Diplomacy).remove_modifier(self.modifier)


class AddGreedModifier(TraitEffect):
    """Add a modifier the greed stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        target.get_component(Greed).add_modifier(self.modifier)

    def remove(self, target: Entity) -> None:
        target.get_component(Greed).remove_modifier(self.modifier)


class AddRationalityModifier(TraitEffect):
    """Add a modifier the rationality stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        target.get_component(Rationality).add_modifier(self.modifier)

    def remove(self, target: Entity) -> None:
        target.get_component(Rationality).remove_modifier(self.modifier)


class AddVengefulnessModifier(TraitEffect):
    """Add a modifier the vengefulness stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        target.get_component(Vengefulness).add_modifier(self.modifier)

    def remove(self, target: Entity) -> None:
        target.get_component(Vengefulness).remove_modifier(self.modifier)


class AddRomancePropensityModifier(TraitEffect):
    """Add a modifier the romance propensity stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        target.get_component(RomancePropensity).add_modifier(self.modifier)

    def remove(self, target: Entity) -> None:
        target.get_component(RomancePropensity).remove_modifier(self.modifier)


class AddLuckModifier(TraitEffect):
    """Add a modifier the luck stat."""

    __slots__ = ("modifier",)

    modifier: StatModifier

    def __init__(self, modifier: StatModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        target.get_component(Luck).add_modifier(self.modifier)

    def remove(self, target: Entity) -> None:
        target.get_component(Luck).remove_modifier(self.modifier)


class AddIncomingRelationshipModifier(TraitEffect):
    """Adds a relationship modifier to the GamObject."""

    __slots__ = ("modifier",)

    modifier: RelationshipModifier

    def __init__(self, modifier: RelationshipModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        relationship_manager = target.get_component(RelationshipManager)
        relationship_manager.incoming_modifiers.append(self.modifier)

    def remove(self, target: Entity) -> None:
        relationship_manager = target.get_component(RelationshipManager)
        relationship_manager.incoming_modifiers.remove(self.modifier)


class AddOutgoingRelationshipModifier(TraitEffect):
    """Adds a relationship modifier to the GamObject."""

    __slots__ = ("modifier",)

    modifier: RelationshipModifier

    def __init__(self, modifier: RelationshipModifier) -> None:
        super().__init__()
        self.modifier = modifier

    def apply(self, target: Entity) -> None:
        relationship_manager = target.get_component(RelationshipManager)
        relationship_manager.outgoing_modifiers.append(self.modifier)

    def remove(self, target: Entity) -> None:
        relationship_manager = target.get_component(RelationshipManager)
        relationship_manager.outgoing_modifiers.remove(self.modifier)
