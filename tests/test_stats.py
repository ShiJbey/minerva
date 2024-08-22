# pylint: disable=W0621
"""Stat System Unit Tests."""

from __future__ import annotations

from minerva.ecs import Component, GameObject, World
from minerva.preconditions.base_types import Precondition
from minerva.relationships.base_types import (
    Relationship,
    RelationshipManager,
    RelationshipModifier,
    Reputation,
    Romance,
    SocialRule,
    SocialRuleLibrary,
    add_relationship,
    get_relationship,
)
from minerva.stats.base_types import (
    StatComponent,
    StatManager,
    StatModifier,
    StatModifierData,
    StatModifierType,
    StatusEffect,
    StatusEffectManager,
)
from minerva.stats.helpers import (
    add_stat_modifier,
    add_status_effect,
    get_relationship_stat_value,
    get_stat_value,
    has_stat_with_name,
    remove_stat_modifier,
    remove_status_effect,
)
from minerva.systems import TickStatusEffectSystem


class Hunger(StatComponent):
    """Tracks a GameObject's hunger."""

    MAX_VALUE: int = 1000

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class HungerState(Component):
    """Tracks character's hunger state as a string"""

    __slots__ = ("state",)

    state: str

    def __init__(self) -> None:
        super().__init__()
        self.state = ""


class HighMetabolismStatusEffect(StatusEffect):
    """Increases hunger."""

    def __init__(self, duration: int = 0) -> None:
        super().__init__("High Metabolism", "Increases hunger", duration)
        self.modifier = StatModifier(
            "High Metabolism", value=70, modifier_type=StatModifierType.FLAT
        )

    def apply(self, target: GameObject) -> None:
        add_stat_modifier(target, "Hunger", self.modifier)

    def remove(self, target: GameObject) -> None:
        remove_stat_modifier(target, "Hunger", self.modifier)


class RivalClansPrecondition(Precondition):
    """Checks if two characters belong to the same clan."""

    @property
    def description(self) -> str:
        return "Target belongs to a rival clan."

    def check(self, gameobject: GameObject) -> bool:
        relationship_component = gameobject.get_component(Relationship)
        owner_rival_clans = relationship_component.owner.metadata["clan_rivals"]
        target_clan = relationship_component.target.metadata["clan"]

        return target_clan in owner_rival_clans


def test_has_stat() -> None:
    """Test checking for stats."""
    world = World()

    character = world.gameobjects.spawn_gameobject(
        components=[StatManager(), Hunger(0)]
    )

    assert has_stat_with_name(character, "Hunger") is True

    assert has_stat_with_name(character, "Health") is False


def test_get_stat() -> None:
    """Test stat get stat when changing base_value."""
    world = World()

    character = world.gameobjects.spawn_gameobject(
        components=[StatManager(), Hunger(0)]
    )

    hunger = character.get_component(Hunger)

    hunger.base_value = 10

    assert hunger.base_value == 10
    assert get_stat_value(character, Hunger) == 10

    hunger.base_value += 100

    assert hunger.base_value == 110
    assert get_stat_value(character, Hunger) == 110


def test_stat_change_listener() -> None:
    """Test stat get stat when changing base_value."""
    world = World()

    def hunger_listener(gameobject: GameObject, stat: StatComponent) -> None:
        hunger_intervals = [
            (200, "STARVING"),
            (100, "FAMISHED"),
            (50, "HUNGRY"),
            (0, "EXCELLENT"),
        ]

        for level, label in hunger_intervals:
            if stat.value >= level:
                gameobject.get_component(HungerState).state = label
                return

    character = world.gameobjects.spawn_gameobject(
        components=[
            StatManager(),
            Hunger(0),
            StatusEffectManager(),
            HungerState(),
        ]
    )

    hunger = character.get_component(Hunger)

    hunger.listeners.append(hunger_listener)

    hunger.base_value = 10

    assert get_stat_value(character, Hunger) == 10
    assert character.get_component(HungerState).state == "EXCELLENT"

    hunger.base_value = 150

    assert get_stat_value(character, Hunger) == 150
    assert character.get_component(HungerState).state == "FAMISHED"


def test_add_stat_modifier() -> None:
    """Test adding stat modifiers."""

    world = World()

    character = world.gameobjects.spawn_gameobject(
        components=[StatManager(), Hunger(0)]
    )

    hunger = character.get_component(Hunger)

    hunger.base_value = 10

    hunger.add_modifier(StatModifier("extra-hungry", 50, StatModifierType.FLAT))

    assert get_stat_value(character, Hunger) == 60

    hunger.add_modifier(
        StatModifier("extra-extra-hungry", 0.5, StatModifierType.PERCENT)
    )

    assert get_stat_value(character, Hunger) == 90


