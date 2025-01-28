# pylint: disable=W0621
"""Stat System Unit Tests."""

from __future__ import annotations

import enum

from minerva.ecs import Component, Entity, World
from minerva.relationships.base_types import (
    Attraction,
    Opinion,
    Relationship,
    RelationshipManager,
    RelationshipModifier,
    RelationshipPrecondition,
    SocialRule,
    SocialRuleLibrary,
)
from minerva.relationships.helpers import add_relationship, get_relationship
from minerva.relationships.preconditions import ConstantPrecondition
from minerva.simulation_events import SimulationEvents
from minerva.stats.base_types import (
    StatComponent,
    StatModifier,
    StatModifierType,
)
from minerva.stats.helpers import (
    default_stat_calc_strategy,
)


class Hunger(StatComponent):
    """Tracks an entity's hunger."""

    MAX_VALUE: int = 1000

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(
            default_stat_calc_strategy, base_value, (0, self.MAX_VALUE), True
        )


class HungerState(Component):
    """Tracks character's hunger state as a string"""

    __slots__ = ("state",)

    state: str

    def __init__(self) -> None:
        super().__init__()
        self.state = ""


class _ClanInfo(Component):
    """Info about a clan affiliation."""

    clan_name: str
    rival_clans: list[str]

    def __init__(self, clan_name: str, clan_rivals: list[str]) -> None:
        super().__init__()
        self.clan_name = clan_name
        self.rival_clans = clan_rivals


class _OpinionStateValue(enum.IntEnum):
    """Opinion state enum."""

    TERRIBLE = 0
    POOR = 1
    NEUTRAL = 2
    GOOD = 3
    EXCELLENT = 4


class _OpinionState(Component):
    """State of an opinion."""

    value: _OpinionStateValue

    def __init__(self, value: _OpinionStateValue = _OpinionStateValue.NEUTRAL) -> None:
        super().__init__()
        self.value = value


class RivalClansPrecondition(RelationshipPrecondition):
    """Checks if two characters belong to the same clan."""

    def evaluate(self, relationship: Entity) -> bool:
        relationship_component = relationship.get_component(Relationship)
        owner_rival_clans = relationship_component.owner.get_component(
            _ClanInfo
        ).rival_clans
        target_clan = relationship_component.target.get_component(_ClanInfo).clan_name

        return target_clan in owner_rival_clans


def test_get_stat() -> None:
    """Test stat get stat when changing base_value."""
    world = World()

    character = world.entity(components=[Hunger(0)])

    hunger = character.get_component(Hunger)

    hunger.base_value = 10

    assert hunger.base_value == 10
    assert hunger.value == 10

    hunger.base_value += 100

    assert hunger.base_value == 110
    assert hunger.value == 110


def test_stat_change_listener() -> None:
    """Test stat get stat when changing base_value."""
    world = World()

    def hunger_listener(entity: Entity, stat: StatComponent) -> None:
        hunger_intervals = [
            (200, "STARVING"),
            (100, "FAMISHED"),
            (50, "HUNGRY"),
            (0, "EXCELLENT"),
        ]

        for level, label in hunger_intervals:
            if stat.value >= level:
                entity.get_component(HungerState).state = label
                return

    character = world.entity(
        components=[
            Hunger(0),
            HungerState(),
        ]
    )

    hunger = character.get_component(Hunger)

    hunger.listeners.append(hunger_listener)

    hunger.base_value = 10

    assert hunger.value == 10
    assert character.get_component(HungerState).state == "EXCELLENT"

    hunger.base_value = 150

    assert hunger.value == 150
    assert character.get_component(HungerState).state == "FAMISHED"


def test_add_stat_modifier() -> None:
    """Test adding stat modifiers."""

    world = World()

    character = world.entity(components=[Hunger(0)])

    hunger = character.get_component(Hunger)

    hunger.base_value = 10

    hunger.add_modifier(StatModifier(50, StatModifierType.FLAT))

    assert hunger.value == 60

    hunger.add_modifier(StatModifier(0.5, StatModifierType.PERCENT))

    assert hunger.value == 90


def test_remove_stat_modifier() -> None:
    """Test removing stat modifiers."""

    world = World()

    character = world.entity(components=[Hunger(0)])

    hunger = character.get_component(Hunger)

    hunger.base_value = 10

    modifier = StatModifier(50, StatModifierType.FLAT)

    hunger.add_modifier(modifier)

    assert hunger.value == 60

    hunger.remove_modifier(modifier)

    assert hunger.value == 10


def test_get_relationship_stat() -> None:
    """Test getting stat of relationship and changing base value."""

    world = World()

    world.add_resource(SocialRuleLibrary())
    world.add_resource(SimulationEvents())

    c1 = world.entity(
        components=[
            Hunger(0),
            RelationshipManager(),
        ]
    )

    c2 = world.entity(
        components=[
            Hunger(0),
            RelationshipManager(),
        ]
    )

    relationship = add_relationship(c1, c2)
    opinion = relationship.get_component(Opinion)

    assert opinion.value == 0

    relationship.get_component(Opinion).base_value = 15

    assert opinion.value == 15


