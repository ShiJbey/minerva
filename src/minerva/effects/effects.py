"""Built-in Effect Types and Factories."""

from __future__ import annotations

import enum
import sys
from typing import Any, Iterable

from pydantic import ValidationError

from minerva.ecs import GameObject, World
from minerva.effects.base_types import Effect, EffectFactory
from minerva.preconditions.base_types import Precondition, PreconditionLibrary
from minerva.relationships.base_types import RelationshipManager, RelationshipModifier
from minerva.relationships.helpers import remove_stat_modifier
from minerva.stats.base_types import StatModifier, StatModifierData, StatModifierType
from minerva.stats.helpers import add_stat_modifier


class AddStatModifier(Effect):
    """Add a modifier to a stat."""

    __slots__ = ("stat", "modifier")

    stat: str
    modifier: StatModifier

    def __init__(
        self,
        stat: str,
        label: str,
        value: float,
        modifier_type: StatModifierType,
    ) -> None:
        super().__init__()
        self.stat = stat
        self.modifier = StatModifier(
            label=label, value=value, modifier_type=modifier_type
        )

    def get_description(self) -> str:
        sign = "+" if self.modifier.value > 0 else "-"
        percent_sign = (
            "%" if self.modifier.modifier_type == StatModifierType.PERCENT else ""
        )
        return f"{sign}{abs(self.modifier.value)}{percent_sign} {self.stat}"

    def apply(self, target: GameObject) -> None:
        add_stat_modifier(target, self.stat, self.modifier)

    def remove(self, target: GameObject) -> None:
        remove_stat_modifier(target, self.stat, self.modifier)


class AddMotiveModifier(Effect):
    """Adds a modifier to a character motive."""

    __slots__ = ("motive_name", "modifier")

    def __init__(
        self,
        motive_name: str,
        label: str,
        value: float,
        modifier_type: StatModifierType,
    ) -> None:
        super().__init__()
        self.motive_name = motive_name.lower()
        self.modifier = StatModifier(
            label=label, value=value, modifier_type=modifier_type
        )

    def get_description(self) -> str:
        sign = "+" if self.modifier.value > 0 else "-"
        percent_sign = (
            "%" if self.modifier.modifier_type == StatModifierType.PERCENT else ""
        )
        return f"{sign}{abs(self.modifier.value)}{percent_sign} {self.motive_name}"

    def apply(self, target: GameObject) -> None:
        # character_motives = target.get_component(CharacterMotives)

        if self.motive_name == "money":
            # character_motives.money.add_modifier(self.modifier)
            pass
        elif self.motive_name == "power":
            # character_motives.power.add_modifier(self.modifier)
            pass
        elif self.motive_name == "respect":
            # character_motives.respect.add_modifier(self.modifier)
            pass
        elif self.motive_name == "happiness":
            # character_motives.happiness.add_modifier(self.modifier)
            pass
        elif self.motive_name == "family":
            # character_motives.family.add_modifier(self.modifier)
            pass
        elif self.motive_name == "honor":
            # character_motives.honor.add_modifier(self.modifier)
            pass
        elif self.motive_name == "lust":
            # character_motives.lust.add_modifier(self.modifier)
            pass
        elif self.motive_name == "dread":
            # character_motives.dread.add_modifier(self.modifier)
            pass
        else:
            raise ValueError(f"Unrecognized character motive name: {self.motive_name}")

    def remove(self, target: GameObject) -> None:
        if self.motive_name == "money":
            # character_motives.money.remove_modifier(self.modifier)
            pass
        elif self.motive_name == "power":
            # character_motives.power.remove_modifier(self.modifier)
            pass
        elif self.motive_name == "respect":
            # character_motives.respect.remove_modifier(self.modifier)
            pass
        elif self.motive_name == "happiness":
            # character_motives.happiness.remove_modifier(self.modifier)
            pass
        elif self.motive_name == "family":
            # character_motives.family.remove_modifier(self.modifier)
            pass
        elif self.motive_name == "honor":
            # character_motives.honor.remove_modifier(self.modifier)
            pass
        elif self.motive_name == "lust":
            # character_motives.lust.remove_modifier(self.modifier)
            pass
        elif self.motive_name == "dread":
            # character_motives.dread.remove_modifier(self.modifier)
            pass
        else:
            raise ValueError(f"Unrecognized character motive name: {self.motive_name}")