def test_remove_stat_modifier() -> None:
    """Test removing stat modifiers."""

    world = World()

    character = world.gameobjects.spawn_gameobject(
        components=[StatManager(), Hunger(0)]
    )

    hunger = character.get_component(Hunger)

    hunger.base_value = 10

    modifier = StatModifier("extra-hungry", 50, StatModifierType.FLAT)

    hunger.add_modifier(modifier)

    assert get_stat_value(character, Hunger) == 60

    hunger.remove_modifier(modifier)

    assert get_stat_value(character, Hunger) == 10


def test_status_effect() -> None:
    """Test add status effect."""

    world = World()

    character = world.gameobjects.spawn_gameobject(
        components=[StatManager(), Hunger(0), StatusEffectManager()]
    )

    hunger = character.get_component(Hunger)

    hunger.base_value = 10

    assert get_stat_value(character, Hunger) == 10

    add_status_effect(character, HighMetabolismStatusEffect())

    assert get_stat_value(character, Hunger) == 80


def test_remove_status_effect() -> None:
    """Test manually removing a status effect."""

    world = World()

    character = world.gameobjects.spawn_gameobject(
        components=[StatManager(), Hunger(0), StatusEffectManager()]
    )

    hunger = character.get_component(Hunger)

    hunger.base_value = 10

    assert get_stat_value(character, Hunger) == 10

    status_effect = HighMetabolismStatusEffect()

    add_status_effect(character, status_effect)

    assert get_stat_value(character, Hunger) == 80

    remove_status_effect(character, status_effect)

    assert get_stat_value(character, Hunger) == 10


def test_status_effect_system() -> None:
    """Test that status effects are removed properly."""

    world = World()

    world.systems.add_system(TickStatusEffectSystem())

    character = world.gameobjects.spawn_gameobject(
        components=[StatManager(), Hunger(0), StatusEffectManager()]
    )

    hunger = character.get_component(Hunger)

    hunger.base_value = 10

    assert get_stat_value(character, Hunger) == 10

    status_effect = HighMetabolismStatusEffect(duration=1)

    add_status_effect(character, status_effect)

    assert get_stat_value(character, Hunger) == 80

    world.step()

    world.step()

    assert get_stat_value(character, Hunger) == 10


def test_get_relationship_stat() -> None:
    """Test getting stat of relationship and changing base value."""

    world = World()

    world.systems.add_system(TickStatusEffectSystem())
    world.resources.add_resource(SocialRuleLibrary())

    c1 = world.gameobjects.spawn_gameobject(
        components=[
            StatManager(),
            Hunger(0),
            StatusEffectManager(),
            RelationshipManager(),
        ]
    )

    c2 = world.gameobjects.spawn_gameobject(
        components=[
            StatManager(),
            Hunger(0),
            StatusEffectManager(),
            RelationshipManager(),
        ]
    )

    relationship = add_relationship(c1, c2)

    assert get_relationship_stat_value(c1, c2, Reputation) == 0

    relationship.get_component(Reputation).base_value = 15

    assert get_relationship_stat_value(c1, c2, Reputation) == 15


def test_get_modifier_to_relationship_stat() -> None:
    """Test getting stat of relationship and changing base value."""

    world = World()

    world.systems.add_system(TickStatusEffectSystem())
    world.resources.add_resource(SocialRuleLibrary())

    c1 = world.gameobjects.spawn_gameobject(
        components=[
            StatManager(),
            Hunger(0),
            StatusEffectManager(),
            RelationshipManager(),
        ]
    )

    c2 = world.gameobjects.spawn_gameobject(
        components=[
            StatManager(),
            Hunger(0),
            StatusEffectManager(),
            RelationshipManager(),
        ]
    )

    relationship = add_relationship(c1, c2)

    assert get_relationship_stat_value(c1, c2, Reputation) == 0

    relationship.get_component(Reputation).add_modifier(
        StatModifier(modifier_type=StatModifierType.FLAT, value=35, label="")
    )

    assert get_relationship_stat_value(c1, c2, Reputation) == 35