def test_get_modifier_to_relationship_stat() -> None:
    """Test getting stat of relationship and changing base value."""

    world = World()

    world.add_resource(SocialRuleLibrary())
    world.add_resource(SimulationEvents())

    c1 = world.entity(
        components=[
            Hunger(0),
            RelationshipManager(),
        ]
    )

    c2 = world.entity(
        components=[
            Hunger(0),
            RelationshipManager(),
        ]
    )

    relationship = add_relationship(c1, c2)
    opinion = relationship.get_component(Opinion)

    assert opinion.value == 0

    opinion.add_modifier(StatModifier(modifier_type=StatModifierType.FLAT, value=35))

    assert opinion.value == 35


def test_relationship_modifiers() -> None:
    """Test getting stat of relationship and changing base value."""

    world = World()

    world.add_resource(SocialRuleLibrary())
    world.add_resource(SimulationEvents())

    c1 = world.entity(
        components=[
            Hunger(0),
            RelationshipManager(),
        ]
    )

    c2 = world.entity(
        components=[
            Hunger(0),
            RelationshipManager(),
        ]
    )

    c1.get_component(RelationshipManager).outgoing_modifiers.append(
        RelationshipModifier(
            precondition=ConstantPrecondition(True),
            opinion_modifier=StatModifier(
                modifier_type=StatModifierType.FLAT,
                value=20,
            ),
        )
    )

    c2.get_component(RelationshipManager).incoming_modifiers.append(
        RelationshipModifier(
            precondition=ConstantPrecondition(True),
            attraction_modifier=StatModifier(
                modifier_type=StatModifierType.FLAT,
                value=12,
            ),
        )
    )

    relationship = get_relationship(c1, c2)
    opinion = relationship.get_component(Opinion)

    assert opinion.value == 20
    assert relationship.get_component(Attraction).value == 12


def test_social_rules() -> None:
    """Test getting stat of relationship and changing base value."""

    world = World()
    world.add_resource(SimulationEvents())

    social_rule_library = SocialRuleLibrary()
    world.add_resource(social_rule_library)
    social_rule_library.add_rule(
        SocialRule(
            rule_id="rival_clans_clash",
            precondition=RivalClansPrecondition(),
            opinion_modifier=StatModifier(
                modifier_type=StatModifierType.FLAT, value=-10
            ),
        )
    )

    c1 = world.entity(
        components=[
            Hunger(0),
            RelationshipManager(),
            _ClanInfo(clan_name="EagleClan", clan_rivals=["BadgerClan"]),
        ]
    )

    c2 = world.entity(
        components=[
            Hunger(0),
            RelationshipManager(),
            _ClanInfo(clan_name="BadgerClan", clan_rivals=["EagleClan"]),
        ]
    )

    c1.get_component(RelationshipManager).outgoing_modifiers.append(
        RelationshipModifier(
            precondition=ConstantPrecondition(True),
            opinion_modifier=StatModifier(
                modifier_type=StatModifierType.FLAT,
                value=20,
            ),
        )
    )

    c2.get_component(RelationshipManager).incoming_modifiers.append(
        RelationshipModifier(
            precondition=ConstantPrecondition(True),
            attraction_modifier=StatModifier(
                modifier_type=StatModifierType.FLAT,
                value=12,
            ),
        )
    )

    assert get_relationship(c1, c2).get_component(Opinion).value == 10


def test_relationship_stat_listener() -> None:
    """Test attaching listeners to relationship stats."""

    def opinion_listener(entity: Entity, stat: StatComponent) -> None:
        if not entity.has_component(_OpinionState):
            entity.add_component(_OpinionState())

        opinion_intervals = [
            (-75, _OpinionStateValue.TERRIBLE),
            (-25, _OpinionStateValue.POOR),
            (25, _OpinionStateValue.NEUTRAL),
            (75, _OpinionStateValue.GOOD),
            (100, _OpinionStateValue.EXCELLENT),
        ]

        for level, label in opinion_intervals:
            if stat.value <= level:
                entity.get_component(_OpinionState).value = label
                return

    world = World()

    world.add_resource(SocialRuleLibrary())
    world.add_resource(SimulationEvents())

    c1 = world.entity(
        components=[
            Hunger(0),
            RelationshipManager(),
        ]
    )

    c2 = world.entity(
        components=[
            Hunger(0),
            RelationshipManager(),
        ]
    )
    relationship = get_relationship(c1, c2)

    opinion = relationship.get_component(Opinion)

    opinion.listeners.append(opinion_listener)

    assert opinion.value == 0
    assert relationship.get_component(_OpinionState).value == _OpinionStateValue.NEUTRAL

    opinion.base_value = 80
    assert opinion.value == 80
    assert (
        relationship.get_component(_OpinionState).value == _OpinionStateValue.EXCELLENT
    )

    opinion.base_value = -60
    assert opinion.value == -60
    assert relationship.get_component(_OpinionState).value == _OpinionStateValue.POOR