class AddCharacterStatModifier(Effect):
    """Adds a modifier to a character stat."""

    __slots__ = ("stat_name", "modifier")

    def __init__(
        self,
        stat_name: str,
        label: str,
        value: float,
        modifier_type: StatModifierType,
    ) -> None:
        super().__init__()
        self.stat_name = stat_name.lower()
        self.modifier = StatModifier(
            label=label, value=value, modifier_type=modifier_type
        )

    def get_description(self) -> str:
        sign = "+" if self.modifier.value > 0 else "-"
        percent_sign = (
            "%" if self.modifier.modifier_type == StatModifierType.PERCENT else ""
        )
        return f"{sign}{abs(self.modifier.value)}{percent_sign} {self.stat_name}"

    def apply(self, target: GameObject) -> None:
        # character_stats = target.get_component(CharacterStats)

        if self.stat_name == "lifespan":
            # character_stats.lifespan.add_modifier(self.modifier)
            pass
        elif self.stat_name == "fertility":
            # character_stats.power.add_modifier(self.modifier)
            pass
        elif self.stat_name == "martial":
            # character_stats.respect.add_modifier(self.modifier)
            pass
        elif self.stat_name == "stewardship":
            # character_stats.happiness.add_modifier(self.modifier)
            pass
        elif self.stat_name == "intrigue":
            # character_stats.family.add_modifier(self.modifier)
            pass
        elif self.stat_name == "learning":
            # character_stats.honor.add_modifier(self.modifier)
            pass
        elif self.stat_name == "prowess":
            # character_stats.lust.add_modifier(self.modifier)
            pass
        elif self.stat_name == "dread":
            # character_stats.dread.add_modifier(self.modifier)
            pass
        else:
            raise ValueError(f"Unrecognized character stat name: {self.stat_name}")

    def remove(self, target: GameObject) -> None:
        if self.stat_name == "money":
            # character_stats.money.remove_modifier(self.modifier)
            pass
        elif self.stat_name == "power":
            # character_stats.power.remove_modifier(self.modifier)
            pass
        elif self.stat_name == "respect":
            # character_stats.respect.remove_modifier(self.modifier)
            pass
        elif self.stat_name == "happiness":
            # character_stats.happiness.remove_modifier(self.modifier)
            pass
        elif self.stat_name == "family":
            # character_stats.family.remove_modifier(self.modifier)
            pass
        elif self.stat_name == "honor":
            # character_stats.honor.remove_modifier(self.modifier)
            pass
        elif self.stat_name == "lust":
            # character_stats.lust.remove_modifier(self.modifier)
            pass
        elif self.stat_name == "dread":
            # character_stats.dread.remove_modifier(self.modifier)
            pass
        else:
            raise ValueError(f"Unrecognized character stat name: {self.stat_name}")


class AddStatModifierFactory(EffectFactory):
    """Creates AddStatModifier effect instances."""

    def __init__(self):
        super().__init__("AddStatModifier")

    def instantiate(self, world: World, params: dict[str, Any]) -> Effect:
        modifier_name: str = params.get("modifier_type", "FLAT")
        value: float = float(params["value"])
        stat: str = str(params["stat"])
        label: str = params.get("label", "")

        modifier_type = StatModifierType[modifier_name.upper()]

        return AddStatModifier(
            label=label,
            stat=stat,
            value=value,
            modifier_type=modifier_type,
        )


class RelationshipModifierDir(enum.Enum):
    """Relationship Modifier Direction."""

    OUTGOING = enum.auto()
    INCOMING = enum.auto()


class AddRelationshipModifier(Effect):
    """Adds a relationship modifier to the GamObject."""

    __effect_name__ = "AddRelationshipModifier"

    __slots__ = ("direction", "modifier")

    direction: RelationshipModifierDir
    modifier: RelationshipModifier

    def __init__(
        self,
        direction: RelationshipModifierDir,
        description: str,
        preconditions: Iterable[Precondition],
        modifiers: dict[str, StatModifierData],
    ) -> None:
        super().__init__()
        self.direction = direction
        self.modifier = RelationshipModifier(
            description=description,
            preconditions=list(preconditions),
            modifiers=modifiers,
        )

    def get_description(self) -> str:
        return self.modifier.description

    def apply(self, target: GameObject) -> None:
        relationship_manager = target.get_component(RelationshipManager)

        if self.direction == RelationshipModifierDir.OUTGOING:
            relationship_manager.outgoing_modifiers.append(self.modifier)
        else:
            relationship_manager.incoming_modifiers.append(self.modifier)

    def remove(self, target: GameObject) -> None:
        relationship_manager = target.get_component(RelationshipManager)

        if self.direction == RelationshipModifierDir.OUTGOING:
            relationship_manager.outgoing_modifiers.remove(self.modifier)
        else:
            relationship_manager.incoming_modifiers.remove(self.modifier)


class AddRelationshipModifierFactory(EffectFactory):
    """Creates AddRelationshipModifier effect instances."""

    def __init__(self) -> None:
        super().__init__("AddRelationshipModifier")

    def instantiate(self, world: World, params: dict[str, Any]) -> Effect:
        modifier_dir = RelationshipModifierDir[
            str(params.get("direction", "OUTGOING")).upper()
        ]
        description = params.get("description", "")

        precondition_library = world.resources.get_resource(PreconditionLibrary)
        preconditions: list[Precondition] = []
        for entry in params.get("preconditions", []):
            preconditions.append(precondition_library.create_from_obj(world, entry))

        modifier_data: dict[str, dict[str, Any]] = params.get("modifiers", {})
        modifiers: dict[str, StatModifierData] = {}
        for stat_name, data in modifier_data.items():
            try:
                modifiers[stat_name] = StatModifierData.model_validate(data)
            except ValidationError as exc:
                error_dict = exc.errors()[0]
                if error_dict["type"] == "missing":
                    print(
                        f"ERROR: Missing required field '{error_dict["loc"][0]}' "
                        f"for {stat_name} stat modifier in '{AddRelationshipModifier}' "
                    )
                    sys.exit(1)

        return AddRelationshipModifier(
            direction=modifier_dir,
            description=description,
            preconditions=preconditions,
            modifiers=modifiers,
        )