def test_relationship_modifiers() -> None:
    """Test getting stat of relationship and changing base value."""

    world = World()

    world.systems.add_system(TickStatusEffectSystem())
    world.resources.add_resource(SocialRuleLibrary())

    c1 = world.gameobjects.spawn_gameobject(
        components=[
            StatManager(),
            Hunger(0),
            StatusEffectManager(),
            RelationshipManager(),
        ]
    )

    c2 = world.gameobjects.spawn_gameobject(
        components=[
            StatManager(),
            Hunger(0),
            StatusEffectManager(),
            RelationshipManager(),
        ]
    )

    c1.get_component(RelationshipManager).outgoing_modifiers.append(
        RelationshipModifier(
            description="Friendly",
            preconditions=[],
            modifiers={
                "Reputation": StatModifierData(
                    modifier_type=StatModifierType.FLAT,
                    value=20,
                )
            },
        )
    )

    c2.get_component(RelationshipManager).incoming_modifiers.append(
        RelationshipModifier(
            description="Attractive",
            preconditions=[],
            modifiers={
                "Romance": StatModifierData(
                    modifier_type=StatModifierType.FLAT,
                    value=12,
                )
            },
        )
    )

    assert get_relationship_stat_value(c1, c2, Reputation) == 20
    assert get_relationship_stat_value(c1, c2, Romance) == 12


def test_social_rules() -> None:
    """Test getting stat of relationship and changing base value."""

    world = World()

    world.systems.add_system(TickStatusEffectSystem())
    social_rule_library = SocialRuleLibrary()
    world.resources.add_resource(social_rule_library)
    social_rule_library.rules.append(
        SocialRule(
            label="RivalClans",
            preconditions=[RivalClansPrecondition()],
            modifiers={
                "Reputation": StatModifierData(
                    modifier_type=StatModifierType.FLAT, value=-10
                )
            },
        )
    )

    c1 = world.gameobjects.spawn_gameobject(
        components=[
            StatManager(),
            Hunger(0),
            StatusEffectManager(),
            RelationshipManager(),
        ]
    )
    c1.metadata["clan"] = "EagleClan"
    c1.metadata["clan_rivals"] = "BadgerClan"

    c2 = world.gameobjects.spawn_gameobject(
        components=[
            StatManager(),
            Hunger(0),
            StatusEffectManager(),
            RelationshipManager(),
        ]
    )
    c2.metadata["clan"] = "BadgerClan"
    c2.metadata["clan_rivals"] = "EagleClan"

    c1.get_component(RelationshipManager).outgoing_modifiers.append(
        RelationshipModifier(
            description="Friendly",
            preconditions=[],
            modifiers={
                "Reputation": StatModifierData(
                    modifier_type=StatModifierType.FLAT,
                    value=20,
                )
            },
        )
    )

    c2.get_component(RelationshipManager).incoming_modifiers.append(
        RelationshipModifier(
            description="Attractive",
            preconditions=[],
            modifiers={
                "Romance": StatModifierData(
                    modifier_type=StatModifierType.FLAT,
                    value=12,
                )
            },
        )
    )

    assert get_relationship_stat_value(c1, c2, Reputation) == 10


def test_relationship_stat_listener() -> None:
    """Test attaching listeners to relationship stats."""

    def reputation_listener(gameobject: GameObject, stat: StatComponent) -> None:
        reputation_intervals = [
            (-75, "TERRIBLE"),
            (-25, "POOR"),
            (25, "NEUTRAL"),
            (75, "GOOD"),
            (100, "EXCELLENT"),
        ]

        for level, label in reputation_intervals:
            if stat.value <= level:
                gameobject.metadata["reputation_state"] = label
                return

    world = World()

    world.systems.add_system(TickStatusEffectSystem())
    world.resources.add_resource(SocialRuleLibrary())

    c1 = world.gameobjects.spawn_gameobject(
        components=[
            StatManager(),
            Hunger(0),
            StatusEffectManager(),
            RelationshipManager(),
        ]
    )

    c2 = world.gameobjects.spawn_gameobject(
        components=[
            StatManager(),
            Hunger(0),
            StatusEffectManager(),
            RelationshipManager(),
        ]
    )
    relationship = get_relationship(c1, c2)

    reputation = relationship.get_component(Reputation)

    reputation.listeners.append(reputation_listener)

    assert get_relationship_stat_value(c1, c2, Reputation) == 0
    assert relationship.metadata["reputation_state"] == "NEUTRAL"

    reputation.base_value = 80
    assert get_relationship_stat_value(c1, c2, Reputation) == 80
    assert relationship.metadata["reputation_state"] == "EXCELLENT"

    reputation.base_value = -60
    assert get_relationship_stat_value(c1, c2, Reputation) == -60
    assert relationship.metadata["reputation_state"] == "POOR"
